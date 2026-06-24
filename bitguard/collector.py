from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .env import load_dotenv
from .storage import utc_now_iso, write_json


READ_ONLY_COMMANDS = {
    "account_assets": ["bgc", "--read-only", "account", "get_account_assets", "--accountType", "all"],
    "futures_positions": [
        "bgc",
        "--read-only",
        "futures",
        "futures_get_positions",
        "--productType",
        "USDT-FUTURES",
    ],
    "futures_orders": [
        "bgc",
        "--read-only",
        "futures",
        "futures_get_orders",
        "--productType",
        "USDT-FUTURES",
        "--status",
        "history",
        "--limit",
        "100",
    ],
    "futures_fills": [
        "bgc",
        "--read-only",
        "futures",
        "futures_get_fills",
        "--productType",
        "USDT-FUTURES",
        "--limit",
        "100",
    ],
    "copy_trading_traders": [
        "bgc",
        "--read-only",
        "copytrading",
        "copy_get_traders",
        "--productType",
        "USDT-FUTURES",
    ],
    "copy_trading_orders": [
        "bgc",
        "--read-only",
        "copytrading",
        "copy_get_orders",
        "--productType",
        "USDT-FUTURES",
    ],
    "copy_trading_positions": [
        "bgc",
        "--read-only",
        "copytrading",
        "copy_get_positions",
        "--productType",
        "USDT-FUTURES",
    ],
}


def collect_bitget_bundle(out_path: str | Path, agent_id: str = "local-bitget-agent") -> dict[str, Any]:
    load_dotenv(".env")
    bundle = {
        "source": "bitget-readonly-export",
        "demo_only": False,
        "agent_id": agent_id,
        "run_id": f"bitget-export-{utc_now_iso()}",
        "exported_at": utc_now_iso(),
        "collection_note": "Generated locally with bgc --read-only. API keys were not written to this file.",
        "bitget_raw": {},
    }

    env = os.environ.copy()
    bgc = _bgc_executable()
    for name, command in READ_ONLY_COMMANDS.items():
        resolved_command = [bgc, *command[1:]] if command and command[0] == "bgc" else command
        bundle["bitget_raw"][name] = _run_json_command(resolved_command, env)

    write_json(out_path, bundle)
    return bundle


def _bgc_executable() -> str:
    if os.name == "nt":
        return shutil.which("bgc.cmd") or shutil.which("bgc") or "bgc.cmd"
    return shutil.which("bgc") or "bgc"

def _run_json_command(command: list[str], env: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=timeout,
        )
    except Exception as exc:
        return {
            "ok": False,
            "command": command,
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "captured_at": utc_now_iso(),
        }

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    try:
        parsed = json.loads(stdout) if stdout else json.loads(stderr) if stderr else {}
    except json.JSONDecodeError:
        parsed = {"raw_stdout": stdout} if stdout else {"stderr": stderr}

    if isinstance(parsed, dict):
        parsed.setdefault("ok", completed.returncode == 0)
        parsed["command"] = command
        parsed["exit_code"] = completed.returncode
        if stderr:
            parsed["stderr"] = stderr
        parsed["captured_at"] = utc_now_iso()
        return parsed

    return {
        "ok": completed.returncode == 0,
        "command": command,
        "exit_code": completed.returncode,
        "data": parsed,
        "stderr": stderr,
        "captured_at": utc_now_iso(),
    }

