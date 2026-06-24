from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .audit import audit_bundle
from .storage import utc_now_iso


DEFAULT_TRUENORTH_TOOLS = (
    "technical_analysis",
    "derivatives_analysis",
    "hyperliquid_smart_money",
    "trending_discovery",
    "events",
)


def intelligence_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    report = audit_bundle(bundle)
    symbol = _primary_symbol(report)
    truenorth = _collect_truenorth(symbol)
    brief = _openrouter_brief(report, truenorth)
    return {
        "generated_at": utc_now_iso(),
        "product": "BitGuard Sentinel",
        "mode": "ai-intelligence",
        "symbol": symbol,
        "audit": report,
        "truenorth": truenorth,
        "brief": brief,
    }


def _collect_truenorth(symbol: str) -> dict[str, Any]:
    mcp_url = os.environ.get("TRUENORTH_MCP_URL", "").strip()
    allowed = _allowed_tools()
    if not mcp_url:
        return {
            "status": "not_configured",
            "tools_requested": allowed,
            "signals": [],
            "summary": "TrueNorth MCP URL is not configured; using submitted Skill Hub snapshots only.",
        }

    client = _McpClient(mcp_url)
    try:
        available = client.list_tools()
        selected = [tool for tool in allowed if tool in available]
        signals = []
        for tool in selected:
            signals.append({"tool": tool, "result": client.call_tool(tool, _tool_args(tool, symbol))})
        return {
            "status": "ok",
            "tools_requested": allowed,
            "tools_available": sorted(available),
            "tools_called": selected,
            "signals": signals,
        }
    except Exception as exc:
        return {
            "status": "error",
            "tools_requested": allowed,
            "signals": [],
            "error": type(exc).__name__,
            "summary": "TrueNorth MCP call failed; using submitted Skill Hub snapshots only.",
        }


def _openrouter_brief(report: dict[str, Any], truenorth: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return _fallback_brief(report, truenorth, "OpenRouter API key is not configured.")

    payload = {
        "model": os.environ.get("OPENROUTER_MODEL", "z-ai/glm-5.2"),
        "temperature": 0.2,
        "max_tokens": 900,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are BitGuard Sentinel's post-trade replay coach for trading agents. "
                    "Treat every order as historical evidence, not as a pending setup. "
                    "Use the deterministic order_audit and market_replay facts as ground truth, then use "
                    "TrueNorth context only to explain what could have been done better during the trade. "
                    "Return strict JSON with keys: headline, execution_posture, thesis, replay_notes, "
                    "what_could_be_better, contradictions, invalidation_triggers, next_checks. "
                    "Do not change deterministic scores. Do not give financial advice."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(_brief_payload(report, truenorth), sort_keys=True),
            },
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://127.0.0.1:8765"),
        "X-Title": os.environ.get("OPENROUTER_APP_NAME", "BitGuard Sentinel"),
    }
    try:
        data = _post_json(_openrouter_url(), payload, headers=headers, timeout=30)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = json.loads(content) if content else {}
        return {
            "status": "ok",
            "provider": "openrouter",
            "model": data.get("model", payload["model"]),
            "usage": data.get("usage", {}),
            "analysis": _normalize_brief(parsed),
        }
    except Exception as exc:
        fallback = _fallback_brief(report, truenorth, "OpenRouter synthesis failed.")
        fallback["error"] = type(exc).__name__
        return fallback


def _fallback_brief(report: dict[str, Any], truenorth: dict[str, Any], reason: str) -> dict[str, Any]:
    perception = report.get("perception_layer", {})
    order = report.get("order_audit", {})
    replay = report.get("market_replay", {})
    replay_notes = _replay_notes(replay)
    improvements = _replay_improvements(replay)
    headline = _fallback_headline(order, perception, replay)
    contradictions = [item.get("summary", "") for item in perception.get("signals", []) if item.get("risk_points", 0) > 0]
    next_checks = _dedupe(
        replay.get("recommendations", [])[:3]
        + perception.get("recommendations", [])[:3]
        + ["Regenerate the brief with TrueNorth/OpenRouter enabled for external market-structure commentary."]
    )
    invalidation_triggers = _dedupe(order.get("recommendations", [])[:3] + replay.get("recommendations", [])[:3])
    return {
        "status": "fallback",
        "provider": "deterministic",
        "reason": reason,
        "analysis": {
            "headline": headline,
            "execution_posture": perception.get("verdict", "watch"),
            "thesis": _fallback_thesis(order, perception, replay),
            "replay_notes": replay_notes,
            "what_could_be_better": improvements,
            "contradictions": contradictions[:4],
            "invalidation_triggers": invalidation_triggers[:4],
            "next_checks": next_checks[:4],
        },
        "truenorth_status": truenorth.get("status", "unknown"),
    }


