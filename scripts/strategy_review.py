#!/usr/bin/env python3
"""UsefulOps growth-loop review: measure, diagnose, learn, and queue next action."""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usefulops_common import ensure_operating_schema


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"


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
    conn.executescript((ROOT / "scripts" / "schema.sql").read_text(encoding="utf-8"))
    ensure_operating_schema(conn)
    conn.commit()


def scalar(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    return int(conn.execute(query, params).fetchone()[0] or 0)


def action_log(conn: sqlite3.Connection, action_type: str, summary: str, risk_notes: str = "") -> None:
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', ?, 'UsefulOps approved authority envelope', 'growth_loop',
                ?, 0, 0, 0, ?)
        """,
        (new_id("log"), utc_now(), action_type, summary, risk_notes),
    )


def ensure_initial_batch(conn: sqlite3.Connection) -> str:
    experiment_id = "experiment-20260530-usefulops-first-outreach"
    batch_id = "batch-20260530-first-12-public-prospects"
    now = utc_now()
    conn.execute(
        """
        INSERT INTO growth_batches (
          id, experiment_id, name, status, hypothesis, target_niche, target_location,
          offer_angle, subject_pattern, cta, planned_count, notes, created_at, updated_at
        )
        VALUES (?, ?, 'First 12 public-source prospects', 'draft',
                'Owner-led businesses with visible booking/intake/service-request friction will respond to specific workflow-audit outreach.',
                'med spa, home services, dental', 'Phoenix metro',
                'Workflow audit for repeat follow-up/admin loops',
                'Quick idea for <specific workflow> follow-up',
                'Would it be useful if I sent over a short workflow-audit outline for this specific use case?',
                ?, 'Seeded automatically by strategy review. No outreach sent until explicitly executed.', ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          planned_count = excluded.planned_count,
          updated_at = excluded.updated_at
        """,
        (
            batch_id,
            experiment_id,
            scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE status = 'draft' AND action_type = 'cold_initial'"),
            now,
            now,
        ),
    )
    drafts = conn.execute(
        """
        SELECT id, prospect_id
        FROM outreach_actions
        WHERE status = 'draft' AND action_type = 'cold_initial'
        ORDER BY created_at
        """
    ).fetchall()
    for draft in drafts:
        conn.execute(
            """
            INSERT INTO growth_batch_items (
              id, batch_id, prospect_id, outreach_action_id, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'draft_ready', ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              status = excluded.status,
              updated_at = excluded.updated_at
            """,
            (
                f"gbi-{batch_id}-{draft['prospect_id']}",
                batch_id,
                draft["prospect_id"],
                draft["id"],
                now,
                now,
            ),
        )
    return batch_id


def metrics(conn: sqlite3.Connection) -> dict[str, Any]:
    by_status = {
        row["status"]: row["count"]
        for row in conn.execute("SELECT status, COUNT(*) AS count FROM outreach_actions GROUP BY status")
    }
    replies = scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE response_at IS NOT NULL OR status = 'replied'")
    positive = scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE outcome IN ('positive_reply', 'interested', 'booked', 'paid')")
    opt_outs = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM suppressions
        WHERE lower(reason) IN ('unsubscribe', 'opt_out', 'do_not_contact')
           OR lower(reason) LIKE '%unsubscribe%'
           OR lower(reason) LIKE '%opt%out%'
        """,
    )
    undeliverable = scalar(
        conn,
        "SELECT COUNT(*) FROM outreach_actions WHERE result_category = 'undeliverable' OR outcome = 'undeliverable'",
    )
    delivery_delayed = scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE result_category = 'delivery_delayed'")
    low_quality_drafts = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM outreach_actions
        WHERE status = 'draft'
          AND COALESCE(quality_score, 100) < 80
        """,
    )
    booked = scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE outcome = 'booked'")
    paid = scalar(conn, "SELECT COUNT(*) FROM clients WHERE payment_status IN ('paid', 'active')")
    revenue = scalar(conn, "SELECT COALESCE(SUM(amount_cents), 0) FROM revenue WHERE status IN ('received', 'paid', 'succeeded')")
    drafts = by_status.get("draft", 0)
    sends = by_status.get("sent", 0) + by_status.get("replied", 0)
    return {
        "drafts": drafts,
        "sends": sends,
        "replies": replies,
        "positive_replies": positive,
        "opt_outs": opt_outs,
        "undeliverable": undeliverable,
        "delivery_delayed": delivery_delayed,
        "low_quality_drafts": low_quality_drafts,
        "booked": booked,
        "paid": paid,
        "revenue_cents": revenue,
        "draft_ready_prospects": scalar(conn, "SELECT COUNT(*) FROM prospects WHERE status = 'draft_ready'"),
        "contact_ready_prospects": scalar(conn, "SELECT COUNT(*) FROM prospects WHERE status = 'contact_ready'"),
        "qualified_research_ready": scalar(conn, "SELECT COUNT(*) FROM prospects WHERE status = 'qualified_research_ready'"),
    }


def diagnose(m: dict[str, Any]) -> tuple[str, str, str, str, str]:
    attempted = max(m["sends"], 1)
    undeliverable_rate = m["undeliverable"] / attempted
    if m["undeliverable"] > 0 and undeliverable_rate >= 0.10:
        return (
            "deliverability_gap",
            f"UsefulOps has {m['undeliverable']} undeliverable result(s) from {m['sends']} sent outreach record(s), so the list quality needs attention before scaling.",
            "Keep the batch small, mark hard bounces as undeliverable, suppress those addresses, and verify the next batch's email sources before sending.",
            "Clean undeliverable contacts and tighten prospect email verification before the next outreach batch.",
            "medium",
        )
    if m["low_quality_drafts"] > 0:
        return (
            "draft_quality_gap",
            f"{m['low_quality_drafts']} draft outreach record(s) scored below the plain-language quality threshold.",
            "Rewrite drafts in a direct owner-to-owner voice before sending: fewer abstractions, fewer workflow/process terms, and a clearer reason for the email.",
            "Review pending outreach drafts for marketing clarity and human readability before the next send.",
            "high",
        )
    if m["sends"] == 0 and m["drafts"] > 0:
        return (
            "execution_gap",
            "The system has prospect drafts but no sent outreach, so the current bottleneck is not strategy quality; it is crossing into real-world send execution.",
            "Send a small controlled batch, then evaluate reply and opt-out rates before changing the offer.",
            "Send or create mailbox drafts for the first 12 prepared outreach records, then run strategy review after responses have time to arrive.",
            "medium",
        )
    if m["sends"] > 0 and m["replies"] == 0:
        return (
            "message_or_list_gap",
            "Outreach has been sent but no replies are recorded. Diagnose list relevance, subject line, and first-line specificity before scaling.",
            "Change one variable in the next batch: either tighter niche selection or a more concrete first-line operational observation.",
            "Prepare a variant batch with one changed variable and keep the CTA stable.",
            "low",
        )
    if m["replies"] > 0 and m["positive_replies"] == 0:
        return (
            "offer_gap",
            "Replies exist but no positive replies are recorded, so the offer/CTA may not be landing yet.",
            "Tighten the offer around one painful workflow and reduce ambiguity in the CTA.",
            "Review reply content and create a revised offer angle before the next batch.",
            "medium",
        )
    if m["positive_replies"] > 0 and m["paid"] == 0:
        return (
            "conversion_gap",
            "Positive replies exist but no payment/customer conversion is recorded.",
            "Improve close path: scope confirmation, payment link routing, and follow-up timing.",
            "Prepare conversion follow-up and make Stripe/website payment path obvious.",
            "medium",
        )
    return (
        "scale_winners",
        "The funnel has signal through conversion or revenue. Scale the winning niche/message while monitoring opt-outs and delivery quality.",
        "Increase daily volume gradually and preserve the winning message variables.",
        "Clone the winning batch into a larger controlled run.",
        "medium",
    )


def task_title_for(diagnosis_type: str) -> str:
    if diagnosis_type == "execution_gap":
        return "Execute first controlled outreach batch"
    if diagnosis_type == "deliverability_gap":
        return "Clean UsefulOps undeliverable outreach results"
    if diagnosis_type == "draft_quality_gap":
        return "Rewrite UsefulOps outreach drafts for human readability"
    if diagnosis_type == "message_or_list_gap":
        return "Prepare revised outreach variant batch"
    if diagnosis_type == "offer_gap":
        return "Revise UsefulOps offer and CTA from reply evidence"
    if diagnosis_type == "conversion_gap":
        return "Tighten UsefulOps conversion and payment follow-up path"
    return "Scale winning UsefulOps outreach pattern"


def upsert_next_task(conn: sqlite3.Connection, next_action: str, diagnosis_type: str) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO tasks (id, title, status, priority, owner, related_type, notes, created_at, updated_at)
        VALUES ('task-growth-loop-next-action',
                ?,
                'pending',
                'high',
                'rowan',
                'strategy_review',
                ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          title = excluded.title,
          status = 'pending',
          priority = 'high',
          notes = excluded.notes,
          updated_at = excluded.updated_at
        """,
        (task_title_for(diagnosis_type), f"{diagnosis_type}: {next_action}", now, now),
    )


