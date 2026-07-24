# Live Demo Instructions

1. Start the API:

```bash
python -m uvicorn src.app:app --reload
```

2. Upload a sample document via `POST /upload` (use curl or Postman).
3. The scaffold returns an acknowledgement; replace placeholders with OCR + extraction logic for full demo.

For the live demo, prepare a short script showing: upload → OCR output → verification summary → generated report.
