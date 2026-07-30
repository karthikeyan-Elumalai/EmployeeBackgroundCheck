import os
from typing import Dict
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

from .connectors import run_external_verifications
from .db import apply_review_decision, get_case, get_dashboard_summary, init_db, list_cases, list_pending_reviews, save_case
from .insights import build_resume_insights
from .llm_report import generate_report_with_fallback
from .ocr import (
    build_background_assessment,
    build_verification,
    extract_document_data,
    generate_background_report,
)
from .rag import build_index_from_corpus, retrieve


app = FastAPI(title="Employee Background Check Prototype")

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(["html", "xml"]),
)


class ReviewDecisionRequest(BaseModel):
    reviewer_name: str = "reviewer"
    review_notes: str | None = None


@app.on_event("startup")
async def startup_event():
    init_db()


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


@app.get("/demo", response_class=HTMLResponse)
async def demo(request: Request):
    template = jinja_env.get_template("upload.html")
    return HTMLResponse(template.render())


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    template = jinja_env.get_template("dashboard.html")
    return HTMLResponse(template.render())


def _save_uploaded_file(file: UploadFile) -> tuple[str, str]:
    tmpdir = os.path.join("data", "uploads")
    os.makedirs(tmpdir, exist_ok=True)

    filename = os.path.basename(file.filename or "upload.bin")
    path = os.path.join(tmpdir, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return path, filename


def _build_document_response(path: str, filename: str, include_ocr: bool = True) -> Dict[str, object]:
    ocr_result = extract_document_data(path)
    verification = build_verification(ocr_result["fields"], ocr_result["raw_text"])

    try:
        build_index_from_corpus([ocr_result["raw_text"]])
        retrieved = retrieve(ocr_result["raw_text"], k=3)
    except Exception:
        retrieved = []

    assessment = build_background_assessment(ocr_result, retrieved)
    external_integrations = run_external_verifications(ocr_result["fields"])
    assessment["external_integrations"] = external_integrations
    template_report = generate_background_report(ocr_result["fields"], verification, assessment, retrieved)
    report, report_generation = generate_report_with_fallback(
        fields=ocr_result["fields"],
        verification=verification,
        assessment=assessment,
        retrieved=retrieved,
        template_report=template_report,
    )
    resume_insights = build_resume_insights(ocr_result["raw_text"])
    case_id = save_case(filename, ocr_result, verification, retrieved, assessment, report)

    response = {
        "case_id": case_id,
        "filename": filename,
        "verification": verification,
        "assessment": assessment,
        "external_verification": external_integrations,
        "resume_insights": resume_insights,
        "report_generation": report_generation,
        "report": report,
    }
    if include_ocr:
        response["ocr"] = ocr_result
    return response


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    path, filename = _save_uploaded_file(file)
    return _build_document_response(path, filename, include_ocr=True)


@app.post("/report")
async def report_document(file: UploadFile = File(...)):
    path, filename = _save_uploaded_file(file)
    return _build_document_response(path, filename, include_ocr=False)


@app.get("/cases")
async def get_cases(limit: int = 20):
    return {"items": list_cases(limit=limit)}


@app.get("/dashboard/summary")
async def dashboard_summary(recent_limit: int = 10):
    return get_dashboard_summary(recent_limit=recent_limit)


@app.get("/cases/{case_id}")
async def get_case_by_id(case_id: int):
    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.get("/reviews/pending")
async def get_pending_reviews(limit: int = 20):
    return {"items": list_pending_reviews(limit=limit)}


@app.post("/reviews/{case_id}/approve")
async def approve_case_review(case_id: int, payload: ReviewDecisionRequest):
    updated = apply_review_decision(
        case_id=case_id,
        decision="approve",
        reviewer_name=payload.reviewer_name,
        review_notes=payload.review_notes,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return updated


@app.post("/reviews/{case_id}/reject")
async def reject_case_review(case_id: int, payload: ReviewDecisionRequest):
    updated = apply_review_decision(
        case_id=case_id,
        decision="reject",
        reviewer_name=payload.reviewer_name,
        review_notes=payload.review_notes,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return updated
