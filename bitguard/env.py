from __future__ import annotations

import os
from pathlib import Path


COLLECTOR_SECRET_KEYS = (
    "BITGET_API_KEY",
    "BITGET_SECRET_KEY",
    "BITGET_PASSPHRASE",
)

INTELLIGENCE_SECRET_KEYS = (
    "TRUENORTH_API_KEY",
    "TRUENORTH_MCP_URL",
    "OPENROUTER_API_KEY",
)

SECRET_KEYS = COLLECTOR_SECRET_KEYS + INTELLIGENCE_SECRET_KEYS


def load_dotenv(path: str | Path = ".env", override: bool = False) -> dict[str, str]:
    env_path = Path(path)
    loaded: dict[str, str] = {}
    if not env_path.exists():
        return loaded

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        loaded[key] = value
        if override or key not in os.environ:
            os.environ[key] = value
    return loaded


def secret_status(keys: tuple[str, ...] = SECRET_KEYS) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key in keys:
        value = os.environ.get(key, "")
        rows.append({"key": key, "present": bool(value), "length": len(value)})
    return rows


def collector_secret_status() -> list[dict[str, object]]:
    return secret_status(COLLECTOR_SECRET_KEYS)


def intelligence_secret_status() -> list[dict[str, object]]:
    return secret_status(INTELLIGENCE_SECRET_KEYS)

