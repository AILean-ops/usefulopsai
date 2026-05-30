#!/usr/bin/env python3
"""Sync read-only UsefulOps Stripe data into the local operating database."""

from __future__ import annotations

import base64
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
DEFAULT_SECRET_ENV = ROOT / "local" / "secrets" / "stripe.env"


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


def load_key() -> str:
    key = os.environ.get("STRIPE_API_KEY", "").strip()
    if key:
        return key

    if DEFAULT_SECRET_ENV.exists():
        for line in DEFAULT_SECRET_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("STRIPE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    raise RuntimeError("Missing STRIPE_API_KEY in environment or local/secrets/stripe.env")


def stripe_get(key: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = urllib.parse.urlencode(params or {})
    url = f"https://api.stripe.com{path}" + (f"?{query}" if query else "")
    token = base64.b64encode(f"{key}:".encode()).decode()
    request = urllib.request.Request(url, headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}
        message = parsed.get("error", {}).get("message", f"Stripe HTTP {exc.code}")
        raise RuntimeError(message) from exc


def stripe_list(key: str, path: str, limit: int = 100) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    starting_after = None
    while True:
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if starting_after:
            params["starting_after"] = starting_after
        body = stripe_get(key, path, params)
        batch = body.get("data", [])
        if not isinstance(batch, list):
            return items
        items.extend(batch)
        if not body.get("has_more") or not batch:
            return items
        starting_after = batch[-1].get("id")


def amount_from_payment_link(link: dict[str, Any]) -> int:
    line_items = link.get("line_items")
    if isinstance(line_items, dict):
        data = line_items.get("data")
        if isinstance(data, list) and data:
            price = data[0].get("price", {})
            if isinstance(price, dict) and isinstance(price.get("unit_amount"), int):
                return price["unit_amount"]
    return 0


def sync_payment_links(conn: sqlite3.Connection, links: list[dict[str, Any]]) -> None:
    now = utc_now()
    for link in links:
        link_id = link.get("id")
        url = link.get("url")
        if not link_id or not url:
            continue
        amount_cents = amount_from_payment_link(link)
        billing_type = "unknown"
        if isinstance(link.get("line_items"), dict):
            data = link["line_items"].get("data")
            if isinstance(data, list) and data:
                recurring = data[0].get("price", {}).get("recurring")
                billing_type = "monthly_subscription" if recurring else "one_time"
        name = link.get("metadata", {}).get("name") or link.get("id")
        conn.execute(
            """
            INSERT INTO payment_links (
              id, name, stripe_url, amount_cents, currency, billing_type, status, notes, updated_at
            )
            VALUES (?, ?, ?, ?, 'USD', ?, ?, 'Synced from Stripe payment_links API.', ?)
            ON CONFLICT(id) DO UPDATE SET
              name = excluded.name,
              stripe_url = excluded.stripe_url,
              amount_cents = CASE WHEN excluded.amount_cents > 0 THEN excluded.amount_cents ELSE payment_links.amount_cents END,
              billing_type = excluded.billing_type,
              status = excluded.status,
              updated_at = excluded.updated_at
            """,
            (
                link_id,
                name,
                url,
                amount_cents,
                billing_type,
                "active" if link.get("active") else "inactive",
                now,
            ),
        )


def sync_revenue(conn: sqlite3.Connection, sessions: list[dict[str, Any]]) -> int:
    inserted = 0
    for session in sessions:
        session_id = session.get("id")
        payment_status = session.get("payment_status")
        amount_total = session.get("amount_total")
        if not session_id or payment_status != "paid" or not isinstance(amount_total, int):
            continue
        created = session.get("created")
        received_at = (
            datetime.fromtimestamp(created, timezone.utc).replace(microsecond=0).isoformat()
            if isinstance(created, int)
            else utc_now()
        )
        before = conn.total_changes
        conn.execute(
            """
            INSERT OR IGNORE INTO revenue (
              id, source, amount_cents, currency, status, received_at, external_id, notes
            )
            VALUES (?, 'stripe_checkout_session', ?, 'USD', 'received', ?, ?, ?)
            """,
            (
                new_id("rev"),
                amount_total,
                received_at,
                session_id,
                "Synced from Stripe checkout sessions API.",
            ),
        )
        if conn.total_changes > before:
            inserted += 1
    return inserted


def monthly_amount_cents(subscription: dict[str, Any]) -> int:
    total = 0
    items = subscription.get("items", {}).get("data", [])
    if not isinstance(items, list):
        return 0
    for item in items:
        price = item.get("price", {})
        amount = price.get("unit_amount")
        interval = price.get("recurring", {}).get("interval")
        quantity = item.get("quantity", 1)
        if not isinstance(amount, int) or not isinstance(quantity, int):
            continue
        if interval == "month":
            total += amount * quantity
        elif interval == "year":
            total += round((amount * quantity) / 12)
    return total


def active_mrr_cents(subscriptions: list[dict[str, Any]]) -> int:
    active_statuses = {"active", "trialing", "past_due"}
    return sum(
        monthly_amount_cents(sub)
        for sub in subscriptions
        if sub.get("status") in active_statuses
    )


def action_log(conn: sqlite3.Connection, action_type: str, summary: str, risk_notes: str = "") -> None:
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', ?, 'UsefulOps approved authority envelope', 'stripe_sync',
                ?, 0, 0, 0, ?)
        """,
        (new_id("log"), utc_now(), action_type, summary, risk_notes),
    )


def complete_task(conn: sqlite3.Connection) -> None:
    note = "2026-05-30: Added and ran read-only Stripe sync into the UsefulOps SQLite database."
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
        WHERE id = 'task-20260529-stripe-api-integration'
        """,
        (note, note, note, utc_now()),
    )


