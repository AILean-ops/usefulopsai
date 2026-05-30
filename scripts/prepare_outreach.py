#!/usr/bin/env python3
"""Prepare UsefulOps outreach compliance records and a first qualified prospect batch."""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
COMPLIANCE_DOC = ROOT / "docs" / "OUTREACH-COMPLIANCE.md"


PROSPECTS = [
    {
        "id": "prospect-20260530-rituel-salon-med-spa",
        "company": "Rituel Salon & Med Spa",
        "website": "https://salonrituel.com/",
        "niche": "med spa",
        "city": "Phoenix",
        "state": "AZ",
        "pain_hypothesis": "Public site describes free consultations, online booking, Instagram DMs as the fastest contact path, memberships, and same-day booking access, which suggests lead follow-up and channel handoff work.",
        "offer_fit": "Workflow audit for consultation follow-up, DM-to-booking handoff, and daily admin summaries.",
        "next_action": "Review public booking/contact flow and draft a specific outreach note; do not send before suppression and quality checks.",
    },
    {
        "id": "prospect-20260530-all-american-heating-cooling",
        "company": "All American Heating & Cooling LLC",
        "website": "https://www.myazhvac.com/",
        "niche": "home services",
        "city": "Gilbert/Phoenix metro",
        "state": "AZ",
        "pain_hypothesis": "Public site emphasizes schedule-service CTAs, AC repair, replacement estimates, maintenance, veteran priority scheduling, and phone booking windows, which suggests dispatch and follow-up loops.",
        "offer_fit": "Implementation sprint for estimate follow-up, service request triage, and daily job-status summaries.",
        "next_action": "Review public service request paths and prepare a practical dispatch/admin workflow angle.",
    },
    {
        "id": "prospect-20260530-sundance-dental-care",
        "company": "Sundance Dental Care",
        "website": "https://www.sundancedentalcare.com/patient-forms",
        "niche": "dental",
        "city": "Phoenix",
        "state": "AZ",
        "pain_hypothesis": "Public patient-forms page asks new patients to complete paperwork before appointments and lists broad office hours, suggesting front-office intake and preparation workflows.",
        "offer_fit": "Workflow audit for non-clinical intake reminders, FAQ response drafts, and daily front-office summaries.",
        "next_action": "Keep outreach limited to public front-office workflow observations; avoid patient data or HIPAA-sensitive claims.",
    },
    {
        "id": "prospect-20260530-tatum-point-dentistry",
        "company": "Tatum Point Dentistry",
        "website": "https://www.tatumpointdentistry.com/new-patients/patient-forms/",
        "niche": "dental",
        "city": "Phoenix",
        "state": "AZ",
        "pain_hypothesis": "Public patient-forms page includes multiple downloadable forms and a request-appointment path, suggesting opportunities around intake completion and appointment preparation.",
        "offer_fit": "Workflow audit for new-patient intake follow-up and non-clinical admin summaries.",
        "next_action": "Prepare a careful workflow-only outreach angle and avoid protected health information.",
    },
    {
        "id": "prospect-20260530-michael-j-fuller-attorney",
        "company": "Michael J. Fuller Attorney at Law",
        "website": "https://cdn.hibuwebsites.com/5cb26a47e257494f9a16df662cb9a3af/files/uploaded/michael-j-fuller-attorney-at-law-client-intake-form.pdf",
        "niche": "legal services",
        "city": "Phoenix",
        "state": "AZ",
        "pain_hypothesis": "Public client-intake form asks for matter description and consultation details, suggesting intake triage and follow-up workflows.",
        "offer_fit": "Workflow audit for client inquiry triage, document-request follow-up, and meeting-note cleanup.",
        "next_action": "Find the current public firm contact page before drafting; do not rely on the PDF alone for sending.",
    },
]


COMPLIANCE_TEXT = """# UsefulOps AI Outreach Compliance

UsefulOps AI may prepare and send direct email outreach inside the approved authority envelope, but the operating default is careful, low-volume, and human-aware.

## Before Any Cold Email

- Use only public business information or a clearly stated operational hypothesis.
- Confirm the business is not suppressed by email, domain, company, or clear prior refusal.
- Keep the message specific enough that it could not be sent unchanged to any business.
- Include a simple opt-out sentence.
- Do not imply a relationship, endorsement, guaranteed result, compliance guarantee, or private knowledge.
- Do not reference private/sensitive data, protected health information, customer lists, inbox contents, or anything creepy.
- Log the draft in `outreach_actions` before sending.

## Daily Limits

- Start at about 50 new cold contacts per day maximum.
- Prefer much smaller batches while the offer and messaging are being validated.
- Stop immediately for unsubscribe, do-not-contact, or clear refusal.

## Approved Initial Positioning

UsefulOps AI helps owner-led small businesses turn repeat admin, follow-up, reporting, and handoff friction into practical AI-assisted workflows. The first offer should usually be a workflow audit or a bounded implementation sprint.

## Not Yet Automated

No automatic sending is enabled by this checklist. Prospect prep and draft creation are allowed; actual sends must still respect suppression checks, message quality, and the current operating context.
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript((ROOT / "scripts" / "schema.sql").read_text(encoding="utf-8"))
    conn.commit()


def action_log(conn: sqlite3.Connection, action_type: str, summary: str, risk_notes: str = "") -> None:
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', ?, 'UsefulOps approved authority envelope', 'outreach_prep',
                ?, 0, 0, 0, ?)
        """,
        (new_id("log"), utc_now(), action_type, summary, risk_notes),
    )


