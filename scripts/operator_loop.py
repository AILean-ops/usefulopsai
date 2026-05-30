#!/usr/bin/env python3
"""Checkpointed UsefulOps daily operator loop helper.

This script does not replace the agent's judgment. It gives each detached cron
run a durable place to record start/resume, checkpoints, and completion so a
temporary runtime failure does not erase the work state.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
WEBSITE_INDEX = ROOT / "website" / "index.html"
STALE_MINUTES = 30


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
    schema = (ROOT / "scripts" / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def json_dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def action_log(conn: sqlite3.Connection, action_type: str, summary: str, risk_notes: str = "") -> None:
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', ?, 'UsefulOps approved authority envelope', 'operator_loop',
                ?, 0, 0, 0, ?)
        """,
        (new_id("log"), utc_now(), action_type, summary, risk_notes),
    )


def site_placeholder_state() -> dict[str, Any]:
    if not WEBSITE_INDEX.exists():
        return {"exists": False, "placeholder": None, "signals": []}
    text = WEBSITE_INDEX.read_text(encoding="utf-8", errors="replace")
    signals = [
        phrase
        for phrase in ("placeholder", "Full launch copy is being prepared", "Site infrastructure test page")
        if phrase.lower() in text.lower()
    ]
    return {
        "exists": True,
        "placeholder": bool(signals),
        "signals": signals,
    }


def select_task(conn: sqlite3.Connection) -> sqlite3.Row | None:
    rows = conn.execute(
        """
        SELECT id, title, status, priority, notes, updated_at
        FROM tasks
        WHERE status IN ('pending', 'in_progress')
        ORDER BY
          CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END,
          CASE
            WHEN lower(title) LIKE '%placeholder website%' THEN 0
            WHEN lower(title) LIKE '%operating dashboard%' THEN 1
            WHEN lower(title) LIKE '%stripe%' THEN 2
            WHEN lower(title) LIKE '%compliance%' THEN 3
            WHEN lower(title) LIKE '%prospect%' THEN 4
            ELSE 5
          END,
          updated_at ASC
        LIMIT 1
        """
    ).fetchone()
    return rows


