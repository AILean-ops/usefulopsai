#!/usr/bin/env python3
"""Checkpointed UsefulOps daily operator loop helper.

This script does not replace the agent's judgment. It gives each detached cron
run a durable place to record start/resume, checkpoints, and completion so a
temporary runtime failure does not erase the work state.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
WEBSITE_INDEX = ROOT / "website" / "index.html"
STALE_MINUTES = 30
DAILY_RETRY_TRIGGER = "cron-0945-retry"
PRIMARY_DAILY_TRIGGER = "cron-0915"
BUILD_TIMEOUT_SECONDS = 120
CODEX_SUBSTEP_TIMEOUT_SECONDS = 180


LAUNCH_SITE_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>UsefulOps AI | Practical AI Operations for Small Business</title>
    <meta name="description" content="UsefulOps AI builds practical AI-assisted workflows for owner-led small businesses that need less admin drag and clearer operating rhythm.">
    <style>
      :root {
        color-scheme: light;
        --ink: #18202a;
        --muted: #566272;
        --line: #d8dee7;
        --paper: #f6f7f9;
        --panel: #ffffff;
        --teal: #0f766e;
        --teal-dark: #115e59;
        --gold: #b7791f;
        --blue: #245b8f;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: var(--paper);
        color: var(--ink);
      }

      a { color: inherit; }

      .wrap {
        width: min(1120px, calc(100% - 40px));
        margin: 0 auto;
      }

      header {
        border-bottom: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.86);
      }

      nav {
        min-height: 72px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
      }

      .brand {
        font-weight: 800;
        font-size: 20px;
        letter-spacing: 0;
      }

      .nav-links {
        display: flex;
        gap: 20px;
        align-items: center;
        color: var(--muted);
        font-size: 15px;
      }

      .nav-links a {
        text-decoration: none;
      }

      .button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        padding: 0 18px;
        border: 1px solid var(--teal-dark);
        background: var(--teal);
        color: #fff;
        font-weight: 700;
        text-decoration: none;
      }

      .button.secondary {
        background: transparent;
        color: var(--teal-dark);
      }

      .hero {
        padding: clamp(56px, 9vw, 104px) 0 48px;
      }

      .hero-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.18fr) minmax(280px, 0.82fr);
        gap: clamp(32px, 6vw, 72px);
        align-items: center;
      }

      .eyebrow {
        margin: 0 0 18px;
        color: var(--teal-dark);
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0;
        text-transform: uppercase;
      }

      h1 {
        margin: 0;
        max-width: 820px;
        font-size: clamp(42px, 7vw, 76px);
        line-height: 0.98;
        letter-spacing: 0;
      }

      .lede {
        max-width: 680px;
        margin: 24px 0 0;
        color: var(--muted);
        font-size: clamp(18px, 2vw, 22px);
        line-height: 1.55;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 30px;
      }

      .proof {
        display: grid;
        gap: 12px;
        border-left: 4px solid var(--gold);
        padding: 18px 0 18px 22px;
        color: var(--muted);
        line-height: 1.55;
      }

      .proof strong {
        display: block;
        color: var(--ink);
        font-size: 18px;
      }

      section {
        padding: 56px 0;
      }

      .band {
        background: #fff;
        border-top: 1px solid var(--line);
        border-bottom: 1px solid var(--line);
      }

      h2 {
        margin: 0 0 22px;
        font-size: clamp(28px, 4vw, 44px);
        line-height: 1.08;
        letter-spacing: 0;
      }

      .grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 18px;
      }

      .card {
        min-height: 210px;
        border: 1px solid var(--line);
        background: var(--panel);
        padding: 24px;
      }

      .card h3 {
        margin: 0 0 12px;
        font-size: 20px;
      }

      .card p, .split p, li {
        color: var(--muted);
        line-height: 1.6;
      }

      .split {
        display: grid;
        grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
        gap: clamp(28px, 5vw, 56px);
      }

      ul {
        margin: 0;
        padding-left: 22px;
      }

      li + li {
        margin-top: 10px;
      }

      .offer-list {
        display: grid;
        gap: 14px;
      }

      .offer {
        border: 1px solid var(--line);
        background: #fff;
        padding: 20px;
      }

      .offer h3 {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
        margin: 0 0 8px;
        font-size: 19px;
      }

      .price {
        color: var(--blue);
        font-size: 15px;
        white-space: nowrap;
      }

      .footer {
        padding: 36px 0;
        color: var(--muted);
        font-size: 14px;
      }

      @media (max-width: 820px) {
        .hero-grid,
        .split,
        .grid {
          grid-template-columns: 1fr;
        }

        .nav-links {
          display: none;
        }

        .proof {
          border-left: 0;
          border-top: 4px solid var(--gold);
          padding: 18px 0 0;
        }
      }
    </style>
  </head>
  <body>
    <header>
      <nav class="wrap" aria-label="Primary navigation">
        <div class="brand">UsefulOps AI</div>
        <div class="nav-links">
          <a href="#services">Services</a>
          <a href="#fit">Fit</a>
          <a href="mailto:rowan.vale@usefulopsai.com">rowan.vale@usefulopsai.com</a>
        </div>
      </nav>
    </header>

    <main>
      <section class="hero">
        <div class="wrap hero-grid">
          <div>
            <p class="eyebrow">Small business AI operations</p>
            <h1>Useful AI workflows for the work that keeps slipping.</h1>
            <p class="lede">
              UsefulOps AI helps owner-led teams turn repeat admin, follow-up, reporting,
              and handoff friction into practical AI-assisted operating routines.
            </p>
            <div class="actions">
              <a class="button" href="mailto:rowan.vale@usefulopsai.com?subject=UsefulOps%20AI%20workflow%20audit">Request a workflow audit</a>
              <a class="button secondary" href="#services">See services</a>
            </div>
          </div>
          <aside class="proof" aria-label="Operating principles">
            <strong>Built for real operators, not demo theater.</strong>
            <span>We start with the messy recurring work, design a smaller reliable process, and add AI only where it saves time or improves follow-through.</span>
          </aside>
        </div>
      </section>

      <section class="band" id="services">
        <div class="wrap">
          <h2>Focused help where AI can actually carry weight.</h2>
          <div class="grid">
            <article class="card">
              <h3>Workflow Audit</h3>
              <p>Map the recurring admin drag, identify the best AI-assisted workflow candidates, and leave with a prioritized implementation plan.</p>
            </article>
            <article class="card">
              <h3>Implementation Sprint</h3>
              <p>Build one useful workflow end to end: intake, drafting, review, follow-up, reporting, or another bounded operating loop.</p>
            </article>
            <article class="card">
              <h3>Operator Support</h3>
              <p>Keep workflows sharp with documentation, prompt/process tuning, lightweight automation fixes, and practical adoption support.</p>
            </article>
          </div>
        </div>
      </section>

      <section id="fit">
        <div class="wrap split">
          <div>
            <h2>A good fit when the work is repetitive, valuable, and currently manual.</h2>
            <p>
              UsefulOps AI is for small businesses that need operational relief without buying
              an enterprise transformation program or pretending every task needs a robot.
            </p>
          </div>
          <ul>
            <li>Lead follow-up and customer response drafts that need human approval.</li>
            <li>Internal reporting, meeting notes, and status summaries that are always late.</li>
            <li>Document, email, or spreadsheet workflows with repeatable decision rules.</li>
            <li>Simple operating dashboards from data the business already controls.</li>
          </ul>
        </div>
      </section>

      <section class="band">
        <div class="wrap split">
          <div>
            <h2>Simple starting points.</h2>
            <p>Pricing is scoped before work starts. No fake guarantees, no hidden subscriptions, and no sensitive data in public tools.</p>
          </div>
          <div class="offer-list">
            <article class="offer">
              <h3>Workflow Audit <span class="price">fixed scope</span></h3>
              <p>Best first step when you know AI should help but need a clear operating target.</p>
            </article>
            <article class="offer">
              <h3>Implementation Sprint <span class="price">project scope</span></h3>
              <p>Best when one workflow is already obvious and needs to be made real.</p>
            </article>
            <article class="offer">
              <h3>Ongoing Support <span class="price">monthly</span></h3>
              <p>Best after the first workflow is live and the business wants steady improvement.</p>
            </article>
          </div>
        </div>
      </section>
    </main>

    <footer class="footer">
      <div class="wrap">UsefulOps AI is an AI Lean Solutions LLC initiative. Contact: <a href="mailto:rowan.vale@usefulopsai.com">rowan.vale@usefulopsai.com</a>.</div>
    </footer>
  </body>
</html>
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
    schema = (ROOT / "scripts" / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def json_dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def command_summary(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "args": result.args,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def run_command(command: list[str], timeout: int, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        details = command_summary(result)
        raise RuntimeError(f"{label} failed: {json.dumps(details, sort_keys=True)}")


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


def update_task_status(conn: sqlite3.Connection, task_id: str, status: str, notes: str) -> None:
    conn.execute(
        """
        UPDATE tasks
        SET status = ?,
            notes = CASE
              WHEN notes IS NULL OR notes = '' THEN ?
              ELSE notes || char(10) || ?
            END,
            updated_at = ?
        WHERE id = ?
        """,
        (status, notes, notes, utc_now(), task_id),
    )


def update_startup_task_doc_for_launch() -> None:
    path = ROOT / "docs" / "STARTUP-TASKS.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "- **Replace UsefulOps AI placeholder website with launch site**\n"
        "  - Status: pending",
        "- **Replace UsefulOps AI placeholder website with launch site**\n"
        "  - Status: completed 2026-05-30",
    )
    text = text.replace(
        "  - Cron rule: daily UsefulOps operator loop should move this forward until the placeholder is replaced.",
        "  - Cron rule: completed by the local orchestrator; future daily runs should move to the next high-priority task.",
    )
    path.write_text(text, encoding="utf-8")


def run_git_commit(push: bool, dry_run: bool) -> dict[str, Any]:
    status = run_command(["git", "status", "--short"], timeout=30)
    require_success(status, "git status")
    changed = bool(status.stdout.strip())
    if dry_run or not changed:
        return {
            "changed": changed,
            "committed": False,
            "pushed": False,
            "status": status.stdout,
            "dry_run": dry_run,
        }

    add = run_command(
        ["git", "add", "website/index.html", "docs/STARTUP-TASKS.md"],
        timeout=30,
    )
    require_success(add, "git add")
    commit = run_command(["git", "commit", "-m", "Launch UsefulOps AI homepage"], timeout=60)
    require_success(commit, "git commit")

    pushed = False
    push_summary = None
    if push:
        push_result = run_command(["git", "push", "origin", "main"], timeout=120)
        require_success(push_result, "git push")
        pushed = True
        push_summary = command_summary(push_result)

    return {
        "changed": True,
        "committed": True,
        "pushed": pushed,
        "commit": command_summary(commit),
        "push": push_summary,
    }


def run_codex_substep(prompt: str, label: str, dry_run: bool) -> dict[str, Any]:
    """Run Codex only as a bounded subprocess, never as the owner of the loop."""
    codex = shutil.which("codex")
    if codex is None:
        raise RuntimeError("codex CLI is not available for bounded substep")

    substep_dir = ROOT / "local" / "operator-substeps"
    substep_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = substep_dir / f"{new_id('codex-prompt')}-{label}.txt"
    output_path = substep_dir / f"{prompt_path.stem}-output.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    if dry_run:
        return {
            "label": label,
            "dry_run": True,
            "prompt_path": str(prompt_path),
            "output_path": str(output_path),
        }

    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    result = subprocess.run(
        [
            codex,
            "exec",
            "--cd",
            str(ROOT),
            "--sandbox",
            "workspace-write",
            "--ask-for-approval",
            "never",
            prompt,
        ],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=CODEX_SUBSTEP_TIMEOUT_SECONDS,
        check=False,
    )
    output_path.write_text(result.stdout + "\n\nSTDERR:\n" + result.stderr, encoding="utf-8")
    require_success(result, f"bounded Codex substep {label}")
    return {
        "label": label,
        "dry_run": False,
        "prompt_path": str(prompt_path),
        "output_path": str(output_path),
        "result": command_summary(result),
    }


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


def retry_status(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return whether the 09:45 retry guard should do real work today."""
    ensure_schema(conn)
    stale = mark_stale_runs(conn)
    today = datetime.now(timezone.utc).date().isoformat()
    todays_runs = conn.execute(
        """
        SELECT *
        FROM operator_runs
        WHERE date(started_at) = date(?)
          AND trigger_source IN (?, ?)
        ORDER BY started_at DESC
        """,
        (today, PRIMARY_DAILY_TRIGGER, DAILY_RETRY_TRIGGER),
    ).fetchall()
    latest = todays_runs[0] if todays_runs else None
    completed = [row for row in todays_runs if row["status"] == "completed"]
    failed_or_interrupted = [
        row for row in todays_runs if row["status"] in ("failed", "interrupted")
    ]
    running = [row for row in todays_runs if row["status"] == "running"]

    should_retry = False
    reason = "No retry needed."
    if completed:
        reason = "A daily UsefulOps operator run already completed today."
    elif failed_or_interrupted:
        should_retry = True
        reason = "A daily UsefulOps operator run failed or was interrupted today."
    elif running:
        should_retry = False
        reason = "A daily UsefulOps operator run is still active; wait for stale-run recovery."
    else:
        should_retry = True
        reason = "No primary daily UsefulOps operator run is recorded today."

    conn.commit()
    return {
        "should_retry": should_retry,
        "reason": reason,
        "stale_runs_marked_interrupted": [row["id"] for row in stale],
        "latest_daily_run": row_to_dict(latest),
        "daily_runs_today": [dict(row) for row in todays_runs],
    }


