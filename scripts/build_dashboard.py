#!/usr/bin/env python3
"""Build a private UsefulOps operating dashboard from local SQLite data."""

from __future__ import annotations

import html
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
EXPORT_DIR = ROOT / "local" / "exports"
DASHBOARD_HTML = EXPORT_DIR / "usefulops-dashboard.html"
DASHBOARD_JSON = EXPORT_DIR / "usefulops-dashboard.json"


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


def scalar(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    value = conn.execute(query, params).fetchone()[0]
    return int(value or 0)


def money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(query, params).fetchall()]


def compute_metrics(conn: sqlite3.Connection) -> dict[str, Any]:
    gross = scalar(
        conn,
        "SELECT COALESCE(SUM(amount_cents), 0) FROM revenue WHERE status IN ('received', 'paid', 'succeeded')",
    )
    latest_sync = conn.execute(
        """
        SELECT *
        FROM stripe_sync_runs
        WHERE status = 'completed'
        ORDER BY synced_at DESC
        LIMIT 1
        """
    ).fetchone()
    mrr = int(latest_sync["active_mrr_cents"]) if latest_sync else 0
    expenses = scalar(conn, "SELECT COALESCE(SUM(amount_cents), 0) FROM expenses WHERE status IN ('approved', 'incurred', 'paid')")
    tax_reserve = round(gross * 0.30)
    post_tax = max(gross - tax_reserve - expenses, 0)
    brian_share = round(post_tax * 0.50)
    growth = post_tax - brian_share
    metrics = {
        "snapshot_at": utc_now(),
        "gross_revenue_cents": gross,
        "active_mrr_cents": mrr,
        "tax_reserve_cents": tax_reserve,
        "brian_share_cents": brian_share,
        "usefulops_growth_cents": growth,
        "operator_discretion_cents": 0,
        "budget_used_cents": expenses,
        "budget_limit_cents": 10000,
        "active_prospects": scalar(conn, "SELECT COUNT(*) FROM prospects WHERE status NOT IN ('disqualified', 'converted')"),
        "cold_contacts_sent": scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE status = 'sent' AND action_type LIKE '%cold%'"),
        "replies": scalar(conn, "SELECT COUNT(*) FROM outreach_actions WHERE response_at IS NOT NULL OR status = 'replied'"),
        "active_clients": scalar(conn, "SELECT COUNT(*) FROM clients WHERE status = 'active'"),
        "open_deliverables": scalar(conn, "SELECT COUNT(*) FROM deliverables WHERE status NOT IN ('delivered', 'cancelled')"),
        "open_tasks": scalar(conn, "SELECT COUNT(*) FROM tasks WHERE status IN ('pending', 'in_progress')"),
        "payment_links": rows(conn, "SELECT name, amount_cents, billing_type, status FROM payment_links ORDER BY amount_cents"),
        "tasks": rows(conn, "SELECT title, status, priority, updated_at FROM tasks ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, updated_at DESC LIMIT 8"),
        "recent_actions": rows(conn, "SELECT action_at, action_type, summary FROM action_log ORDER BY action_at DESC LIMIT 10"),
        "latest_stripe_sync": dict(latest_sync) if latest_sync else None,
    }
    return metrics


def write_snapshot(conn: sqlite3.Connection, metrics: dict[str, Any]) -> str:
    snapshot_id = new_id("dash")
    conn.execute(
        """
        INSERT INTO dashboard_snapshots (
          id, snapshot_at, gross_revenue_cents, active_mrr_cents, tax_reserve_cents,
          brian_share_cents, usefulops_growth_cents, operator_discretion_cents,
          budget_used_cents, active_prospects, cold_contacts_sent, replies,
          active_clients, open_deliverables, open_tasks, metrics_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot_id,
            metrics["snapshot_at"],
            metrics["gross_revenue_cents"],
            metrics["active_mrr_cents"],
            metrics["tax_reserve_cents"],
            metrics["brian_share_cents"],
            metrics["usefulops_growth_cents"],
            metrics["operator_discretion_cents"],
            metrics["budget_used_cents"],
            metrics["active_prospects"],
            metrics["cold_contacts_sent"],
            metrics["replies"],
            metrics["active_clients"],
            metrics["open_deliverables"],
            metrics["open_tasks"],
            json.dumps(metrics, sort_keys=True),
        ),
    )
    return snapshot_id


def action_log(conn: sqlite3.Connection, summary: str) -> None:
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', 'dashboard_snapshot_built',
                'UsefulOps approved authority envelope', 'dashboard',
                ?, 0, 0, 0, 'Private local dashboard export only; not published.')
        """,
        (new_id("log"), utc_now(), summary),
    )


def complete_task(conn: sqlite3.Connection, snapshot_id: str) -> None:
    note = (
        "2026-05-30: Built private local dashboard export from SQLite at "
        f"local/exports/usefulops-dashboard.html; latest snapshot {snapshot_id}."
    )
    conn.execute(
        """
        UPDATE tasks
        SET status = 'completed',
            notes = CASE
              WHEN notes IS NULL OR notes = '' THEN ?
              WHEN instr(notes, ?) = 0 THEN notes || char(10) || ?
              ELSE notes
            END,
            updated_at = ?
        WHERE id = 'task-20260529-usefulops-dashboard'
        """,
        (note, note, note, utc_now()),
    )


