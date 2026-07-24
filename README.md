# Employee Background Check — Prototype

This repository contains a minimal scaffold for the AI-Powered Employee Background Check project (open-source-only).

## Project Overview
Organizations often face slow, manual, and fragmented background verification processes that lead to delays, high costs, inconsistent data, and fraud risk. This project proposes an AI-driven platform that uses OCR, local/open-source models, and retrieval-based workflows to automate document processing, cross-verification, fraud detection, and reporting.

### Key capabilities
- OCR and LLM-based document extraction
- Entity matching and cross-verification
- Fraud detection and anomaly identification
- Risk scoring
- Automated report generation
- External API integration support

### Business value
- Reduce turnaround time from weeks to 1–3 days
- Lower costs by 30–50%
- Improve fraud detection
- Improve compliance and audit readiness

### Recommended approach
- Hybrid AI + human review model
- Retrieval-Augmented Generation (RAG) for document understanding
- Governance and compliance controls
- Phased rollout strategy

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

Model usage policy:
- Use open-source models only for this project.
- Prefer local inference setups such as Ollama or LM Studio for LLM-based tasks.
- Keep sensitive employee data processing local where possible and avoid sending it to external hosted APIs unless approved by the organization.
- The current retrieval prototype uses an open-source embedding model for semantic search.

Recommended tools for running models:
- Ollama (preferred for local LLM usage)
- Supported examples: Llama 3, Mistral, Phi-3, Gemma
- For retrieval tasks, use local sentence-transformers embeddings with CPU-friendly models.

Notes:
- Local runner preference: Ollama / LM Studio (install separately).
- This scaffold includes placeholder modules for OCR, RAG, and verification logic.