def run_website_launch_step(conn: sqlite3.Connection, run_id: str, task: sqlite3.Row, dry_run: bool, push: bool) -> dict[str, Any]:
    checkpoint(
        conn,
        run_id,
        "website_launch_started",
        "Local orchestrator selected the bounded website-launch handler.",
        "Write the launch page, run the static build, and commit/push only if verification passes.",
        "running",
    )

    if not dry_run:
        WEBSITE_INDEX.write_text(LAUNCH_SITE_HTML, encoding="utf-8")
        update_startup_task_doc_for_launch()

    checkpoint(
        conn,
        run_id,
        "website_launch_written",
        "Launch-site files prepared by the local orchestrator.",
        "Run npm build.",
        "running",
    )

    build = run_command(["npm", "run", "build"], timeout=BUILD_TIMEOUT_SECONDS)
    require_success(build, "npm run build")

    checkpoint(
        conn,
        run_id,
        "website_launch_build_verified",
        "Static website build completed successfully.",
        "Record task completion and commit/push if enabled.",
        "running",
    )

    if not dry_run:
        update_task_status(
            conn,
            task["id"],
            "completed",
            "2026-05-30: Local orchestrator replaced the placeholder homepage and verified npm run build.",
        )
        action_log(
            conn,
            "website_launch_prepared",
            "Local UsefulOps operator orchestrator replaced the placeholder homepage and verified the static build.",
            "Git push may publish the public UsefulOps AI homepage through Cloudflare Pages auto-deploy.",
        )

    git_result = run_git_commit(push=push, dry_run=dry_run)
    return {
        "handler": "website_launch",
        "dry_run": dry_run,
        "build": command_summary(build),
        "git": git_result,
        "site": site_placeholder_state(),
    }


