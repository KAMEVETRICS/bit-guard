import os
import unittest
from unittest.mock import patch

from bitguard.audit import audit_bundle, load_bundle, redact_bundle
from bitguard.intelligence import intelligence_bundle
from bitguard.market import enrich_public_market_context


class AuditTest(unittest.TestCase):
    def test_audits_demo_bundle(self):
        report = audit_bundle(load_bundle("samples/demo_agent_log_bundle.json"))
        self.assertTrue(report["demo_only"])
        self.assertEqual(report["summary"]["completed_trades"], 2)
        self.assertEqual(report["summary"]["fills"], 4)
        self.assertGreater(report["summary"]["risk_score"], 0)
        self.assertIn("order_audit", report)
        self.assertIn(report["order_audit"]["verdict"], {"pass", "watch", "caution", "fail"})
        self.assertGreaterEqual(report["order_audit"]["score"], 0)
        self.assertTrue(report["order_audit"]["evidence"])
        self.assertTrue(report["order_audit"]["recommendations"])
        self.assertEqual(report["summary"]["order_audit_score"], report["order_audit"]["score"])
        self.assertIn("perception_layer", report)
        self.assertIn(report["perception_layer"]["verdict"], {"opportunity", "watch", "caution", "avoid"})
        self.assertGreaterEqual(report["perception_layer"]["score"], 0)
        self.assertTrue(report["perception_layer"]["signals"])
        self.assertTrue(report["perception_layer"]["whale_pings"])
        self.assertEqual(report["summary"]["perception_score"], report["perception_layer"]["score"])
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("demo_data", codes)
        self.assertIn("missing_stop_loss", codes)

    def test_ignores_failed_bitget_sections(self):
        failed_section = {"ok": False, "error": {"type": "FileNotFoundError", "message": "bgc missing"}}
        report = audit_bundle(
            {
                "source": "bitget-readonly-export",
                "demo_only": False,
                "bitget_raw": {
                    "futures_positions": failed_section,
                    "futures_orders": failed_section,
                    "futures_fills": failed_section,
                    "account_assets": failed_section,
                },
            }
        )

        self.assertEqual(report["summary"]["positions"], 0)
        self.assertEqual(report["summary"]["orders"], 0)
        self.assertEqual(report["summary"]["fills"], 0)
    def test_redaction_hashes_order_ids(self):
        bundle = load_bundle("samples/demo_agent_log_bundle.json")
        redacted = redact_bundle(bundle)
        first_order = redacted["orders"][0]
        self.assertNotIn("order_id", first_order)
        self.assertIn("order_id_hash", first_order)
        self.assertEqual(len(first_order["order_id_hash"]), 12)

    def test_market_replay_uses_supplied_candles(self):
        report = audit_bundle(load_bundle("samples/demo_agent_log_bundle.json"))

        self.assertEqual(report["summary"]["market_type"], "futures")
        self.assertEqual(report["summary"]["product_type"], "USDT-FUTURES")
        self.assertEqual(report["market_replay"]["status"], "available")
        self.assertEqual(len(report["market_replay"]["trade_replays"]), 2)
        classifications = {item["classification"] for item in report["market_replay"]["trade_replays"]}
        self.assertIn("aligned_win", classifications)
        self.assertIn("wrong_side_loss", classifications)

    def test_detects_spot_trade_logs(self):
        report = audit_bundle(
            {
                "source": "demo-agent-log-schema",
                "demo_only": False,
                "product_type": "SPOT",
                "orders": [
                    {"order_id": "s1", "symbol": "SOLUSDT", "side": "buy", "price": 100, "quantity": 2, "status": "filled"},
                    {"order_id": "s2", "symbol": "SOLUSDT", "side": "sell", "price": 104, "quantity": 2, "status": "filled"},
                ],
                "fills": [
                    {"fill_id": "sf1", "order_id": "s1", "symbol": "SOLUSDT", "side": "buy", "price": 100, "quantity": 2, "timestamp": "2026-06-20T10:00:00Z"},
                    {"fill_id": "sf2", "order_id": "s2", "symbol": "SOLUSDT", "side": "sell", "price": 104, "quantity": 2, "timestamp": "2026-06-20T11:00:00Z"},
                ],
            }
        )

        self.assertEqual(report["summary"]["market_type"], "spot")
        self.assertEqual(report["summary"]["product_type"], "SPOT")
        self.assertEqual(report["trades"][0]["market_type"], "spot")
    def test_public_market_enrichment_fetches_futures_candles(self):
        bundle = {
            "source": "demo-agent-log-schema",
            "demo_only": False,
            "product_type": "USDT-FUTURES",
            "fills": [
                {"fill_id": "f1", "symbol": "BTCUSDT", "side": "buy", "price": 65000, "quantity": 0.01, "timestamp": "2026-06-20T10:00:00Z"},
                {"fill_id": "f2", "symbol": "BTCUSDT", "side": "sell", "price": 65300, "quantity": 0.01, "timestamp": "2026-06-20T10:30:00Z"},
            ],
        }
        response = {
            "code": "00000",
            "data": [
                ["1781949600000", "64900", "65100", "64800", "65000", "100"],
                ["1781951400000", "65000", "65400", "64950", "65300", "120"],
            ],
        }
        with patch("bitguard.market._get_json", return_value=response) as mocked:
            enriched = enrich_public_market_context(bundle)

        url = mocked.call_args.args[0]
        self.assertIn("/api/v2/mix/market/candles", url)
        self.assertIn("productType=usdt-futures", url)
        self.assertEqual(enriched["market_context"]["fetch_status"], "fetched")
        report = audit_bundle(enriched)
        self.assertEqual(report["market_replay"]["status"], "available")
    def test_intelligence_falls_back_without_external_keys(self):
        saved = {key: os.environ.pop(key, None) for key in ("TRUENORTH_MCP_URL", "OPENROUTER_API_KEY")}
        try:
            report = intelligence_bundle(load_bundle("samples/demo_agent_log_bundle.json"))
        finally:
            for key, value in saved.items():
                if value is not None:
                    os.environ[key] = value

        self.assertEqual(report["truenorth"]["status"], "not_configured")
        self.assertEqual(report["brief"]["status"], "fallback")
        self.assertEqual(report["brief"]["provider"], "deterministic")
        self.assertIn("audit", report)
        self.assertIn("analysis", report["brief"])
        analysis = report["brief"]["analysis"]
        self.assertTrue(analysis["replay_notes"])
        self.assertTrue(analysis["what_could_be_better"])
        self.assertIn("candle replay", analysis["headline"].lower())


if __name__ == "__main__":
    unittest.main()
