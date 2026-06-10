#!/usr/bin/env python3
"""Check UsefulOps booking/client signals and report newly observed items."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
STATE_PATH = ROOT / "local" / "state" / "booking_client_alert_state.json"
GOG_ACCOUNT = "rowan.vale@usefulopsai.com"
GOG_CLIENT = "usefulops"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_json(command: list[str], timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-1200:],
                    "stderr": completed.stderr[-1200:],
                },
                sort_keys=True,
            )
        )
    if not completed.stdout.strip():
        return {}
    return json.loads(completed.stdout)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "calendar_event_ids": [],
            "client_ids": [],
            "revenue_ids": [],
            "intake_response_ids": [],
        }
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def calendar_events() -> list[dict[str, Any]]:
    payload = run_json(
        [
            "gog",
            "calendar",
            "events",
            "--all",
            "--days",
            "60",
            "--max",
            "100",
            "--account",
            GOG_ACCOUNT,
            "--client",
            GOG_CLIENT,
            "--json",
            "--no-input",
        ],
        timeout=180,
    )
    events = payload.get("events", [])
    return [event for event in events if is_relevant_calendar_event(event)]


def is_relevant_calendar_event(event: dict[str, Any]) -> bool:
    status = str(event.get("status") or "").lower()
    if status and status != "confirmed":
        return False
    organizer_email = str(event.get("organizer", {}).get("email") or "").lower()
    creator_email = str(event.get("creator", {}).get("email") or "").lower()
    summary = str(event.get("summary") or "").lower()
    description = str(event.get("description") or "").lower()
    if "holiday" in organizer_email or "holiday" in creator_email:
        return False
    text = f"{summary}\n{description}"
    appointment_words = ("usefulops", "usefulops ai", "rowan", "intake", "workflow", "consult")
    return any(word in text for word in appointment_words)


def sync_stripe() -> dict[str, Any]:
    return run_json(["scripts/stripe_sync.py"], timeout=180)


def db_rows() -> dict[str, list[sqlite3.Row]]:
    with connect() as conn:
        clients = conn.execute(
            "SELECT id, company, status, package, payment_status, created_at FROM clients ORDER BY created_at"
        ).fetchall()
        revenue = conn.execute(
            "SELECT id, amount_cents, currency, status, received_at, external_id FROM revenue ORDER BY created_at"
        ).fetchall()
        intakes = conn.execute(
            """
            SELECT response_id, submitted_at, business_name, business_type, urgency, workflow_needing_help
            FROM intake_form_responses
            ORDER BY submitted_at, response_id
            """
        ).fetchall()
    return {"clients": clients, "revenue": revenue, "intakes": intakes}


def row_ids(rows: list[sqlite3.Row], key: str) -> set[str]:
    return {str(row[key]) for row in rows if row[key]}


def event_ids(events: list[dict[str, Any]]) -> set[str]:
    return {str(event.get("id")) for event in events if event.get("id")}


def event_time(event: dict[str, Any]) -> str:
    start = event.get("start", {})
    return str(start.get("dateTime") or start.get("date") or "unknown time")


def main() -> int:
    alerts: list[str] = []
    errors: list[str] = []
    state = load_state()

    try:
        # Keep the form response table fresh before inspecting it.
        run_json(["scripts/check_intake_responses.py"], timeout=180)
    except Exception as exc:
        errors.append(f"intake check failed: {exc}")

    try:
        stripe_result = sync_stripe()
        if not stripe_result.get("ok"):
            errors.append(f"Stripe sync failed: {stripe_result.get('error')}")
    except Exception as exc:
        errors.append(f"Stripe sync failed: {exc}")

    try:
        events = calendar_events()
    except Exception as exc:
        events = []
        errors.append(f"calendar check failed: {exc}")

    rows = db_rows()
    seen_events = set(state.get("calendar_event_ids", []))
    seen_clients = set(state.get("client_ids", []))
    seen_revenue = set(state.get("revenue_ids", []))
    seen_intakes = set(state.get("intake_response_ids", []))

    new_events = [event for event in events if str(event.get("id")) not in seen_events]
    for event in new_events:
        alerts.append(
            "New UsefulOps booking detected: "
            f"{event.get('summary') or 'Untitled event'} at {event_time(event)}."
        )

    new_clients = [row for row in rows["clients"] if str(row["id"]) not in seen_clients]
    for row in new_clients:
        alerts.append(
            "New UsefulOps client row detected: "
            f"{row['company']} ({row['status']}, payment={row['payment_status'] or 'unknown'})."
        )

    new_revenue = [row for row in rows["revenue"] if str(row["id"]) not in seen_revenue]
    for row in new_revenue:
        amount = f"{(row['amount_cents'] or 0) / 100:.2f} {row['currency'] or 'USD'}"
        alerts.append(f"New UsefulOps revenue detected: {amount}, status={row['status']}.")

    new_intakes = [row for row in rows["intakes"] if str(row["response_id"]) not in seen_intakes]
    for row in new_intakes:
        alerts.append(
            "New UsefulOps intake response recorded: "
            f"{row['business_name'] or 'unknown business'}; urgency={row['urgency'] or 'not specified'}."
        )

    state.update(
        {
            "calendar_event_ids": sorted(event_ids(events)),
            "client_ids": sorted(row_ids(rows["clients"], "id")),
            "revenue_ids": sorted(row_ids(rows["revenue"], "id")),
            "intake_response_ids": sorted(row_ids(rows["intakes"], "response_id")),
            "last_checked_at": utc_now(),
        }
    )
    save_state(state)

    result = {
        "ok": not errors,
        "checked_at": utc_now(),
        "alerts": alerts,
        "alert_count": len(alerts),
        "errors": errors,
        "counts": {
            "calendar_relevant_events": len(events),
            "clients": len(rows["clients"]),
            "revenue_rows": len(rows["revenue"]),
            "intake_responses": len(rows["intakes"]),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
