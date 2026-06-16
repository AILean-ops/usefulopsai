# UsefulOps CRM v1

UsefulOps CRM v1 is the local canonical lead layer for inbound responses from AIPromotionGuy.com and UsefulOpsAI.com.

## Source Of Truth

- Database: `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`
- Schema: `/Users/aileansolutions/usefulopsai/scripts/schema.sql`
- Shared CRM helper: `/Users/aileansolutions/usefulopsai/scripts/usefulops_common.py`
- Integrity checker: `/Users/aileansolutions/usefulopsai/scripts/crm_integrity_check.py`
- Private dashboard export: `/Users/aileansolutions/usefulopsai/local/exports/usefulops-dashboard.html`

## Inbound Sources

### AIPromotionGuy.com

- Public site form provider: Web3Forms.
- Watcher: `/Users/aileansolutions/.openclaw/workspace/scripts/watch_aipromotion_web3forms.py`
- Watch method: Gmail search for Web3Forms notifications with subject `New AI wins signup`.
- Writes:
  - `intake_form_responses`
  - `tasks`
  - `prospects` and `contacts` for business-like leads
  - `crm_leads`
  - `crm_source_submissions`
  - `crm_stage_history`
  - `crm_touchpoints`

### UsefulOpsAI.com

- Public site form provider: Google Forms.
- Checker: `/Users/aileansolutions/usefulopsai/scripts/check_intake_responses.py`
- OpenClaw cron: `06b1222e-7b4a-4607-9ac7-2cd484bd3e55`
- Writes:
  - `intake_form_responses`
  - `tasks` for new non-baseline responses
  - `crm_leads`
  - `crm_source_submissions`
  - `crm_stage_history`
  - `crm_touchpoints`

## CRM Tables

- `crm_leads`: canonical deduped leads.
- `crm_source_submissions`: source-level audit trail; one row per inbound form/email/form-response record.
- `crm_stage_history`: stage timeline.
- `crm_touchpoints`: inbound/outbound interaction log.
- `crm_opportunities`: opportunity tracking shell for future conversion work.
- `crm_integrity_checks`: durable integrity check results.

## Dedupe Rules

Lead dedupe key priority:

1. Email
2. Website
3. Company name
4. Phone
5. Unknown fallback

This means a person who submits through both sites with the same email should become one `crm_leads` row with multiple `crm_source_submissions`.

## Integrity Check

Run:

```bash
cd /Users/aileansolutions/usefulopsai
scripts/crm_integrity_check.py --backfill
```

The check fails if:

- An `intake_form_responses` row has no CRM source submission.
- A non-baseline intake has no follow-up task.
- CRM leads contain duplicate primary emails.

The check writes a row to `crm_integrity_checks` and prints JSON.

## Current Verification

2026-06-15 CRM v1 hardening pass:

- Backfilled existing intake rows: `3`
- CRM source submissions: `3`
- Deduped CRM leads: `2`
- Missing CRM submissions: `0`
- Missing follow-up tasks: `0`
- Duplicate emails: `0`
- Dashboard rebuilt with CRM metrics.

## Current Limits

This is a local CRM layer, not an external CRM SaaS. It still depends on:

- Web3Forms notification email delivery for AIPromotionGuy.com.
- Google Forms API polling for UsefulOpsAI.com.
- Local SQLite and local automation health.

Future hardening should add direct webhook ingestion, scheduled CRM integrity alerts, and a richer review dashboard before meaningful paid traffic.
