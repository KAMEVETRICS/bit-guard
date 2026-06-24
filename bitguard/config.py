from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


FALSE_VALUES = {"0", "false", "off", "no", ""}


@dataclass(frozen=True)
class RuntimeConfig:
    api_keys: tuple[str, ...]
    require_auth: bool
    db_path: str
    cors_origins: tuple[str, ...]
    max_body_bytes: int
    rate_limit_per_minute: int
    public_candle_fetch_enabled: bool


def load_runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        api_keys=_csv_env("BITGUARD_API_KEYS"),
        require_auth=_bool_env("BITGUARD_REQUIRE_AUTH", default=False),
        db_path=os.environ.get("BITGUARD_DB_PATH", str(Path("data") / "bitguard.db")),
        cors_origins=_csv_env("BITGUARD_CORS_ORIGINS"),
        max_body_bytes=_int_env("BITGUARD_MAX_BODY_BYTES", 1_000_000),
        rate_limit_per_minute=_int_env("BITGUARD_RATE_LIMIT_PER_MINUTE", 60),
        public_candle_fetch_enabled=_bool_env("BITGUARD_FETCH_PUBLIC_CANDLES", default=True),
    )


def _csv_env(name: str) -> tuple[str, ...]:
    value = os.environ.get(name, "")
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in FALSE_VALUES


def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, str(default))))
    except ValueError:
        return default
