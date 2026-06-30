import os
import re
from typing import Dict
from PIL import Image
import pytesseract
from pdf2image import convert_from_path


def _normalize_text(text: str) -> str:
    return " ".join(text.replace("\r", " ").split())


def extract_key_fields(text: str) -> Dict[str, str]:
    """Extract basic fields from OCR text for the prototype."""
    if not text:
        return {"name": None, "date": None, "document_type": None, "id_number": None}

    raw_text = text.strip()
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    normalized = _normalize_text(raw_text)

    fields = {"name": None, "date": None, "document_type": None, "id_number": None}

    date_matches = re.findall(
        r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b",
        normalized,
    )
    if date_matches:
        fields["date"] = date_matches[0]

    for line in lines:
        lower = line.lower()
        if fields["name"] is None and ("full name" in lower or lower.startswith("name") or "applicant" in lower):
            parts = re.split(r":\s*", line, maxsplit=1)
            fields["name"] = parts[1].strip() if len(parts) == 2 and parts[1].strip() else line

        if fields["document_type"] is None and any(token in lower for token in ["passport", "driver", "license", "id card", "identity card"]):
            fields["document_type"] = line

        if fields["id_number"] is None and re.search(r"\b(id|no|number|document)\b", lower) and re.search(r"\d{4,}", line):
            parts = re.split(r":\s*", line, maxsplit=1)
            fields["id_number"] = parts[1].strip() if len(parts) == 2 and parts[1].strip() else re.sub(r"[^0-9A-Za-z]", "", line)

    if fields["name"] is None and lines:
        fields["name"] = lines[0]

    return fields


def extract_text_from_image(path: str) -> str:
    """Simple OCR extraction supporting images and PDFs.

    Notes:
    - Requires Tesseract OCR installed on the host system.
    - For PDFs this converts pages to images then OCRs each page.
    """
    ext = os.path.splitext(path)[1].lower()
    text_parts = []
    try:
        if ext == ".pdf":
            pages = convert_from_path(path, dpi=200)
            for page in pages:
                text = pytesseract.image_to_string(page)
                text_parts.append(text)
        else:
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            text_parts.append(text)
    except Exception:
        return ""
    return "\n".join(text_parts)


def extract_document_data(path: str) -> Dict[str, object]:
    raw_text = extract_text_from_image(path)
    return {
        "raw_text": raw_text,
        "preview": raw_text[:1000],
        "fields": extract_key_fields(raw_text),
    }
