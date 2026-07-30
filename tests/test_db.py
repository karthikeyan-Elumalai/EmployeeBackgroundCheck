import os
import tempfile
import unittest

from src import db


class DatabaseFoundationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = os.path.join(self.tempdir.name, "background_checks_test.db")
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_save_and_get_case(self):
        case_id = db.save_case(
            filename="sample.txt",
            ocr_result={"raw_text": "Full Name: John Doe", "fields": {"name": "John Doe", "date": "12-03-2024", "id_number": "123"}},
            verification={"status": "passed", "issues": [], "missing_fields": [], "message": "ok"},
            retrieved=["John Doe worked at ACME Corp"],
            assessment={"risk_score": 85, "recommendation": "approve", "fraud_signals": [], "cross_verification": {"status": "matched", "matched_documents": []}},
            report="Background check summary for John Doe.",
        )

        saved = db.get_case(case_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["case_id"], case_id)
        self.assertEqual(saved["filename"], "sample.txt")
        self.assertEqual(saved["status"], "passed")
        self.assertEqual(saved["recommendation"], "approve")
        self.assertEqual(saved["risk_score"], 85)

    def test_list_cases_returns_latest_first(self):
        first_id = db.save_case(
            filename="first.txt",
            ocr_result={"raw_text": "text", "fields": {}},
            verification={"status": "needs_review", "issues": [], "missing_fields": [], "message": "review"},
            retrieved=[],
            assessment={"risk_score": 40, "recommendation": "review", "fraud_signals": [], "cross_verification": {"status": "unmatched", "matched_documents": []}},
            report="report",
        )
        second_id = db.save_case(
            filename="second.txt",
            ocr_result={"raw_text": "text", "fields": {}},
            verification={"status": "needs_review", "issues": [], "missing_fields": [], "message": "review"},
            retrieved=[],
            assessment={"risk_score": 35, "recommendation": "manual_review", "fraud_signals": [], "cross_verification": {"status": "unmatched", "matched_documents": []}},
            report="report",
        )

        cases = db.list_cases(limit=10)
        self.assertEqual(cases[0]["case_id"], second_id)
        self.assertEqual(cases[1]["case_id"], first_id)

    def test_pending_review_queue_excludes_auto_approved_cases(self):
        db.save_case(
            filename="auto-approved.txt",
            ocr_result={"raw_text": "text", "fields": {}},
            verification={"status": "passed", "issues": [], "missing_fields": [], "message": "ok"},
            retrieved=[],
            assessment={"risk_score": 95, "recommendation": "approve", "fraud_signals": [], "cross_verification": {"status": "matched", "matched_documents": []}},
            report="report",
        )
        review_case_id = db.save_case(
            filename="needs-review.txt",
            ocr_result={"raw_text": "text", "fields": {}},
            verification={"status": "needs_review", "issues": ["Missing required fields"], "missing_fields": ["id_number"], "message": "review"},
            retrieved=[],
            assessment={"risk_score": 35, "recommendation": "manual_review", "fraud_signals": ["missing_required_fields"], "cross_verification": {"status": "unmatched", "matched_documents": []}},
            report="report",
        )

        pending = db.list_pending_reviews(limit=10)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["case_id"], review_case_id)
        self.assertEqual(pending[0]["review_status"], "pending")

    def test_apply_review_decision_updates_case(self):
        case_id = db.save_case(
            filename="review-target.txt",
            ocr_result={"raw_text": "text", "fields": {}},
            verification={"status": "needs_review", "issues": ["Date unclear"], "missing_fields": [], "message": "review"},
            retrieved=[],
            assessment={"risk_score": 45, "recommendation": "manual_review", "fraud_signals": ["unstructured_date"], "cross_verification": {"status": "unmatched", "matched_documents": []}},
            report="report",
        )

        updated = db.apply_review_decision(
            case_id=case_id,
            decision="approve",
            reviewer_name="qa_reviewer",
            review_notes="Verified supporting documents manually.",
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["review_status"], "completed")
        self.assertEqual(updated["review_decision"], "approve")
        self.assertEqual(updated["reviewer_name"], "qa_reviewer")
        self.assertEqual(updated["review_notes"], "Verified supporting documents manually.")
        self.assertEqual(updated["status"], "passed")
        self.assertEqual(updated["recommendation"], "approve")


if __name__ == "__main__":
    unittest.main()