def mark_stale_runs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM operator_runs
        WHERE status = 'running'
          AND datetime(updated_at) <= datetime('now', ?)
        ORDER BY updated_at ASC
        """,
        (f"-{STALE_MINUTES} minutes",),
    ).fetchall()
    marked = []
    for row in rows:
        now = utc_now()
        summary = (
            "Previous operator run was still marked running after "
            f"{STALE_MINUTES} minutes; recorded as interrupted for safe resume."
        )
        conn.execute(
            """
            UPDATE operator_runs
            SET status = 'interrupted',
                completed_at = ?,
                updated_at = ?,
                last_error = COALESCE(last_error, ?),
                summary = COALESCE(summary, ?)
            WHERE id = ?
            """,
            (now, now, summary, summary, row["id"]),
        )
        conn.execute(
            """
            INSERT INTO operator_checkpoints (
              id, run_id, checkpoint_at, step, status, summary, next_action, metadata_json
            )
            VALUES (?, ?, ?, 'runtime_recovery', 'interrupted', ?, ?, '{}')
            """,
            (new_id("chk"), row["id"], now, summary, row["next_action"]),
        )
        marked.append(dict(row))
    if marked:
        action_log(
            conn,
            "operator_loop_recovery",
            f"Marked {len(marked)} stale UsefulOps operator run(s) as interrupted before resuming.",
            "Internal recovery bookkeeping only; no external action performed.",
        )
    return marked


def start_run(conn: sqlite3.Connection, trigger: str, objective: str) -> dict[str, Any]:
    ensure_schema(conn)
    stale = mark_stale_runs(conn)
    task = select_task(conn)
    site_state = site_placeholder_state()
    run_id = new_id("oprun")
    now = utc_now()
    previous = stale[-1]["id"] if stale else None
    next_action = next_action_for(task, site_state)
    metadata = {
        "site": site_state,
        "selected_task": row_to_dict(task),
        "recovered_stale_run_ids": [row["id"] for row in stale],
    }
    conn.execute(
        """
        INSERT INTO operator_runs (
          id, started_at, updated_at, status, trigger_source, objective,
          selected_task_id, current_step, next_action, previous_run_id, metadata_json
        )
        VALUES (?, ?, ?, 'running', ?, ?, ?, 'started', ?, ?, ?)
        """,
        (
            run_id,
            now,
            now,
            trigger,
            objective,
            task["id"] if task else None,
            next_action,
            previous,
            json_dump(metadata),
        ),
    )
    conn.execute(
        """
        INSERT INTO operator_checkpoints (
          id, run_id, checkpoint_at, step, status, summary, next_action, metadata_json
        )
        VALUES (?, ?, ?, 'started', 'running', ?, ?, ?)
        """,
        (
            new_id("chk"),
            run_id,
            now,
            "UsefulOps operator loop started and selected the next durable task.",
            next_action,
            json_dump(metadata),
        ),
    )
    action_log(
        conn,
        "operator_loop_started",
        f"Started checkpointed UsefulOps operator run {run_id}. Next action: {next_action}",
        "Internal checkpoint only; no external action performed.",
    )
    conn.commit()
    return build_status(conn, run_id)


def next_action_for(task: sqlite3.Row | None, site_state: dict[str, Any]) -> str:
    if task is None:
        return "No pending UsefulOps tasks found; review docs/STARTUP-TASKS.md and create the next task."
    title = task["title"].lower()
    if "placeholder website" in title and site_state.get("placeholder"):
        return "Replace website/index.html placeholder with credible launch-page content, then run npm run build."
    if "placeholder website" in title:
        return "Verify the launch site is no longer a placeholder, then update task/docs and mark complete."
    if "dashboard" in title:
        return "Build the first Brian-viewable dashboard from local SQLite data without exposing secrets."
    if "stripe" in title:
        return "Add Stripe revenue/MRR sync using the private restricted key without committing secrets."
    return f"Move selected task forward: {task['title']}"


def checkpoint(conn: sqlite3.Connection, run_id: str, step: str, summary: str, next_action: str, status: str) -> dict[str, Any]:
    ensure_schema(conn)
    now = utc_now()
    conn.execute(
        """
        INSERT INTO operator_checkpoints (
          id, run_id, checkpoint_at, step, status, summary, next_action, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, '{}')
        """,
        (new_id("chk"), run_id, now, step, status, summary, next_action),
    )
    conn.execute(
        """
        UPDATE operator_runs
        SET updated_at = ?, current_step = ?, next_action = ?
        WHERE id = ? AND status = 'running'
        """,
        (now, step, next_action, run_id),
    )
    conn.commit()
    return build_status(conn, run_id)


def complete_run(conn: sqlite3.Connection, run_id: str, summary: str, next_action: str) -> dict[str, Any]:
    ensure_schema(conn)
    now = utc_now()
    conn.execute(
        """
        UPDATE operator_runs
        SET status = 'completed',
            completed_at = ?,
            updated_at = ?,
            current_step = 'completed',
            summary = ?,
            next_action = ?
        WHERE id = ?
        """,
        (now, now, summary, next_action, run_id),
    )
    conn.execute(
        """
        INSERT INTO operator_checkpoints (
          id, run_id, checkpoint_at, step, status, summary, next_action, metadata_json
        )
        VALUES (?, ?, ?, 'completed', 'completed', ?, ?, '{}')
        """,
        (new_id("chk"), run_id, now, summary, next_action),
    )
    action_log(
        conn,
        "operator_loop_completed",
        f"Completed UsefulOps operator run {run_id}: {summary}",
        "Completion log only; underlying work has its own action log if it changed external or material state.",
    )
    conn.commit()
    return build_status(conn, run_id)


def fail_run(conn: sqlite3.Connection, run_id: str, error: str, next_action: str) -> dict[str, Any]:
    ensure_schema(conn)
    now = utc_now()
    conn.execute(
        """
        UPDATE operator_runs
        SET status = 'failed',
            completed_at = ?,
            updated_at = ?,
            current_step = 'failed',
            last_error = ?,
            next_action = ?
        WHERE id = ?
        """,
        (now, now, error, next_action, run_id),
    )
    conn.execute(
        """
        INSERT INTO operator_checkpoints (
          id, run_id, checkpoint_at, step, status, summary, next_action, metadata_json
        )
        VALUES (?, ?, ?, 'failed', 'failed', ?, ?, '{}')
        """,
        (new_id("chk"), run_id, now, error, next_action),
    )
    action_log(
        conn,
        "operator_loop_failed",
        f"UsefulOps operator run {run_id} failed: {error}",
        "Failure log only; next run can resume from the recorded next action.",
    )
    conn.commit()
    return build_status(conn, run_id)


def build_status(conn: sqlite3.Connection, run_id: str | None = None) -> dict[str, Any]:
    ensure_schema(conn)
    if run_id:
        run = conn.execute("SELECT * FROM operator_runs WHERE id = ?", (run_id,)).fetchone()
    else:
        run = conn.execute("SELECT * FROM operator_runs ORDER BY started_at DESC LIMIT 1").fetchone()
    checkpoints = []
    if run:
        checkpoints = [
            dict(row)
            for row in conn.execute(
                """
                SELECT checkpoint_at, step, status, summary, next_action
                FROM operator_checkpoints
                WHERE run_id = ?
                ORDER BY checkpoint_at DESC
                LIMIT 5
                """,
                (run["id"],),
            ).fetchall()
        ]
    return {
        "database": str(DB_PATH),
        "run": row_to_dict(run),
        "recent_checkpoints": checkpoints,
        "site": site_placeholder_state(),
        "selected_task": row_to_dict(select_task(conn)),
    }


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="UsefulOps checkpointed operator loop helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")
    sub.add_parser("status")

    start = sub.add_parser("start")
    start.add_argument("--trigger", default="manual")
    start.add_argument("--objective", default="Move one high-priority UsefulOps startup item forward.")

    chk = sub.add_parser("checkpoint")
    chk.add_argument("--run-id", required=True)
    chk.add_argument("--step", required=True)
    chk.add_argument("--summary", required=True)
    chk.add_argument("--next-action", default="")
    chk.add_argument("--status", default="running")

    done = sub.add_parser("complete")
    done.add_argument("--run-id", required=True)
    done.add_argument("--summary", required=True)
    done.add_argument("--next-action", default="")

    fail = sub.add_parser("fail")
    fail.add_argument("--run-id", required=True)
    fail.add_argument("--error", required=True)
    fail.add_argument("--next-action", default="")

    args = parser.parse_args()
    with connect() as conn:
        if args.command == "init":
            ensure_schema(conn)
            print_json(build_status(conn))
        elif args.command == "status":
            print_json(build_status(conn))
        elif args.command == "start":
            print_json(start_run(conn, args.trigger, args.objective))
        elif args.command == "checkpoint":
            print_json(checkpoint(conn, args.run_id, args.step, args.summary, args.next_action, args.status))
        elif args.command == "complete":
            print_json(complete_run(conn, args.run_id, args.summary, args.next_action))
        elif args.command == "fail":
            print_json(fail_run(conn, args.run_id, args.error, args.next_action))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
