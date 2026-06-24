from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json(path: str | Path, payload: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_usage_record(
    path: str | Path,
    event_type: str,
    request_payload: Any,
    response_payload: Any,
) -> dict[str, Any]:
    record = {
        "timestamp": utc_now_iso(),
        "event_type": event_type,
        "request": request_payload,
        "response": response_payload,
    }
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def read_usage_records(path: str | Path, limit: int = 50) -> list[dict[str, Any]]:
    log_path = Path(path)
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()[-limit:]
    records: list[dict[str, Any]] = []
    for line in lines:
        if line.strip():
            records.append(json.loads(line))
    return records
