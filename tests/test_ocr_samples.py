import os
import unittest

from PIL import Image, ImageDraw, ImageFont

from src.ocr import build_verification, extract_document_data


class OcrSampleTests(unittest.TestCase):
    def setUp(self):
        self.sample_dir = os.path.join(os.path.dirname(__file__), "samples")
        os.makedirs(self.sample_dir, exist_ok=True)
        self._create_text_sample()
        self._create_image_sample()
        self._create_pdf_sample()

    def _create_text_sample(self):
        path = os.path.join(self.sample_dir, "sample_text.txt")
        if not os.path.exists(path):
            content = (
                "Full Name: John Doe\n"
                "Date: 12-03-2024\n"
                "Document Type: Passport\n"
                "ID Number: 123456\n"
            )
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)

    def _create_image_sample(self):
        path = os.path.join(self.sample_dir, "sample_document.png")
        if not os.path.exists(path):
            image = Image.new("RGB", (1200, 600), color="white")
            draw = ImageDraw.Draw(image)
            text = (
                "Full Name: Jane Smith\n"
                "Date of Birth: 03/05/1990\n"
                "Passport Number: P-889912\n"
            )
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            draw.text((50, 50), text, fill="black", font=font)
            image.save(path, format="PNG")

    def _create_pdf_sample(self):
        path = os.path.join(self.sample_dir, "sample_document.pdf")
        if not os.path.exists(path):
            image = Image.new("RGB", (1200, 600), color="white")
            draw = ImageDraw.Draw(image)
            text = (
                "Applicant Name: Alice Johnson\n"
                "Issued On: 09/15/2018\n"
                "Driver License Number: D-334455\n"
            )
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            draw.text((50, 50), text, fill="black", font=font)
            image.save(path, format="PDF", resolution=300)

    def test_plain_text_sample(self):
        path = os.path.join(self.sample_dir, "sample_text.txt")
        result = extract_document_data(path)

        self.assertTrue(result["raw_text"].strip())
        self.assertEqual(result["fields"]["name"], "John Doe")
        self.assertEqual(result["fields"]["document_type"], "Passport")
        self.assertEqual(result["fields"]["id_number"], "123456")
        self.assertGreaterEqual(result["confidence"], 90)

    def test_pdf_sample(self):
        path = os.path.join(self.sample_dir, "sample_document.pdf")
        result = extract_document_data(path)
        verification = build_verification(result["fields"], result["raw_text"])

        self.assertTrue(result["raw_text"].strip())
        self.assertIn(result["fields"]["document_type"], {"Passport", "Driver License", "ID Card", "License"})
        self.assertIn(verification["status"], {"passed", "needs_review"})
        self.assertGreaterEqual(result["confidence"], 30)
        self.assertEqual(result["fields"]["name"], "Alice Johnson")
        self.assertEqual(result["fields"]["date"], "09/15/2018")

    def test_image_sample(self):
        path = os.path.join(self.sample_dir, "sample_document.png")
        result = extract_document_data(path)

        self.assertTrue(result["raw_text"].strip())
        self.assertGreaterEqual(result["confidence"], 30)
        self.assertEqual(result["fields"]["name"], "Jane Smith")
        self.assertEqual(result["fields"]["document_type"], "Passport")
        self.assertEqual(result["fields"]["id_number"], "P-689912")


if __name__ == "__main__":
    unittest.main()
