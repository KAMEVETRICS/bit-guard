from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .audit import audit_bundle, redact_bundle
from .config import RuntimeConfig, load_runtime_config
from .database import init_database, read_usage_records_db, ready_status, record_audit_run, record_usage
from .env import collector_secret_status, intelligence_secret_status, load_dotenv
from .intelligence import intelligence_bundle
from .market import enrich_public_market_context
from .validation import ValidationError, validate_evidence_bundle
from .web import DASHBOARD_HTML

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}
SENSITIVE_POSTS = {"/api/audit", "/api/intelligence", "/api/redact"}
SENSITIVE_GETS = {"/api/usage"}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Any | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


class AppHandler(BaseHTTPRequestHandler):
    server_version = "BitGuardSentinel/0.1"
    log_path = "logs/usage.jsonl"
    db_path = "data/bitguard.db"
    rate_buckets: dict[str, list[float]] = {}

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_OPTIONS(self) -> None:
        self._begin_request()
        self._send_empty(204)

    def do_GET(self) -> None:
        self._begin_request()
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_text(_landing_html(), content_type="text/html; charset=utf-8")
            return
        if parsed.path in {"/dashboard", "/code.html"}:
            self._send_text(DASHBOARD_HTML, content_type="text/html; charset=utf-8")
            return
        if parsed.path in {"/style.css", "/screen.png", "/bg.png"}:
            self._send_static(ROOT_DIR / parsed.path.lstrip("/"))
            return
        if parsed.path == "/api/health":
            self._send_json(_health_payload())
            return
        if parsed.path == "/api/ready":
            self._send_json(_ready_payload())
            return
        if parsed.path == "/api/usage":
            if not self._authorize_sensitive() or not self._check_rate_limit():
                return
            query = parse_qs(parsed.query)
            limit = _safe_int(query.get("limit", ["50"])[0], 50)
            self._send_json({"ok": True, "records": read_usage_records_db(load_runtime_config().db_path, limit=limit)})
            return
        self._send_error(404, "not_found", "Route not found.")

    def do_POST(self) -> None:
        self._begin_request()
        parsed = urlparse(self.path)
        if parsed.path not in SENSITIVE_POSTS:
            self._send_error(404, "not_found", "Route not found.")
            return
        if not self._authorize_sensitive() or not self._check_rate_limit():
            return

        try:
            payload = self._read_json()
            if parsed.path == "/api/audit":
                validate_evidence_bundle(payload)
                enriched = enrich_public_market_context(payload)
                result = audit_bundle(enriched)
                record_usage(load_runtime_config().db_path, "api.sentinel.audit", _usage_request(enriched), result["summary"])
                record_audit_run(load_runtime_config().db_path, self.request_id, result)
                self._send_json(result)
                return
            if parsed.path == "/api/intelligence":
                validate_evidence_bundle(payload)
                enriched = enrich_public_market_context(payload)
                result = intelligence_bundle(enriched)
                record_usage(
                    load_runtime_config().db_path,
                    "api.sentinel.intelligence",
                    _usage_request(enriched),
                    {
                        "symbol": result["symbol"],
                        "brief_status": result["brief"]["status"],
                        "truenorth_status": result["truenorth"]["status"],
                        "perception_verdict": result["audit"]["summary"].get("perception_verdict"),
                    },
                )
                record_audit_run(load_runtime_config().db_path, self.request_id, result["audit"])
                self._send_json(result)
                return
            if parsed.path == "/api/redact":
                if not isinstance(payload, dict):
                    raise ApiError(422, "validation_error", "Payload must be a JSON object.")
                self._send_json(redact_bundle(payload))
                return
        except ValidationError as exc:
            self._send_error(422, "validation_error", "Evidence bundle failed schema validation.", exc.errors)
        except ApiError as exc:
            self._send_error(exc.status, exc.code, exc.message, exc.details)
        except Exception as exc:
            self._send_error(400, "bad_request", str(exc))

    def _begin_request(self) -> None:
        self.request_id = uuid.uuid4().hex[:16]
        self.auth_token = ""

    def _read_json(self) -> Any:
        content_type = self.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            raise ApiError(415, "unsupported_media_type", "Use content-type: application/json.")
        raw_length = self.headers.get("content-length", "")
        if not raw_length:
            raise ApiError(400, "missing_content_length", "Missing content-length header.")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ApiError(400, "bad_content_length", "Invalid content-length header.") from exc
        max_body = load_runtime_config().max_body_bytes
        if length > max_body:
            raise ApiError(413, "payload_too_large", f"Request body exceeds {max_body} bytes.")
        body = self.rfile.read(length).decode("utf-8-sig")
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise ApiError(400, "invalid_json", "Request body is not valid JSON.") from exc

    def _authorize_sensitive(self) -> bool:
        config = load_runtime_config()
        if not config.require_auth:
            return True
        header = self.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            self._send_error(401, "auth_required", "Missing bearer token.")
            return False
        token = token.strip()
        for candidate in config.api_keys:
            if hmac.compare_digest(token, candidate):
                self.auth_token = token
                return True
        self._send_error(403, "auth_invalid", "Bearer token is invalid.")
        return False

    def _check_rate_limit(self) -> bool:
        config = load_runtime_config()
        limit = config.rate_limit_per_minute
        key = self._rate_limit_key()
        now = time.monotonic()
        window_start = now - 60
        bucket = [stamp for stamp in self.rate_buckets.get(key, []) if stamp >= window_start]
        if len(bucket) >= limit:
            self.rate_buckets[key] = bucket
            self._send_error(429, "rate_limited", "Too many requests. Try again shortly.", {"limit_per_minute": limit})
            return False
        bucket.append(now)
        self.rate_buckets[key] = bucket
        return True

    def _rate_limit_key(self) -> str:
        if self.auth_token:
            token_hash = hashlib.sha256(self.auth_token.encode("utf-8")).hexdigest()[:16]
            return f"token:{token_hash}"
        return f"ip:{self.client_address[0]}"

    def _send_json(self, payload: Any, status: int = 200) -> None:
        if isinstance(payload, dict):
            body_payload = {"request_id": self.request_id, **payload}
        else:
            body_payload = {"request_id": self.request_id, "data": payload}
        body = json.dumps(body_payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self._send_common_headers("application/json", len(body), api_response=True)
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, code: str, message: str, details: Any | None = None) -> None:
        error = {"code": code, "message": message}
        if details is not None:
            error["details"] = details
        self._send_json({"ok": False, "error": error}, status=status)

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self._send_common_headers("text/plain", 0, api_response=True)
        self.end_headers()

    def _send_static(self, path: Path) -> None:
        resolved = path.resolve()
        if not resolved.is_file() or ROOT_DIR not in resolved.parents:
            self._send_error(404, "not_found", "Static asset not found.")
            return
        body = resolved.read_bytes()
        content_type = STATIC_TYPES.get(resolved.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        self._send_common_headers(content_type, len(body), api_response=False)
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, body: str, content_type: str = "text/plain") -> None:
        payload = body.encode("utf-8")
        self.send_response(200)
        self._send_common_headers(content_type, len(payload), api_response=False)
        self.end_headers()
        self.wfile.write(payload)

    def _send_common_headers(self, content_type: str, content_length: int, api_response: bool) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("X-Request-ID", self.request_id)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        if api_response:
            self.send_header("Cache-Control", "no-store")
        origin = self._allowed_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")

    def _allowed_origin(self) -> str:
        config = load_runtime_config()
        origin = self.headers.get("origin", "")
        if "*" in config.cors_origins:
            return "*"
        if origin and origin in config.cors_origins:
            return origin
        if not config.cors_origins:
            return "*"
        return ""


