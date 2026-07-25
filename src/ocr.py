import os
import re
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}


def _normalize_text(text: str) -> str:
    return " ".join(text.replace("\r", " ").split())


def _clean_value(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip(" :;-.\n")
    return cleaned


def _normalize_ocr_label(line: str) -> str:
    normalized = line.lower()
    replacements = {
        r"\bfullname\b": "full name",
        r"\bfnll name\b": "full name",
        r"\bcate of birth\b": "date of birth",
        r"\bdate of birfh\b": "date of birth",
        r"\bkeued on\b": "issued on",
        r"\bdrrvet\b": "driver",
        r"\bdrivet\b": "driver",
        r"\bnumher\b": "number",
        r"\bnumbe\b": "number",
        r"\bpassport number\.\b": "passport number",
        r"\bdriver license number\b": "driver license number",
    }
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized)
    normalized = re.sub(r"[^a-z0-9\s:.-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _extract_field_value(line: str, patterns: List[str], normalized_line: str | None = None) -> str | None:
    normalized = normalized_line if normalized_line is not None else line.lower()
    for pattern in patterns:
        if re.search(pattern, normalized):
            if ":" in line:
                _, value = line.split(":", 1)
                return _clean_value(value)

            regex = re.compile(rf"{pattern}\s*[:\.\-]?\s*(.+)$", flags=re.IGNORECASE)
            match = regex.search(line)
            if match:
                return _clean_value(match.group(1))

            match = regex.search(normalized)
            if match:
                return _clean_value(match.group(1))

            return _clean_value(line)
    return None


def _deskew_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if coords.size == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def _preprocess_image(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    array = np.array(image)
    array = _deskew_image(array)
    gray = cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        15,
        10,
    )
    return Image.fromarray(thresh)


def _extract_text_and_confidence(image: Image.Image) -> Tuple[str, float]:
    ocr_config = "--psm 6 --oem 3"
    raw_text = pytesseract.image_to_string(image, lang="eng", config=ocr_config)
    data = pytesseract.image_to_data(image, lang="eng", config=ocr_config, output_type=pytesseract.Output.DICT)
    confidences = []
    for conf in data.get("conf", []):
        try:
            conf_value = int(conf)
            if conf_value >= 0:
                confidences.append(conf_value)
        except (TypeError, ValueError):
            continue
    avg_conf = float(sum(confidences)) / len(confidences) if confidences else 0.0
    return raw_text, avg_conf


def extract_key_fields(text: str) -> Dict[str, str | None]:
    """Extract common fields from OCR or plain-text document content."""
    if not text:
        return {"name": None, "date": None, "document_type": None, "id_number": None}

    raw_text = text.strip()
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    normalized = _normalize_text(raw_text)

    fields = {"name": None, "date": None, "document_type": None, "id_number": None}

    name_patterns = [r"\bfull name\b", r"\bapplicant name\b", r"\bapplicant\b", r"^name\b"]
    date_patterns = [r"\bissued on\b", r"\bissued date\b", r"\bdate of birth\b", r"\bdob\b", r"\bdate\b"]
    document_patterns = [r"\bdocument type\b", r"\bpassport\b", r"\bdriver\b", r"\blicense\b", r"\bid card\b", r"\bidentity card\b"]
    id_patterns = [r"\bpassport number\b", r"\bid number\b", r"\blicense number\b", r"\bdocument number\b", r"\bnumber\b"]

    date_matches = re.findall(
        r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b",
        normalized,
    )
    if date_matches:
        fields["date"] = date_matches[0]

    for line in lines:
        normalized_line = _normalize_ocr_label(line)

        if fields["name"] is None:
            extracted = _extract_field_value(line, name_patterns, normalized_line)
            if extracted:
                fields["name"] = extracted

        if fields["document_type"] is None:
            if "document type" in normalized_line:
                document_type_value = _extract_field_value(line, document_patterns, normalized_line)
                if document_type_value:
                    fields["document_type"] = document_type_value.title()
            elif re.search(r"\bpassport\b", normalized_line) and not re.search(r"\bnumber\b", normalized_line):
                fields["document_type"] = "Passport"
            elif re.search(r"\bdriver\b", normalized_line):
                fields["document_type"] = "Driver License"
            elif re.search(r"\blicense\b", normalized_line):
                fields["document_type"] = "License"
            elif re.search(r"\bid card\b|\bidentity card\b", normalized_line):
                fields["document_type"] = "ID Card"

        if fields["id_number"] is None:
            id_value = _extract_field_value(line, id_patterns, normalized_line)
            if id_value and re.search(r"\d", id_value):
                fields["id_number"] = re.sub(r"[^0-9A-Za-z-]", "", id_value)

        if fields["date"] is None:
            if any(label in normalized_line for label in ["issued on", "issued date", "date of birth", "dob", "date"]):
                date_value = _extract_field_value(line, date_patterns, normalized_line)
                if date_value:
                    fields["date"] = date_value

    if fields["name"] is None and lines:
        candidate = lines[0]
        if ":" in candidate or "-" in candidate:
            candidate = re.split(r"[:\-]", candidate, maxsplit=1)[-1]
        fields["name"] = _clean_value(candidate)

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


def extract_text_from_image(path: str) -> Tuple[str, float]:
    """Extraction supporting plain text, images, and PDFs."""
    ext = os.path.splitext(path)[1].lower()

    if ext in TEXT_EXTENSIONS:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read(), 100.0
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as handle:
                return handle.read(), 100.0
        except Exception:
            return "", 0.0

    text_parts = []
    confidences = []
    try:
        if ext == ".pdf":
            pages = convert_from_path(path, dpi=300)
            for page in pages:
                prepped = _preprocess_image(page)
                text, conf = _extract_text_and_confidence(prepped)
                text_parts.append(text)
                confidences.append(conf)
        else:
            img = Image.open(path)
            prepped = _preprocess_image(img)
            text, conf = _extract_text_and_confidence(prepped)
            text_parts.append(text)
            confidences.append(conf)
    except Exception:
        return "", 0.0

    raw_text = "\n".join(text_parts)
    avg_confidence = float(sum(confidences)) / len(confidences) if confidences else 0.0
    return raw_text, avg_confidence


def extract_document_data(path: str) -> Dict[str, object]:
    raw_text, confidence = extract_text_from_image(path)
    fields = extract_key_fields(raw_text)
    notes = []
    if not raw_text:
        notes.append("No text could be extracted automatically; please review the document or provide a clearer scan.")
    elif confidence < 55:
        notes.append("OCR confidence is low; verify the extracted fields manually.")

    return {
        "raw_text": raw_text,
        "preview": raw_text[:1000],
        "fields": fields,
        "source": "plain_text" if os.path.splitext(path)[1].lower() in TEXT_EXTENSIONS else "ocr",
        "confidence": confidence,
        "notes": notes,
    }
