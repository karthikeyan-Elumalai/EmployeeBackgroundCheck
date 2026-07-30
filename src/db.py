import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .insights import build_talent_insights_from_texts


DB_PATH = os.path.join("data", "background_checks.db")


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS background_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                raw_text TEXT,
                fields_json TEXT NOT NULL,
                verification_json TEXT NOT NULL,
                retrieved_json TEXT NOT NULL,
                assessment_json TEXT NOT NULL,
                report TEXT NOT NULL,
                status TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'pending',
                review_decision TEXT,
                reviewer_name TEXT,
                review_notes TEXT,
                reviewed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_schema_updates(conn)
        conn.commit()
    finally:
        conn.close()


def _ensure_schema_updates(conn: sqlite3.Connection) -> None:
    existing = {
        row["name"] for row in conn.execute("PRAGMA table_info(background_cases)").fetchall()
    }
    required = {
        "review_status": "TEXT NOT NULL DEFAULT 'pending'",
        "review_decision": "TEXT",
        "reviewer_name": "TEXT",
        "review_notes": "TEXT",
        "reviewed_at": "TEXT",
    }

    for column_name, column_def in required.items():
        if column_name not in existing:
            conn.execute(
                f"ALTER TABLE background_cases ADD COLUMN {column_name} {column_def}"
            )

    conn.execute(
        """
        UPDATE background_cases
        SET review_status = 'not_required'
        WHERE recommendation = 'approve'
          AND (review_status IS NULL OR review_status = '' OR review_status = 'pending')
        """
    )

    conn.execute(
        """
        UPDATE background_cases
        SET review_status = 'pending'
        WHERE recommendation <> 'approve'
          AND (review_status IS NULL OR review_status = '')
        """
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_case(
    filename: str,
    ocr_result: Dict[str, object],
    verification: Dict[str, object],
    retrieved: List[str],
    assessment: Dict[str, object],
    report: str,
) -> int:
    now = _now_iso()
    fields = ocr_result.get("fields", {})
    recommendation = assessment.get("recommendation", "manual_review")
    review_status = "not_required" if recommendation == "approve" else "pending"

    conn = _get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO background_cases (
                filename,
                raw_text,
                fields_json,
                verification_json,
                retrieved_json,
                assessment_json,
                report,
                status,
                recommendation,
                risk_score,
                review_status,
                review_decision,
                reviewer_name,
                review_notes,
                reviewed_at,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                ocr_result.get("raw_text", ""),
                json.dumps(fields),
                json.dumps(verification),
                json.dumps(retrieved),
                json.dumps(assessment),
                report,
                verification.get("status", "needs_review"),
                recommendation,
                int(assessment.get("risk_score", 0)),
                review_status,
                None,
                None,
                None,
                None,
                now,
                now,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _decode_case_row(row: sqlite3.Row) -> Dict[str, object]:
    return {
        "case_id": row["id"],
        "filename": row["filename"],
        "raw_text": row["raw_text"],
        "fields": json.loads(row["fields_json"]),
        "verification": json.loads(row["verification_json"]),
        "retrieved": json.loads(row["retrieved_json"]),
        "assessment": json.loads(row["assessment_json"]),
        "report": row["report"],
        "status": row["status"],
        "recommendation": row["recommendation"],
        "risk_score": row["risk_score"],
        "review_status": row["review_status"],
        "review_decision": row["review_decision"],
        "reviewer_name": row["reviewer_name"],
        "review_notes": row["review_notes"],
        "reviewed_at": row["reviewed_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_case(case_id: int) -> Optional[Dict[str, object]]:
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM background_cases WHERE id = ?",
            (case_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return _decode_case_row(row)


def list_cases(limit: int = 20) -> List[Dict[str, object]]:
    safe_limit = max(1, min(limit, 100))
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM background_cases ORDER BY id DESC LIMIT ?",
            (safe_limit,),
        ).fetchall()
    finally:
        conn.close()

    return [_decode_case_row(row) for row in rows]


def list_pending_reviews(limit: int = 20) -> List[Dict[str, object]]:
    safe_limit = max(1, min(limit, 100))
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM background_cases
            WHERE review_status = 'pending'
                            AND recommendation <> 'approve'
            ORDER BY risk_score ASC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    finally:
        conn.close()

    return [_decode_case_row(row) for row in rows]


def apply_review_decision(
    case_id: int,
    decision: str,
    reviewer_name: str,
    review_notes: str | None = None,
) -> Optional[Dict[str, object]]:
    if decision not in {"approve", "reject"}:
        raise ValueError("decision must be 'approve' or 'reject'")

    existing = get_case(case_id)
    if existing is None:
        return None

    updated_status = "passed" if decision == "approve" else "needs_review"
    updated_recommendation = "approve" if decision == "approve" else "manual_review"
    assessment = existing.get("assessment") or {}
    assessment["recommendation"] = updated_recommendation

    now = _now_iso()
    conn = _get_connection()
    try:
        conn.execute(
            """
            UPDATE background_cases
            SET status = ?,
                recommendation = ?,
                assessment_json = ?,
                review_status = 'completed',
                review_decision = ?,
                reviewer_name = ?,
                review_notes = ?,
                reviewed_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                updated_status,
                updated_recommendation,
                json.dumps(assessment),
                decision,
                reviewer_name,
                review_notes,
                now,
                now,
                case_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return get_case(case_id)


def get_dashboard_summary(recent_limit: int = 10) -> Dict[str, object]:
    safe_limit = max(1, min(recent_limit, 50))
    conn = _get_connection()
    try:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total_cases,
                SUM(CASE WHEN review_status = 'pending' AND recommendation <> 'approve' THEN 1 ELSE 0 END) AS pending_reviews,
                SUM(CASE WHEN recommendation = 'approve' THEN 1 ELSE 0 END) AS approved_cases,
                SUM(CASE WHEN review_decision = 'reject' THEN 1 ELSE 0 END) AS rejected_cases,
                AVG(risk_score) AS avg_risk_score
            FROM background_cases
            """
        ).fetchone()

        buckets = conn.execute(
            """
            SELECT
                SUM(CASE WHEN risk_score >= 80 THEN 1 ELSE 0 END) AS low_risk,
                SUM(CASE WHEN risk_score >= 50 AND risk_score < 80 THEN 1 ELSE 0 END) AS medium_risk,
                SUM(CASE WHEN risk_score < 50 THEN 1 ELSE 0 END) AS high_risk
            FROM background_cases
            """
        ).fetchone()

        recent_rows = conn.execute(
            """
            SELECT
                id,
                filename,
                status,
                recommendation,
                risk_score,
                review_status,
                review_decision,
                created_at
            FROM background_cases
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

        insight_rows = conn.execute(
            """
            SELECT raw_text, filename
            FROM background_cases
            WHERE raw_text IS NOT NULL AND raw_text <> ''
            """
        ).fetchall()
    finally:
        conn.close()

    recent_cases = [
        {
            "case_id": row["id"],
            "filename": row["filename"],
            "status": row["status"],
            "recommendation": row["recommendation"],
            "risk_score": row["risk_score"],
            "review_status": row["review_status"],
            "review_decision": row["review_decision"],
            "created_at": row["created_at"],
        }
        for row in recent_rows
    ]

    talent_insights = build_talent_insights_from_texts([row["raw_text"] or "" for row in insight_rows])

    return {
        "total_cases": int(totals["total_cases"] or 0),
        "pending_reviews": int(totals["pending_reviews"] or 0),
        "approved_cases": int(totals["approved_cases"] or 0),
        "rejected_cases": int(totals["rejected_cases"] or 0),
        "avg_risk_score": round(float(totals["avg_risk_score"] or 0.0), 2),
        "risk_distribution": {
            "low_risk": int(buckets["low_risk"] or 0),
            "medium_risk": int(buckets["medium_risk"] or 0),
            "high_risk": int(buckets["high_risk"] or 0),
        },
        "talent_insights": talent_insights,
        "recent_cases": recent_cases,
    }