def run_codex_planning_step(conn: sqlite3.Connection, run_id: str, task: sqlite3.Row | None, dry_run: bool) -> dict[str, Any]:
    title = task["title"] if task else "No selected task"
    prompt = f"""You are running a bounded UsefulOps AI planning substep.

Constraints:
- Do not edit files.
- Do not send messages or take external action.
- Read only what you need from /Users/aileansolutions/usefulopsai.
- Return concise JSON with keys: task, recommended_next_handler, rationale, files_to_touch, risks.

Task: {title}
"""
    checkpoint(
        conn,
        run_id,
        "bounded_codex_planning_started",
        f"No deterministic handler exists yet for selected task: {title}. Running Codex as a bounded planning-only subprocess.",
        "Review the bounded substep output and add a deterministic handler for the next recurring task.",
        "running",
    )
    result = run_codex_substep(prompt, "planning", dry_run=dry_run)
    action_log(
        conn,
        "bounded_codex_substep",
        f"Ran bounded Codex planning substep for UsefulOps task: {title}",
        "Planning only; no external action or file edit performed by the substep prompt.",
    )
    return {
        "handler": "bounded_codex_planning",
        "dry_run": dry_run,
        "codex": result,
    }


def run_once(conn: sqlite3.Connection, trigger: str, objective: str, dry_run: bool, push: bool) -> dict[str, Any]:
    status = start_run(conn, trigger, objective)
    run_id = status["run"]["id"]
    task = select_task(conn)
    try:
        site_state = site_placeholder_state()
        if task and "placeholder website" in task["title"].lower() and site_state.get("placeholder"):
            result = run_website_launch_step(conn, run_id, task, dry_run=dry_run, push=push)
            summary = "UsefulOps homepage launch step completed by the local orchestrator."
            if dry_run:
                summary = "Dry run completed: local orchestrator can execute the homepage launch handler."
            final = complete_run(
                conn,
                run_id,
                summary,
                "Continue with the next high-priority UsefulOps task on the next daily run.",
            )
        else:
            result = run_codex_planning_step(conn, run_id, task, dry_run=dry_run)
            final = complete_run(
                conn,
                run_id,
                "Bounded Codex planning substep completed; no deterministic task handler was available.",
                "Add or select a deterministic handler before allowing the daily loop to modify files for this task.",
            )
        final["orchestrator"] = result
        return final
    except Exception as exc:
        failed = fail_run(
            conn,
            run_id,
            str(exc),
            "Inspect the failure, fix the deterministic handler or environment, then rerun scripts/operator_loop.py run.",
        )
        failed["orchestrator_error"] = str(exc)
        return failed


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="UsefulOps checkpointed operator loop helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")
    sub.add_parser("status")
    sub.add_parser("retry-status")

    start = sub.add_parser("start")
    start.add_argument("--trigger", default="manual")
    start.add_argument("--objective", default="Move one high-priority UsefulOps startup item forward.")

    run = sub.add_parser("run")
    run.add_argument("--trigger", default="manual")
    run.add_argument("--objective", default="Move one high-priority UsefulOps startup item forward.")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--push", action="store_true")

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
        elif args.command == "retry-status":
            print_json(retry_status(conn))
        elif args.command == "start":
            print_json(start_run(conn, args.trigger, args.objective))
        elif args.command == "run":
            result = run_once(conn, args.trigger, args.objective, args.dry_run, args.push)
            print_json(result)
            if result.get("run", {}).get("status") == "failed":
                return 1
        elif args.command == "checkpoint":
            print_json(checkpoint(conn, args.run_id, args.step, args.summary, args.next_action, args.status))
        elif args.command == "complete":
            print_json(complete_run(conn, args.run_id, args.summary, args.next_action))
        elif args.command == "fail":
            print_json(fail_run(conn, args.run_id, args.error, args.next_action))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
