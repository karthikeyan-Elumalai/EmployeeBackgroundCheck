import os
import re
import time
from typing import Any, Callable, Dict, List, Optional

import requests


DEFAULT_TIMEOUT_SECONDS = 2.0
DEFAULT_RETRIES = 1


def _normalize_result(
    source: str,
    status: str,
    matched: Optional[bool],
    confidence: Optional[float],
    reference_id: Optional[str],
    raw: Dict[str, Any],
    error: Optional[str],
    attempts: int,
    duration_ms: int,
) -> Dict[str, Any]:
    return {
        "source": source,
        "status": status,
        "matched": matched,
        "confidence": confidence,
        "reference_id": reference_id,
        "error": error,
        "attempts": attempts,
        "duration_ms": duration_ms,
        "raw": raw,
    }


def _mock_employment_verification(fields: Dict[str, Any]) -> Dict[str, Any]:
    name = (fields.get("name") or "").strip()
    if not name:
        return {"status": "not_found", "matched": False, "confidence": 0.0, "reference_id": None}

    score = 0.92 if len(name) >= 5 else 0.75
    return {
        "status": "success",
        "matched": True,
        "confidence": score,
        "reference_id": f"EMP-{abs(hash(name)) % 100000}",
        "employment_status": "active",
    }


def _mock_identity_verification(fields: Dict[str, Any]) -> Dict[str, Any]:
    id_number = (fields.get("id_number") or "").strip()
    if not id_number:
        return {"status": "not_found", "matched": False, "confidence": 0.0, "reference_id": None}

    is_valid = bool(re.match(r"^[0-9A-Za-z-]{5,}$", id_number))
    return {
        "status": "success" if is_valid else "error",
        "matched": is_valid,
        "confidence": 0.9 if is_valid else 0.25,
        "reference_id": f"ID-{abs(hash(id_number)) % 100000}" if is_valid else None,
    }


def _request_with_retry(
    url: str,
    payload: Dict[str, Any],
    timeout_seconds: float,
    retries: int,
    request_fn: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    request_callable = request_fn or requests.post
    attempts = 0
    started_at = time.monotonic()

    while attempts <= retries:
        attempts += 1
        try:
            response = request_callable(url, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            body = response.json() if hasattr(response, "json") else {}
            duration_ms = int((time.monotonic() - started_at) * 1000)
            return {
                "status": "success",
                "body": body if isinstance(body, dict) else {"data": body},
                "error": None,
                "attempts": attempts,
                "duration_ms": duration_ms,
            }
        except requests.Timeout:
            if attempts > retries:
                duration_ms = int((time.monotonic() - started_at) * 1000)
                return {
                    "status": "timeout",
                    "body": {},
                    "error": "Request timed out",
                    "attempts": attempts,
                    "duration_ms": duration_ms,
                }
        except Exception as exc:
            if attempts > retries:
                duration_ms = int((time.monotonic() - started_at) * 1000)
                return {
                    "status": "error",
                    "body": {},
                    "error": str(exc),
                    "attempts": attempts,
                    "duration_ms": duration_ms,
                }

    duration_ms = int((time.monotonic() - started_at) * 1000)
    return {
        "status": "error",
        "body": {},
        "error": "Unknown connector failure",
        "attempts": attempts,
        "duration_ms": duration_ms,
    }


def _from_live_response(source: str, call_result: Dict[str, Any]) -> Dict[str, Any]:
    body = call_result.get("body") or {}
    return _normalize_result(
        source=source,
        status=call_result.get("status", "error"),
        matched=body.get("matched"),
        confidence=body.get("confidence"),
        reference_id=body.get("reference_id"),
        raw=body,
        error=call_result.get("error"),
        attempts=int(call_result.get("attempts", 1)),
        duration_ms=int(call_result.get("duration_ms", 0)),
    )


def _run_single_connector(
    source: str,
    fields: Dict[str, Any],
    mode: str,
    endpoint: Optional[str],
    timeout_seconds: float,
    retries: int,
) -> Dict[str, Any]:
    started_at = time.monotonic()

    if mode == "mock":
        raw = _mock_employment_verification(fields) if source == "employment_api" else _mock_identity_verification(fields)
        duration_ms = int((time.monotonic() - started_at) * 1000)
        return _normalize_result(
            source=source,
            status=raw.get("status", "success"),
            matched=raw.get("matched"),
            confidence=raw.get("confidence"),
            reference_id=raw.get("reference_id"),
            raw=raw,
            error=None,
            attempts=1,
            duration_ms=duration_ms,
        )

    if not endpoint:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        return _normalize_result(
            source=source,
            status="not_configured",
            matched=None,
            confidence=None,
            reference_id=None,
            raw={},
            error="Endpoint is not configured",
            attempts=0,
            duration_ms=duration_ms,
        )

    call_result = _request_with_retry(
        url=endpoint,
        payload={"fields": fields, "source": source},
        timeout_seconds=timeout_seconds,
        retries=retries,
    )
    return _from_live_response(source, call_result)


def run_external_verifications(
    fields: Dict[str, Any],
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
    mode: Optional[str] = None,
) -> List[Dict[str, Any]]:
    connector_mode = (mode or os.getenv("EXTERNAL_CONNECTOR_MODE", "mock")).lower()

    connectors = [
        ("employment_api", os.getenv("EXTERNAL_EMPLOYMENT_URL")),
        ("identity_api", os.getenv("EXTERNAL_IDENTITY_URL")),
    ]

    results = []
    for source, endpoint in connectors:
        results.append(
            _run_single_connector(
                source=source,
                fields=fields,
                mode=connector_mode,
                endpoint=endpoint,
                timeout_seconds=timeout_seconds,
                retries=retries,
            )
        )
    return results