def upsert_task(conn: sqlite3.Connection, task_id: str, title: str, status: str, notes: str) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO tasks (id, title, status, priority, owner, notes, created_at, updated_at)
        VALUES (?, ?, ?, 'high', 'rowan', ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          title = excluded.title,
          status = excluded.status,
          notes = excluded.notes,
          updated_at = excluded.updated_at
        """,
        (task_id, title, status, notes, now, now),
    )


def prepare() -> dict[str, Any]:
    COMPLIANCE_DOC.write_text(COMPLIANCE_TEXT, encoding="utf-8")
    with connect() as conn:
        ensure_schema(conn)
        now = utc_now()
        conn.execute(
            """
            UPDATE prospects
            SET status = 'superseded',
                next_action = 'Superseded by named public-prospect batch prepared on 2026-05-30.',
                updated_at = ?
            WHERE source = 'operator_prepared_target_category'
              AND status = 'research_needed'
            """,
            (now,),
        )
        experiment_id = "experiment-20260530-usefulops-first-outreach"
        conn.execute(
            """
            INSERT INTO experiments (
              id, name, status, target_market, offer, authority_envelope,
              budget_limit_cents, started_at, notes, created_at, updated_at
            )
            VALUES (?, 'UsefulOps first outreach prep', 'draft',
                    'Owner-led small businesses with repeat admin/follow-up friction',
                    'Workflow audit or bounded implementation sprint',
                    'UsefulOps AI Authority Envelope approved 2026-05-29',
                    10000, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              status = 'draft',
              updated_at = excluded.updated_at,
              notes = excluded.notes
            """,
            (
                experiment_id,
                now,
                "Prepared initial target categories only. No cold emails sent.",
                now,
                now,
            ),
        )
        inserted = 0
        for prospect in PROSPECTS:
            before = conn.total_changes
            conn.execute(
                """
                INSERT INTO prospects (
                  id, experiment_id, company, website, niche, city, state, source, status,
                  approval_state, pain_hypothesis, offer_fit, next_action, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'public_web_research',
                        'qualified_research_ready', 'not_requested', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  experiment_id = excluded.experiment_id,
                  niche = excluded.niche,
                  city = excluded.city,
                  state = excluded.state,
                  status = excluded.status,
                  pain_hypothesis = excluded.pain_hypothesis,
                  offer_fit = excluded.offer_fit,
                  next_action = excluded.next_action,
                  notes = excluded.notes,
                  updated_at = excluded.updated_at
                """,
                (
                    prospect["id"],
                    experiment_id,
                    prospect["company"],
                    prospect["website"],
                    prospect["niche"],
                    prospect["city"],
                    prospect["state"],
                    prospect["pain_hypothesis"],
                    prospect["offer_fit"],
                    prospect["next_action"],
                    f"Named prospect from public web research. Source URL: {prospect['website']}. Requires suppression check and final contact-page verification before outreach.",
                    now,
                    now,
                ),
            )
            if conn.total_changes > before:
                inserted += 1
        upsert_task(
            conn,
            "task-20260530-outreach-compliance",
            "Complete UsefulOps outreach compliance and suppression process",
            "completed",
            "Created docs/OUTREACH-COMPLIANCE.md and seeded compliance guardrails. No emails sent.",
        )
        upsert_task(
            conn,
            "task-20260530-first-prospect-batch",
            "Prepare first UsefulOps prospect batch",
            "completed",
            "Seeded five target-category prospect records with concrete operating hypotheses. These are not send-ready individual companies; next step is public research into named businesses.",
        )
        action_log(
            conn,
            "outreach_compliance_prepared",
            "Created UsefulOps outreach compliance checklist and first target-category prospect batch.",
            "No external outreach sent; records require public research and suppression checks before contact.",
        )
        conn.commit()
    return {
        "ok": True,
        "compliance_doc": str(COMPLIANCE_DOC),
        "experiment_id": experiment_id,
        "prospect_records": len(PROSPECTS),
        "inserted_or_updated": inserted,
    }


def main() -> int:
    print(json.dumps(prepare(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
