# Phase 3 Demo Flow

## Goal
Show a simple end-to-end demo for the upload endpoint, including:
- input document upload
- OCR extraction
- verification result
- retrieval behavior

## Demo steps
1. Start the API:
   ```bash
   python -m uvicorn src.app:app --reload
   ```
2. Open the browser at `http://127.0.0.1:8000/demo`
3. Upload a sample document using the form
4. Observe the JSON output:
   - `filename`
   - `ocr.raw_text`
   - `ocr.fields`
   - `verification`
   - `retrieved`
   - `assessment`
   - `report`
5. Use sample documents in `tests/samples/` or `data/corpus/`

## What to show
- Input: sample text / image / PDF document
- Output: structured response with extracted fields
- OCR extraction: `raw_text`, `fields`
- Verification result: `passed` or `needs_review`, plus `issues`
- Retrieval behavior: related corpus text from `data/corpus`

## Recommended first 5 tasks
1. Start the upload endpoint and test with a sample document
2. Validate OCR extraction and the structured fields returned
3. Check the verification rules in the response
4. Confirm retrieval returns similar corpus documents
5. Document the flow in `README.md` and `demo/demo_flow.md`

## Notes
- Use the browser demo for interactive verification
- Keep sample docs realistic and short for demo clarity
- The current prototype is local-first and open-source only
