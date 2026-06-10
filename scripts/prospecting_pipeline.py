#!/usr/bin/env python3
"""Prepare UsefulOps prospects up to send-ready draft outreach, without sending."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usefulops_common import assess_outreach_copy, ensure_operating_schema


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"


PROSPECTS = [
    {
        "id": "prospect-20260530-senza-pelo-med-spa",
        "company": "Senza Pelo Med Spa",
        "website": "https://senzapelo.com/contact/",
        "niche": "med spa",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@senzapelo.com",
        "phone": "(602) 246-1966",
        "reason": "public contact page lists email, phone, Book Now path, and broad weekly appointment hours",
        "pain": "Booking, questions, and follow-up likely cross phone, email, forms, and online scheduling.",
        "fit": "Workflow audit for booking follow-up, inquiry triage, and daily admin summaries.",
    },
    {
        "id": "prospect-20260530-le-posh-aesthetics",
        "company": "Le Posh Aesthetics",
        "website": "https://leposhaesthetics.com/contact/",
        "niche": "med spa",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@leposhaesthetics.com",
        "phone": "480-881-6329",
        "reason": "public contact page lists an email, phone, inquiry form, and booking CTA",
        "pain": "A small aesthetics team can lose time moving inquiries from form/email into booked visits and follow-ups.",
        "fit": "Workflow audit for inquiry response drafts and consult follow-up.",
    },
    {
        "id": "prospect-20260530-smooch",
        "company": "Smooch",
        "website": "https://www.smoochxo.com/",
        "niche": "med spa",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@smoochxo.com",
        "phone": "(757) 773-3182",
        "reason": "public site has Book Now, email, phone, and location details for an aesthetics practice",
        "pain": "Booking interest and questions can create repetitive reply and follow-up work.",
        "fit": "Workflow audit for booking handoffs and response templates.",
    },
    {
        "id": "prospect-20260530-skinfairy-aesthetics",
        "company": "SkinFairy Aesthetics",
        "website": "https://www.skinfairyaesthetics.com/contact",
        "niche": "med spa",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@skinfairyaesthetics.com",
        "phone": "(602) 730-5860",
        "reason": "public page says appointments can be booked through the website, phone, or clinic visit and lists a direct email",
        "pain": "Multiple booking and question paths create repeat admin loops.",
        "fit": "Workflow audit for inquiry triage and appointment-prep follow-up.",
    },
    {
        "id": "prospect-20260530-intelligent-aging-studio",
        "company": "Intelligent Aging Studio",
        "website": "https://intelligentagingstudio.com/book-now/",
        "niche": "med spa",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@intelligentagingstudio.com",
        "phone": "+1 480 687 4894",
        "reason": "public booking page lists online booking, phone, email, and a boutique studio positioning",
        "pain": "A boutique practice benefits from consistent booking follow-up without adding admin overhead.",
        "fit": "Workflow audit for booking confirmations, consult prep, and post-visit follow-up drafts.",
    },
    {
        "id": "prospect-20260530-sapper-hvac",
        "company": "Sapper HVAC",
        "website": "https://sapperhvac.com/contact",
        "niche": "home services",
        "city": "Chandler/Phoenix metro",
        "state": "AZ",
        "email": "info@sapperhvac.com",
        "phone": "(602) 206-7359",
        "reason": "public contact page emphasizes same-day HVAC service, phone/text, email, service-needed form, and city/zip intake",
        "pain": "Same-day service requests need fast triage, status updates, and follow-up.",
        "fit": "Implementation sprint for service-request triage and daily dispatch summaries.",
    },
    {
        "id": "prospect-20260530-phoenix-heating-cooling-authority",
        "company": "Phoenix Heating & Cooling Authority",
        "website": "https://www.phoenixheatingcoolingauthority.com/",
        "niche": "home services",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@phoenixheatingcoolingauthority.com",
        "phone": "(480) 520-3392",
        "reason": "public site lists 24/7 HVAC service, Schedule Service CTA, phone, email, and maintenance offerings",
        "pain": "Emergency and maintenance requests can create repetitive dispatch and quote follow-up work.",
        "fit": "Workflow audit for emergency-service intake and maintenance-plan follow-up.",
    },
    {
        "id": "prospect-20260530-orca-ac",
        "company": "Orca AC",
        "website": "https://www.orcaac.com/services",
        "niche": "home services",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@orcaac.com",
        "phone": "480-798-5756",
        "reason": "public site lists Schedule Service, commercial/residential services, phone, email, and a Phoenix address",
        "pain": "Residential and commercial service channels need consistent triage and follow-up.",
        "fit": "Workflow audit for service intake routing and daily open-request summaries.",
    },
    {
        "id": "prospect-20260530-phoenix-heating-cooling",
        "company": "Phoenix Heating & Cooling",
        "website": "https://azairpros.com/",
        "niche": "home services",
        "city": "Phoenix",
        "state": "AZ",
        "email": "info@azairpros.com",
        "phone": "(602) 679-6039",
        "reason": "public site lists emergency service, scheduler, phone, email, and service request categories",
        "pain": "Scheduler submissions and after-hours requests create repeat admin and callback work.",
        "fit": "Implementation sprint for request triage and next-day follow-up summaries.",
    },
    {
        "id": "prospect-20260530-airsurance",
        "company": "Airsurance Heating & Cooling",
        "website": "https://airsurancellc.com/",
        "niche": "home services",
        "city": "Phoenix metro",
        "state": "AZ",
        "email": "info@airsurancellc.com",
        "phone": "480-450-2575",
        "reason": "public site lists Schedule Your Service Today, financing, phone, email, and repair/maintenance/replacement service lines",
        "pain": "Financing, tune-up, repair, and replacement paths can generate repetitive follow-up.",
        "fit": "Workflow audit for service inquiry triage and quote follow-up.",
    },
    {
        "id": "prospect-20260530-smith-family-dental",
        "company": "Smith Family Dental",
        "website": "https://www.smith-family-dental.com/patient-forms/",
        "niche": "dental",
        "city": "Phoenix",
        "state": "AZ",
        "email": "mail@smithfamilydental.org",
        "phone": "(602) 889-7835",
        "reason": "public patient-forms page lists new-patient forms, phone, email, and office hours",
        "pain": "Patient form completion and appointment prep create non-clinical front-office loops.",
        "fit": "Workflow audit for intake reminders and front-office admin summaries.",
    },
    {
        "id": "prospect-20260530-we-care-dental",
        "company": "We Care Dental",
        "website": "https://www.wecaredentalaz.com/patient-forms/",
        "niche": "dental",
        "city": "Phoenix",
        "state": "AZ",
        "email": "wecaredentalaz@gmail.com",
        "phone": "602-595-7523",
        "reason": "public patient-forms page lists forms, booking, phone numbers, email, address, and holiday schedule notices",
        "pain": "Forms, booking, reminders, and holiday notices create repeat patient-admin communication.",
        "fit": "Workflow audit for non-clinical intake and appointment-prep follow-up.",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(ROOT / "local" / "data" / "usefulopsai.sqlite3")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript((ROOT / "scripts" / "schema.sql").read_text(encoding="utf-8"))
    ensure_operating_schema(conn)
    conn.commit()


def domain_from_email(email: str) -> str:
    return email.split("@", 1)[1].lower()


def is_suppressed(conn: sqlite3.Connection, prospect_id: str, email: str) -> bool:
    domain = domain_from_email(email)
    row = conn.execute(
        """
        SELECT 1
        FROM suppressions
        WHERE lower(email) = lower(?)
           OR lower(domain) = lower(?)
           OR prospect_id = ?
        LIMIT 1
        """,
        (email, domain, prospect_id),
    ).fetchone()
    return row is not None


def action_log(conn: sqlite3.Connection, action_type: str, summary: str, risk_notes: str = "") -> None:
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', ?, 'UsefulOps approved authority envelope', 'prospecting',
                ?, 0, 0, 0, ?)
        """,
        (new_id("log"), utc_now(), action_type, summary, risk_notes),
    )