def review(scope: str = "daily") -> dict[str, Any]:
    with connect() as conn:
        ensure_schema(conn)
        batch_id = ensure_initial_batch(conn)
        m = metrics(conn)
        diagnosis_type, diagnosis, recommendation, next_action, confidence = diagnose(m)
        review_id = new_id("strategy-review")
        conn.execute(
            """
            INSERT INTO strategy_reviews (
              id, reviewed_at, scope, sends, drafts, replies, positive_replies,
              opt_outs, undeliverable, delivery_delayed, booked, paid, revenue_cents, diagnosis, recommendation,
              next_action, metrics_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                utc_now(),
                scope,
                m["sends"],
                m["drafts"],
                m["replies"],
                m["positive_replies"],
                m["opt_outs"],
                m["undeliverable"],
                m["delivery_delayed"],
                m["booked"],
                m["paid"],
                m["revenue_cents"],
                diagnosis,
                recommendation,
                next_action,
                json.dumps(m, sort_keys=True),
            ),
        )
        conn.execute(
            """
            INSERT INTO learning_log (
              id, learned_at, source_type, source_id, lesson_type, finding,
              decision, confidence, applies_to
            )
            VALUES (?, ?, 'strategy_review', ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("learn"),
                utc_now(),
                review_id,
                diagnosis_type,
                diagnosis,
                recommendation,
                confidence,
                batch_id,
            ),
        )
        upsert_next_task(conn, next_action, diagnosis_type)
        action_log(
            conn,
            "strategy_review_completed",
            f"Growth loop review {review_id}: {diagnosis_type}. Next action: {next_action}",
            "Internal strategy loop only; no external outreach sent.",
        )
        conn.commit()
    return {
        "ok": True,
        "review_id": review_id,
        "batch_id": batch_id,
        "diagnosis_type": diagnosis_type,
        "diagnosis": diagnosis,
        "recommendation": recommendation,
        "next_action": next_action,
        "metrics": m,
    }


def main() -> int:
    result = review()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
