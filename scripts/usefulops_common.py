"""Shared helpers for UsefulOps local operator scripts."""

from __future__ import annotations

import re
import sqlite3


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
