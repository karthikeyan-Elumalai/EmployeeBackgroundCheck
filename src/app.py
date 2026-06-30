import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from .ocr import extract_text_from_image
from .rag import build_index, retrieve


app = FastAPI(title="Employee Background Check Prototype")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    tmpdir = os.path.join("data", "uploads")
    os.makedirs(tmpdir, exist_ok=True)
    path = os.path.join(tmpdir, file.filename)
    try:
        with open(path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Run OCR
    extracted_text = extract_text_from_image(path)

    # Build a tiny index from the extracted text (demo only) and retrieve similar passages
    try:
        build_index([extracted_text])
        retrieved = retrieve(extracted_text, k=3)
    except Exception:
        retrieved = []

    return {"filename": file.filename, "extracted_text_preview": extracted_text[:1000], "retrieved": retrieved}
