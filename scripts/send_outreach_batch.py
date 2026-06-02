#!/usr/bin/env python3
"""Send a bounded UsefulOps cold-outreach batch through GOG Gmail."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local" / "data" / "usefulopsai.sqlite3"
GOG_ACCOUNT = "rowan.vale@usefulopsai.com"
GOG_CLIENT = "usefulops"


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


def domain_for(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else ""


def is_suppressed(conn: sqlite3.Connection, prospect_id: str, email: str) -> bool:
    email = email.lower()
    domain = domain_for(email)
    row = conn.execute(
        """
        SELECT 1
        FROM suppressions
        WHERE (? != '' AND lower(email) = ?)
           OR (? != '' AND lower(domain) = ?)
           OR prospect_id = ?
        LIMIT 1
        """,
        (email, email, domain, domain, prospect_id),
    ).fetchone()
    return row is not None


def has_opt_out(body: str) -> bool:
    lower = body.lower()
    return (
        "no thanks" in lower
        or "do not follow up" in lower
        or "not relevant" in lower
        or "unsubscribe" in lower
    )


def action_log(
    conn: sqlite3.Connection,
    action_type: str,
    summary: str,
    external_effect: int,
    risk_notes: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO action_log (
          id, action_at, actor, action_type, authority_basis, target_type,
          summary, external_effect, cost_cents, revenue_cents, risk_notes
        )
        VALUES (?, ?, 'rowan', ?, 'UsefulOps approved authority envelope', 'outreach_batch',
                ?, ?, 0, 0, ?)
        """,
        (new_id("log"), utc_now(), action_type, summary, external_effect, risk_notes),
    )


def candidates(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          oa.id AS outreach_id,
          oa.prospect_id,
          oa.contact_id,
          oa.subject,
          oa.body,
          oa.notes,
          p.company,
          p.website,
          p.niche,
          c.email
        FROM outreach_actions oa
        JOIN prospects p ON p.id = oa.prospect_id
        JOIN contacts c ON c.id = oa.contact_id
        WHERE oa.status = 'draft'
          AND oa.channel = 'email'
          AND oa.action_type = 'cold_initial'
          AND c.email IS NOT NULL
        ORDER BY oa.created_at, oa.id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def gog_send(row: sqlite3.Row, dry_run: bool) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as body_file:
        body_file.write(row["body"])
        body_path = body_file.name
    command = [
        "gog",
        "gmail",
        "send",
        "--to",
        row["email"],
        "--subject",
        row["subject"],
        "--body-file",
        body_path,
        "--account",
        GOG_ACCOUNT,
        "--client",
        GOG_CLIENT,
        "--json",
        "--no-input",
    ]
    if dry_run:
        command.append("--dry-run")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    Path(body_path).unlink(missing_ok=True)
    payload: dict[str, Any]
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"stdout": completed.stdout[-1000:]}
    payload.update(
        {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-1000:],
        }
    )
    return payload


def send_batch(limit: int, dry_run: bool) -> dict[str, Any]:
    sent: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []
    with connect() as conn:
        ensure_schema(conn)
        rows = candidates(conn, limit)
        for row in rows:
            email = row["email"].lower()
            if is_suppressed(conn, row["prospect_id"], email):
                skipped.append({"outreach_id": row["outreach_id"], "email": email, "reason": "suppressed"})
                continue
            if not row["subject"] or not row["body"]:
                skipped.append({"outreach_id": row["outreach_id"], "email": email, "reason": "missing subject/body"})
                continue
            if not has_opt_out(row["body"]):
                skipped.append({"outreach_id": row["outreach_id"], "email": email, "reason": "missing opt-out language"})
                continue
            result = gog_send(row, dry_run=dry_run)
            if not result.get("ok"):
                failed.append(
                    {
                        "outreach_id": row["outreach_id"],
                        "email": email,
                        "reason": f"gog send failed: {result.get('stderr') or result.get('stdout') or result.get('returncode')}",
                    }
                )
                continue
            now = utc_now()
            if not dry_run:
                result_note = json.dumps(
                    {
                        key: result.get(key)
                        for key in ("id", "messageId", "threadId", "dry_run", "op")
                        if key in result
                    },
                    sort_keys=True,
                )
                conn.execute(
                    """
                    UPDATE outreach_actions
                    SET status = 'sent',
                        sent_at = ?,
                        approved_by = 'rowan',
                        approved_at = COALESCE(approved_at, ?),
                        notes = COALESCE(notes, '') || char(10) || ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (now, now, f"Sent via GOG Gmail. Result: {result_note}", now, row["outreach_id"]),
                )
                conn.execute(
                    """
                    UPDATE prospects
                    SET status = 'sent',
                        next_action = 'Monitor for reply, bounce, opt-out, or follow-up timing.',
                        next_action_at = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (now, now, row["prospect_id"]),
                )
            sent.append({"outreach_id": row["outreach_id"], "email": email, "company": row["company"]})
        action_log(
            conn,
            "outreach_batch_dry_run" if dry_run else "outreach_batch_sent",
            f"{'Dry-run verified' if dry_run else 'Sent'} UsefulOps outreach batch: sent={len(sent)}, skipped={len(skipped)}, failed={len(failed)}.",
            0 if dry_run else 1,
            "Bounded batch; suppression and opt-out checks enforced before each message.",
        )
        conn.commit()
    return {
        "ok": not failed,
        "dry_run": dry_run,
        "requested_limit": limit,
        "sent_count": len(sent),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "sent": sent,
        "skipped": skipped,
        "failed": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a bounded UsefulOps outreach batch.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 10:
        raise SystemExit("--limit must be between 1 and 10")
    result = send_batch(args.limit, args.dry_run)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