def _brief_payload(report: dict[str, Any], truenorth: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": "Post-trade critique of completed agent orders. Explain replay evidence and improvement loops only.",
        "summary": report.get("summary", {}),
        "order_audit": report.get("order_audit", {}),
        "market_replay": report.get("market_replay", {}),
        "perception_layer": report.get("perception_layer", {}),
        "metrics": report.get("metrics", {}),
        "truenorth": truenorth,
    }


def _fallback_headline(order: dict[str, Any], perception: dict[str, Any], replay: dict[str, Any]) -> str:
    rows = replay.get("trade_replays", [])
    available = sum(1 for item in rows if item.get("status") == "available")
    if rows:
        return f"{order.get('label', 'Trade review')} with {available}/{len(rows)} candle replay(s) scored"
    return f"{perception.get('label', 'No ping verdict')} with {perception.get('confidence', 'unknown')} confidence"


def _fallback_thesis(order: dict[str, Any], perception: dict[str, Any], replay: dict[str, Any]) -> str:
    parts = [
        order.get("summary", ""),
        replay.get("summary", ""),
        perception.get("summary", ""),
    ]
    return " ".join(part for part in parts if part) or "No replay thesis available yet."


def _replay_notes(replay: dict[str, Any]) -> list[str]:
    rows = replay.get("trade_replays", [])
    if not rows:
        return [replay.get("summary", "No candle replay was available for these completed trades.")]

    notes: list[str] = []
    for item in rows:
        symbol = item.get("symbol", "UNKNOWN")
        status = item.get("status", "unknown")
        if status != "available":
            notes.append(f"{symbol}: replay was not scored because {str(status).replace('_', ' ')}.")
            continue

        classification = str(item.get("classification", "not_scored")).replace("_", " ")
        direction = item.get("direction", "unknown")
        entry_move = _pct_text(item.get("entry_to_exit_move_pct"))
        market_move = _pct_text(item.get("directional_market_move_pct"))
        favorable = _pct_text(item.get("favorable_excursion_pct"))
        notes.append(
            f"{symbol} {direction}: {classification}; trade moved {entry_move} while candles moved {market_move} "
            f"in-trade, with {favorable} max favorable excursion."
        )
    return _dedupe(notes)[:5]


def _replay_improvements(replay: dict[str, Any]) -> list[str]:
    rows = replay.get("trade_replays", [])
    if not rows:
        return replay.get("recommendations", [])[:4] or [
            "Attach OHLCV candles covering each entry and exit window so the replay coach can judge timing."
        ]

    improvements: list[str] = []
    for item in rows:
        symbol = item.get("symbol", "UNKNOWN")
        if item.get("status") != "available":
            improvements.append(f"{symbol}: supply candles that cover the entry-through-exit interval before judging the agent logic.")
            continue

        classification = item.get("classification", "")
        directional_move = _pct_text(item.get("directional_market_move_pct"))
        favorable = _pct_text(item.get("favorable_excursion_pct"))
        adverse = _pct_text(item.get("adverse_excursion_pct"))
        if classification == "wrong_side_loss":
            improvements.append(
                f"{symbol}: add a regime check before entry; replay candles moved {directional_move} against the trade while the position closed red."
            )
        elif classification == "poor_exit_after_favorable_move":
            improvements.append(
                f"{symbol}: tighten exit logic; price offered {favorable} favorable excursion before the close failed to retain it."
            )
        elif classification == "execution_loss":
            improvements.append(
                f"{symbol}: review slippage, fees, and stop discipline; direction was not the only issue and adverse excursion reached {adverse}."
            )
        elif classification == "countertrend_win":
            improvements.append(
                f"{symbol}: tag this as a fragile countertrend win; require stronger confirmation before repeating the pattern."
            )
        elif classification == "aligned_win":
            improvements.append(
                f"{symbol}: preserve the setup constraints; replay shows price action and trade outcome were aligned."
            )

        entry_quality = str(item.get("entry_quality", "")).lower()
        exit_quality = str(item.get("exit_quality", "")).lower()
        if "chased" in entry_quality:
            improvements.append(f"{symbol}: avoid chasing range extremes; require pullback, confirmation, or reduced size on late entries.")
        if "gave back" in exit_quality:
            improvements.append(f"{symbol}: add a trailing exit or partial take-profit rule so favorable movement is not handed back.")

    return _dedupe(improvements)[:6]


