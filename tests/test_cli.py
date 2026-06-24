import contextlib
import io
import json
import unittest

from bitguard.cli import main


class CliTest(unittest.TestCase):
    def test_connect_outputs_agent_connection_modes(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(["connect", "--port", "8765"])

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["product"], "BitGuard Sentinel")
        modes = {item["mode"] for item in payload["agent_connection_modes"]}
        self.assertIn("local-cli-file", modes)
        self.assertIn("local-http-api", modes)
        self.assertIn("local-bitget-collector", modes)


if __name__ == "__main__":
    unittest.main()