def run_sync() -> dict[str, Any]:
    key = load_key()
    with connect() as conn:
        ensure_schema(conn)
        run_id = new_id("stripe-sync")
        try:
            payment_links = stripe_list(key, "/v1/payment_links")
            sessions = stripe_list(key, "/v1/checkout/sessions")
            subscriptions = stripe_list(key, "/v1/subscriptions")
            sync_payment_links(conn, payment_links)
            revenue_inserted = sync_revenue(conn, sessions)
            gross = conn.execute(
                "SELECT COALESCE(SUM(amount_cents), 0) FROM revenue WHERE status IN ('received', 'paid', 'succeeded')"
            ).fetchone()[0]
            mrr = active_mrr_cents(subscriptions)
            summary = {
                "payment_links_seen": len(payment_links),
                "checkout_sessions_seen": len(sessions),
                "subscriptions_seen": len(subscriptions),
                "new_revenue_rows": revenue_inserted,
                "gross_revenue_cents": gross,
                "active_mrr_cents": mrr,
            }
            conn.execute(
                """
                INSERT INTO stripe_sync_runs (
                  id, synced_at, status, payment_links_seen, checkout_sessions_seen,
                  subscriptions_seen, gross_revenue_cents, active_mrr_cents, summary_json
                )
                VALUES (?, ?, 'completed', ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    utc_now(),
                    len(payment_links),
                    len(sessions),
                    len(subscriptions),
                    gross,
                    mrr,
                    json.dumps(summary, sort_keys=True),
                ),
            )
            action_log(
                conn,
                "stripe_sync_completed",
                f"Synced Stripe data: {len(payment_links)} payment links, {len(sessions)} checkout sessions, {len(subscriptions)} subscriptions.",
                "Read-only Stripe sync; no charges, refunds, customer messages, or external mutations performed.",
            )
            complete_task(conn)
            conn.commit()
            return {"ok": True, "run_id": run_id, **summary}
        except Exception as exc:
            conn.execute(
                """
                INSERT INTO stripe_sync_runs (id, synced_at, status, summary_json, error)
                VALUES (?, ?, 'failed', '{}', ?)
                """,
                (run_id, utc_now(), str(exc)),
            )
            action_log(conn, "stripe_sync_failed", f"Stripe sync failed: {exc}")
            conn.commit()
            return {"ok": False, "run_id": run_id, "error": str(exc)}


def main() -> int:
    result = run_sync()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
