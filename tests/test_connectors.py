import unittest
from unittest.mock import Mock, patch

import requests

from src.connectors import _request_with_retry, run_external_verifications


class ExternalConnectorTests(unittest.TestCase):
    def test_mock_mode_returns_normalized_results(self):
        fields = {"name": "John Doe", "id_number": "P-12345"}
        results = run_external_verifications(fields, mode="mock")

        self.assertEqual(len(results), 2)
        for item in results:
            self.assertIn("source", item)
            self.assertIn("status", item)
            self.assertIn("matched", item)
            self.assertIn("confidence", item)
            self.assertIn("reference_id", item)
            self.assertIn("attempts", item)
            self.assertIn("duration_ms", item)
            self.assertIn("raw", item)

    def test_live_mode_without_endpoints_returns_not_configured(self):
        fields = {"name": "Jane Smith", "id_number": "D-334455"}
        with patch("src.connectors.os.getenv") as mock_getenv:
            values = {
                "EXTERNAL_CONNECTOR_MODE": "live",
                "EXTERNAL_EMPLOYMENT_URL": None,
                "EXTERNAL_IDENTITY_URL": None,
            }
            mock_getenv.side_effect = lambda key, default=None: values.get(key, default)

            results = run_external_verifications(fields)

        self.assertEqual(results[0]["status"], "not_configured")
        self.assertEqual(results[1]["status"], "not_configured")

    def test_request_with_retry_retries_timeout_then_succeeds(self):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"matched": True, "confidence": 0.93, "reference_id": "EMP-123"}

        with patch("src.connectors.requests.post", side_effect=[requests.Timeout(), mock_response]):
            result = _request_with_retry(
                url="http://fake.local/verify",
                payload={"fields": {"name": "John Doe"}},
                timeout_seconds=0.1,
                retries=1,
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["body"]["matched"], True)


if __name__ == "__main__":
    unittest.main()