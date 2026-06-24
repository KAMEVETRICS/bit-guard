from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_POLICY: dict[str, Any] = {
    "policy_name": "default-local-guardrail",
    "dry_run": True,
    "max_notional_usdt": 250.0,
    "max_leverage": 2.0,
    "require_stop_loss": True,
    "min_risk_reward": 1.2,
    "allowed_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "allowed_product_types": ["SPOT", "USDT-FUTURES"],
    "blocked_sides": [],
}


def load_policy(path: str | Path | None = None) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    loaded_from_file = False
    if path:
        policy_path = Path(path)
        if policy_path.exists():
            with policy_path.open("r", encoding="utf-8") as handle:
                policy.update(json.load(handle))
            loaded_from_file = True

    if not loaded_from_file:
        env_overrides = {
            "dry_run": _env_bool("DRY_RUN"),
            "max_notional_usdt": _env_float("MAX_NOTIONAL_USDT"),
            "max_leverage": _env_float("MAX_LEVERAGE"),
            "require_stop_loss": _env_bool("REQUIRE_STOP_LOSS"),
        }
        for key, value in env_overrides.items():
            if value is not None:
                policy[key] = value

    return normalize_policy(policy)


def normalize_policy(policy: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(policy)
    normalized["dry_run"] = bool(normalized.get("dry_run", True))
    normalized["max_notional_usdt"] = float(normalized.get("max_notional_usdt", 250.0))
    normalized["max_leverage"] = float(normalized.get("max_leverage", 2.0))
    normalized["require_stop_loss"] = bool(normalized.get("require_stop_loss", True))
    normalized["min_risk_reward"] = float(normalized.get("min_risk_reward", 1.2))
    normalized["allowed_symbols"] = [str(s).upper() for s in normalized.get("allowed_symbols", [])]
    normalized["allowed_product_types"] = [
        str(s).upper() for s in normalized.get("allowed_product_types", [])
    ]
    normalized["blocked_sides"] = [str(s).lower() for s in normalized.get("blocked_sides", [])]
    return normalized


def _env_float(key: str) -> float | None:
    value = os.environ.get(key)
    if value is None or value == "":
        return None
    return float(value)


def _env_bool(key: str) -> bool | None:
    value = os.environ.get(key)
    if value is None or value == "":
        return None
    return value.lower() in {"1", "true", "yes", "on"}