def seed(conn: sqlite3.Connection) -> dict[str, Any]:
    now = utc_now()
    experiment_id = "experiment-20260530-usefulops-first-outreach"
    created = 0
    for prospect in PROSPECTS:
        before = conn.total_changes
        conn.execute(
            """
            INSERT INTO prospects (
              id, experiment_id, company, website, niche, city, state, source, status,
              approval_state, pain_hypothesis, offer_fit, next_action, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'public_web_research', 'qualified_research_ready',
                    'not_requested', ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              website = excluded.website,
              niche = excluded.niche,
              city = excluded.city,
              state = excluded.state,
              source = excluded.source,
              status = CASE WHEN prospects.status IN ('sent', 'replied', 'converted') THEN prospects.status ELSE excluded.status END,
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
                prospect["pain"],
                prospect["fit"],
                "Verify suppression status, then use the prepared draft for first outreach.",
                f"Public-source reason: {prospect['reason']}. Source URL: {prospect['website']}",
                now,
                now,
            ),
        )
        if conn.total_changes > before:
            created += 1
    action_log(conn, "prospect_batch_seeded", f"Seeded or refreshed {len(PROSPECTS)} named public prospects.")
    conn.commit()
    return {"prospects": len(PROSPECTS), "created_or_updated": created}


def research_contacts(conn: sqlite3.Connection) -> dict[str, Any]:
    now = utc_now()
    ready = 0
    for prospect in PROSPECTS:
        contact_id = f"contact-{prospect['id'].replace('prospect-', '')}-public"
        email = prospect["email"].lower()
        conn.execute(
            """
            INSERT INTO contacts (
              id, prospect_id, role, email, phone, source, verification_status,
              is_primary, notes, created_at, updated_at
            )
            VALUES (?, ?, 'public business inbox', ?, ?, 'public_web_research',
                    'public_source_verified', 1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              phone = excluded.phone,
              verification_status = excluded.verification_status,
              is_primary = 1,
              notes = excluded.notes,
              updated_at = excluded.updated_at
            """,
            (
                contact_id,
                prospect["id"],
                email,
                prospect["phone"],
                f"Verified from public page/search result. Reason: {prospect['reason']}.",
                now,
                now,
            ),
        )
        suppressed = is_suppressed(conn, prospect["id"], email)
        conn.execute(
            """
            UPDATE prospects
            SET status = ?,
                next_action = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                "suppressed" if suppressed else "contact_ready",
                "Suppressed; do not contact." if suppressed else "Draft initial outreach email.",
                now,
                prospect["id"],
            ),
        )
        if not suppressed:
            ready += 1
    action_log(conn, "prospect_contacts_researched", f"Prepared public contact records for {ready} unsuppressed prospects.")
    conn.commit()
    return {"contact_ready": ready}


