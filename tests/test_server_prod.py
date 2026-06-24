import contextlib
import json
import os
import threading
import uuid
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from bitguard.server import AppHandler



def _db_path() -> str:
    Path("data").mkdir(exist_ok=True)
    return str(Path("data") / f"test_server_{uuid.uuid4().hex}.db")
def _bundle() -> dict:
    return {
        "source": "demo-agent-log-schema",
        "demo_only": True,
        "agent_id": "agent-http",
        "run_id": "run-http",
        "product_type": "USDT-FUTURES",
        "fills": [
            {"symbol": "BTCUSDT", "side": "buy", "price": 65000, "quantity": 0.01, "timestamp": "2026-06-24T10:00:00Z"},
            {"symbol": "BTCUSDT", "side": "sell", "price": 65300, "quantity": 0.01, "timestamp": "2026-06-24T10:30:00Z"},
        ],
    }


@contextlib.contextmanager
def _patched_env(**updates):
    old = {key: os.environ.get(key) for key in updates}
    for key, value in updates.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(value)
    try:
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextlib.contextmanager
def _server():
    AppHandler.rate_buckets = {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), AppHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _request(method: str, url: str, payload=None, token: str | None = None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {}
    if payload is not None:
        headers["content-type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


class ServerProductionTest(unittest.TestCase):
    def test_auth_rejects_missing_token(self):
        with _patched_env(
            BITGUARD_REQUIRE_AUTH="1",
            BITGUARD_API_KEYS="secret-token",
            BITGUARD_DB_PATH=_db_path(),
            BITGUARD_FETCH_PUBLIC_CANDLES="0",
        ), _server() as base:
            status, data = _request("POST", f"{base}/api/audit", _bundle())

        self.assertEqual(status, 401)
        self.assertEqual(data["error"]["code"], "auth_required")

    def test_auth_accepts_valid_bearer_token(self):
        with _patched_env(
            BITGUARD_REQUIRE_AUTH="1",
            BITGUARD_API_KEYS="secret-token",
            BITGUARD_DB_PATH=_db_path(),
            BITGUARD_FETCH_PUBLIC_CANDLES="0",
        ), _server() as base:
            status, data = _request("POST", f"{base}/api/audit", _bundle(), token="secret-token")

        self.assertEqual(status, 200)
        self.assertEqual(data["agent_id"], "agent-http")
        self.assertEqual(data["summary"]["completed_trades"], 1)

    def test_rate_limiter_returns_429(self):
        with _patched_env(
            BITGUARD_REQUIRE_AUTH="1",
            BITGUARD_API_KEYS="secret-token",
            BITGUARD_DB_PATH=_db_path(),
            BITGUARD_FETCH_PUBLIC_CANDLES="0",
            BITGUARD_RATE_LIMIT_PER_MINUTE="1",
        ), _server() as base:
            first_status, _ = _request("POST", f"{base}/api/audit", _bundle(), token="secret-token")
            second_status, second_data = _request("POST", f"{base}/api/audit", _bundle(), token="secret-token")

        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 429)
        self.assertEqual(second_data["error"]["code"], "rate_limited")

    def test_dashboard_api_works_with_auth_disabled(self):
        with _patched_env(
            BITGUARD_REQUIRE_AUTH="0",
            BITGUARD_API_KEYS=None,
            BITGUARD_DB_PATH=_db_path(),
            BITGUARD_FETCH_PUBLIC_CANDLES="0",
            BITGUARD_RATE_LIMIT_PER_MINUTE="60",
        ), _server() as base:
            ready_status, ready = _request("GET", f"{base}/api/ready")
            audit_status, audit = _request("POST", f"{base}/api/audit", _bundle())

        self.assertEqual(ready_status, 200)
        self.assertTrue(ready["ok"])
        self.assertEqual(audit_status, 200)
        self.assertEqual(audit["summary"]["completed_trades"], 1)

    def test_usage_endpoint_reads_sqlite_records(self):
        with _patched_env(
            BITGUARD_REQUIRE_AUTH="1",
            BITGUARD_API_KEYS="secret-token",
            BITGUARD_DB_PATH=_db_path(),
            BITGUARD_FETCH_PUBLIC_CANDLES="0",
            BITGUARD_RATE_LIMIT_PER_MINUTE="60",
        ), _server() as base:
            _request("POST", f"{base}/api/audit", _bundle(), token="secret-token")
            status, data = _request("GET", f"{base}/api/usage?limit=5", token="secret-token")

        self.assertEqual(status, 200)
        self.assertEqual(data["records"][0]["event_type"], "api.sentinel.audit")
        self.assertEqual(data["records"][0]["agent_id"], "agent-http")


if __name__ == "__main__":
    unittest.main()
