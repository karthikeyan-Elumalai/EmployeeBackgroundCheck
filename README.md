# Employee Background Check — Prototype

This repository contains a minimal scaffold for the AI-Powered Employee Background Check project (open-source-only).

Quick start:

1. Create a Python virtualenv and install dependencies: see `requirements.txt`.
   - Use `py -m venv venv` and then activate with `.
venv\Scripts\Activate.ps1`.
   - Install packages with `py -m pip install -r requirements.txt`.
2. Install Tesseract OCR on your system for text extraction.
   - On Windows, install from https://github.com/tesseract-ocr/tesseract or use Chocolatey.
   - For PDF OCR, install Poppler and ensure `pdftoppm` is on your PATH.
3. Run the API (FastAPI): `python -m uvicorn src.app:app --reload`.
4. See `demo/demo_instructions.md` for the live demo steps.

Notes:
- Local runner preference: Ollama / LM Studio (install separately).
- This scaffold includes placeholder modules for OCR, RAG, and verification logic.
