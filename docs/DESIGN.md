# Design Notes

Architecture (logical):
- Upload → OCR → Extraction → Normalization → Verification → Fraud Detection → Report

Components to implement:
- OCR pipeline
- Embeddings + Vector DB (RAG)
- Verification connectors (mocked)
- Fraud detection rules + ML
- Human review UI
