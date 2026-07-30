import unittest

from fastapi.testclient import TestClient

from src.app import app


class UploadEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_upload_txt_file_returns_processed_result(self):
        content = b"Full Name: John Doe\nDate: 12-03-2024\nDocument Type: Passport\nID Number: 123456"

        response = self.client.post(
            "/upload",
            files={"file": ("sample.txt", content, "text/plain")},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["filename"], "sample.txt")
        self.assertIn("raw_text", payload["ocr"])
        self.assertEqual(payload["ocr"]["fields"]["name"], "John Doe")
        self.assertEqual(payload["ocr"]["fields"]["date"], "12-03-2024")
        self.assertEqual(payload["ocr"]["fields"]["id_number"], "123456")

    def test_upload_returns_verification_summary(self):
        content = b"Applicant Name: Jane Smith\nIssued On: 03/05/1990\nPassport Number: P-889912"

        response = self.client.post(
            "/upload",
            files={"file": ("sample2.txt", content, "text/plain")},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("verification", payload)
        self.assertIn("issues", payload["verification"])

    def test_upload_returns_assessment_and_report(self):
        content = b"Full Name: John Doe\nDate: 12-03-2024\nDocument Type: Passport\nID Number: 123456"

        response = self.client.post(
            "/upload",
            files={"file": ("sample3.txt", content, "text/plain")},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("ocr", payload)
        self.assertIn("assessment", payload)
        self.assertIn("risk_score", payload["assessment"])
        self.assertIn("recommendation", payload["assessment"])
        self.assertIsInstance(payload["report"], str)
        self.assertTrue(payload["report"].startswith("Background check summary"))

    def test_report_endpoint_returns_generated_report(self):
        content = b"Full Name: Jane Smith\nDate of Birth: 03/05/1990\nDocument Type: Passport\nPassport Number: P-889912"

        response = self.client.post(
            "/report",
            files={"file": ("report_sample.txt", content, "text/plain")},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["filename"], "report_sample.txt")
        self.assertNotIn("ocr", payload)
        self.assertIn("assessment", payload)
        self.assertIn("report", payload)
        self.assertTrue(payload["report"].startswith("Background check summary"))

    def test_demo_route_serves_upload_page(self):
        response = self.client.get("/demo")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Employee Background Check Demo", response.text)


if __name__ == "__main__":
    unittest.main()