def _pct_text(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "n/a"


class _McpClient:
    def __init__(self, url: str):
        self.url = url
        self.session_id = ""
        self.next_id = 1

    def list_tools(self) -> set[str]:
        self._request("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "bitguard-sentinel", "version": "0.1.0"}})
        self._notify("notifications/initialized")
        response = self._request("tools/list", {})
        return {item.get("name", "") for item in response.get("tools", []) if item.get("name")}

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        return self._request("tools/call", {"name": name, "arguments": arguments})

    def _notify(self, method: str) -> None:
        self._send({"jsonrpc": "2.0", "method": method})

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        response = self._send(payload)
        if "error" in response:
            raise RuntimeError(response["error"])
        return response.get("result", {})

    def _send(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        response = _post_json(self.url, payload, headers=headers, timeout=25, return_headers=True)
        self.session_id = response["headers"].get("mcp-session-id", self.session_id)
        return response["body"]


def _allowed_tools() -> list[str]:
    raw = os.environ.get("TRUENORTH_MCP_ALLOWED_TOOLS", "").strip()
    if not raw:
        return list(DEFAULT_TRUENORTH_TOOLS)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _tool_args(tool: str, symbol: str) -> dict[str, Any]:
    base = symbol.replace("-", "").replace("/", "").upper()
    if tool in {"technical_analysis", "derivatives_analysis", "hyperliquid_smart_money"}:
        return {"symbol": base}
    if tool in {"events", "trending_discovery", "combo_token_analysis"}:
        return {"query": base, "symbol": base}
    return {"symbol": base, "query": base}


def _primary_symbol(report: dict[str, Any]) -> str:
    for ping in report.get("perception_layer", {}).get("whale_pings", []):
        if ping.get("symbol"):
            return ping["symbol"]
    for row in report.get("metrics", {}).get("exposure", {}).get("by_symbol", []):
        if row.get("symbol"):
            return row["symbol"]
    return "BTCUSDT"


def _openrouter_url() -> str:
    base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    return f"{base}/chat/completions"


def _normalize_brief(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "headline": str(value.get("headline", "")),
        "execution_posture": str(value.get("execution_posture", "")),
        "thesis": str(value.get("thesis", "")),
        "replay_notes": _list_of_strings(value.get("replay_notes", [])),
        "what_could_be_better": _list_of_strings(value.get("what_could_be_better", [])),
        "contradictions": _list_of_strings(value.get("contradictions", [])),
        "invalidation_triggers": _list_of_strings(value.get("invalidation_triggers", [])),
        "next_checks": _list_of_strings(value.get("next_checks", [])),
    }


def _list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    clean = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            clean.append(item)
    return clean


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: int,
    return_headers: bool = False,
) -> Any:
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = _parse_response_body(response.read(), response.headers.get("content-type", ""))
            if return_headers:
                return {"body": body, "headers": {key.lower(): value for key, value in response.headers.items()}}
            return body
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:300]}") from exc


def _parse_response_body(body: bytes, content_type: str) -> dict[str, Any]:
    text = body.decode("utf-8", errors="replace").strip()
    if "text/event-stream" in content_type or text.startswith("event:") or text.startswith("data:"):
        for line in reversed(text.splitlines()):
            if line.startswith("data:"):
                data = line[5:].strip()
                if data and data != "[DONE]":
                    return json.loads(data)
        return {}
    return json.loads(text) if text else {}