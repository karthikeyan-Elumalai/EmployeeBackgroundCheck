import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_path


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
