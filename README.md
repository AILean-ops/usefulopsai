# UsefulOps AI

UsefulOps AI is the public-facing sandbox business operated by Rowan Vale under Brian Bricker's governance.

## Public Identity

- Brand: UsefulOps AI
- Domain: `UsefulOpsAI.com`
- Public operator persona: Rowan Vale
- Recommended primary mailbox: `rowan.vale@usefulopsai.com`
- Recommended aliases: `hello@usefulopsai.com`, `ops@usefulopsai.com`

Sauron is an internal identity only and must not appear in public-facing UsefulOps AI material.

## Operating Rule

UsefulOps AI may only operate inside the guardrails defined in:

- `/Users/aileansolutions/.openclaw/workspace/SAURON-BUSINESS-SANDBOX.md`

Market-intelligence work remains the priority. UsefulOps AI runs around that day job, not through it.

## Repository Layout

- `docs/` - public/internal operating docs that are safe to commit
- `templates/` - reusable non-client-specific templates
- `scripts/` - automation scripts
- `website/` - future site source
- `local/` - ignored private operating state, databases, logs, clients, exports, and secrets

Do not commit customer data, prospect exports, secrets, payment details, inbox data, or SQLite databases.

## Daily Operator Loop

The daily UsefulOps cron job uses `scripts/operator_loop.py` to create durable
`operator_runs` and `operator_checkpoints` records in the local SQLite database.
This keeps the work restartable if a detached Codex/OpenClaw run dies before it
can deliver a final report.

## Private Local Dashboard

Brian can view the UsefulOps operating dashboard locally at:

`http://localhost:8766`

Start it from the repo with:

```bash
./start_dashboard.sh
```

The server binds to `127.0.0.1` only. It is for private local monitoring, not a
public website.