def run_server(host: str, port: int, log_path: str) -> None:
    load_dotenv(".env")
    config = load_runtime_config()
    init_database(config.db_path)
    AppHandler.log_path = log_path
    AppHandler.db_path = config.db_path
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"BitGuard Sentinel running at http://{host}:{port}")
    print(f"SQLite usage records: {config.db_path}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _landing_html() -> str:
    path = ROOT_DIR / "index.html"
    html = path.read_text(encoding="utf-8-sig")
    return (
        html.replace('href="style.css"', 'href="/style.css"')
        .replace('href="code.html"', 'href="/dashboard"')
        .replace('src="screen.png"', 'src="/screen.png"')
    )


def _health_payload() -> dict[str, Any]:
    config = load_runtime_config()
    return {
        "ok": True,
        "service": "bitguard-sentinel",
        "mode": "log-audit",
        "auth": {"required": config.require_auth, "configured": bool(config.api_keys)},
        "api_keys_required_by_dashboard": False,
        "supported_sources": ["bitget-readonly-export", "demo-agent-log-schema"],
        "public_market_data": {"provider": "bitget", "auto_fetch_candles": config.public_candle_fetch_enabled},
        "local_collector_credentials": _public_secret_status(collector_secret_status()),
        "optional_intelligence_credentials": _public_secret_status(intelligence_secret_status()),
        "routes": {
            "landing": "/",
            "dashboard": "/dashboard",
            "audit": "/api/audit",
            "intelligence": "/api/intelligence",
            "ready": "/api/ready",
        },
    }


def _ready_payload() -> dict[str, Any]:
    config = load_runtime_config()
    database = ready_status(config.db_path)
    auth_ready = (not config.require_auth) or bool(config.api_keys)
    return {
        "ok": bool(database["ok"] and auth_ready),
        "service": "bitguard-sentinel",
        "database": database,
        "auth": {"required": config.require_auth, "configured": bool(config.api_keys)},
        "config_loaded": True,
        "public_market_data": {"provider": "bitget", "auto_fetch_candles": config.public_candle_fetch_enabled},
    }


def _public_secret_status(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{"key": row.get("key"), "present": bool(row.get("present"))} for row in rows]


def _usage_request(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": payload.get("source", "unknown"),
        "demo_only": bool(payload.get("demo_only", False)),
        "agent_id": payload.get("agent_id", "unknown-agent"),
        "run_id": payload.get("run_id", "unknown-run"),
    }


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default