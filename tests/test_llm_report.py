import unittest
from unittest.mock import Mock

from src.llm_report import generate_report_with_fallback


class LlmReportGenerationTests(unittest.TestCase):
    def setUp(self):
        self.fields = {
            "name": "John Doe",
            "date": "12-03-2024",
            "document_type": "Passport",
            "id_number": "123456",
        }
        self.verification = {
            "status": "passed",
            "missing_fields": [],
            "issues": [],
            "message": "Core fields were extracted successfully.",
        }
        self.assessment = {
            "risk_score": 90,
            "recommendation": "approve",
            "fraud_signals": [],
            "cross_verification": {"status": "matched", "matched_documents": []},
            "external_integrations": [],
        }
        self.retrieved = ["Sample corpus document text"]
        self.template_report = "Background check summary for John Doe."

    def test_template_mode_returns_template_report(self):
        report, meta = generate_report_with_fallback(
            fields=self.fields,
            verification=self.verification,
            assessment=self.assessment,
            retrieved=self.retrieved,
            template_report=self.template_report,
            mode="template",
        )

        self.assertEqual(report, self.template_report)
        self.assertEqual(meta["provider"], "template")
        self.assertFalse(meta["used_fallback"])

    def test_ollama_mode_success_returns_generated_report(self):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "Generated local LLM report"}

        def fake_request(*args, **kwargs):
            return mock_response

        report, meta = generate_report_with_fallback(
            fields=self.fields,
            verification=self.verification,
            assessment=self.assessment,
            retrieved=self.retrieved,
            template_report=self.template_report,
            mode="ollama",
            request_fn=fake_request,
        )

        self.assertEqual(report, "Generated local LLM report")
        self.assertEqual(meta["provider"], "ollama")
        self.assertEqual(meta["status"], "success")
        self.assertFalse(meta["used_fallback"])

    def test_ollama_mode_failure_falls_back_to_template(self):
        def failing_request(*args, **kwargs):
            raise RuntimeError("Connection refused")

        report, meta = generate_report_with_fallback(
            fields=self.fields,
            verification=self.verification,
            assessment=self.assessment,
            retrieved=self.retrieved,
            template_report=self.template_report,
            mode="ollama",
            request_fn=failing_request,
        )

        self.assertEqual(report, self.template_report)
        self.assertEqual(meta["provider"], "ollama")
        self.assertEqual(meta["status"], "fallback")
        self.assertTrue(meta["used_fallback"])
        self.assertIn("Connection refused", meta["error"])


if __name__ == "__main__":
    unittest.main()