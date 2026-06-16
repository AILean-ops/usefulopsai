"""Shared helpers for UsefulOps local operator scripts."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


OUTREACH_RESULT_CATEGORIES = (
    "sent",
    "reply",
    "positive_reply",
    "undeliverable",
    "delivery_delayed",
    "opt_out",
    "no_response",
    "booked",
    "paid",
)

JARGON_PHRASES = (
    "ai-assisted workflows",
    "admin drag",
    "working hypothesis",
    "human-reviewed workflow",
    "handoff",
    "workflow-audit",
    "operational",
    "optimize",
    "leverage",
    "systematize",
    "process improvement",
)

ROBOTIC_PHRASES = (
    "i came across your public site while looking for",
    "my working hypothesis",
    "for you, the likely starting point would be",
    "that kind of repeat follow-up",
)


def ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def ensure_operating_schema(conn: sqlite3.Connection) -> None:
    ensure_columns(
        conn,
        "outreach_actions",
        {
            "result_category": "TEXT",
            "result_recorded_at": "TEXT",
            "quality_score": "INTEGER",
            "quality_notes": "TEXT",
        },
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def stable_id(prefix: str, *parts: str | None) -> str:
    raw = "|".join(part or "" for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def clean_text(value: str | None) -> str | None:
    text = " ".join((value or "").split())
    return text or None


def normalize_email(value: str | None) -> str | None:
    text = clean_text(value)
    return text.lower() if text and "@" in text else text


def normalize_website(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = text.lower()
    text = re.sub(r"^https?://", "", text)
    text = re.sub(r"^www\.", "", text)
    return text.rstrip("/")


def dedupe_key(email: str | None, website: str | None, company: str | None, phone: str | None) -> str:
    email_norm = normalize_email(email)
    if email_norm:
        return f"email:{email_norm}"
    website_norm = normalize_website(website)
    if website_norm:
        return f"website:{website_norm}"
    company_norm = clean_text(company)
    if company_norm:
        return "company:" + re.sub(r"[^a-z0-9]+", "-", company_norm.lower()).strip("-")
    phone_norm = re.sub(r"\D+", "", phone or "")
    if phone_norm:
        return f"phone:{phone_norm}"
    return f"unknown:{uuid.uuid4().hex}"


def ensure_crm_schema(conn: sqlite3.Connection) -> None:
    ensure_columns(
        conn,
        "crm_leads",
        {
            "dedupe_key": "TEXT",
            "person_name": "TEXT",
            "company": "TEXT",
            "primary_email": "TEXT",
            "primary_phone": "TEXT",
            "website": "TEXT",
            "business_type": "TEXT",
            "stage": "TEXT NOT NULL DEFAULT 'new_inquiry'",
            "priority": "TEXT NOT NULL DEFAULT 'normal'",
            "owner": "TEXT NOT NULL DEFAULT 'rowan'",
            "source_first": "TEXT",
            "source_latest": "TEXT",
            "first_seen_at": "TEXT",
            "last_seen_at": "TEXT",
            "last_source_record_id": "TEXT",
            "intake_response_id": "TEXT",
            "prospect_id": "TEXT",
            "client_id": "TEXT",
            "urgency": "TEXT",
            "pain_point": "TEXT",
            "workflow_needing_help": "TEXT",
            "next_action": "TEXT",
            "next_action_at": "TEXT",
            "notes": "TEXT",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        },
    )


def upsert_crm_lead(
    conn: sqlite3.Connection,
    *,
    source: str,
    source_record_id: str,
    intake_response_id: str | None,
    submitted_at: str | None,
    alert_status: str | None,
    created_task_id: str | None,
    person_name: str | None,
    email: str | None,
    phone: str | None,
    company: str | None,
    website: str | None,
    business_type: str | None,
    urgency: str | None,
    pain_point: str | None,
    workflow_needing_help: str | None,
    prospect_id: str | None = None,
    client_id: str | None = None,
    payload: dict[str, Any] | None = None,
    notes: str | None = None,
    actor: str = "rowan",
) -> dict[str, Any]:
    """Create or update the canonical CRM lead for an inbound source record."""
    ensure_crm_schema(conn)
    now = utc_now()
    key = dedupe_key(email, website, company, phone)
    existing = conn.execute("SELECT * FROM crm_leads WHERE dedupe_key = ?", (key,)).fetchone()
    is_new = existing is None
    lead_id = stable_id("lead", key)
    priority = "high" if clean_text(urgency) else "normal"
    next_action = "Review inbound request and decide follow-up."

    values = {
        "id": lead_id,
        "dedupe_key": key,
        "person_name": clean_text(person_name),
        "company": clean_text(company),
        "primary_email": normalize_email(email),
        "primary_phone": clean_text(phone),
        "website": clean_text(website),
        "business_type": clean_text(business_type),
        "stage": "new_inquiry",
        "priority": priority,
        "owner": actor,
        "source_first": source,
        "source_latest": source,
        "first_seen_at": submitted_at or now,
        "last_seen_at": submitted_at or now,
        "last_source_record_id": source_record_id,
        "intake_response_id": intake_response_id,
        "prospect_id": prospect_id,
        "client_id": client_id,
        "urgency": clean_text(urgency),
        "pain_point": clean_text(pain_point),
        "workflow_needing_help": clean_text(workflow_needing_help),
        "next_action": next_action,
        "notes": clean_text(notes),
        "created_at": now,
        "updated_at": now,
    }

    if is_new:
        conn.execute(
            """
            INSERT INTO crm_leads (
              id, dedupe_key, person_name, company, primary_email, primary_phone,
              website, business_type, stage, priority, owner, source_first,
              source_latest, first_seen_at, last_seen_at, last_source_record_id,
              intake_response_id, prospect_id, client_id, urgency, pain_point,
              workflow_needing_help, next_action, notes, created_at, updated_at
            )
            VALUES (
              :id, :dedupe_key, :person_name, :company, :primary_email, :primary_phone,
              :website, :business_type, :stage, :priority, :owner, :source_first,
              :source_latest, :first_seen_at, :last_seen_at, :last_source_record_id,
              :intake_response_id, :prospect_id, :client_id, :urgency, :pain_point,
              :workflow_needing_help, :next_action, :notes, :created_at, :updated_at
            )
            """,
            values,
        )
        conn.execute(
            """
            INSERT INTO crm_stage_history (
              id, lead_id, changed_at, from_stage, to_stage, actor, reason, source_record_id
            )
            VALUES (?, ?, ?, NULL, 'new_inquiry', ?, ?, ?)
            """,
            (
                stable_id("crm-stage", lead_id, "new_inquiry", source_record_id),
                lead_id,
                now,
                actor,
                f"New inbound submission from {source}.",
                source_record_id,
            ),
        )
    else:
        lead_id = existing["id"]
        conn.execute(
            """
            UPDATE crm_leads
            SET person_name = COALESCE(:person_name, person_name),
                company = COALESCE(:company, company),
                primary_email = COALESCE(:primary_email, primary_email),
                primary_phone = COALESCE(:primary_phone, primary_phone),
                website = COALESCE(:website, website),
                business_type = COALESCE(:business_type, business_type),
                priority = CASE WHEN :priority = 'high' THEN 'high' ELSE priority END,
                source_latest = :source_latest,
                last_seen_at = :last_seen_at,
                last_source_record_id = :last_source_record_id,
                intake_response_id = COALESCE(:intake_response_id, intake_response_id),
                prospect_id = COALESCE(:prospect_id, prospect_id),
                client_id = COALESCE(:client_id, client_id),
                urgency = COALESCE(:urgency, urgency),
                pain_point = COALESCE(:pain_point, pain_point),
                workflow_needing_help = COALESCE(:workflow_needing_help, workflow_needing_help),
                next_action = COALESCE(next_action, :next_action),
                notes = COALESCE(:notes, notes),
                updated_at = :updated_at
            WHERE id = :lead_id
            """,
            {**values, "lead_id": lead_id},
        )

    submission_id = stable_id("crm-src", source, source_record_id)
    conn.execute(
        """
        INSERT INTO crm_source_submissions (
          id, source, source_record_id, lead_id, intake_response_id, submitted_at,
          recorded_at, alert_status, created_task_id, payload_json, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, source_record_id) DO UPDATE SET
          lead_id = excluded.lead_id,
          intake_response_id = COALESCE(excluded.intake_response_id, crm_source_submissions.intake_response_id),
          alert_status = COALESCE(excluded.alert_status, crm_source_submissions.alert_status),
          created_task_id = COALESCE(excluded.created_task_id, crm_source_submissions.created_task_id),
          payload_json = excluded.payload_json,
          notes = COALESCE(excluded.notes, crm_source_submissions.notes)
        """,
        (
            submission_id,
            source,
            source_record_id,
            lead_id,
            intake_response_id,
            submitted_at,
            now,
            alert_status,
            created_task_id,
            json.dumps(payload or {}, sort_keys=True),
            notes,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO crm_touchpoints (
          id, lead_id, occurred_at, channel, direction, summary, source, source_record_id
        )
        VALUES (?, ?, ?, 'web_form', 'inbound', ?, ?, ?)
        """,
        (
            stable_id("crm-touch", lead_id, source, source_record_id),
            lead_id,
            submitted_at or now,
            f"Inbound {source} submission recorded.",
            source,
            source_record_id,
        ),
    )
    return {"lead_id": lead_id, "is_new": is_new, "dedupe_key": key, "source_submission_id": submission_id}
    ensure_columns(
        conn,
        "strategy_reviews",
        {
            "undeliverable": "INTEGER NOT NULL DEFAULT 0",
            "delivery_delayed": "INTEGER NOT NULL DEFAULT 0",
        },
    )
    ensure_columns(
        conn,
        "growth_batches",
        {
            "undeliverable_count": "INTEGER NOT NULL DEFAULT 0",
            "delivery_delay_count": "INTEGER NOT NULL DEFAULT 0",
        },
    )


