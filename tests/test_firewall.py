import unittest

from bitguard.firewall import evaluate_intent
from bitguard.policy import DEFAULT_POLICY, normalize_policy


class FirewallTest(unittest.TestCase):
    def setUp(self):
        self.policy = normalize_policy(
            {
                **DEFAULT_POLICY,
                "max_notional_usdt": 300,
                "max_leverage": 2,
                "min_risk_reward": 1.2,
            }
        )

    def test_approves_guarded_intent(self):
        result = evaluate_intent(
            {
                "agent_id": "agent-a",
                "strategy_id": "trend",
                "symbol": "BTCUSDT",
                "product_type": "USDT-FUTURES",
                "side": "buy",
                "entry_price": 65000,
                "notional_usdt": 200,
                "leverage": 2,
                "stop_loss": 63700,
                "take_profit": 67600,
            },
            self.policy,
        )
        self.assertEqual(result["decision"], "approved")
        self.assertEqual(result["route"], "dry_run_accept")

    def test_rejects_overlevered_missing_stop(self):
        result = evaluate_intent(
            {
                "agent_id": "agent-b",
                "strategy_id": "breakout",
                "symbol": "BTCUSDT",
                "product_type": "USDT-FUTURES",
                "side": "buy",
                "entry_price": 65000,
                "notional_usdt": 900,
                "leverage": 8,
                "take_profit": 67600,
            },
            self.policy,
        )
        codes = {item["code"] for item in result["violations"]}
        self.assertEqual(result["decision"], "rejected")
        self.assertIn("max_notional_exceeded", codes)
        self.assertIn("max_leverage_exceeded", codes)
        self.assertIn("missing_stop_loss", codes)


if __name__ == "__main__":
    unittest.main()