def render_dashboard(metrics: dict[str, Any], snapshot_id: str) -> str:
    cards = [
        ("Gross revenue", money(metrics["gross_revenue_cents"])),
        ("Active MRR", money(metrics["active_mrr_cents"])),
        ("Tax reserve", money(metrics["tax_reserve_cents"])),
        ("Brian / AI Lean share", money(metrics["brian_share_cents"])),
        ("UsefulOps growth", money(metrics["usefulops_growth_cents"])),
        ("Budget used", f"{money(metrics['budget_used_cents'])} / {money(metrics['budget_limit_cents'])}"),
        ("Active prospects", str(metrics["active_prospects"])),
        ("Open tasks", str(metrics["open_tasks"])),
    ]
    card_html = "\n".join(
        f"<section class=\"card\"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></section>"
        for label, value in cards
    )
    task_rows = "\n".join(
        f"<tr><td>{html.escape(row['title'])}</td><td>{html.escape(row['status'])}</td><td>{html.escape(row['priority'])}</td></tr>"
        for row in metrics["tasks"]
    )
    action_rows = "\n".join(
        f"<li><strong>{html.escape(row['action_type'])}</strong><span>{html.escape(row['summary'])}</span></li>"
        for row in metrics["recent_actions"]
    )
    link_rows = "\n".join(
        f"<tr><td>{html.escape(row['name'])}</td><td>{money(int(row['amount_cents'] or 0))}</td><td>{html.escape(row['billing_type'])}</td><td>{html.escape(row['status'])}</td></tr>"
        for row in metrics["payment_links"]
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>UsefulOps Private Dashboard</title>
    <style>
      :root {{ --ink:#18202a; --muted:#5b6675; --line:#d8dee7; --paper:#f6f7f9; --panel:#fff; --accent:#0f766e; }}
      * {{ box-sizing: border-box; }}
      body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:var(--paper); color:var(--ink); }}
      main {{ width:min(1180px, calc(100% - 40px)); margin:0 auto; padding:36px 0 56px; }}
      header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; margin-bottom:28px; }}
      h1 {{ margin:0; font-size:34px; letter-spacing:0; }}
      .meta {{ color:var(--muted); font-size:14px; }}
      .grid {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px; }}
      .card {{ border:1px solid var(--line); background:var(--panel); padding:18px; min-height:104px; }}
      .card span {{ display:block; color:var(--muted); font-size:13px; margin-bottom:12px; }}
      .card strong {{ display:block; font-size:26px; }}
      .section {{ margin-top:28px; border:1px solid var(--line); background:var(--panel); padding:22px; }}
      h2 {{ margin:0 0 16px; font-size:22px; }}
      table {{ width:100%; border-collapse:collapse; }}
      th, td {{ text-align:left; padding:10px 0; border-top:1px solid var(--line); vertical-align:top; }}
      th {{ color:var(--muted); font-size:13px; font-weight:700; }}
      ul {{ margin:0; padding:0; list-style:none; display:grid; gap:12px; }}
      li {{ display:grid; gap:4px; }}
      li span {{ color:var(--muted); line-height:1.45; }}
      @media (max-width: 880px) {{ .grid {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} header {{ display:block; }} }}
      @media (max-width: 560px) {{ .grid {{ grid-template-columns:1fr; }} }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>UsefulOps Private Dashboard</h1>
          <div class="meta">Snapshot {html.escape(snapshot_id)} at {html.escape(metrics['snapshot_at'])}</div>
        </div>
        <div class="meta">Local private export. Do not publish.</div>
      </header>
      <div class="grid">{card_html}</div>
      <section class="section">
        <h2>Payment Links</h2>
        <table><thead><tr><th>Name</th><th>Amount</th><th>Billing</th><th>Status</th></tr></thead><tbody>{link_rows}</tbody></table>
      </section>
      <section class="section">
        <h2>Tasks</h2>
        <table><thead><tr><th>Task</th><th>Status</th><th>Priority</th></tr></thead><tbody>{task_rows}</tbody></table>
      </section>
      <section class="section">
        <h2>Recent Action Log</h2>
        <ul>{action_rows}</ul>
      </section>
    </main>
  </body>
</html>
"""


def build_dashboard() -> dict[str, Any]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        ensure_schema(conn)
        metrics = compute_metrics(conn)
        snapshot_id = write_snapshot(conn, metrics)
        metrics["snapshot_id"] = snapshot_id
        DASHBOARD_JSON.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
        DASHBOARD_HTML.write_text(render_dashboard(metrics, snapshot_id), encoding="utf-8")
        action_log(conn, f"Built UsefulOps private dashboard snapshot {snapshot_id}.")
        complete_task(conn, snapshot_id)
        conn.commit()
    return {
        "ok": True,
        "snapshot_id": snapshot_id,
        "html": str(DASHBOARD_HTML),
        "json": str(DASHBOARD_JSON),
        "gross_revenue_cents": metrics["gross_revenue_cents"],
        "active_mrr_cents": metrics["active_mrr_cents"],
        "open_tasks": metrics["open_tasks"],
    }


def main() -> int:
    print(json.dumps(build_dashboard(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
