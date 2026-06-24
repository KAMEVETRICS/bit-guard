from __future__ import annotations

from typing import Any

from .storage import utc_now_iso


REQUIRED_FIELDS = ("agent_id", "strategy_id", "symbol", "side", "entry_price")


def evaluate_intent(intent: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_intent(intent)
    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for field in REQUIRED_FIELDS:
        if not normalized.get(field):
            violations.append(_violation("missing_field", f"Missing required field: {field}"))

    symbol = normalized.get("symbol", "")
    if policy["allowed_symbols"] and symbol not in policy["allowed_symbols"]:
        violations.append(_violation("symbol_not_allowed", f"{symbol} is not allowed by policy"))

    product_type = normalized.get("product_type", "SPOT")
    if policy["allowed_product_types"] and product_type not in policy["allowed_product_types"]:
        violations.append(
            _violation("product_not_allowed", f"{product_type} is not allowed by policy")
        )

    side = normalized.get("side", "")
    if side not in {"buy", "sell"}:
        violations.append(_violation("invalid_side", "side must be buy or sell"))
    if side in policy["blocked_sides"]:
        violations.append(_violation("side_blocked", f"{side} is blocked by policy"))

    notional = _notional(normalized)
    normalized["notional_usdt"] = round(notional, 6)
    if notional <= 0:
        violations.append(_violation("invalid_notional", "notional_usdt must be positive"))
    elif notional > policy["max_notional_usdt"]:
        violations.append(
            _violation(
                "max_notional_exceeded",
                f"{notional:.2f} USDT exceeds max {policy['max_notional_usdt']:.2f} USDT",
            )
        )

    leverage = _as_float(normalized.get("leverage"), default=1.0)
    normalized["leverage"] = leverage
    if leverage <= 0:
        violations.append(_violation("invalid_leverage", "leverage must be positive"))
    elif leverage > policy["max_leverage"]:
        violations.append(
            _violation(
                "max_leverage_exceeded",
                f"{leverage:g}x exceeds max {policy['max_leverage']:g}x",
            )
        )
    if product_type == "SPOT" and leverage != 1:
        violations.append(_violation("spot_leverage", "spot intents must use 1x leverage"))

    rr = _risk_reward(normalized)
    normalized["risk_reward"] = rr
    if policy["require_stop_loss"] and normalized.get("stop_loss") in (None, ""):
        violations.append(_violation("missing_stop_loss", "stop_loss is required"))
    if rr is None:
        if normalized.get("take_profit") in (None, ""):
            warnings.append(_warning("missing_take_profit", "take_profit is missing"))
    elif rr <= 0:
        violations.append(_violation("invalid_exit_geometry", "stop_loss/take_profit are inverted"))
    elif rr < policy["min_risk_reward"]:
        violations.append(
            _violation(
                "risk_reward_too_low",
                f"risk_reward {rr:.2f} is below minimum {policy['min_risk_reward']:.2f}",
            )
        )

    risk_score = _risk_score(violations, warnings, notional, policy)
    approved = not violations
    decision = "approved" if approved else "rejected"
    route = "dry_run_accept" if approved and policy["dry_run"] else "forward_to_exchange"
    if not approved:
        route = "blocked"

    return {
        "checked_at": utc_now_iso(),
        "decision": decision,
        "route": route,
        "risk_score": risk_score,
        "violations": violations,
        "warnings": warnings,
        "normalized_intent": normalized,
        "policy_snapshot": {
            "policy_name": policy.get("policy_name"),
            "dry_run": policy["dry_run"],
            "max_notional_usdt": policy["max_notional_usdt"],
            "max_leverage": policy["max_leverage"],
            "require_stop_loss": policy["require_stop_loss"],
            "min_risk_reward": policy["min_risk_reward"],
        },
    }


def evaluate_intents(intents: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    decisions = [evaluate_intent(intent, policy) for intent in intents]
    approved = sum(1 for item in decisions if item["decision"] == "approved")
    rejected = len(decisions) - approved
    return {
        "generated_at": utc_now_iso(),
        "summary": {
            "total": len(decisions),
            "approved": approved,
            "rejected": rejected,
            "approval_rate_pct": round((approved / len(decisions)) * 100, 2) if decisions else 0,
        },
        "decisions": decisions,
    }


def _normalize_intent(intent: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(intent)
    normalized["symbol"] = str(normalized.get("symbol", "")).upper()
    normalized["product_type"] = str(normalized.get("product_type", "SPOT")).upper()
    normalized["side"] = str(normalized.get("side", "")).lower()
    for key in ("entry_price", "quantity", "notional_usdt", "leverage", "stop_loss", "take_profit"):
        if key in normalized and normalized[key] not in (None, ""):
            normalized[key] = _as_float(normalized[key])
    return normalized


def _notional(intent: dict[str, Any]) -> float:
    explicit = _as_float(intent.get("notional_usdt"), default=0.0)
    if explicit > 0:
        return explicit
    quantity = _as_float(intent.get("quantity"), default=0.0)
    entry = _as_float(intent.get("entry_price"), default=0.0)
    return quantity * entry


def _risk_reward(intent: dict[str, Any]) -> float | None:
    entry = _as_float(intent.get("entry_price"), default=0.0)
    stop = intent.get("stop_loss")
    take = intent.get("take_profit")
    side = intent.get("side")
    if not entry or stop in (None, "") or take in (None, ""):
        return None
    stop = _as_float(stop)
    take = _as_float(take)
    if side == "buy":
        risk = entry - stop
        reward = take - entry
    elif side == "sell":
        risk = stop - entry
        reward = entry - take
    else:
        return None
    if risk <= 0:
        return -1.0
    return round(reward / risk, 4)


def _risk_score(
    violations: list[dict[str, str]],
    warnings: list[dict[str, str]],
    notional: float,
    policy: dict[str, Any],
) -> int:
    score = 100 - (len(violations) * 22) - (len(warnings) * 6)
    if policy["max_notional_usdt"]:
        utilization = min(max(notional / policy["max_notional_usdt"], 0), 1)
        score -= int(utilization * 10)
    return max(0, min(100, score))


def _violation(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message, "severity": "hard"}


def _warning(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message, "severity": "soft"}


def _as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)
