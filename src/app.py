import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from .ocr import extract_document_data
from .rag import build_index, retrieve


app = FastAPI(title="Employee Background Check Prototype")


@app.get("/")
async def root():
    return {
        "message": "Employee Background Check API",
        "version": "0.1.0",
        "docs": "Visit /docs for interactive API documentation",
        "health": "/health",
        "upload": "POST /upload (multipart/form-data)",
    }


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

    # Run OCR and extract fields
    ocr_result = extract_document_data(path)

    # Build a tiny index from the extracted text (demo only) and retrieve similar passages
    try:
        build_index([ocr_result["raw_text"]])
        retrieved = retrieve(ocr_result["raw_text"], k=3)
    except Exception:
        retrieved = []

    return {
        "filename": file.filename,
        "ocr": ocr_result,
        "retrieved": retrieved,
    }