def subject_for(prospect: sqlite3.Row) -> str:
    niche = prospect["niche"]
    if niche == "home services":
        return "Quick idea for service-request follow-up"
    if niche == "dental":
        return "Quick idea for patient intake follow-up"
    return "Quick idea for booking follow-up"


def body_for(prospect: sqlite3.Row, contact: sqlite3.Row) -> str:
    company = prospect["company"]
    reason = re.sub(r"\s+", " ", prospect["notes"] or "").replace("Public-source reason: ", "")
    fit = prospect["offer_fit"]
    return f"""Hi {company} team,

I was looking at your public site and noticed this: {reason}

I run UsefulOps AI. We help small owner-led teams use AI for the everyday stuff that eats time: first replies, follow-ups, quote notes, review responses, and owner summaries.

Based on what I saw, a useful first project might be: {fit}

Would you want me to send over a short, specific outline for how that could work for your team?

Best,
Rowan Vale
UsefulOps AI
rowan.vale@usefulopsai.com

If this is not relevant, reply "no thanks" and I will not follow up."""


def draft(conn: sqlite3.Connection, limit: int | None) -> dict[str, Any]:
    prospects = conn.execute(
        """
        SELECT *
        FROM prospects
        WHERE status = 'contact_ready'
        ORDER BY
          CASE niche WHEN 'med spa' THEN 0 WHEN 'home services' THEN 1 WHEN 'dental' THEN 2 ELSE 3 END,
          company
        """
    ).fetchall()
    if limit is not None:
        prospects = prospects[:limit]
    created = 0
    skipped = 0
    now = utc_now()
    for prospect in prospects:
        contact = conn.execute(
            """
            SELECT *
            FROM contacts
            WHERE prospect_id = ? AND is_primary = 1 AND email IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (prospect["id"],),
        ).fetchone()
        if contact is None or is_suppressed(conn, prospect["id"], contact["email"]):
            skipped += 1
            continue
        before = conn.total_changes
        subject = subject_for(prospect)
        body = body_for(prospect, contact)
        quality_score, quality_notes = assess_outreach_copy(subject, body)
        conn.execute(
            """
            INSERT OR IGNORE INTO outreach_actions (
              id, prospect_id, contact_id, channel, action_type, subject, body,
              status, result_category, quality_score, quality_notes, notes,
              created_at, updated_at
            )
            VALUES (?, ?, ?, 'email', 'cold_initial', ?, ?, 'draft', NULL, ?, ?, ?, ?, ?)
            """,
            (
                new_id("outreach"),
                prospect["id"],
                contact["id"],
                subject,
                body,
                quality_score,
                quality_notes,
                "Ready for send review. Suppression checked at draft time. Not sent.",
                now,
                now,
            ),
        )
        if conn.total_changes > before:
            created += 1
        conn.execute(
            """
            UPDATE prospects
            SET status = 'draft_ready',
                next_action = 'Review and send initial outreach when ready.',
                updated_at = ?
            WHERE id = ?
            """,
            (now, prospect["id"]),
        )
    action_log(conn, "outreach_drafts_prepared", f"Prepared {created} initial outreach drafts; skipped {skipped}.")
    conn.commit()
    return {"drafts_created": created, "skipped": skipped}


def check(conn: sqlite3.Connection, email: str = "", domain: str = "", prospect_id: str = "") -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT *
        FROM suppressions
        WHERE (? != '' AND lower(email) = lower(?))
           OR (? != '' AND lower(domain) = lower(?))
           OR (? != '' AND prospect_id = ?)
        LIMIT 1
        """,
        (email, email, domain, domain, prospect_id, prospect_id),
    ).fetchone()
    return {"suppressed": row is not None, "record": dict(row) if row else None}


