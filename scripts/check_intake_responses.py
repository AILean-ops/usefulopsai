#!/usr/bin/env python3
"""Poll UsefulOps Google Form intake responses and record new submissions."""

from __future__ import annotations

import argparse
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
FORM_ID = "1MWRj6Otr5THMgmvKccfTsN16HzhQIWqI-ggAoN15bw4"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf4I2PCTYqdUgcJhTSK48hG6-RaubbbyEBdTBOzrvg9Vt-Zmw/viewform"
FORM_EDIT_URL = f"https://docs.google.com/forms/d/{FORM_ID}/edit"
GOG_ACCOUNT = "rowan.vale@usefulopsai.com"
GOG_CLIENT = "usefulops"

FIELD_MAP = {
    "Your name": "name",
    "Email address": "email",
    "Phone number": "phone",
    "Business name": "business_name",
    "Business website or social page": "website",
    "Type of business": "business_type",
    "Team size": "team_size",
    "Biggest operational pain point": "pain_point",
    "Workflow that needs the most help": "workflow_needing_help",
    "Tools you already use": "tools_used",
    "How urgent is this?": "urgency",
    "What would make this worth fixing?": "worth_fixing",
}


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


def run_gog(args: list[str]) -> dict[str, Any]:
    command = [
        "gog",
        *args,
        "--account",
        GOG_ACCOUNT,
        "--client",
        GOG_CLIENT,
        "--json",
        "--no-input",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
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
                indent=2,
            )
        )
    return json.loads(completed.stdout)


def response_question_map(form_payload: dict[str, Any]) -> dict[str, str]:
    form = form_payload.get("form", {})
    mapping: dict[str, str] = {}
    for item in form.get("items", []):
        question = item.get("questionItem", {}).get("question", {})
        question_id = question.get("questionId")
        title = item.get("title")
        if question_id and title:
            mapping[question_id] = title
    return mapping


def answer_value(answer: dict[str, Any]) -> str:
    answers = answer.get("textAnswers", {}).get("answers", [])
    values = [str(item.get("value", "")).strip() for item in answers if item.get("value")]
    return ", ".join(values)


def normalize_response(response: dict[str, Any], question_titles: dict[str, str]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "response_id": response["responseId"],
        "form_id": FORM_ID,
        "submitted_at": response.get("lastSubmittedTime") or response.get("createTime"),
        "raw_json": json.dumps(response, sort_keys=True),
    }
    for question_id, answer in response.get("answers", {}).items():
        title = question_titles.get(question_id, question_id)
        field = FIELD_MAP.get(title)
        if field:
            normalized[field] = answer_value(answer)
    return normalized


def shorten(value: str | None, limit: int = 180) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def alert_message(row: dict[str, Any]) -> str:
    business = row.get("business_name") or "Unknown business"
    business_type = row.get("business_type") or "not specified"
    urgency = row.get("urgency") or "not specified"
    pain = shorten(row.get("pain_point"), 220) or "not provided"
    workflow = shorten(row.get("workflow_needing_help"), 220) or "not provided"
    submitted_at = row.get("submitted_at") or "unknown time"
    return (
        "**New UsefulOps intake submitted**\n"
        f"- Business: {business}\n"
        f"- Type: {business_type}\n"
        f"- Urgency: {urgency}\n"
        f"- Submitted: {submitted_at}\n"
        f"- Pain point: {pain}\n"
        f"- Workflow: {workflow}\n"
        f"- Form responses: <{FORM_EDIT_URL}>"
    )


def insert_response(
    conn: sqlite3.Connection,
    row: dict[str, Any],
    alert_status: str,
    dry_run: bool,
) -> bool:
    exists = conn.execute(
        "SELECT 1 FROM intake_form_responses WHERE response_id = ?",
        (row["response_id"],),
    ).fetchone()
    if exists:
        return False
    if dry_run:
        return True
    conn.execute(
        """
        INSERT INTO intake_form_responses (
          response_id, form_id, submitted_at, recorded_at, alert_status,
          name, email, phone, business_name, website, business_type, team_size,
          urgency, pain_point, workflow_needing_help, tools_used, worth_fixing, raw_json
        )
        VALUES (
          :response_id, :form_id, :submitted_at, :recorded_at, :alert_status,
          :name, :email, :phone, :business_name, :website, :business_type, :team_size,
          :urgency, :pain_point, :workflow_needing_help, :tools_used, :worth_fixing, :raw_json
        )
        """,
        {
            **{key: None for key in FIELD_MAP.values()},
            **row,
            "recorded_at": utc_now(),
            "alert_status": alert_status,
        },
    )
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type, target_id,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', 'intake_form_response_recorded',
                'UsefulOps autonomous operating authority; Brian delegated business setup decisions',
                'intake_form_response', ?, ?, 0, 0, 0, ?)
        """,
        (
            new_id("log"),
            utc_now(),
            row["response_id"],
            f"Recorded UsefulOps intake form response from {row.get('business_name') or 'unknown business'}",
            f"alert_status={alert_status}",
        ),
    )
    return True


def mark_alerted(conn: sqlite3.Connection, response_ids: list[str], dry_run: bool) -> None:
    if dry_run or not response_ids:
        return
    now = utc_now()
    conn.executemany(
        """
        UPDATE intake_form_responses
        SET alerted_at = ?, alert_status = 'alerted'
        WHERE response_id = ?
        """,
        [(now, response_id) for response_id in response_ids],
    )


def check(mark_existing: bool, dry_run: bool, max_responses: int) -> dict[str, Any]:
    form_payload = run_gog(["forms", "get", FORM_ID])
    responses_payload = run_gog(["forms", "responses", "list", FORM_ID, "--max", str(max_responses)])
    question_titles = response_question_map(form_payload)
    responses = [
        normalize_response(response, question_titles)
        for response in responses_payload.get("responses", [])
    ]
    responses.sort(key=lambda item: item.get("submitted_at") or "")

    conn = connect()
    ensure_schema(conn)

    new_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    try:
        for row in responses:
            alert_status = "seen_baseline" if mark_existing else "pending"
            inserted = insert_response(conn, row, alert_status, dry_run)
            if not inserted:
                continue
            if mark_existing:
                baseline_rows.append(row)
            else:
                new_rows.append(row)

        if new_rows:
            mark_alerted(conn, [row["response_id"] for row in new_rows], dry_run)
        if not dry_run:
            conn.commit()
    finally:
        conn.close()

    return {
        "ok": True,
        "form_id": FORM_ID,
        "form_url": FORM_URL,
        "checked_at": utc_now(),
        "dry_run": dry_run,
        "mark_existing": mark_existing,
        "seen_count": len(responses),
        "new_count": len(new_rows),
        "baseline_count": len(baseline_rows),
        "alerts": [alert_message(row) for row in new_rows],
        "new_response_ids": [row["response_id"] for row in new_rows],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mark-existing", action="store_true", help="Record unseen responses without alerting")
    parser.add_argument("--dry-run", action="store_true", help="Do not write database state")
    parser.add_argument("--max", type=int, default=50, help="Maximum responses to inspect")
    args = parser.parse_args()

    try:
        result = check(mark_existing=args.mark_existing, dry_run=args.dry_run, max_responses=args.max)
    except Exception as exc:
        result = {
            "ok": False,
            "checked_at": utc_now(),
            "error": str(exc),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
