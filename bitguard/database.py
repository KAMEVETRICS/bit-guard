from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .storage import utc_now_iso


SCHEMA = """
CREATE TABLE IF NOT EXISTS usage_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    summary_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    agent_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    pattern_summary_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def init_database(path: str | Path) -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA)


def ready_status(path: str | Path) -> dict[str, Any]:
    try:
        init_database(path)
        with sqlite3.connect(path) as connection:
            connection.execute("SELECT 1").fetchone()
        return {"ok": True, "path": str(path), "writable": True}
    except Exception as exc:
        return {"ok": False, "path": str(path), "writable": False, "error": type(exc).__name__, "message": str(exc)}


def record_usage(
    path: str | Path,
    event_type: str,
    request_payload: dict[str, Any],
    summary: dict[str, Any],
    status: str = "ok",
) -> dict[str, Any]:
    init_database(path)
    record = {
        "timestamp": utc_now_iso(),
        "event_type": event_type,
        "agent_id": str(request_payload.get("agent_id", "unknown-agent")),
        "run_id": str(request_payload.get("run_id", "unknown-run")),
        "source": str(request_payload.get("source", "unknown")),
        "status": status,
        "summary": summary,
    }
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO usage_records (timestamp, event_type, agent_id, run_id, source, status, summary_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["timestamp"],
                record["event_type"],
                record["agent_id"],
                record["run_id"],
                record["source"],
                record["status"],
                json.dumps(summary, sort_keys=True),
            ),
        )
    return record


def record_audit_run(path: str | Path, request_id: str, report: dict[str, Any]) -> None:
    init_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO audit_runs
            (request_id, agent_id, run_id, summary_json, pattern_summary_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                str(report.get("agent_id", "unknown-agent")),
                str(report.get("run_id", "unknown-run")),
                json.dumps(report.get("summary", {}), sort_keys=True),
                json.dumps(report.get("pattern_library", {}).get("summary", {}), sort_keys=True),
                utc_now_iso(),
            ),
        )


def read_usage_records_db(path: str | Path, limit: int = 50) -> list[dict[str, Any]]:
    init_database(path)
    rows = []
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            """
            SELECT timestamp, event_type, agent_id, run_id, source, status, summary_json
            FROM usage_records
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(limit, 500)),),
        )
        rows = list(cursor.fetchall())
    records = []
    for row in rows:
        records.append(
            {
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "agent_id": row["agent_id"],
                "run_id": row["run_id"],
                "source": row["source"],
                "status": row["status"],
                "summary": json.loads(row["summary_json"]),
            }
        )
    return records