def assess_outreach_copy(subject: str | None, body: str | None) -> tuple[int, str]:
    text = f"{subject or ''}\n{body or ''}".strip()
    lower = text.lower()
    score = 100
    notes: list[str] = []

    if not (subject or "").strip():
        score -= 20
        notes.append("missing subject")
    if not (body or "").strip():
        score -= 50
        notes.append("missing body")
        return max(score, 0), "; ".join(notes)

    jargon_hits = [phrase for phrase in JARGON_PHRASES if phrase in lower]
    if jargon_hits:
        score -= min(35, 7 * len(jargon_hits))
        notes.append("jargon: " + ", ".join(jargon_hits[:5]))

    robotic_hits = [phrase for phrase in ROBOTIC_PHRASES if phrase in lower]
    if robotic_hits:
        score -= min(30, 10 * len(robotic_hits))
        notes.append("robotic phrasing: " + ", ".join(robotic_hits[:3]))

    workflow_count = len(re.findall(r"\bworkflow", lower))
    if workflow_count > 2:
        score -= min(20, (workflow_count - 2) * 5)
        notes.append(f"uses workflow {workflow_count} times")

    sentences = [part.strip() for part in re.split(r"[.!?]\s+", text) if part.strip()]
    long_sentences = [s for s in sentences if len(s.split()) > 30]
    if long_sentences:
        score -= min(20, 8 * len(long_sentences))
        notes.append(f"{len(long_sentences)} long sentence(s)")

    if "would it be useful" not in lower and "would you want" not in lower:
        score -= 8
        notes.append("CTA could be clearer and more conversational")

    if "no thanks" not in lower and "not relevant" not in lower:
        score -= 15
        notes.append("missing plain opt-out language")

    if not notes:
        notes.append("plain-language check passed")

    return max(score, 0), "; ".join(notes)
