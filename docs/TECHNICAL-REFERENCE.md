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
- Stripe sync script: `/Users/aileansolutions/usefulopsai/scripts/stripe_sync.py`.
- 2026-05-30 sync result: read-only sync completed with 3 payment links, 1 checkout session, 0 subscriptions, 0 paid revenue rows, and 0 active MRR. Sync history is stored in SQLite table `stripe_sync_runs`; paid checkout sessions are inserted into `revenue` by external session id.

## Private Dashboard

- Builder script: `/Users/aileansolutions/usefulopsai/scripts/build_dashboard.py`.
- Private export paths:
  - HTML: `/Users/aileansolutions/usefulopsai/local/exports/usefulops-dashboard.html`
  - JSON: `/Users/aileansolutions/usefulopsai/local/exports/usefulops-dashboard.json`
- Snapshot table: `dashboard_snapshots`.
- 2026-05-30 latest verified snapshot: `dash-20260530T221644Z-e6912040`; gross revenue `$0`, active MRR `$0`, open tasks `0`.
- The dashboard is a private local file, not a public site or customer portal. Do not publish it because it can include private operating data.

## Outreach Prep

- Compliance checklist: `/Users/aileansolutions/usefulopsai/docs/OUTREACH-COMPLIANCE.md`.
- Prep script: `/Users/aileansolutions/usefulopsai/scripts/prepare_outreach.py`.
- 2026-05-30 result: seeded five named public-prospect records with public URLs, operating hypotheses, offer fit, and next actions. They are research-ready only; no emails were sent and no contacts were created.
- Prospect records use `status='qualified_research_ready'` and still require final public contact-page verification, suppression checks, and draft quality review before any outreach.
- Prospecting pipeline script: `/Users/aileansolutions/usefulopsai/scripts/prospecting_pipeline.py`.
- 2026-05-30 prospecting-ready result: pipeline seeded 12 named public prospects, created 12 public-source contact records, checked suppressions, and created 12 unsent `outreach_actions` draft rows. No emails were sent and no Gmail drafts were created.
- Suppression CLI examples:

```bash
scripts/prospecting_pipeline.py check-suppression --email info@example.com
scripts/prospecting_pipeline.py suppress --email info@example.com --reason "Unsubscribed or do-not-contact request"
```

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
- Stripe sync runs
- Dashboard snapshots
- Tasks
- Real-world action log
- Checkpointed operator runs and checkpoints

The database is for internal operating control only. It is not a CRM product, customer portal, or public service.

## Checkpointed Daily Operator Loop

- Helper script: `/Users/aileansolutions/usefulopsai/scripts/operator_loop.py`.
- Durable tables: `operator_runs` and `operator_checkpoints`.
- Purpose: make the daily UsefulOps operator loop restartable and locally orchestrated so temporary Codex/OpenClaw detached-run failures do not own or derail the work.
- Primary run command:

```bash
cd /Users/aileansolutions/usefulopsai
scripts/operator_loop.py run --trigger cron-0915 --objective "Move one high-priority UsefulOps startup item forward." --push
```

- Manual dry-run verification command:

```bash
scripts/operator_loop.py run --trigger manual-dry-run --objective "Verify local orchestrator path without publishing." --dry-run
```

- Lower-level checkpoint commands still exist for inspection and recovery:

```bash
scripts/operator_loop.py start --trigger manual --objective "Move one high-priority UsefulOps startup item forward."
scripts/operator_loop.py checkpoint --run-id <run_id> --step <step> --summary "<what changed>" --next-action "<next step>"
scripts/operator_loop.py complete --run-id <run_id> --summary "<result>" --next-action "<next step>"
scripts/operator_loop.py fail --run-id <run_id> --error "<error>" --next-action "<recovery step>"
```

- Stale protection: `start` marks any `running` operator run older than 30 minutes as `interrupted`, writes a recovery checkpoint, and starts a fresh run linked through `previous_run_id`.
- Local orchestration: `run` owns start/checkpoint/handler/verification/complete-or-fail. The first deterministic handler replaces the placeholder homepage, runs `npm run build`, updates task state/action log, and commits/pushes only when `--push` is supplied.
- 2026-05-30 handler expansion: `run` now has deterministic local handlers for dashboard build, Stripe sync, outreach compliance, and prospect prep. These call `scripts/build_dashboard.py`, `scripts/stripe_sync.py`, and `scripts/prepare_outreach.py` rather than asking a detached Codex turn to perform multi-step work.
- Bounded Codex use: `run_codex_substep` invokes `codex exec` as a subprocess with a fixed timeout and scoped prompt. It is for planning or narrow future substeps only; detached OpenClaw cron turns should not perform edits or multi-step reasoning themselves.
- Retry guard: OpenClaw cron job `ed7eb2ee-d5a2-40e0-b2e4-7ba807ba94ed` (`UsefulOps daily operator retry guard`) runs daily at `09:45 America/Los_Angeles`. It first calls `scripts/operator_loop.py retry-status`; it only runs `scripts/operator_loop.py run --trigger cron-0945-retry ... --push` if the 09:15 run failed, was interrupted, or never recorded a completed daily run. Normal no-retry days use `delivery.mode=none` to avoid chat noise.
- Smoke tests completed 2026-05-30: `start`, `checkpoint`, and `complete` wrote durable state to `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`; `scripts/operator_loop.py run --dry-run` selected the website handler, ran `npm run build`, marked the earlier failed manual run interrupted, and completed without publishing.
