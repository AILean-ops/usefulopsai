#!/usr/bin/env python3
"""Backfill and verify UsefulOps CRM v1 state."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usefulops_common import upsert_crm_lead


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
SCHEMA_PATH = ROOT / "scripts" / "schema.sql"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def load_payload(row: sqlite3.Row) -> dict[str, Any]:
    try:
        payload = json.loads(row["raw_json"] or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def task_for_response(conn: sqlite3.Connection, response_id: str) -> str | None:
    row = conn.execute(
        """
        SELECT id
        FROM tasks
        WHERE related_type = 'intake_form_response'
          AND related_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (response_id,),
    ).fetchone()
    return str(row["id"]) if row else None


def source_for_response(row: sqlite3.Row) -> tuple[str, str]:
    response_id = str(row["response_id"])
    if row["form_id"] == "aipromotionguy_web3forms":
        return "aipromotionguy_web3forms", response_id.removeprefix("aipromotion-web3forms-")
    return "usefulops_google_form", response_id


def prospect_for_response(conn: sqlite3.Connection, row: sqlite3.Row, source_record_id: str) -> str | None:
    if row["form_id"] != "aipromotionguy_web3forms":
        return None
    prospect_id = f"apg-{source_record_id}"
    exists = conn.execute("SELECT 1 FROM prospects WHERE id = ?", (prospect_id,)).fetchone()
    return prospect_id if exists else None


def backfill(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM intake_form_responses ORDER BY recorded_at, response_id").fetchall()
    backfilled = 0
    seen = 0
    for row in rows:
        source, source_record_id = source_for_response(row)
        existing = conn.execute(
            "SELECT 1 FROM crm_source_submissions WHERE source = ? AND source_record_id = ?",
            (source, source_record_id),
        ).fetchone()
        if existing:
            seen += 1
            continue
        payload = load_payload(row)
        result = upsert_crm_lead(
            conn,
            source=source,
            source_record_id=source_record_id,
            intake_response_id=row["response_id"],
            submitted_at=row["submitted_at"],
            alert_status=row["alert_status"],
            created_task_id=task_for_response(conn, row["response_id"]),
            person_name=row["name"],
            email=row["email"],
            phone=row["phone"],
            company=row["business_name"],
            website=row["website"],
            business_type=row["business_type"],
            urgency=row["urgency"],
            pain_point=row["pain_point"],
            workflow_needing_help=row["workflow_needing_help"],
            prospect_id=prospect_for_response(conn, row, source_record_id),
            payload=payload,
            notes="CRM v1 backfill from existing intake_form_responses.",
            actor="rowan",
        )
        backfilled += 1
        conn.execute(
            """
            INSERT INTO action_log (
              id, action_at, actor, action_type, authority_basis, target_type, target_id,
              summary, external_effect, cost_cents, revenue_cents, risk_notes
            )
            VALUES (?, ?, 'rowan', 'crm_lead_backfilled',
                    'Brian approved CRM v1 hardening on 2026-06-15.',
                    'crm_lead', ?, ?, 0, 0, 0, ?)
            """,
            (
                new_id("log"),
                utc_now(),
                result["lead_id"],
                f"Backfilled CRM lead from {source} intake response.",
                f"source_record_id={source_record_id}",
            ),
        )
    return {"seen_existing": seen, "backfilled": backfilled}


def integrity(conn: sqlite3.Connection) -> dict[str, Any]:
    intake_count = conn.execute("SELECT COUNT(*) FROM intake_form_responses").fetchone()[0]
    source_submission_count = conn.execute("SELECT COUNT(*) FROM crm_source_submissions").fetchone()[0]
    lead_count = conn.execute("SELECT COUNT(*) FROM crm_leads").fetchone()[0]
    open_followup_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM crm_leads
        WHERE stage IN ('new_inquiry', 'qualified', 'contacted')
        """
    ).fetchone()[0]
    missing_task_rows = conn.execute(
        """
        SELECT response_id, form_id, alert_status
        FROM intake_form_responses r
        WHERE alert_status != 'seen_baseline'
          AND NOT EXISTS (
            SELECT 1
            FROM tasks t
            WHERE t.related_type = 'intake_form_response'
              AND t.related_id = r.response_id
          )
        ORDER BY recorded_at
        """
    ).fetchall()
    missing_crm_rows = conn.execute(
        """
        SELECT response_id, form_id
        FROM intake_form_responses r
        WHERE NOT EXISTS (
          SELECT 1
          FROM crm_source_submissions s
          WHERE s.intake_response_id = r.response_id
        )
        ORDER BY recorded_at
        """
    ).fetchall()
    duplicate_email_rows = conn.execute(
        """
        SELECT primary_email, COUNT(*) AS count
        FROM crm_leads
        WHERE primary_email IS NOT NULL AND primary_email != ''
        GROUP BY lower(primary_email)
        HAVING COUNT(*) > 1
        ORDER BY count DESC, primary_email
        """
    ).fetchall()
    details = {
        "intake_count": intake_count,
        "missing_crm_submissions": [dict(row) for row in missing_crm_rows],
        "missing_followup_tasks": [dict(row) for row in missing_task_rows],
        "duplicate_emails": [dict(row) for row in duplicate_email_rows],
    }
    status = "ok" if not missing_crm_rows and not missing_task_rows and not duplicate_email_rows else "needs_attention"
    check_id = new_id("crm-check")
    conn.execute(
        """
        INSERT INTO crm_integrity_checks (
          id, checked_at, status, source_submission_count, lead_count,
          open_followup_count, missing_task_count, duplicate_email_count, details_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            check_id,
            utc_now(),
            status,
            source_submission_count,
            lead_count,
            open_followup_count,
            len(missing_task_rows) + len(missing_crm_rows),
            len(duplicate_email_rows),
            json.dumps(details, sort_keys=True),
        ),
    )
    return {
        "ok": status == "ok",
        "status": status,
        "check_id": check_id,
        "source_submission_count": source_submission_count,
        "lead_count": lead_count,
        "open_followup_count": open_followup_count,
        "missing_crm_submission_count": len(missing_crm_rows),
        "missing_task_count": len(missing_task_rows),
        "duplicate_email_count": len(duplicate_email_rows),
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backfill", action="store_true", help="Create CRM rows for existing intake responses.")
    args = parser.parse_args()

    with connect() as conn:
        ensure_schema(conn)
        backfill_result = backfill(conn) if args.backfill else {"seen_existing": 0, "backfilled": 0}
        integrity_result = integrity(conn)
        conn.commit()

    result = {"ok": integrity_result["ok"], "backfill": backfill_result, "integrity": integrity_result}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if integrity_result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
