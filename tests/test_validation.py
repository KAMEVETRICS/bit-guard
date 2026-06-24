import unittest

from bitguard.audit import load_bundle
from bitguard.validation import ValidationError, validate_evidence_bundle


class ValidationTest(unittest.TestCase):
    def test_accepts_valid_bundle(self):
        bundle = load_bundle("samples/demo_agent_log_bundle.json")
        self.assertIs(validate_evidence_bundle(bundle), bundle)

    def test_rejects_missing_fills(self):
        with self.assertRaises(ValidationError) as raised:
            validate_evidence_bundle({"agent_id": "a1", "run_id": "r1"})
        self.assertIn("fills must be a non-empty array", raised.exception.errors)

    def test_rejects_missing_timestamp(self):
        with self.assertRaises(ValidationError) as raised:
            validate_evidence_bundle(
                {
                    "agent_id": "a1",
                    "run_id": "r1",
                    "fills": [{"symbol": "BTCUSDT", "side": "buy", "price": 65000, "quantity": 0.01}],
                }
            )
        self.assertIn("fills[0].timestamp is required", raised.exception.errors)

    def test_rejects_bad_side(self):
        with self.assertRaises(ValidationError) as raised:
            validate_evidence_bundle(
                {
                    "agent_id": "a1",
                    "run_id": "r1",
                    "fills": [{"symbol": "BTCUSDT", "side": "hold", "price": 65000, "quantity": 0.01, "timestamp": "2026-06-24T10:00:00Z"}],
                }
            )
        self.assertTrue(any("side must be one of" in item for item in raised.exception.errors))


if __name__ == "__main__":
    unittest.main()
