from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


VALID_SIDES = {"buy", "sell", "long", "short", "open_long", "open_short", "close_long", "close_short"}


class ValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def validate_evidence_bundle(payload: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        raise ValidationError(["payload must be a JSON object"])

    _required_text(payload, "agent_id", errors)
    _required_text(payload, "run_id", errors)

    if isinstance(payload.get("bitget_raw"), dict):
        if errors:
            raise ValidationError(errors)
        return payload

    fills = payload.get("fills")
    if not isinstance(fills, list) or not fills:
        errors.append("fills must be a non-empty array")
    elif isinstance(fills, list):
        for index, fill in enumerate(fills):
            _validate_fill(fill, index, errors)

    if errors:
        raise ValidationError(errors)
    return payload


def _required_text(payload: dict[str, Any], key: str, errors: list[str]) -> None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} is required")


def _validate_fill(fill: Any, index: int, errors: list[str]) -> None:
    prefix = f"fills[{index}]"
    if not isinstance(fill, dict):
        errors.append(f"{prefix} must be an object")
        return

    for key in ("symbol", "side", "price", "quantity", "timestamp"):
        if fill.get(key) in (None, ""):
            errors.append(f"{prefix}.{key} is required")

    side = str(fill.get("side", "")).lower()
    if side and side not in VALID_SIDES:
        errors.append(f"{prefix}.side must be one of {sorted(VALID_SIDES)}")

    for key in ("price", "quantity"):
        try:
            value = float(fill.get(key))
        except (TypeError, ValueError):
            errors.append(f"{prefix}.{key} must be numeric")
            continue
        if value <= 0:
            errors.append(f"{prefix}.{key} must be greater than zero")

    if fill.get("timestamp") not in (None, "") and _parse_time(fill.get("timestamp")) is None:
        errors.append(f"{prefix}.timestamp must be ISO-8601 or unix time")


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
