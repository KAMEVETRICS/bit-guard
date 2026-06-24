from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import utc_now_iso


SENSITIVE_KEYS = {
    "uid",
    "user_id",
    "account_id",
    "accountid",
    "subaccount",
    "sub_account",
    "apikey",
    "api_key",
    "secret",
    "secret_key",
    "passphrase",
    "address",
    "wallet_address",
    "deposit_address",
    "clientoid",
    "client_oid",
    "clientorderid",
    "client_order_id",
}

HASH_KEYS = {
    "order_id",
    "orderid",
    "fill_id",
    "fillid",
    "trade_id",
    "tradeid",
    "position_id",
    "positionid",
}


def load_bundle(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def redact_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    redacted = _redact(copy.deepcopy(bundle))
    redacted["redacted_at"] = utc_now_iso()
    return redacted


def audit_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_bundle(bundle)
    trades = reconstruct_trades(normalized["fills"])
    market_replay = build_market_replay(normalized, trades)
    metrics = compute_metrics(normalized, trades)
    findings = build_findings(normalized, trades, metrics)
    order_audit = build_order_audit(normalized, trades, metrics, findings, market_replay)
    perception_layer = build_perception_layer(normalized, metrics, order_audit)
    pattern_library = build_pattern_library(normalized, trades, metrics, market_replay, perception_layer)
    return {
        "generated_at": utc_now_iso(),
        "product": "BitGuard Sentinel",
        "mode": "demo" if normalized["demo_only"] else "bitget-readonly-export",
        "source": normalized["source"],
        "demo_only": normalized["demo_only"],
        "agent_id": normalized["agent_id"],
        "run_id": normalized["run_id"],
        "privacy": {
            "api_keys_required_by_dashboard": False,
            "redaction": "Sensitive identifiers are omitted or hashed in reports.",
        },
        "summary": {
            "fills": len(normalized["fills"]),
            "orders": len(normalized["orders"]),
            "positions": len(normalized["positions"]),
            "completed_trades": len(trades),
            "market_type": normalized["market_type"],
            "product_type": normalized["product_type"],
            "market_context_status": market_replay["status"],
            "risk_score": metrics["risk_score"],
            "health_grade": _health_grade(metrics["risk_score"]),
            "total_realized_pnl_usdt": metrics["pnl"]["total_realized_pnl_usdt"],
            "max_drawdown_pct": metrics["pnl"]["max_drawdown_pct"],
            "order_audit_verdict": order_audit["verdict"],
            "order_audit_score": order_audit["score"],
            "perception_verdict": perception_layer["verdict"],
            "perception_score": perception_layer["score"],
            "patterns": pattern_library["summary"]["total_patterns"],
            "verified_patterns": pattern_library["summary"]["verified_patterns"],
        },
        "metrics": metrics,
        "findings": findings,
        "order_audit": order_audit,
        "perception_layer": perception_layer,
        "market_replay": market_replay,
        "pattern_library": pattern_library,
        "trades": trades,
        "normalized_preview": {
            "positions": normalized["positions"][:10],
            "funding_payments": normalized["funding_payments"][:10],
            "agent_decisions": normalized["agent_decisions"][:10],
        },
    }


def normalize_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    data = _unwrap_bitget_data(bundle)
    raw_orders = [item for item in data.get("orders", []) if isinstance(item, dict)]
    raw_fills = [item for item in data.get("fills", []) if isinstance(item, dict)]
    raw_positions = [item for item in data.get("positions", []) if isinstance(item, dict)]
    product_types = _infer_product_types(data, raw_orders, raw_fills, raw_positions)
    product_type = product_types[0] if len(product_types) == 1 else "MIXED" if product_types else "UNKNOWN"
    market_type = _market_type(product_type, raw_positions, data.get("funding_payments", []))

    return {
        "source": str(bundle.get("source", "demo-agent-log-schema")),
        "demo_only": bool(bundle.get("demo_only", bundle.get("source") != "bitget-readonly-export")),
        "agent_id": str(bundle.get("agent_id", "unknown-agent")),
        "run_id": str(bundle.get("run_id", "unknown-run")),
        "exported_at": str(bundle.get("exported_at", "")),
        "market_type": market_type,
        "product_type": product_type,
        "product_types": product_types,
        "orders": [_normalize_order(_with_default_product_type(item, product_type)) for item in raw_orders],
        "fills": sorted(
            [_normalize_fill(_with_default_product_type(item, product_type)) for item in raw_fills],
            key=lambda item: item["timestamp"],
        ),
        "positions": [_normalize_position(_with_default_product_type(item, product_type)) for item in raw_positions],
        "funding_payments": [_normalize_funding(_with_default_product_type(item, product_type)) for item in data.get("funding_payments", [])],
        "account_snapshots": data.get("account_snapshots", []),
        "agent_decisions": [_normalize_decision(_with_default_product_type(item, product_type)) for item in data.get("agent_decisions", [])],
        "skill_hub": _normalize_skill_hub(data.get("skill_hub", {})),
        "copy_trading": _normalize_copy_trading(data),
        "market_context": _normalize_market_context(data.get("market_context", data.get("chart_context", data.get("candles", data.get("ohlcv", {}))))),
    }


def reconstruct_trades(fills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state: dict[str, dict[str, Any]] = defaultdict(_empty_position)
    trades: list[dict[str, Any]] = []

    for fill in fills:
        symbol = fill["symbol"]
        side = fill["side"]
        qty = fill["quantity"]
        price = fill["price"]
        fee = fill["fee_usdt"]
        pos = state[symbol]

        if side == "buy":
            if pos["quantity"] < 0:
                close_qty = min(qty, abs(pos["quantity"]))
                trades.append(_close_trade(symbol, "short", close_qty, price, fee, fill, pos))
                pos["quantity"] += close_qty
                qty -= close_qty
                if abs(pos["quantity"]) < 1e-12:
                    pos.clear()
                    pos.update(_empty_position())
            if qty > 0:
                _open_or_add(pos, "long", qty, price, fee, fill)
        elif side == "sell":
            if pos["quantity"] > 0:
                close_qty = min(qty, pos["quantity"])
                trades.append(_close_trade(symbol, "long", close_qty, price, fee, fill, pos))
                pos["quantity"] -= close_qty
                qty -= close_qty
                if abs(pos["quantity"]) < 1e-12:
                    pos.clear()
                    pos.update(_empty_position())
            if qty > 0:
                _open_or_add(pos, "short", qty, price, fee, fill)

    return trades


def compute_metrics(normalized: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    realized = sum(trade["realized_pnl_usdt"] for trade in trades)
    wins = [trade for trade in trades if trade["realized_pnl_usdt"] > 0]
    losses = [trade for trade in trades if trade["realized_pnl_usdt"] <= 0]
    gross_profit = sum(trade["realized_pnl_usdt"] for trade in wins)
    gross_loss = abs(sum(trade["realized_pnl_usdt"] for trade in losses))
    fees = sum(fill["fee_usdt"] for fill in normalized["fills"])
    funding = sum(item["amount_usdt"] for item in normalized["funding_payments"])
    starting_equity = _starting_equity(normalized)
    equity_curve = _equity_curve(trades, starting_equity)
    positions = normalized["positions"]
    total_notional = sum(abs(item["notional_usdt"]) for item in positions)
    max_position_notional = max([abs(item["notional_usdt"]) for item in positions] or [0.0])
    concentration = (max_position_notional / total_notional * 100) if total_notional else 0.0
    leverage_values = [abs(item["leverage"]) for item in positions if item["leverage"]]
    missing_stop_count = sum(1 for item in normalized["agent_decisions"] if not item["stop_loss"])
    overtrading = _overtrading_metrics(normalized["fills"])

    pnl_metrics = {
        "total_realized_pnl_usdt": round(realized, 4),
        "gross_profit_usdt": round(gross_profit, 4),
        "gross_loss_usdt": round(gross_loss, 4),
        "fees_usdt": round(fees, 4),
        "funding_pnl_usdt": round(funding, 4),
        "win_rate_pct": round(len(wins) / len(trades) * 100, 2) if trades else 0.0,
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else round(gross_profit, 4),
        "starting_equity_usdt": round(starting_equity, 4),
        "max_drawdown_pct": round(_max_drawdown_pct(equity_curve), 4),
    }
    exposure_metrics = {
        "open_position_count": len(positions),
        "total_notional_usdt": round(total_notional, 4),
        "largest_position_notional_usdt": round(max_position_notional, 4),
        "largest_position_concentration_pct": round(concentration, 2),
        "max_leverage": round(max(leverage_values or [0.0]), 2),
        "weighted_leverage": round(
            sum(abs(item["notional_usdt"]) * abs(item["leverage"]) for item in positions) / total_notional,
            2,
        )
        if total_notional
        else 0.0,
        "by_symbol": _position_concentration(positions),
    }
    behavior_metrics = {
        "fill_count": len(normalized["fills"]),
        "completed_trade_count": len(trades),
        "max_fills_in_day": overtrading["max_fills_in_day"],
        "active_trading_days": overtrading["active_trading_days"],
        "missing_stop_loss_decisions": missing_stop_count,
    }
    risk_score = _risk_score(pnl_metrics, exposure_metrics, behavior_metrics)
    return {
        "risk_score": risk_score,
        "pnl": pnl_metrics,
        "exposure": exposure_metrics,
        "behavior": behavior_metrics,
    }


def build_order_audit(
    normalized: dict[str, Any],
    trades: list[dict[str, Any]],
    metrics: dict[str, Any],
    findings: list[dict[str, Any]],
    market_replay: dict[str, Any],
) -> dict[str, Any]:
    pnl = metrics["pnl"]
    exposure = metrics["exposure"]
    behavior = metrics["behavior"]
    orders_count = len(normalized["orders"])
    fills_count = len(normalized["fills"])
    completed_count = len(trades)
    high_findings = sum(1 for item in findings if item["severity"] == "high")
    medium_findings = sum(1 for item in findings if item["severity"] == "medium")

    score = 100.0
    score -= metrics["risk_score"] * 0.42
    score -= high_findings * 9
    score -= medium_findings * 4
    if fills_count == 0:
        score -= 35
    elif completed_count == 0:
        score -= 22
    if pnl["profit_factor"] and pnl["profit_factor"] < 1:
        score -= 9
    if completed_count and pnl["win_rate_pct"] < 40:
        score -= 7
    if pnl["total_realized_pnl_usdt"] < 0:
        loss_pct = abs(pnl["total_realized_pnl_usdt"]) / max(abs(pnl["starting_equity_usdt"]), 1.0) * 100
        score -= min(12, loss_pct * 2.5)
    if exposure["open_position_count"] and completed_count == 0:
        score -= 8
    score = int(max(0, min(100, round(score))))

    if score >= 75:
        verdict = "pass"
        label = "Strong post-trade execution"
    elif score >= 55:
        verdict = "watch"
        label = "Review before repeating"
    elif score >= 35:
        verdict = "caution"
        label = "Weak trade process"
    else:
        verdict = "fail"
        label = "Post-trade failure"

    confidence = _order_audit_confidence(normalized, completed_count)
    evidence = _order_audit_evidence(normalized, trades, metrics, findings, market_replay)
    recommendations = _order_audit_recommendations(metrics, findings, completed_count, market_replay)
    summary = _order_audit_summary(label, score, confidence, pnl, exposure, behavior, completed_count, market_replay)

    return {
        "verdict": verdict,
        "label": label,
        "score": score,
        "confidence": confidence,
        "summary": summary,
        "basis": {
            "orders_analyzed": orders_count,
            "fills_analyzed": fills_count,
            "completed_trades": completed_count,
            "open_positions": exposure["open_position_count"],
            "market_type": normalized["market_type"],
            "product_type": normalized["product_type"],
            "market_context_status": market_replay["status"],
            "high_findings": high_findings,
            "medium_findings": medium_findings,
            "pairing_method": "net_position_fifo_v1",
        },
        "evidence": evidence,
        "recommendations": recommendations,
    }

def build_perception_layer(
    normalized: dict[str, Any],
    metrics: dict[str, Any],
    order_audit: dict[str, Any],
) -> dict[str, Any]:
    signals = _perception_signals(normalized["skill_hub"])
    whale_pings = _whale_pings(normalized["copy_trading"], metrics)
    opportunity_points = sum(item["opportunity_points"] for item in signals)
    risk_points = sum(item["risk_points"] for item in signals)
    opportunity_points += sum(item["opportunity_points"] for item in whale_pings)
    risk_points += sum(item["risk_points"] for item in whale_pings)
    risk_points += metrics["risk_score"] * 0.08
    if order_audit["verdict"] == "fail":
        risk_points += 8
    elif order_audit["verdict"] == "caution":
        risk_points += 5

    base_score = 85 if signals or whale_pings else 45
    score = int(max(0, min(100, round(base_score + opportunity_points - risk_points))))
    if score >= 70:
        verdict = "opportunity"
        label = "High-quality ping"
    elif score >= 50:
        verdict = "watch"
        label = "Watchlist only"
    elif score >= 35:
        verdict = "caution"
        label = "Crowded or conflicted"
    else:
        verdict = "avoid"
        label = "Likely trap"

    confidence = _perception_confidence(signals, whale_pings)
    recommendations = _perception_recommendations(signals, whale_pings, order_audit, verdict)
    summary = _perception_summary(label, score, confidence, signals, whale_pings)
    return {
        "verdict": verdict,
        "label": label,
        "score": score,
        "confidence": confidence,
        "summary": summary,
        "basis": {
            "skill_hub_signals": len(signals),
            "whale_pings": len(whale_pings),
            "order_audit_verdict": order_audit["verdict"],
            "method": "skill_hub_copy_trading_v1",
        },
        "signals": [_public_signal(item) for item in signals],
        "whale_pings": [_public_ping(item) for item in whale_pings],
        "recommendations": recommendations,
    }


def _perception_signals(skill_hub: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    signals = []
    for skill, payload in skill_hub.items():
        text = " ".join(
            str(payload.get(key, ""))
            for key in ("stance", "verdict", "bias", "regime", "signal", "setup", "positioning", "summary")
        ).lower()
        risk = 0.0
        opportunity = 0.0
        if any(word in text for word in ("risk-on", "bullish", "accumulation", "support", "breakout", "tailwind")):
            opportunity += 12
        if any(word in text for word in ("risk-off", "bearish", "headwind", "breakdown", "resistance", "negative")):
            risk += 12
        if any(word in text for word in ("crowded", "overleveraged", "euphoric", "squeeze", "event risk", "funding elevated")):
            risk += 14
        if any(word in text for word in ("mixed", "neutral", "divergence")):
            risk += 5
        signals.append(
            {
                "skill": skill,
                "stance": str(payload.get("stance") or payload.get("verdict") or payload.get("bias") or "observed"),
                "summary": str(payload.get("summary") or payload.get("note") or payload.get("headline") or "Signal snapshot supplied."),
                "risk_points": risk,
                "opportunity_points": opportunity,
            }
        )
    return signals


def _whale_pings(copy_trading: dict[str, Any], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    pings = []
    for item in copy_trading.get("pings", []):
        notional = abs(item.get("notional_usdt", 0.0))
        followers = item.get("followers", 0)
        drawdown = item.get("leader_drawdown_pct", 0.0)
        risk = 0.0
        opportunity = 0.0
        if notional >= 1000:
            opportunity += 8
        if followers >= 1000:
            risk += 8
        if drawdown >= 10:
            risk += 10
        if metrics["exposure"]["largest_position_concentration_pct"] >= 65:
            risk += 8
        ping_score = int(max(0, min(100, round(55 + opportunity - risk))))
        pings.append(
            {
                **item,
                "score": ping_score,
                "verdict": "opportunity" if ping_score >= 70 else "watch" if ping_score >= 50 else "avoid",
                "risk_points": risk,
                "opportunity_points": opportunity,
            }
        )
    return pings


def _perception_confidence(signals: list[dict[str, Any]], whale_pings: list[dict[str, Any]]) -> str:
    if len(signals) >= 4 and whale_pings:
        return "high"
    if len(signals) >= 2 or whale_pings:
        return "medium"
    return "low"


def _perception_recommendations(
    signals: list[dict[str, Any]],
    whale_pings: list[dict[str, Any]],
    order_audit: dict[str, Any],
    verdict: str,
) -> list[str]:
    text = " ".join(f"{item['stance']} {item['summary']}" for item in signals).lower()
    recommendations = []
    if not signals:
        recommendations.append("Attach Skill Hub snapshots so the ping can be judged against macro, market structure, news, sentiment, and chart context.")
    if not whale_pings:
        recommendations.append("Add copy-trading or large-flow observations to distinguish whale activity from ordinary agent execution.")
    if "crowded" in text or "overleveraged" in text or "funding elevated" in text:
        recommendations.append("Do not mirror the whale ping blindly; compare it with order-book depth, candle replay, and leverage crowding before acting on the signal.")
    if "risk-off" in text or "headwind" in text:
        recommendations.append("Treat bullish pings as counter-trend until the macro or news backdrop improves.")
    if order_audit["verdict"] in {"fail", "caution"}:
        recommendations.append("Treat this as failed agent behavior until a later trade log shows cleaner risk controls.")
    if verdict == "opportunity":
        recommendations.append("Keep the ping on watch and size any follow-up conservatively; this is decision support, not a standalone trade instruction.")
    if not recommendations:
        recommendations.append("Perception inputs are balanced; continue monitoring with fresh Skill Hub and copy-trading snapshots.")
    return recommendations


def _perception_summary(
    label: str,
    score: int,
    confidence: str,
    signals: list[dict[str, Any]],
    whale_pings: list[dict[str, Any]],
) -> str:
    return (
        f"{label}: scored {score}/100 with {confidence} confidence from "
        f"{len(signals)} Skill Hub signal(s) and {len(whale_pings)} copy-trading/whale ping(s). "
        "The score rewards aligned whale, market-structure, and technical context while penalizing crowded positioning, weak macro, and risky agent execution."
    )


def _public_signal(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill": item["skill"],
        "stance": item["stance"],
        "summary": item["summary"],
        "risk_points": round(item["risk_points"], 2),
        "opportunity_points": round(item["opportunity_points"], 2),
    }


def _public_ping(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": item.get("symbol", "UNKNOWN"),
        "direction": item.get("direction", "unknown"),
        "source": item.get("source", "copy_trading"),
        "notional_usdt": item.get("notional_usdt", 0.0),
        "followers": item.get("followers", 0),
        "leader_drawdown_pct": item.get("leader_drawdown_pct", 0.0),
        "score": item["score"],
        "verdict": item["verdict"],
        "summary": item.get("summary", "Copy-trading activity supplied by the log bundle."),
    }


def build_pattern_library(
    normalized: dict[str, Any],
    trades: list[dict[str, Any]],
    metrics: dict[str, Any],
    market_replay: dict[str, Any],
    perception_layer: dict[str, Any],
) -> dict[str, Any]:
    trade_by_ref = {trade.get("trade_ref", ""): trade for trade in trades}
    patterns: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for replay in market_replay.get("trade_replays", []):
        if replay.get("status") == "available":
            grouped[str(replay.get("classification", "not_scored"))].append(replay)

    for classification, rows in sorted(grouped.items()):
        pattern = _replay_pattern(classification, rows, trade_by_ref)
        if pattern:
            patterns.append(pattern)

    funding = metrics.get("pnl", {}).get("funding_pnl_usdt", 0.0)
    if funding < 0:
        patterns.append(
            {
                "id": "funding-bleed-under-leverage",
                "status": "observed",
                "title": "Funding bleed under leverage",
                "description": "The run paid net funding while carrying futures exposure, so holding windows need a funding gate.",
                "conditions": ["funding pnl < 0", f"max leverage = {metrics['exposure']['max_leverage']}x"],
                "symbols": [item["symbol"] for item in metrics.get("exposure", {}).get("by_symbol", [])][:4],
                "sample_size": max(1, len(normalized.get("funding_payments", []))),
                "win_rate_pct": metrics.get("pnl", {}).get("win_rate_pct", 0.0),
                "avg_pnl_usdt": round(funding, 2),
                "last_seen": _last_seen(trades),
                "action": "Replay funding settlement before approving long holds.",
            }
        )

    if perception_layer.get("whale_pings") and perception_layer.get("verdict") in {"avoid", "caution"}:
        symbols = sorted({ping.get("symbol", "UNKNOWN") for ping in perception_layer.get("whale_pings", [])})
        patterns.append(
            {
                "id": "whale-ping-conflict",
                "status": "risk",
                "title": "Whale ping conflict",
                "description": "Copy or whale activity was present, but the perception layer marked the setup as risky.",
                "conditions": ["whale ping observed", f"perception verdict = {perception_layer.get('verdict')}", "agent execution risk present"],
                "symbols": symbols,
                "sample_size": len(perception_layer.get("whale_pings", [])),
                "win_rate_pct": metrics.get("pnl", {}).get("win_rate_pct", 0.0),
                "avg_pnl_usdt": metrics.get("pnl", {}).get("total_realized_pnl_usdt", 0.0),
                "last_seen": _last_seen(trades),
                "action": "Treat whale pings as context, then require replay and risk confirmation.",
            }
        )

    patterns.sort(key=lambda item: (0 if item["status"] == "verified" else 1 if item["status"] == "observed" else 2, -item["sample_size"]))
    verified = sum(1 for item in patterns if item["status"] == "verified")
    avg_win_rate = round(sum(item["win_rate_pct"] for item in patterns) / len(patterns), 2) if patterns else 0.0
    return {
        "source": "current-audit-run",
        "summary": {
            "total_patterns": len(patterns),
            "verified_patterns": verified,
            "observed_patterns": sum(1 for item in patterns if item["status"] == "observed"),
            "risk_patterns": sum(1 for item in patterns if item["status"] == "risk"),
            "avg_win_rate_pct": avg_win_rate,
        },
        "narrative": "Every uploaded agent run teaches BitGuard which behaviors repeat, which ones paid, and which ones need guardrails.",
        "patterns": patterns,
    }


def _replay_pattern(classification: str, rows: list[dict[str, Any]], trade_by_ref: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    trades = [trade_by_ref.get(row.get("trade_ref", ""), {}) for row in rows]
    sample_size = len(rows)
    if not sample_size:
        return None
    wins = sum(1 for trade in trades if trade.get("realized_pnl_usdt", 0.0) > 0)
    pnl_values = [trade.get("realized_pnl_usdt", 0.0) for trade in trades]
    win_rate = round((wins / sample_size) * 100, 2)
    avg_pnl = round(sum(pnl_values) / sample_size, 2) if pnl_values else 0.0
    symbols = sorted({row.get("symbol", "UNKNOWN") for row in rows})
    entry_tags = sorted({row.get("entry_quality", "not scored") for row in rows if row.get("entry_quality")})[:2]
    exit_tags = sorted({row.get("exit_quality", "not scored") for row in rows if row.get("exit_quality")})[:2]
    label = classification.replace("_", " ")
    titles = {
        "aligned_win": "Aligned replay win",
        "countertrend_win": "Countertrend win",
        "poor_exit_after_favorable_move": "Poor exit after favorable move",
        "wrong_side_loss": "Wrong-side candle loss",
        "execution_loss": "Execution loss despite replay support",
    }
    actions = {
        "aligned_win": "Promote this setup into an agent rule candidate and retest on more runs.",
        "countertrend_win": "Mark as fragile until the agent explains why countertrend risk was acceptable.",
        "poor_exit_after_favorable_move": "Add trailing exits or partial take-profit rules before rerunning this strategy.",
        "wrong_side_loss": "Require a regime filter before taking this setup again.",
        "execution_loss": "Check fees, slippage, sizing, and stop discipline before reuse.",
    }
    status = "verified" if sample_size >= 10 and win_rate >= 60 else "risk" if "loss" in classification else "observed"
    directional_moves = [row.get("directional_market_move_pct", 0.0) for row in rows]
    avg_move = round(sum(directional_moves) / sample_size, 2) if directional_moves else 0.0
    return {
        "id": classification,
        "status": status,
        "title": titles.get(classification, label.title()),
        "description": f"Observed {sample_size} completed trade(s) where replay classified behavior as {label}.",
        "conditions": _dedupe([f"replay = {label}", f"avg in-trade candle move = {avg_move}%"] + entry_tags + exit_tags)[:4],
        "symbols": symbols,
        "sample_size": sample_size,
        "win_rate_pct": win_rate,
        "avg_pnl_usdt": avg_pnl,
        "last_seen": _last_seen(trades),
        "action": actions.get(classification, "Retest this behavior against more completed trade logs."),
    }


def _last_seen(trades: list[dict[str, Any]]) -> str:
    timestamps = [trade.get("exit_time", "") for trade in trades if trade.get("exit_time")]
    return max(timestamps) if timestamps else "current run"

def build_market_replay(normalized: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    context = normalized.get("market_context", {})
    candles_by_symbol = context.get("candles", {}) if isinstance(context, dict) else {}
    symbols = sorted({item["symbol"] for item in normalized.get("fills", [])} | {trade["symbol"] for trade in trades})
    product_type = normalized.get("product_type", "UNKNOWN")

    if not trades:
        return {
            "status": "no_completed_trades",
            "source": context.get("source", "none") if isinstance(context, dict) else "none",
            "product_type": product_type,
            "market_type": normalized.get("market_type", "unknown"),
            "symbols": symbols,
            "summary": "No completed entry/exit pairs were reconstructed, so chart replay is waiting for closed trades.",
            "by_symbol": [],
            "trade_replays": [],
            "recommendations": ["Upload fills with both entry and exit legs so Sentinel can compare execution against market movement."],
        }

    if not candles_by_symbol:
        return {
            "status": context.get("fetch_status", "missing_candles") if isinstance(context, dict) else "missing_candles",
            "source": context.get("source", "none") if isinstance(context, dict) else "none",
            "product_type": product_type,
            "market_type": normalized.get("market_type", "unknown"),
            "symbols": symbols,
            "summary": "Trade lifecycle was reconstructed, but no candle data was available for market replay.",
            "by_symbol": [],
            "trade_replays": [],
            "recommendations": ["Attach market_context.candles from the agent/exporter so the audit can judge entry and exit timing."],
        }

    by_symbol = []
    for symbol in symbols:
        series = _candles_for_symbol(candles_by_symbol, symbol)
        if not series:
            continue
        first = series[0]
        last = series[-1]
        lows = [item["low"] for item in series if item["low"]]
        highs = [item["high"] for item in series if item["high"]]
        start = first.get("open") or first.get("close") or 0.0
        end = last.get("close") or last.get("open") or 0.0
        by_symbol.append(
            {
                "symbol": symbol,
                "product_type": product_type,
                "candles": len(series),
                "first_timestamp": first.get("timestamp", ""),
                "last_timestamp": last.get("timestamp", ""),
                "market_move_pct": round(((end - start) / start) * 100, 4) if start else 0.0,
                "high_low_range_pct": round(((max(highs) - min(lows)) / start) * 100, 4) if start and highs and lows else 0.0,
            }
        )

    trade_replays = []
    recommendations = []
    for trade in trades:
        replay = _trade_market_replay(trade, candles_by_symbol)
        trade_replays.append(replay)
        if replay["status"] != "available":
            recommendations.append(f"Add candles around {trade['symbol']} from {trade['entry_time']} to {trade['exit_time']} for chart-aware feedback.")
            continue
        if replay["classification"] == "wrong_side_loss":
            recommendations.append(f"Review {trade['symbol']}: the trade lost while market movement favored the opposite side.")
        elif replay["classification"] == "poor_exit_after_favorable_move":
            recommendations.append(f"Review {trade['symbol']} exit logic: price offered a favorable move before the trade closed poorly.")
        if "chased" in replay["entry_quality"].lower():
            recommendations.append(f"Review {trade['symbol']} entry timing: entry was near the extreme of the replay window.")

    available = sum(1 for item in trade_replays if item["status"] == "available")
    status = "available" if available == len(trade_replays) else "partial" if available else "missing_candles"
    if not recommendations:
        recommendations.append("Use these replay tags as agent iteration feedback: preserve aligned wins, rewrite setups that chased range extremes, and retest exits that left favorable movement uncaptured.")

    return {
        "status": status,
        "source": context.get("source", "supplied_candles"),
        "fetch_status": context.get("fetch_status", "supplied"),
        "product_type": product_type,
        "market_type": normalized.get("market_type", "unknown"),
        "symbols": symbols,
        "summary": f"Market replay covered {available}/{len(trade_replays)} completed trade(s) with candle context.",
        "by_symbol": by_symbol,
        "trade_replays": trade_replays,
        "recommendations": _dedupe(recommendations),
    }


def _trade_market_replay(trade: dict[str, Any], candles_by_symbol: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    series = _candles_for_symbol(candles_by_symbol, trade["symbol"])
    entry_time = _parse_time(trade.get("entry_time", ""))
    exit_time = _parse_time(trade.get("exit_time", ""))
    if not series or not entry_time or not exit_time:
        return {
            "trade_ref": trade.get("trade_ref", ""),
            "symbol": trade.get("symbol", "UNKNOWN"),
            "status": "missing_candles",
            "classification": "not_scored",
            "summary": "No matching candle window was available for this completed trade.",
        }

    window = [item for item in series if entry_time <= item.get("dt", entry_time) <= exit_time]
    if not window:
        return {
            "trade_ref": trade.get("trade_ref", ""),
            "symbol": trade.get("symbol", "UNKNOWN"),
            "status": "missing_window",
            "classification": "not_scored",
            "summary": "Candles exist for the symbol, but not for the trade entry/exit interval.",
        }

    entry = trade.get("entry_price", 0.0)
    exit_price = trade.get("exit_price", 0.0)
    lows = [item["low"] for item in window if item["low"]]
    highs = [item["high"] for item in window if item["high"]]
    start = window[0].get("open") or window[0].get("close") or entry
    end = window[-1].get("close") or window[-1].get("open") or exit_price
    min_low = min(lows or [entry])
    max_high = max(highs or [entry])
    direction = trade.get("direction", "unknown")
    market_move_pct = ((end - start) / start) * 100 if start else 0.0
    trade_move_pct = ((exit_price - entry) / entry) * 100 if entry else 0.0
    if direction == "short":
        trade_move_pct *= -1
        directional_market_move = -market_move_pct
        favorable = ((entry - min_low) / entry) * 100 if entry else 0.0
        adverse = ((entry - max_high) / entry) * 100 if entry else 0.0
    else:
        directional_market_move = market_move_pct
        favorable = ((max_high - entry) / entry) * 100 if entry else 0.0
        adverse = ((min_low - entry) / entry) * 100 if entry else 0.0

    classification = _trade_replay_classification(trade, directional_market_move, favorable)
    entry_quality = _range_quality(direction, entry, min_low, max_high, "entry")
    exit_quality = _range_quality(direction, exit_price, min_low, max_high, "exit")
    summary = (
        f"{trade['symbol']} {direction} moved {round(trade_move_pct, 4)}% from entry to exit while "
        f"the replay window moved {round(directional_market_move, 4)}% in trade direction. "
        f"Favorable excursion was {round(favorable, 4)}%; adverse excursion was {round(adverse, 4)}%."
    )
    return {
        "trade_ref": trade.get("trade_ref", ""),
        "symbol": trade.get("symbol", "UNKNOWN"),
        "product_type": trade.get("product_type", "UNKNOWN"),
        "market_type": trade.get("market_type", "unknown"),
        "direction": direction,
        "status": "available",
        "classification": classification,
        "candles": len(window),
        "market_move_pct": round(market_move_pct, 4),
        "directional_market_move_pct": round(directional_market_move, 4),
        "entry_to_exit_move_pct": round(trade_move_pct, 4),
        "favorable_excursion_pct": round(favorable, 4),
        "adverse_excursion_pct": round(adverse, 4),
        "entry_quality": entry_quality,
        "exit_quality": exit_quality,
        "summary": summary,
    }


def _trade_replay_classification(trade: dict[str, Any], directional_market_move: float, favorable: float) -> str:
    pnl = trade.get("realized_pnl_usdt", 0.0)
    if pnl > 0 and directional_market_move >= 0:
        return "aligned_win"
    if pnl > 0:
        return "countertrend_win"
    if favorable >= 0.25 and directional_market_move >= 0:
        return "poor_exit_after_favorable_move"
    if directional_market_move < 0:
        return "wrong_side_loss"
    return "execution_loss"


def _range_quality(direction: str, price: float, low: float, high: float, stage: str) -> str:
    if not price or high <= low:
        return "not_scored"
    percentile = ((price - low) / (high - low)) * 100
    if direction == "short":
        percentile = 100 - percentile
    if stage == "entry":
        if percentile >= 75:
            return "chased upper range"
        if percentile <= 35:
            return "entered favorable range"
        return "entered mid range"
    if percentile >= 70:
        return "exited favorable range"
    if percentile <= 35:
        return "gave back range"
    return "exited mid range"


def _candles_for_symbol(candles_by_symbol: dict[str, list[dict[str, Any]]], symbol: str) -> list[dict[str, Any]]:
    candidates = [symbol, symbol.upper(), symbol.replace("USDT", "/USDT"), symbol.replace("/", "")]
    for key in candidates:
        series = candles_by_symbol.get(key)
        if series:
            return series
    return []


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    clean = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            clean.append(item)
    return clean
def build_findings(
    normalized: dict[str, Any],
    trades: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if normalized["demo_only"]:
        findings.append(
            {
                "severity": "info",
                "code": "demo_data",
                "message": "This audit uses demo-only simulated logs for hackathon reproduction.",
            }
        )
    if metrics["exposure"]["largest_position_concentration_pct"] >= 65:
        findings.append(
            {
                "severity": "high",
                "code": "position_concentration",
                "message": "Largest symbol exposure is above 65% of open notional.",
            }
        )
    if metrics["exposure"]["max_leverage"] > 3:
        findings.append(
            {
                "severity": "high",
                "code": "leverage_exposure",
                "message": "Observed leverage above 3x. Agent should justify or reduce risk.",
            }
        )
    if metrics["pnl"]["funding_pnl_usdt"] < 0:
        findings.append(
            {
                "severity": "medium",
                "code": "funding_bleed",
                "message": "Funding payments were net negative during the audited run.",
            }
        )
    if metrics["behavior"]["max_fills_in_day"] >= 10:
        findings.append(
            {
                "severity": "medium",
                "code": "overtrading",
                "message": "High intraday fill count suggests possible overtrading.",
            }
        )
    if metrics["behavior"]["missing_stop_loss_decisions"] > 0:
        findings.append(
            {
                "severity": "high",
                "code": "missing_stop_loss",
                "message": "One or more agent decisions did not include a stop-loss.",
            }
        )
    if trades and metrics["pnl"]["win_rate_pct"] < 40:
        findings.append(
            {
                "severity": "medium",
                "code": "low_win_rate",
                "message": "Completed trade win rate is below 40%.",
            }
        )
    return findings


def _unwrap_bitget_data(bundle: dict[str, Any]) -> dict[str, Any]:
    data = dict(bundle)
    raw = bundle.get("bitget_raw")
    if isinstance(raw, dict):
        data["positions"] = _tag_rows(_extract_data(raw.get("futures_positions", [])), "USDT-FUTURES", "futures_positions")
        data["orders"] = _tag_rows(_extract_data(raw.get("futures_orders", [])), "USDT-FUTURES", "futures_orders")
        data["fills"] = _tag_rows(_extract_data(raw.get("futures_fills", [])), "USDT-FUTURES", "futures_fills")
        data["account_snapshots"] = _extract_data(raw.get("account_assets", []))
        data["copy_trading_traders"] = _tag_rows(_extract_data(raw.get("copy_trading_traders", [])), "USDT-FUTURES", "copy_trading_traders")
        data["copy_trading_orders"] = _tag_rows(_extract_data(raw.get("copy_trading_orders", [])), "USDT-FUTURES", "copy_trading_orders")
        data["copy_trading_positions"] = _tag_rows(_extract_data(raw.get("copy_trading_positions", [])), "USDT-FUTURES", "copy_trading_positions")
    return data



def _tag_rows(rows: list[dict[str, Any]], product_type: str, source_section: str) -> list[dict[str, Any]]:
    tagged = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item.setdefault("product_type", product_type)
        item.setdefault("productType", product_type)
        item.setdefault("_source_section", source_section)
        tagged.append(item)
    return tagged
def _extract_data(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and payload.get("ok") is False and "error" in payload:
        return []
    if isinstance(payload, dict):
        payload = payload.get("data", payload)
    if isinstance(payload, dict):
        for key in ("list", "result", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return [payload]
    if isinstance(payload, list):
        return payload
    return []


def _normalize_order(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_ref": _hash_value(_pick(item, "order_id", "orderId", "id")),
        "symbol": _symbol(item),
        "product_type": _product_type(item),
        "market_type": _market_type(_product_type(item), [item], []),
        "side": _side(item),
        "type": str(_pick(item, "order_type", "orderType", "type", default="unknown")).lower(),
        "status": str(_pick(item, "status", "state", default="unknown")).lower(),
        "price": _num(_pick(item, "price", "avgPrice", default=0)),
        "quantity": _num(_pick(item, "quantity", "size", "baseVolume", default=0)),
        "created_at": _time(_pick(item, "created_at", "createdAt", "cTime", "timestamp", default="")),
    }


def _normalize_fill(item: dict[str, Any]) -> dict[str, Any]:
    qty = _num(_pick(item, "quantity", "size", "baseVolume", "fillSize", default=0))
    price = _num(_pick(item, "price", "fillPrice", default=0))
    return {
        "fill_ref": _hash_value(_pick(item, "fill_id", "fillId", "tradeId", "id")),
        "order_ref": _hash_value(_pick(item, "order_id", "orderId", "orderNo", default="")),
        "symbol": _symbol(item),
        "product_type": _product_type(item),
        "market_type": _market_type(_product_type(item), [item], []),
        "side": _side(item),
        "price": price,
        "quantity": qty,
        "notional_usdt": round(abs(price * qty), 8),
        "fee_usdt": abs(_num(_pick(item, "fee", "fee_usdt", "feeDetail", default=0))),
        "timestamp": _time(_pick(item, "timestamp", "time", "cTime", "created_at", default="")),
    }


def _normalize_position(item: dict[str, Any]) -> dict[str, Any]:
    notional = _num(_pick(item, "notional_usdt", "notional", "marginSize", "total", default=0))
    mark_price = _num(_pick(item, "mark_price", "markPrice", "price", default=0))
    qty = _num(_pick(item, "quantity", "size", "total", default=0))
    if notional == 0 and mark_price and qty:
        notional = mark_price * qty
    return {
        "position_ref": _hash_value(_pick(item, "position_id", "positionId", "id")),
        "symbol": _symbol(item),
        "product_type": _product_type(item),
        "market_type": _market_type(_product_type(item), [item], []),
        "side": str(_pick(item, "side", "holdSide", "posSide", default="unknown")).lower(),
        "notional_usdt": round(notional, 8),
        "leverage": _num(_pick(item, "leverage", "lever", default=1)),
        "unrealized_pnl_usdt": _num(_pick(item, "unrealized_pnl", "unrealizedPL", "upl", default=0)),
        "margin_usdt": _num(_pick(item, "margin", "marginSize", default=0)),
        "timestamp": _time(_pick(item, "timestamp", "cTime", "uTime", default="")),
    }


def _normalize_funding(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": _symbol(item),
        "product_type": _product_type(item),
        "market_type": _market_type(_product_type(item), [item], []),
        "amount_usdt": _num(_pick(item, "amount_usdt", "amount", "funding", "pnl", default=0)),
        "rate": _num(_pick(item, "rate", "fundingRate", default=0)),
        "timestamp": _time(_pick(item, "timestamp", "time", "fundingTime", default="")),
    }


def _normalize_decision(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_ref": _hash_value(_pick(item, "decision_id", "id")),
        "symbol": _symbol(item),
        "action": str(_pick(item, "action", "side", default="unknown")).lower(),
        "confidence": _num(_pick(item, "confidence", default=0)),
        "stop_loss": _num(_pick(item, "stop_loss", "stopLoss", default=0)),
        "take_profit": _num(_pick(item, "take_profit", "takeProfit", default=0)),
        "rationale": str(_pick(item, "rationale", "reason", default="")),
        "timestamp": _time(_pick(item, "timestamp", "created_at", default="")),
    }


def _usable_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in rows if not (isinstance(item, dict) and item.get("ok") is False and "error" in item)]
def _normalize_skill_hub(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    normalized = {}
    for key, payload in value.items():
        name = str(key).replace("_", "-").lower()
        if isinstance(payload, dict):
            normalized[name] = payload
        else:
            normalized[name] = {"summary": str(payload), "stance": "observed"}
    return normalized


def _normalize_copy_trading(data: dict[str, Any]) -> dict[str, Any]:
    explicit = data.get("copy_trading_pings", data.get("copy_trading", []))
    if isinstance(explicit, dict) and isinstance(explicit.get("pings"), list):
        explicit = explicit["pings"]
    if isinstance(explicit, dict):
        explicit = [explicit]
    pings = [_normalize_copy_ping(item) for item in explicit if isinstance(item, dict)] if isinstance(explicit, list) else []

    raw_traders = _usable_rows(_extract_data(data.get("copy_trading_traders", [])))
    raw_orders = _usable_rows(_extract_data(data.get("copy_trading_orders", [])))
    raw_positions = _usable_rows(_extract_data(data.get("copy_trading_positions", [])))
    for item in raw_positions[:5]:
        if isinstance(item, dict):
            pings.append(_normalize_copy_ping(item))

    return {
        "pings": pings,
        "raw_counts": {
            "traders": len(raw_traders),
            "orders": len(raw_orders),
            "positions": len(raw_positions),
        },
    }


def _normalize_copy_ping(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": _symbol(item),
        "direction": str(_pick(item, "direction", "side", "holdSide", "posSide", default="unknown")).lower(),
        "source": str(_pick(item, "source", default="copy_trading")),
        "notional_usdt": _num(_pick(item, "notional_usdt", "notional", "marginSize", "total", default=0)),
        "followers": int(_safe_num(_pick(item, "followers", "followerCount", "copyTraderCount", default=0))),
        "leader_drawdown_pct": _safe_num(_pick(item, "leader_drawdown_pct", "drawdown", "maxDrawdown", default=0)),
        "summary": str(_pick(item, "summary", "note", default="Copy-trading activity supplied by the log bundle.")),
    }
def _empty_position() -> dict[str, Any]:
    return {
        "direction": "",
        "quantity": 0.0,
        "avg_entry": 0.0,
        "entry_time": "",
        "entry_fees": 0.0,
        "product_type": "",
    }


def _open_or_add(pos: dict[str, Any], direction: str, qty: float, price: float, fee: float, fill: dict[str, Any]) -> None:
    signed_qty = qty if direction == "long" else -qty
    current_abs = abs(pos["quantity"])
    new_abs = current_abs + qty
    if new_abs <= 0:
        return
    pos["avg_entry"] = ((pos["avg_entry"] * current_abs) + (price * qty)) / new_abs
    pos["quantity"] += signed_qty
    pos["direction"] = direction
    pos["entry_time"] = pos["entry_time"] or fill["timestamp"]
    pos["entry_fees"] += fee
    pos["product_type"] = pos.get("product_type") or fill.get("product_type", "UNKNOWN")


def _close_trade(
    symbol: str,
    direction: str,
    qty: float,
    exit_price: float,
    exit_fee: float,
    fill: dict[str, Any],
    pos: dict[str, Any],
) -> dict[str, Any]:
    entry_price = pos["avg_entry"]
    gross = (exit_price - entry_price) * qty if direction == "long" else (entry_price - exit_price) * qty
    allocated_entry_fee = pos["entry_fees"] * (qty / abs(pos["quantity"])) if pos["quantity"] else 0.0
    pnl = gross - allocated_entry_fee - exit_fee
    return {
        "trade_ref": _hash_value(f"{symbol}:{pos['entry_time']}:{fill['timestamp']}:{qty}"),
        "symbol": symbol,
        "direction": direction,
        "product_type": pos.get("product_type") or fill.get("product_type", "UNKNOWN"),
        "market_type": _market_type(pos.get("product_type") or fill.get("product_type", "UNKNOWN"), [], []),
        "entry_time": pos["entry_time"],
        "exit_time": fill["timestamp"],
        "entry_price": round(entry_price, 8),
        "exit_price": round(exit_price, 8),
        "quantity": round(qty, 8),
        "notional_usdt": round(entry_price * qty, 4),
        "fees_usdt": round(allocated_entry_fee + exit_fee, 4),
        "realized_pnl_usdt": round(pnl, 4),
        "return_pct": round((pnl / (entry_price * qty)) * 100, 4) if entry_price and qty else 0.0,
        "outcome": "win" if pnl > 0 else "loss",
    }


def _order_audit_confidence(normalized: dict[str, Any], completed_count: int) -> str:
    fills_count = len(normalized["fills"])
    orders_count = len(normalized["orders"])
    has_timestamps = all(fill["timestamp"] for fill in normalized["fills"])
    has_positions = bool(normalized["positions"])
    if fills_count and completed_count and has_timestamps and has_positions:
        return "high"
    if fills_count and (completed_count or orders_count):
        return "medium"
    return "low"


def _order_audit_evidence(
    normalized: dict[str, Any],
    trades: list[dict[str, Any]],
    metrics: dict[str, Any],
    findings: list[dict[str, Any]],
    market_replay: dict[str, Any],
) -> list[dict[str, str]]:
    pnl = metrics["pnl"]
    exposure = metrics["exposure"]
    behavior = metrics["behavior"]
    evidence = [
        {
            "severity": "info" if normalized["market_type"] != "unknown" else "medium",
            "signal": "Market type",
            "message": f"Detected {normalized['market_type']} market structure from {normalized['product_type']} logs.",
        },
        {
            "severity": "info" if market_replay["status"] in {"available", "partial"} else "medium",
            "signal": "Chart replay",
            "message": market_replay.get("summary", "No market replay summary available."),
        },        {
            "severity": "info",
            "signal": "Data coverage",
            "message": f"Analyzed {len(normalized['orders'])} orders, {len(normalized['fills'])} fills, and reconstructed {len(trades)} completed trades.",
        },
        {
            "severity": "high" if pnl["total_realized_pnl_usdt"] < 0 else "info",
            "signal": "Realized outcome",
            "message": f"Realized PnL is {pnl['total_realized_pnl_usdt']} USDT with {pnl['win_rate_pct']}% win rate and {pnl['profit_factor']} profit factor.",
        },
        {
            "severity": "high" if exposure["max_leverage"] > 3 else "info",
            "signal": "Leverage",
            "message": f"Maximum observed leverage is {exposure['max_leverage']}x with {exposure['weighted_leverage']}x weighted leverage.",
        },
        {
            "severity": "high" if exposure["largest_position_concentration_pct"] >= 65 else "info",
            "signal": "Concentration",
            "message": f"Largest symbol concentration is {exposure['largest_position_concentration_pct']}% of open notional.",
        },
        {
            "severity": "medium" if pnl["funding_pnl_usdt"] < 0 else "info",
            "signal": "Funding drag",
            "message": f"Net funding during the audited run is {pnl['funding_pnl_usdt']} USDT.",
        },
    ]
    if behavior["missing_stop_loss_decisions"]:
        evidence.append(
            {
                "severity": "high",
                "signal": "Risk controls",
                "message": f"{behavior['missing_stop_loss_decisions']} agent decision(s) were missing stop-loss values.",
            }
        )
    if behavior["max_fills_in_day"] >= 10:
        evidence.append(
            {
                "severity": "medium",
                "signal": "Order frequency",
                "message": f"Peak trading day had {behavior['max_fills_in_day']} fills, which may indicate overtrading.",
            }
        )
    if not normalized["fills"]:
        evidence.append(
            {
                "severity": "high",
                "signal": "Missing fills",
                "message": "No fills were present, so execution quality could not be reconstructed.",
            }
        )
    return evidence


def _order_audit_recommendations(
    metrics: dict[str, Any],
    findings: list[dict[str, Any]],
    completed_count: int,
    market_replay: dict[str, Any],
) -> list[str]:
    codes = {item["code"] for item in findings}
    recommendations: list[str] = []
    if "missing_stop_loss" in codes:
        recommendations.append("Flag this agent pattern: every future entry decision should include a stop-loss before it can be trusted.")
    if "leverage_exposure" in codes:
        recommendations.append("For the next iteration, reduce leverage or require the agent to explain why this completed trade needed that exposure.")
    if "position_concentration" in codes:
        recommendations.append("Tune sizing rules so one symbol cannot dominate realized and open risk.")
    if "funding_bleed" in codes:
        recommendations.append("Add a funding-rate replay check before holding futures trades through settlement windows again.")
    if metrics["pnl"]["profit_factor"] and metrics["pnl"]["profit_factor"] < 1:
        recommendations.append("Treat this strategy version as unproven until profit factor recovers above 1.0 on fresh completed trade logs.")
    if completed_count == 0:
        recommendations.append("Upload fills that include both entry and exit legs so the audit can score the completed trade lifecycle.")
    if market_replay.get("status") not in {"available", "partial"}:
        recommendations.append("Attach candle or order-book context from the agent/exporter so feedback can compare the trade against actual market movement.")
    else:
        recommendations.extend(market_replay.get("recommendations", [])[:3])
    if not recommendations:
        recommendations.append("This completed trade log passed the current audit thresholds; keep collecting fresh logs and compare future iterations against this baseline.")
    return _dedupe(recommendations)


def _order_audit_summary(
    label: str,
    score: int,
    confidence: str,
    pnl: dict[str, Any],
    exposure: dict[str, Any],
    behavior: dict[str, Any],
    completed_count: int,
    market_replay: dict[str, Any],
) -> str:
    return (
        f"{label}: scored {score}/100 with {confidence} confidence after reconstructing "
        f"{completed_count} completed trade(s). Realized PnL is {pnl['total_realized_pnl_usdt']} USDT, "
        f"max drawdown is {pnl['max_drawdown_pct']}%, max leverage is {exposure['max_leverage']}x, "
        f"chart replay status is {market_replay['status']}, and "
        f"{behavior['missing_stop_loss_decisions']} decision(s) missed stop-loss controls."
    )


def _starting_equity(normalized: dict[str, Any]) -> float:
    for snapshot in normalized.get("account_snapshots", []):
        value = snapshot.get("equity_usdt") or snapshot.get("equity") or snapshot.get("totalEquity")
        if value not in (None, ""):
            return float(value)
    margin = sum(abs(item.get("margin_usdt", 0.0)) for item in normalized.get("positions", []))
    return margin if margin > 0 else 10000.0


def _equity_curve(trades: list[dict[str, Any]], starting_equity: float) -> list[float]:
    equity = starting_equity
    curve = [equity]
    for trade in trades:
        equity += trade["realized_pnl_usdt"]
        curve.append(equity)
    return curve


def _max_drawdown_pct(curve: list[float]) -> float:
    if not curve:
        return 0.0
    peak = curve[0]
    max_drawdown = 0.0
    for equity in curve:
        peak = max(peak, equity)
        drawdown = peak - equity
        denominator = max(abs(peak), 1.0)
        max_drawdown = max(max_drawdown, drawdown / denominator)
    return max_drawdown * 100


def _position_concentration(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, float] = defaultdict(float)
    for item in positions:
        totals[item["symbol"]] += abs(item["notional_usdt"])
    total = sum(totals.values())
    rows = [
        {
            "symbol": symbol,
            "notional_usdt": round(notional, 4),
            "share_pct": round((notional / total) * 100, 2) if total else 0.0,
        }
        for symbol, notional in totals.items()
    ]
    return sorted(rows, key=lambda item: item["notional_usdt"], reverse=True)


def _overtrading_metrics(fills: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for fill in fills:
        day = fill["timestamp"][:10] if fill["timestamp"] else "unknown"
        counts[day] += 1
    return {
        "max_fills_in_day": max(counts.values() or [0]),
        "active_trading_days": len(counts),
    }


def _risk_score(
    pnl: dict[str, Any],
    exposure: dict[str, Any],
    behavior: dict[str, Any],
) -> int:
    score = 15
    score += min(25, exposure["largest_position_concentration_pct"] * 0.28)
    score += min(25, max(0, exposure["max_leverage"] - 1) * 7)
    score += min(15, behavior["max_fills_in_day"] * 1.2)
    score += min(15, behavior["missing_stop_loss_decisions"] * 6)
    if pnl["funding_pnl_usdt"] < 0:
        score += min(10, abs(pnl["funding_pnl_usdt"]))
    if pnl["max_drawdown_pct"] > 0:
        score += min(20, pnl["max_drawdown_pct"] * 0.8)
    return int(max(0, min(100, round(score))))


def _health_grade(risk_score: int) -> str:
    if risk_score < 30:
        return "A"
    if risk_score < 45:
        return "B"
    if risk_score < 65:
        return "C"
    if risk_score < 80:
        return "D"
    return "F"



def _infer_product_types(
    data: dict[str, Any],
    orders: list[dict[str, Any]],
    fills: list[dict[str, Any]],
    positions: list[dict[str, Any]],
) -> list[str]:
    values = []
    for key in ("product_type", "productType", "market_type", "marketType", "accountType", "category"):
        if data.get(key):
            values.append(_canonical_product_type(data[key]))
    for item in [*orders, *fills, *positions, *data.get("funding_payments", [])]:
        if isinstance(item, dict):
            values.append(_product_type(item, default=""))
    if positions or data.get("funding_payments"):
        values.append("USDT-FUTURES")
    clean = sorted({item for item in values if item})
    if "MIXED" in clean:
        return ["MIXED"]
    return clean


def _with_default_product_type(item: dict[str, Any], product_type: str) -> dict[str, Any]:
    if _product_type(item, default=""):
        return item
    enriched = dict(item)
    enriched["product_type"] = product_type
    enriched["productType"] = product_type
    return enriched


def _product_type(item: dict[str, Any], default: str = "UNKNOWN") -> str:
    explicit = _pick(
        item,
        "product_type",
        "productType",
        "market_type",
        "marketType",
        "instType",
        "category",
        "accountType",
        default="",
    )
    if explicit:
        return _canonical_product_type(explicit)
    source = str(item.get("_source_section", "")).lower()
    if "future" in source or "copy_trading" in source:
        return "USDT-FUTURES"
    futures_keys = {"leverage", "lever", "holdSide", "posSide", "marginCoin", "marginMode", "tradeSide", "reduceOnly"}
    if any(key in item for key in futures_keys):
        return "USDT-FUTURES"
    return default


def _canonical_product_type(value: Any) -> str:
    text = str(value or "").replace("_", "-").upper()
    if not text:
        return ""
    if text in {"SPOT", "SPOT-USDT"} or "SPOT" in text:
        return "SPOT"
    if any(token in text for token in ("FUTURE", "PERP", "SWAP", "MIX", "CONTRACT", "LINEAR")):
        if "USDC" in text:
            return "USDC-FUTURES"
        if "COIN" in text:
            return "COIN-FUTURES"
        return "USDT-FUTURES"
    if text in {"MIXED", "MULTI"}:
        return "MIXED"
    return text


def _market_type(product_type: str, positions: list[dict[str, Any]], funding_payments: list[Any]) -> str:
    text = str(product_type or "").upper()
    if text == "MIXED":
        return "mixed"
    if "FUTURES" in text or positions or funding_payments:
        return "futures"
    if text == "SPOT":
        return "spot"
    return "unknown"


def _normalize_market_context(value: Any) -> dict[str, Any]:
    if not value:
        return {"source": "none", "fetch_status": "not_supplied", "candles": {}, "requests": []}
    source = "supplied"
    fetch_status = "supplied"
    requests = []
    payload = value
    if isinstance(value, dict):
        source = str(value.get("source", source))
        fetch_status = str(value.get("fetch_status", value.get("status", fetch_status)))
        requests = value.get("requests", []) if isinstance(value.get("requests", []), list) else []
        payload = value.get("candles", value.get("ohlcv", value.get("data", value)))

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if isinstance(payload, dict):
        for key, rows in payload.items():
            if key in {"source", "fetch_status", "status", "requests"}:
                continue
            target = str(key).replace("/", "").upper()
            if isinstance(rows, dict) and isinstance(rows.get("candles"), list):
                rows = rows["candles"]
            if isinstance(rows, list):
                grouped[target].extend(_normalize_candle(row) for row in rows)
    elif isinstance(payload, list):
        for row in payload:
            candle = _normalize_candle(row)
            symbol = "UNKNOWN"
            if isinstance(row, dict):
                symbol = _symbol(row)
            grouped[symbol].append(candle)

    cleaned = {}
    for symbol, rows in grouped.items():
        candles = [row for row in rows if row.get("timestamp") and row.get("close")]
        candles.sort(key=lambda item: item.get("dt") or datetime.min.replace(tzinfo=timezone.utc))
        cleaned[symbol] = candles
    return {"source": source, "fetch_status": fetch_status, "candles": cleaned, "requests": requests}


def _normalize_candle(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        timestamp = _time(_pick(row, "timestamp", "time", "ts", "t", "openTime", default=""))
        candle = {
            "timestamp": timestamp,
            "open": _safe_num(_pick(row, "open", "o", default=0)),
            "high": _safe_num(_pick(row, "high", "h", default=0)),
            "low": _safe_num(_pick(row, "low", "l", default=0)),
            "close": _safe_num(_pick(row, "close", "c", default=0)),
            "volume": _safe_num(_pick(row, "volume", "v", "baseVolume", default=0)),
        }
    elif isinstance(row, (list, tuple)) and len(row) >= 5:
        timestamp = _time(row[0])
        candle = {
            "timestamp": timestamp,
            "open": _safe_num(row[1]),
            "high": _safe_num(row[2]),
            "low": _safe_num(row[3]),
            "close": _safe_num(row[4]),
            "volume": _safe_num(row[5]) if len(row) > 5 else 0.0,
        }
    else:
        candle = {"timestamp": "", "open": 0.0, "high": 0.0, "low": 0.0, "close": 0.0, "volume": 0.0}
    candle["dt"] = _parse_time(candle["timestamp"])
    return candle


def _parse_time(value: Any) -> datetime | None:
    text = _time(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
def _redact(value: Any) -> Any:
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = key.replace("-", "_").lower()
            compact_key = normalized_key.replace("_", "")
            if normalized_key in HASH_KEYS or compact_key in HASH_KEYS:
                clean[f"{key}_hash"] = _hash_value(item)
            elif normalized_key in SENSITIVE_KEYS or compact_key in SENSITIVE_KEYS:
                clean[key] = "[redacted]"
            else:
                clean[key] = _redact(item)
        return clean
    return value


def _pick(item: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return default


def _symbol(item: dict[str, Any]) -> str:
    return str(_pick(item, "symbol", "instId", "contract", default="UNKNOWN")).replace("-", "").upper()


def _side(item: dict[str, Any]) -> str:
    side = str(_pick(item, "side", "tradeSide", "direction", default="")).lower()
    if side in {"open_long", "close_short", "long", "buy"}:
        return "buy"
    if side in {"open_short", "close_long", "short", "sell"}:
        return "sell"
    return side


def _num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, dict):
        return 0.0
    return float(value)


def _safe_num(value: Any) -> float:
    try:
        return _num(value)
    except (TypeError, ValueError):
        return 0.0


def _time(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        number = int(value)
        if number > 10_000_000_000:
            number = number // 1000
        return datetime.fromtimestamp(number, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    text = str(value)
    if text.endswith("Z"):
        return text
    return text


def _hash_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return digest[:12]


