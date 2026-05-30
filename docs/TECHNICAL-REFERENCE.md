# UsefulOps AI Technical Reference

**Created:** 2026-05-29

## Repository

- GitHub repo: `AILean-ops/usefulopsai`
- SSH remote: `git@github-workspace:AILean-ops/usefulopsai.git`
- Local repo: `/Users/aileansolutions/usefulopsai`
- Current status at creation: repo existed on GitHub and cloned successfully as an empty repository.
- Initial push: commit `aefec0b` (`Initialize UsefulOps AI workspace`) pushed to `main` on 2026-05-29.
- Repo-local Git identity for future commits: `Rowan Vale <rowan.vale@usefulopsai.com>`.
- Planned GOG account: `rowan.vale@usefulopsai.com`.
- GOG account: `rowan.vale@usefulopsai.com`.
- GOG client label: `usefulops`.
- GOG configured successfully on 2026-05-29 with services `calendar,contacts,docs,drive,forms,gmail,sheets`.
- Gmail smoke test returned the Google Workspace welcome email.
- Drive smoke test completed successfully and returned no files.
- Setup guide: `/Users/aileansolutions/usefulopsai/docs/GOG-SETUP.md`.
- Current authority envelope: `/Users/aileansolutions/usefulopsai/docs/AUTHORITY-ENVELOPE.md`.

The plain `git@github.com:AILean-ops/usefulopsai.git` form failed on this machine because GitHub SSH access is configured through the `github-workspace` host alias.

## Website / Cloudflare Pages

- Domain: `UsefulOpsAI.com`.
- Static site source: `/Users/aileansolutions/usefulopsai/website/`.
- Build command: `npm run build`.
- Deploy command, if Cloudflare asks for one: `npm run deploy`.
- Current build output directory: `dist`.
- Wrangler config: `/Users/aileansolutions/usefulopsai/wrangler.toml`.
- Pages project name: `usefulopsai-com`.
- 2026-05-29 GitHub path test: static placeholder site added and pushed to `main`.
- 2026-05-29 Cloudflare CLI status: `npx wrangler whoami` reports not authenticated; `npx wrangler pages project list` fails without `CLOUDFLARE_API_TOKEN`. Brian must connect Cloudflare Pages to the GitHub repo or provide a Cloudflare API token/login before Sauron can publish/verify deployment from the Mac mini.
- 2026-05-29 live status: `https://usefulopsai.com/`, `https://www.usefulopsai.com/`, and `https://usefulopsai-com.pages.dev/` return the expected UsefulOps AI placeholder HTML.
- 2026-05-29 Stripe success path: `/thank-you/` page added because Stripe payment links point to `https://usefulopsai.com/thank-you`.

## Local Private State

Private operating state lives under:

- `/Users/aileansolutions/usefulopsai/local/`

This directory is intentionally ignored by Git.

Key local paths:

- Database: `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`
- Logs: `/Users/aileansolutions/usefulopsai/local/logs/`
- Client folders: `/Users/aileansolutions/usefulopsai/local/clients/`
- Prospect working files: `/Users/aileansolutions/usefulopsai/local/prospects/`
- Deliverables: `/Users/aileansolutions/usefulopsai/local/deliverables/`
- Secrets placeholder: `/Users/aileansolutions/usefulopsai/local/secrets/`
- Exports: `/Users/aileansolutions/usefulopsai/local/exports/`

Do not place card numbers, API keys, OAuth secrets, customer credentials, or sensitive client data in Git-tracked files.

## Stripe

- Stripe account is tied to AI Lean Solutions LLC; UsefulOps AI is an affiliate.
- Local Stripe secret storage: `/Users/aileansolutions/usefulopsai/local/secrets/stripe.env`, ignored by Git.
- Smoke-test script: `/Users/aileansolutions/usefulopsai/scripts/stripe_smoke_test.py`.
- 2026-05-29 restricted-key verification: `payment_links`, `checkout_sessions`, `customers`, and `subscriptions` are readable. This is enough for the first dashboard revenue/MRR sync.

## Database Purpose

The initial SQLite database tracks:

- Experiments
- Prospects
- Contacts
- Outreach actions
- Suppression entries
- Approvals
- Clients
- Deliverables
- Revenue
- Payment links
- Expenses
- Tasks
- Real-world action log
- Checkpointed operator runs and checkpoints

The database is for internal operating control only. It is not a CRM product, customer portal, or public service.

## Checkpointed Daily Operator Loop

- Helper script: `/Users/aileansolutions/usefulopsai/scripts/operator_loop.py`.
- Durable tables: `operator_runs` and `operator_checkpoints`.
- Purpose: make the daily UsefulOps operator loop restartable so a temporary Codex/OpenClaw detached-run failure does not erase the selected task, current step, or next action.
- Start command:

```bash
cd /Users/aileansolutions/usefulopsai
scripts/operator_loop.py start --trigger cron-0915 --objective "Move one high-priority UsefulOps startup item forward."
```

- During work, record progress:

```bash
scripts/operator_loop.py checkpoint --run-id <run_id> --step <step> --summary "<what changed>" --next-action "<next step>"
```

- On success:

```bash
scripts/operator_loop.py complete --run-id <run_id> --summary "<result>" --next-action "<next step>"
```

- On failure:

```bash
scripts/operator_loop.py fail --run-id <run_id> --error "<error>" --next-action "<recovery step>"
```

- Stale protection: `start` marks any `running` operator run older than 30 minutes as `interrupted`, writes a recovery checkpoint, and starts a fresh run linked through `previous_run_id`.
- Retry guard: OpenClaw cron job `ed7eb2ee-d5a2-40e0-b2e4-7ba807ba94ed` (`UsefulOps daily operator retry guard`) runs daily at `09:45 America/Los_Angeles`. It first calls `scripts/operator_loop.py retry-status`; it only starts real work if the 09:15 run failed, was interrupted, or never recorded a completed daily run. Normal no-retry days use `delivery.mode=none` to avoid chat noise.
- Smoke test completed 2026-05-30: `start`, `checkpoint`, and `complete` all wrote durable state to `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`.
