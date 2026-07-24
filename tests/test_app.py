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
        self.assertIn(payload["verification"]["status"], {"passed", "needs_review"})
        self.assertEqual(payload["ocr"]["fields"]["name"], "Jane Smith")
        self.assertEqual(payload["ocr"]["fields"]["date"], "03/05/1990")
        self.assertEqual(payload["ocr"]["fields"]["document_type"], "Passport")


if __name__ == "__main__":
    unittest.main()