def add_suppression(conn: sqlite3.Connection, email: str, domain: str, prospect_id: str, reason: str) -> dict[str, Any]:
    conn.execute(
        """
        INSERT INTO suppressions (id, email, domain, prospect_id, reason, source, created_at)
        VALUES (?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), ?, 'operator_cli', ?)
        """,
        (new_id("sup"), email, domain, prospect_id, reason, utc_now()),
    )
    conn.commit()
    return {"ok": True}


def summary(conn: sqlite3.Connection) -> dict[str, Any]:
    return {
        "prospects_by_status": [dict(row) for row in conn.execute("SELECT status, COUNT(*) AS count FROM prospects GROUP BY status ORDER BY status")],
        "contacts": conn.execute("SELECT COUNT(*) FROM contacts WHERE verification_status = 'public_source_verified'").fetchone()[0],
        "drafts": conn.execute("SELECT COUNT(*) FROM outreach_actions WHERE status = 'draft'").fetchone()[0],
        "suppression_count": conn.execute("SELECT COUNT(*) FROM suppressions").fetchone()[0],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="UsefulOps prospecting pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed")
    sub.add_parser("research")
    draft_parser = sub.add_parser("draft")
    draft_parser.add_argument("--limit", type=int)
    sub.add_parser("summary")
    check_parser = sub.add_parser("check-suppression")
    check_parser.add_argument("--email", default="")
    check_parser.add_argument("--domain", default="")
    check_parser.add_argument("--prospect-id", default="")
    add_parser = sub.add_parser("suppress")
    add_parser.add_argument("--email", default="")
    add_parser.add_argument("--domain", default="")
    add_parser.add_argument("--prospect-id", default="")
    add_parser.add_argument("--reason", required=True)

    args = parser.parse_args()
    with connect() as conn:
        ensure_schema(conn)
        if args.command == "seed":
            result = seed(conn)
        elif args.command == "research":
            result = research_contacts(conn)
        elif args.command == "draft":
            result = draft(conn, args.limit)
        elif args.command == "summary":
            result = summary(conn)
        elif args.command == "check-suppression":
            result = check(conn, args.email, args.domain, args.prospect_id)
        elif args.command == "suppress":
            result = add_suppression(conn, args.email, args.domain, args.prospect_id, args.reason)
        else:
            raise AssertionError(args.command)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
