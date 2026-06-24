from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .audit import audit_bundle, load_bundle, redact_bundle
from .collector import collect_bitget_bundle
from .env import load_dotenv, secret_status
from .firewall import evaluate_intents
from .intelligence import intelligence_bundle
from .policy import load_policy
from .server import run_server
from .storage import append_usage_record, write_json


DEFAULT_LOG = "logs/usage.jsonl"
DEFAULT_BUNDLE = "samples/demo_agent_log_bundle.json"


def main(argv: list[str] | None = None) -> None:
    load_dotenv(".env")
    parser = argparse.ArgumentParser(
        prog="bitguard",
        description="BitGuard Sentinel: agent risk and order audit dashboard.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="Audit an exported agent order log bundle.")
    audit_parser.add_argument("input", help="JSON bundle from Bitget read-only export or demo schema.")
    audit_parser.add_argument("--out", default="outputs/audit_report.json")
    audit_parser.add_argument("--log", default=DEFAULT_LOG)

    intelligence_parser = subparsers.add_parser("intelligence", help="Generate an AI replay coach report for an exported bundle.")
    intelligence_parser.add_argument("input", help="JSON bundle from Bitget read-only export or demo schema.")
    intelligence_parser.add_argument("--out", default="outputs/intelligence_report.json")
    intelligence_parser.add_argument("--log", default=DEFAULT_LOG)

    redact_parser = subparsers.add_parser("redact", help="Redact sensitive identifiers in a log bundle.")
    redact_parser.add_argument("input", help="JSON bundle to redact.")
    redact_parser.add_argument("--out", default="outputs/redacted_bundle.json")

    collect_parser = subparsers.add_parser(
        "collect-bitget",
        help="Run local bgc read-only commands and write a Bitget export bundle.",
    )
    collect_parser.add_argument("--out", default="exports/bitget-log-bundle.json")
    collect_parser.add_argument("--agent-id", default="local-bitget-agent")

    firewall_parser = subparsers.add_parser("firewall", help="Evaluate proposed trade intents.")
    firewall_parser.add_argument("input", help="JSON file containing one intent or a list of intents.")
    firewall_parser.add_argument("--policy", default="samples/policy.json")
    firewall_parser.add_argument("--out", default="outputs/firewall_report.json")
    firewall_parser.add_argument("--log", default=DEFAULT_LOG)

    demo_parser = subparsers.add_parser("demo", help="Generate reproducible demo audit records.")
    demo_parser.add_argument("--input", default=DEFAULT_BUNDLE)
    demo_parser.add_argument("--records-dir", default="sample_records")

    serve_parser = subparsers.add_parser("serve", help="Run the local API and dashboard.")
    serve_parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    serve_parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    serve_parser.add_argument("--log", default=DEFAULT_LOG)

    connect_parser = subparsers.add_parser("connect", help="Print agent connection options and API examples.")
    connect_parser.add_argument("--port", type=int, default=8765)

    status_parser = subparsers.add_parser("status", help="Check local configuration.")
    status_parser.add_argument("--policy", default="samples/policy.json")

    args = parser.parse_args(argv)

    if args.command == "audit":
        bundle = load_bundle(args.input)
        report = audit_bundle(bundle)
        write_json(args.out, report)
        append_usage_record(args.log, "sentinel.audit", {"input": args.input}, report["summary"])
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
        print(f"Wrote {args.out}")
        return

    if args.command == "intelligence":
        bundle = load_bundle(args.input)
        report = intelligence_bundle(bundle)
        write_json(args.out, report)
        append_usage_record(
            args.log,
            "sentinel.intelligence",
            {"input": args.input},
            {"symbol": report["symbol"], "brief_status": report["brief"]["status"], "truenorth_status": report["truenorth"]["status"]},
        )
        print(
            json.dumps(
                {
                    "symbol": report["symbol"],
                    "brief_status": report["brief"]["status"],
                    "truenorth_status": report["truenorth"]["status"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        print(f"Wrote {args.out}")
        return

    if args.command == "redact":
        redacted = redact_bundle(load_bundle(args.input))
        write_json(args.out, redacted)
        print(f"Wrote {args.out}")
        return

    if args.command == "collect-bitget":
        bundle = collect_bitget_bundle(args.out, agent_id=args.agent_id)
        summary = {
            "source": bundle["source"],
            "agent_id": bundle["agent_id"],
            "raw_sections": sorted(bundle["bitget_raw"].keys()),
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        print(f"Wrote {args.out}")
        return

    if args.command == "firewall":
        policy = load_policy(args.policy)
        intents = _load_list(args.input)
        report = evaluate_intents(intents, policy)
        write_json(args.out, report)
        append_usage_record(args.log, "firewall.batch_check", {"input": args.input}, report["summary"])
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
        print(f"Wrote {args.out}")
        return

    if args.command == "demo":
        _run_demo(args.input, args.records_dir)
        return

    if args.command == "serve":
        run_server(args.host, args.port, args.log)
        return

    if args.command == "connect":
        print(_connect_guide(args.port))
        return

    if args.command == "status":
        policy = load_policy(args.policy)
        print(json.dumps({"policy": policy, "secrets": secret_status()}, indent=2, sort_keys=True))
        return


def _run_demo(input_path: str, records_dir: str) -> None:
    records = Path(records_dir)
    records.mkdir(parents=True, exist_ok=True)
    usage_log = records / "usage_records.jsonl"
    if usage_log.exists():
        usage_log.unlink()

    bundle = load_bundle(input_path)
    report = audit_bundle(bundle)
    redacted = redact_bundle(bundle)
    saved_intel_env = {key: os.environ.pop(key, None) for key in ("TRUENORTH_MCP_URL", "OPENROUTER_API_KEY")}
    try:
        intelligence_report = intelligence_bundle(bundle)
    finally:
        for key, value in saved_intel_env.items():
            if value is not None:
                os.environ[key] = value

    audit_path = records / "audit_report.json"
    intelligence_path = records / "intelligence_report.json"
    redacted_path = records / "redacted_demo_bundle.json"
    write_json(audit_path, report)
    write_json(intelligence_path, intelligence_report)
    write_json(redacted_path, redacted)

    append_usage_record(
        usage_log,
        "sentinel.audit",
        {"input": input_path, "mode": "demo-only"},
        report["summary"],
    )

    print(f"Wrote {audit_path}")
    print(f"Wrote {intelligence_path}")
    print(f"Wrote {redacted_path}")
    print(f"Wrote {usage_log}")


def _load_list(path: str) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return [payload]


def _connect_guide(port: int) -> str:
    base = f"http://127.0.0.1:{port}"
    guide = {
        "product": "BitGuard Sentinel",
        "agent_connection_modes": [
            {
                "mode": "local-cli-file",
                "when_to_use": "Agent can write a JSON evidence bundle to disk.",
                "commands": [
                    "bitguard audit exports/agent-log-bundle.json --out outputs/audit_report.json",
                    "bitguard intelligence exports/agent-log-bundle.json --out outputs/intelligence_report.json",
                ],
            },
            {
                "mode": "local-http-api",
                "when_to_use": "Agent can POST JSON to a local or deployed BitGuard service.",
                "commands": [
                    f"bitguard serve --port {port}",
                    f"curl -X POST {base}/api/audit -H 'Authorization: Bearer $BITGUARD_API_KEY' -H 'content-type: application/json' --data-binary @exports/agent-log-bundle.json",
                    f"curl -X POST {base}/api/intelligence -H 'Authorization: Bearer $BITGUARD_API_KEY' -H 'content-type: application/json' --data-binary @exports/agent-log-bundle.json",
                ],
            },
            {
                "mode": "local-bitget-collector",
                "when_to_use": "Trader wants to collect their own Bitget read-only logs locally before audit.",
                "commands": [
                    "bitguard collect-bitget --agent-id my-agent --out exports/bitget-log-bundle.json",
                    "bitguard audit exports/bitget-log-bundle.json --out outputs/audit_report.json",
                ],
            },
        ],
        "minimum_bundle_fields": {
            "source": "demo-agent-log-schema or bitget-readonly-export",
            "agent_id": "agent identifier",
            "run_id": "strategy/run identifier",
            "orders": "optional list of order objects",
            "fills": "required for entry/exit pairing",
            "positions": "optional open exposure snapshot",
            "agent_decisions": "optional rationale/stop/take-profit evidence",
            "skill_hub": "optional analyst snapshots",
            "copy_trading_pings": "optional whale/copy-trading observations",
        },
        "privacy": "The dashboard/API do not require private Bitget keys. Public candles may be fetched by BitGuard; private account logs are supplied by the user or local collector.",
    }
    return json.dumps(guide, indent=2, sort_keys=True)