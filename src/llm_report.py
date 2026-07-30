import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests


def _build_prompt(
    fields: Dict[str, Any],
    verification: Dict[str, Any],
    assessment: Dict[str, Any],
    retrieved: List[str],
) -> str:
    payload = {
        "fields": fields,
        "verification": verification,
        "assessment": assessment,
        "retrieved_preview": retrieved[:2],
    }
    return (
        "You are generating a concise HR background verification report. "
        "Use professional language and include key findings, risks, and recommendation.\n"
        "Return plain text only (no markdown).\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=True)}"
    )


def _call_ollama_generate(
    prompt: str,
    model: str,
    timeout_seconds: float,
    retries: int,
    request_fn: Optional[Callable[..., Any]] = None,
) -> Tuple[str, Dict[str, Any]]:
    post = request_fn or requests.post
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    url = f"{base_url.rstrip('/')}/api/generate"

    attempts = 0
    last_error: Optional[str] = None
    for _ in range(retries + 1):
        attempts += 1
        try:
            response = post(
                url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            body = response.json() if hasattr(response, "json") else {}
            text = (body.get("response") or "").strip() if isinstance(body, dict) else ""
            if text:
                return text, {
                    "provider": "ollama",
                    "mode": "ollama",
                    "used_fallback": False,
                    "status": "success",
                    "attempts": attempts,
                    "error": None,
                }
            last_error = "Empty response from local LLM"
        except Exception as exc:
            last_error = str(exc)

    return "", {
        "provider": "ollama",
        "mode": "ollama",
        "used_fallback": True,
        "status": "fallback",
        "attempts": attempts,
        "error": last_error or "Local LLM call failed",
    }


def generate_report_with_fallback(
    fields: Dict[str, Any],
    verification: Dict[str, Any],
    assessment: Dict[str, Any],
    retrieved: List[str],
    template_report: str,
    mode: Optional[str] = None,
    request_fn: Optional[Callable[..., Any]] = None,
) -> Tuple[str, Dict[str, Any]]:
    selected_mode = (mode or os.getenv("REPORT_GENERATION_MODE", "template")).lower()
    timeout_seconds = float(os.getenv("REPORT_LLM_TIMEOUT_SECONDS", "8"))
    retries = int(os.getenv("REPORT_LLM_RETRIES", "1"))

    if selected_mode != "ollama":
        return template_report, {
            "provider": "template",
            "mode": "template",
            "used_fallback": False,
            "status": "success",
            "attempts": 0,
            "error": None,
        }

    prompt = _build_prompt(fields, verification, assessment, retrieved)
    model = os.getenv("REPORT_LLM_MODEL", "llama3")
    generated, meta = _call_ollama_generate(
        prompt=prompt,
        model=model,
        timeout_seconds=timeout_seconds,
        retries=max(0, retries),
        request_fn=request_fn,
    )

    if generated:
        return generated, meta
    return template_report, meta