import json
import sqlite3
import unittest
import uuid
from pathlib import Path

from bitguard.database import read_usage_records_db, record_audit_run, record_usage


def _db_path() -> Path:
    Path("data").mkdir(exist_ok=True)
    return Path("data") / f"test_{uuid.uuid4().hex}.db"


class DatabaseTest(unittest.TestCase):
    def test_writes_usage_and_audit_summaries(self):
        db_path = _db_path()
        record_usage(
            db_path,
            "api.sentinel.audit",
            {"agent_id": "agent-1", "run_id": "run-1", "source": "demo-agent-log-schema"},
            {"completed_trades": 2},
        )
        record_audit_run(
            db_path,
            "req-1",
            {
                "agent_id": "agent-1",
                "run_id": "run-1",
                "summary": {"completed_trades": 2},
                "pattern_library": {"summary": {"total_patterns": 1}},
            },
        )

        records = read_usage_records_db(db_path, limit=5)
        self.assertEqual(records[0]["event_type"], "api.sentinel.audit")
        self.assertEqual(records[0]["summary"]["completed_trades"], 2)

        with sqlite3.connect(db_path) as connection:
            row = connection.execute("SELECT summary_json, pattern_summary_json FROM audit_runs WHERE request_id = ?", ("req-1",)).fetchone()
        self.assertEqual(json.loads(row[0])["completed_trades"], 2)
        self.assertEqual(json.loads(row[1])["total_patterns"], 1)


if __name__ == "__main__":
    unittest.main()