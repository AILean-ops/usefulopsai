#!/usr/bin/env python3
"""Bounded nightly self-improvement loop for UsefulOps AI.

This script is intentionally conservative: it reviews outcomes, records lessons,
creates at most one improvement task, and never contacts prospects or spends money.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
STRATEGY_REVIEW = ROOT / "scripts" / "strategy_review.py"
BUILD_DASHBOARD = ROOT / "scripts" / "build_dashboard.py"


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
        VALUES (?, ?, 'rowan', ?, 'UsefulOps approved authority envelope', 'self_improvement',
                ?, 0, 0, 0, ?)
        """,
        (new_id("log"), utc_now(), action_type, summary, risk_notes),
    )


def run_json(command: list[str], timeout: int = 180) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "ok": False,
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {"ok": True, "stdout": completed.stdout[-2000:]}
    return payload


def existing_open_task(conn: sqlite3.Connection, title: str) -> bool:
    return (
        scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE lower(title) = lower(?)
              AND status NOT IN ('done', 'completed', 'cancelled')
            """,
            (title,),
        )
        > 0
    )


def create_task(
    conn: sqlite3.Connection,
    title: str,
    notes: str,
    priority: str = "normal",
    related_id: str | None = None,
) -> bool:
    if existing_open_task(conn, title):
        return False
    now = utc_now()
    conn.execute(
        """
        INSERT INTO tasks (
          id, title, status, priority, owner, related_type, related_id,
          notes, created_at, updated_at
        )
        VALUES (?, ?, 'pending', ?, 'rowan', 'self_improvement', ?, ?, ?, ?)
        """,
        (new_id("task-self"), title, priority, related_id, notes, now, now),
    )
    return True


def latest_review(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT *
        FROM strategy_reviews
        ORDER BY reviewed_at DESC
        LIMIT 1
        """
    ).fetchone()


def choose_improvement(conn: sqlite3.Connection, review: sqlite3.Row | None) -> dict[str, str]:
    """Choose at most one meta-improvement, with business action taking priority."""

    sends = scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE status IN ('sent', 'replied')")
    drafts = scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE status = 'draft'")
    open_tasks = scalar(conn, "SELECT COUNT(*) FROM tasks WHERE status NOT IN ('done', 'completed', 'cancelled')")
    signature_tasks = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE lower(title) LIKE '%signature%'
          AND status NOT IN ('done', 'completed', 'cancelled')
        """,
    )
    recent_blockers = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM action_log
        WHERE action_at >= datetime('now', '-2 days')
          AND (
            lower(summary) LIKE '%block%'
            OR lower(risk_notes) LIKE '%block%'
            OR lower(summary) LIKE '%failed%'
            OR lower(risk_notes) LIKE '%failed%'
          )
        """,
    )

    if recent_blockers:
        return {
            "title": "Reduce latest UsefulOps execution blocker",
            "priority": "high",
            "notes": "Nightly self-improvement found recent blocker/failure language in action_log. Inspect the latest blocker, narrow root cause, and add a deterministic script/check/cron change so it does not recur.",
        }

    if drafts > 0 and sends == 0:
        return {
            "title": "Verify first-batch send path end to end",
            "priority": "high",
            "notes": "Nightly self-improvement found drafts but zero sends. Verify sender auth, suppression checks, send command, and SQLite send recording path before the controlled batch executes.",
        }

    if signature_tasks == 0 and sends <= 10:
        return {
            "title": "Create and test UsefulOps cold-email signature block",
            "priority": "normal",
            "notes": "Research practical B2B cold-email signature psychology, then implement a concise Rowan Vale / UsefulOps signature that improves trust without looking salesy. Track whether reply quality changes after adoption.",
        }

    if review and review["diagnosis"]:
        return {
            "title": f"Improve UsefulOps system for {review['diagnosis'][:50]}",
            "priority": "normal",
            "notes": f"Nightly review diagnosis: {review['diagnosis']}. Recommendation: {review['recommendation']}. Add one concrete workflow, copy, dashboard, or script improvement that supports the next action.",
        }

    return {
        "title": "Tighten UsefulOps next measurable experiment",
        "priority": "low",
        "notes": f"Nightly self-improvement fallback. Current open task count: {open_tasks}. Make the next experiment more measurable without adding external risk.",
    }


def record_learning(conn: sqlite3.Connection, source_id: str, finding: str, decision: str) -> None:
    conn.execute(
        """
        INSERT INTO learning_log (
          id, learned_at, source_type, source_id, lesson_type, finding,
          decision, confidence, applies_to
        )
        VALUES (?, ?, 'self_improvement', ?, 'operator_improvement', ?, ?, 'medium', 'UsefulOps operating system')
        """,
        (new_id("learn"), utc_now(), source_id, finding, decision),
    )


def main() -> int:
    strategy_result = run_json([sys.executable, str(STRATEGY_REVIEW)], timeout=240)

    with connect() as conn:
        ensure_schema(conn)
        review = latest_review(conn)
        improvement = choose_improvement(conn, review)
        created = create_task(
            conn,
            improvement["title"],
            improvement["notes"],
            improvement["priority"],
            review["id"] if review else None,
        )
        finding = "Nightly self-improvement reviewed business metrics and operator behavior with a one-task governor."
        decision = (
            f"Created improvement task: {improvement['title']}"
            if created
            else f"Improvement task already existed: {improvement['title']}"
        )
        record_learning(conn, review["id"] if review else "no-review", finding, decision)
        action_log(
            conn,
            "nightly_self_improvement_completed",
            decision,
            "No external action, no spend, one improvement task maximum.",
        )
        conn.commit()

    dashboard_result = run_json([sys.executable, str(BUILD_DASHBOARD)], timeout=180)
    result = {
        "ok": True,
        "strategy_review": strategy_result,
        "improvement_task": improvement,
        "task_created": created,
        "dashboard_rebuilt": bool(dashboard_result.get("ok", False) or dashboard_result.get("snapshot_id")),
        "limits": {
            "external_action": False,
            "spend": False,
            "max_new_tasks": 1,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
