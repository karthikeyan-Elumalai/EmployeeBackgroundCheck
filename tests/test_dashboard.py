import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from src import db
from src.app import app


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tempdir.name, "dashboard_test.db")
        db.init_db()

        db.save_case(
            filename="resume_approved.txt",
            ocr_result={"raw_text": "Full Name: A", "fields": {"name": "A"}},
            verification={"status": "passed", "issues": [], "missing_fields": [], "message": "ok"},
            retrieved=[],
            assessment={"risk_score": 88, "recommendation": "approve", "fraud_signals": [], "cross_verification": {"status": "matched", "matched_documents": []}},
            report="report",
        )
        db.save_case(
            filename="resume_review.txt",
            ocr_result={"raw_text": "Full Name: B", "fields": {"name": "B"}},
            verification={"status": "needs_review", "issues": ["missing id"], "missing_fields": ["id_number"], "message": "review"},
            retrieved=[],
            assessment={"risk_score": 35, "recommendation": "manual_review", "fraud_signals": [], "cross_verification": {"status": "unmatched", "matched_documents": []}},
            report="report",
        )

        self.client = TestClient(app)

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_dashboard_summary_returns_expected_metrics(self):
        response = self.client.get("/dashboard/summary?recent_limit=10")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["total_cases"], 2)
        self.assertEqual(payload["pending_reviews"], 1)
        self.assertEqual(payload["approved_cases"], 1)
        self.assertIn("risk_distribution", payload)
        self.assertIn("talent_insights", payload)
        self.assertIn("experience_levels", payload["talent_insights"])
        self.assertIn("education_levels", payload["talent_insights"])
        self.assertGreaterEqual(len(payload["recent_cases"]), 2)

    def test_dashboard_page_renders(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("HR Resume Review Dashboard", response.text)


if __name__ == "__main__":
    unittest.main()
