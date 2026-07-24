import os
import re
from typing import Dict, List

from PIL import Image
import pytesseract
from pdf2image import convert_from_path

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}


def _normalize_text(text: str) -> str:
    return " ".join(text.replace("\r", " ").split())


def _clean_value(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip(" :;-")
    return cleaned


def _extract_field_value(line: str, patterns: List[str]) -> str | None:
    lower = line.lower()
    for pattern in patterns:
        if re.search(pattern, lower):
            if ":" in line:
                _, value = line.split(":", 1)
                return _clean_value(value)
            if "-" in line:
                _, value = line.split("-", 1)
                return _clean_value(value)
            return _clean_value(line)
    return None


def extract_key_fields(text: str) -> Dict[str, str | None]:
    """Extract common fields from OCR or plain-text document content."""
    if not text:
        return {"name": None, "date": None, "document_type": None, "id_number": None}

    raw_text = text.strip()
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    normalized = _normalize_text(raw_text)

    fields = {"name": None, "date": None, "document_type": None, "id_number": None}

    name_patterns = [r"\bfull name\b", r"\bapplicant name\b", r"\bapplicant\b", r"^name\b"]
    date_patterns = [r"\bissued on\b", r"\bissued date\b", r"\bdate of birth\b", r"\bdate\b"]
    document_patterns = [r"\bdocument type\b", r"\bpassport\b", r"\bdriver\b", r"\blicense\b", r"\bid card\b", r"\bidentity card\b"]
    id_patterns = [r"\bpassport number\b", r"\bid number\b", r"\blicense number\b", r"\bdocument number\b", r"\bnumber\b"]

    date_matches = re.findall(
        r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b",
        normalized,
    )
    if date_matches:
        fields["date"] = date_matches[0]

    for line in lines:
        lower = line.lower()
        if fields["name"] is None:
            extracted = _extract_field_value(line, name_patterns)
            if extracted:
                fields["name"] = extracted

        if fields["document_type"] is None:
            if "document type" in lower:
                document_type_value = _extract_field_value(line, document_patterns)
                if document_type_value:
                    fields["document_type"] = document_type_value
            elif re.search(r"\bpassport\b", lower) and not re.search(r"\bnumber\b", lower):
                fields["document_type"] = "Passport"
            elif re.search(r"\bdriver\b", lower):
                fields["document_type"] = "Driver License"
            elif re.search(r"\blicense\b", lower):
                fields["document_type"] = "License"
            elif re.search(r"\bid card\b|\bidentity card\b", lower):
                fields["document_type"] = "ID Card"

        if fields["id_number"] is None:
            id_value = _extract_field_value(line, id_patterns)
            if id_value and re.search(r"\d", id_value):
                fields["id_number"] = id_value

    if fields["name"] is None and lines:
        fields["name"] = lines[0]

    if fields["document_type"] is None:
        if re.search(r"\bpassport\b", normalized, re.I):
            fields["document_type"] = "Passport"
        elif re.search(r"\bdriver\b", normalized, re.I):
            fields["document_type"] = "Driver License"
        elif re.search(r"\blicense\b", normalized, re.I):
            fields["document_type"] = "License"

    return fields


def build_verification(fields: Dict[str, str | None], raw_text: str) -> Dict[str, object]:
    """Create a lightweight verification summary for the extracted fields."""
    required_fields = ["name", "date", "id_number"]
    missing = [field for field in required_fields if not (fields.get(field) or "")]

    if not raw_text:
        return {
            "status": "needs_review",
            "missing_fields": required_fields,
            "message": "No text was extracted from the document.",
        }

    if not missing and fields.get("document_type"):
        return {
            "status": "passed",
            "missing_fields": [],
            "message": "Core fields were extracted successfully.",
        }

    return {
        "status": "needs_review",
        "missing_fields": missing,
        "message": "Some fields are missing or need manual review.",
    }


def extract_text_from_image(path: str) -> str:
    """Simple extraction supporting plain text, images, and PDFs.

    Notes:
    - Requires Tesseract OCR installed on the host system for image/PDF input.
    - Plain text files are read directly for the MVP flow.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext in TEXT_EXTENSIONS:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as handle:
                return handle.read()
        except Exception:
            return ""

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
    fields = extract_key_fields(raw_text)
    return {
        "raw_text": raw_text,
        "preview": raw_text[:1000],
        "fields": fields,
        "source": "plain_text" if os.path.splitext(path)[1].lower() in TEXT_EXTENSIONS else "ocr",
        "notes": [] if raw_text else ["No text could be extracted automatically; please review the document or provide a clearer scan."],
    }
