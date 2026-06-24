from __future__ import annotations

import copy
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from .audit import normalize_bundle
from .storage import utc_now_iso


DISABLED_VALUES = {"0", "false", "off", "no"}
TIME_BUFFER = timedelta(minutes=30)
TIMEOUT_SECONDS = 12


def enrich_public_market_context(bundle: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, dict) or not _public_fetch_enabled() or _has_candles(bundle):
        return bundle

    try:
        normalized = normalize_bundle(bundle)
    except Exception:
        return _with_market_context_status(bundle, "normalize_failed", [])

    requests = _build_requests(normalized)
    if not requests:
        return _with_market_context_status(bundle, "insufficient_trade_window", [])

    candles: dict[str, list[dict[str, Any]]] = {}
    request_logs: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for request in requests:
        try:
            rows = _fetch_candles(request)
            request_logs.append({**request, "status": "ok", "candles": len(rows)})
            if rows:
                candles[request["symbol"]] = rows
        except Exception as exc:
            request_logs.append({**request, "status": "error", "error": type(exc).__name__})
            errors.append({"symbol": request["symbol"], "error": type(exc).__name__, "message": str(exc)[:160]})

    enriched = copy.deepcopy(bundle)
    existing = enriched.get("market_context") if isinstance(enriched.get("market_context"), dict) else {}
    context = dict(existing)
    context.update(
        {
            "source": "bitget-public-api",
            "fetch_status": "fetched" if candles else "fetch_failed",
            "retrieved_at": utc_now_iso(),
            "market_type": normalized.get("market_type", "unknown"),
            "product_type": normalized.get("product_type", "UNKNOWN"),
            "candles": candles,
            "requests": request_logs,
        }
    )
    if errors:
        context["errors"] = errors
    enriched["market_context"] = context
    return enriched


def _public_fetch_enabled() -> bool:
    value = os.environ.get("BITGUARD_FETCH_PUBLIC_CANDLES", "1").strip().lower()
    return value not in DISABLED_VALUES


def _has_candles(bundle: dict[str, Any]) -> bool:
    candidates = [bundle.get("market_context"), bundle.get("chart_context"), bundle.get("candles"), bundle.get("ohlcv")]
    for value in candidates:
        payload = value.get("candles") if isinstance(value, dict) and "candles" in value else value
        if isinstance(payload, dict):
            for rows in payload.values():
                if isinstance(rows, dict):
                    rows = rows.get("candles", [])
                if isinstance(rows, list) and rows:
                    return True
        if isinstance(payload, list) and payload:
            return True
    return False


def _with_market_context_status(bundle: dict[str, Any], status: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = copy.deepcopy(bundle)
    existing = enriched.get("market_context") if isinstance(enriched.get("market_context"), dict) else {}
    context = dict(existing)
    context.update({"source": "bitget-public-api", "fetch_status": status, "candles": {}, "requests": requests})
    enriched["market_context"] = context
    return enriched


def _build_requests(normalized: dict[str, Any]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str], list[datetime]] = {}
    for row in normalized.get("fills", []):
        _add_row_time(buckets, row, row.get("timestamp"))
    if not buckets:
        for row in normalized.get("orders", []):
            _add_row_time(buckets, row, row.get("created_at"))

    requests = []
    for (symbol, market_type, product_type), times in sorted(buckets.items()):
        clean_times = [item for item in times if item]
        if not clean_times or symbol == "UNKNOWN" or market_type not in {"spot", "futures"}:
            continue
        start = min(clean_times) - TIME_BUFFER
        end = max(clean_times) + TIME_BUFFER
        granularity = _granularity(start, end, market_type)
        requests.append(
            {
                "symbol": symbol,
                "market_type": market_type,
                "product_type": product_type,
                "granularity": granularity,
                "startTime": _ms(start),
                "endTime": _ms(end),
                "limit": 1000,
            }
        )
    return requests


def _add_row_time(buckets: dict[tuple[str, str, str], list[datetime]], row: dict[str, Any], value: Any) -> None:
    timestamp = _parse_time(value)
    if not timestamp:
        return
    symbol = str(row.get("symbol", "UNKNOWN")).replace("/", "").upper()
    product_type = str(row.get("product_type", "UNKNOWN")).upper()
    market_type = str(row.get("market_type", "unknown")).lower()
    if market_type == "unknown" and "FUTURES" in product_type:
        market_type = "futures"
    if market_type == "unknown" and product_type == "SPOT":
        market_type = "spot"
    buckets.setdefault((symbol, market_type, product_type), []).append(timestamp)


def _granularity(start: datetime, end: datetime, market_type: str) -> str:
    minutes = max((end - start).total_seconds() / 60, 1)
    if minutes <= 12 * 60:
        base = "1m"
    elif minutes <= 36 * 60:
        base = "3m"
    elif minutes <= 3 * 24 * 60:
        base = "5m"
    elif minutes <= 10 * 24 * 60:
        base = "15m"
    elif minutes <= 20 * 24 * 60:
        base = "30m"
    elif minutes <= 45 * 24 * 60:
        base = "1H"
    else:
        base = "4H"
    if market_type == "spot":
        return {"1m": "1min", "3m": "3min", "5m": "5min", "15m": "15min", "30m": "30min"}.get(base, base.lower().replace("h", "h"))
    return base


def _fetch_candles(request: dict[str, Any]) -> list[dict[str, Any]]:
    market_type = request["market_type"]
    if market_type == "spot":
        endpoint = "/api/v2/spot/market/candles"
        params = {
            "symbol": request["symbol"],
            "granularity": request["granularity"],
            "startTime": str(request["startTime"]),
            "endTime": str(request["endTime"]),
            "limit": str(request["limit"]),
        }
    else:
        endpoint = "/api/v2/mix/market/candles"
        params = {
            "symbol": request["symbol"],
            "productType": request["product_type"].lower(),
            "granularity": request["granularity"],
            "startTime": str(request["startTime"]),
            "endTime": str(request["endTime"]),
            "limit": str(request["limit"]),
            "kLineType": "MARKET",
        }

    url = f"{_base_url()}{endpoint}?{urllib.parse.urlencode(params)}"
    payload = _get_json(url)
    if str(payload.get("code", "00000")) not in {"00000", "0"}:
        raise RuntimeError(payload.get("msg", "Bitget candle request failed"))
    return [_normalize_candle(row) for row in payload.get("data", []) if isinstance(row, list) and len(row) >= 5]


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "bitguard-sentinel/0.1"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalize_candle(row: list[Any]) -> dict[str, Any]:
    return {
        "timestamp": _iso_from_ms(row[0]),
        "open": _float(row[1]),
        "high": _float(row[2]),
        "low": _float(row[3]),
        "close": _float(row[4]),
        "volume": _float(row[5]) if len(row) > 5 else 0.0,
    }


def _parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        number = int(value)
        if number < 10_000_000_000:
            number *= 1000
        return datetime.fromtimestamp(number / 1000, tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _iso_from_ms(value: Any) -> str:
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _base_url() -> str:
    return os.environ.get("BITGET_PUBLIC_BASE_URL", "https://api.bitget.com").rstrip("/")