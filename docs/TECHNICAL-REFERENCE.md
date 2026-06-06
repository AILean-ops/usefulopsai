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
- 2026-06-05 site positioning update: homepage copy now presents Rowan Vale as the public AI operator, explains the consulting process from intake through workflow monitoring for non-technical small business owners, embeds the UsefulOps AI Workflow Intake Google Form, and states the initial phone-intake posture of 12-15 minutes with no video calls.
- UsefulOps AI Workflow Intake Google Form: form id `1MWRj6Otr5THMgmvKccfTsN16HzhQIWqI-ggAoN15bw4`; public response URL `https://docs.google.com/forms/d/e/1FAIpQLSf4I2PCTYqdUgcJhTSK48hG6-RaubbbyEBdTBOzrvg9Vt-Zmw/viewform`; edit URL `https://docs.google.com/forms/d/1MWRj6Otr5THMgmvKccfTsN16HzhQIWqI-ggAoN15bw4/edit`. Created under `rowan.vale@usefulopsai.com` via `gog forms` with 12 qualification questions. It asks for name, email, phone, business name, website/social page, business type, team size, pain point, workflow needing help, tools used, urgency, and what would make the fix worthwhile. Google Drive permission is `anyoneWithLink` reader; public response URL verified HTTP 200 without login on 2026-06-05.
- Calendar booking link status 2026-06-05: not yet configured in repo/site. Replace the temporary mailto intake-call CTA with Rowan's Google Calendar Appointment Schedule booking URL once Brian creates or provides it.

## Intake Form Internal Follow-Up Loop

- Script: `/Users/aileansolutions/usefulopsai/scripts/check_intake_responses.py`.
- Durable table: `intake_form_responses` in `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`; every recorded submission also writes an `action_log` row.
- Internal handling policy: the script records full response details locally and creates a high-priority `tasks` row for each new submission. Normal form submissions do not post Discord alerts. Email and phone remain in the local response record unless Rowan/Brian explicitly choose to surface them later.
- Existing Brian test response was marked as baseline on 2026-06-05 so future alerts only fire for new submissions.
- OpenClaw cron job `06b1222e-7b4a-4607-9ac7-2cd484bd3e55` (`UsefulOps intake form internal follow-up loop`) polls every 10 minutes in an isolated session with `delivery.mode=none`. New submissions are handled internally through SQLite/action-log/task state, not Discord lead alerts. Failure alerts still go to `#announcements` (`1511152439859085463`) with a 1-hour cooldown. Manual forced run on 2026-06-05 completed with `lastRunStatus=ok`.

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
- Localhost-only server: `/Users/aileansolutions/usefulopsai/scripts/dashboard_server.py`.
- Start command: `cd /Users/aileansolutions/usefulopsai && ./start_dashboard.sh`.
- Local browser URL: `http://localhost:8766`.
- Server bind address: `127.0.0.1`; this is intentionally loopback-only and is not public.
- Local API:
  - `GET /health`
  - `GET /api/dashboard`
  - `POST /api/refresh`
- Private export paths:
  - HTML: `/Users/aileansolutions/usefulopsai/local/exports/usefulops-dashboard.html`
  - JSON: `/Users/aileansolutions/usefulopsai/local/exports/usefulops-dashboard.json`
- Snapshot table: `dashboard_snapshots`.
- 2026-05-30 latest verified snapshot: `dash-20260530T221644Z-e6912040`; gross revenue `$0`, active MRR `$0`, open tasks `0`.
- The dashboard is a private local file, not a public site or customer portal. Do not publish it because it can include private operating data.
- 2026-05-30 dashboard expansion: dashboard now includes latest strategy review and recent learning-log entries.
- 2026-05-30 local server added: dashboard can now be opened at `http://localhost:8766` with a Refresh button that calls `POST /api/refresh` to rebuild from SQLite.

- 2026-06-05 budget fix: Google Workspace `$8.60/month` row `expense-google-workspace-20260602` is an approved UsefulOps commitment and must count in `Budget used`. `scripts/build_dashboard.py` now upserts this known recurring commitment as `status='approved'` before computing metrics. Rebuilt dashboard snapshot `dash-20260606T032910Z-51aee61b`; exported JSON showed `budget_used_cents=860` and HTML showed `$8.60 / $100.00`.

## Growth Loop

- Operating doc: `/Users/aileansolutions/usefulopsai/docs/GROWTH-LOOP.md`.
- Review script: `/Users/aileansolutions/usefulopsai/scripts/strategy_review.py`.
- Nightly self-improvement script: `/Users/aileansolutions/usefulopsai/scripts/nightly_self_improvement.py`.
- Durable tables: `growth_batches`, `growth_batch_items`, `strategy_reviews`, and `learning_log`.
- Purpose: automatically measure the funnel, diagnose the current bottleneck, record a lesson, and queue the next concrete high-priority task.
- Diagnoses currently encoded: `execution_gap`, `message_or_list_gap`, `offer_gap`, `conversion_gap`, and `scale_winners`.
- 2026-05-30 first review: `strategy-review-20260530T225139Z-de38bfe1` diagnosed an `execution_gap` because UsefulOps had 12 draft outreach rows and 0 sends. It queued task `task-growth-loop-next-action` titled `Execute first controlled outreach batch`. No emails were sent.
- 2026-05-31 nightly self-improvement loop added: the script runs strategy review, reviews operator/system improvement opportunities, creates at most one improvement task, writes `learning_log` and `action_log`, rebuilds the private dashboard, and exits. It never sends outreach, spends money, accesses customer systems, or changes OpenClaw gateway state.
- OpenClaw cron job `9defe561-8895-485b-944b-5110a9734db5` (`UsefulOps nightly self-improvement loop`) runs daily at `22:30 America/Los_Angeles`. It executes only `scripts/nightly_self_improvement.py` and reports the JSON summary to Discord `#announcements` (`channel:1511152439859085463`) in the UsefulOps AI category.

## Outreach Prep

- Compliance checklist: `/Users/aileansolutions/usefulopsai/docs/OUTREACH-COMPLIANCE.md`.
- Prep script: `/Users/aileansolutions/usefulopsai/scripts/prepare_outreach.py`.
- 2026-05-30 result: seeded five named public-prospect records with public URLs, operating hypotheses, offer fit, and next actions. They are research-ready only; no emails were sent and no contacts were created.
- Prospect records use `status='qualified_research_ready'` and still require final public contact-page verification, suppression checks, and draft quality review before any outreach.
- Prospecting pipeline script: `/Users/aileansolutions/usefulopsai/scripts/prospecting_pipeline.py`.
- 2026-05-30 prospecting-ready result: pipeline seeded 12 named public prospects, created 12 public-source contact records, checked suppressions, and created 12 unsent `outreach_actions` draft rows. No emails were sent and no Gmail drafts were created.
- Send script: `/Users/aileansolutions/usefulopsai/scripts/send_outreach_batch.py`.
- 2026-05-31 direct-send path decision: for the first controlled outreach batch, direct Gmail send is the default because the UsefulOps authority envelope allows direct prospect contact and the compliance doc allows direct email outreach. Mailbox drafts are not the default fallback; if direct-send preflight fails, record a blocker and send 0.
- 2026-05-31 dry-run verification: `scripts/send_outreach_batch.py --limit 2 --dry-run` succeeded through GOG Gmail dry-run, selected two draft candidates, enforced suppression/opt-out preflight, wrote a dry-run `action_log`, and sent no emails.
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

## Reply Handling

- Reply-handling policy: `/Users/aileansolutions/usefulopsai/docs/REPLY-HANDLING.md`.
- Default sales mode is email-first, not email-only.
- If a qualified prospect asks for a phone call or online meeting, Rowan should treat that as buying intent, qualify the workflow, offer async outline when sufficient, and schedule/escalate a short 15-minute discovery call only when a real attendance path exists.
- Current live-human dependency: Brian is the likely human for live UsefulOps calls until another attendance path exists. Do not book him casually. Before asking Brian to attend, prepare a prospect call packet with company summary, qualification rationale, thread summary, pain hypothesis, agenda, questions, likely objections, no-promise boundaries, recommended next step, follow-up draft, and payment/scope path.
- Meeting outcomes should update `outreach_actions.response_at`, `outreach_actions.outcome`, and tasks/action logs as appropriate.

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
- 2026-05-30 strategy handler: `run` can call `scripts/strategy_review.py` for explicit strategy/growth-loop tasks. Strategy review is internal only; it does not send outreach.
- Bounded Codex use: `run_codex_substep` invokes `codex --ask-for-approval never exec ...` as a subprocess with a fixed timeout and scoped prompt. `--ask-for-approval` must be passed before the `exec` subcommand for the current Codex CLI. This fallback is for planning only; deterministic handlers should own recurring UsefulOps work.
- 2026-06-02 autonomy hardening: `run` now has deterministic routing for `Reduce latest UsefulOps execution blocker` and `Execute first controlled outreach batch`. The blocker handler validates the Codex approval-policy syntax and records recovery. The controlled outreach handler runs `scripts/send_outreach_batch.py --limit 5`, which sends only inside the approved UsefulOps authority envelope and its suppression/opt-out checks.
- Retry guard: OpenClaw cron job `ed7eb2ee-d5a2-40e0-b2e4-7ba807ba94ed` (`UsefulOps daily operator retry guard`) runs daily at `09:45 America/Los_Angeles`. It first calls `scripts/operator_loop.py retry-status`; it only runs `scripts/operator_loop.py run --trigger cron-0945-retry ... --push` if the 09:15 run failed, was interrupted, or never recorded a completed daily run. Normal no-retry days use `delivery.mode=none` to avoid chat noise.
- Discord routing: as of 2026-06-01, UsefulOps AI discussion with Brian belongs in Deckard Ops `#ops-chat` (`channel:1511152390592659466`), and automated scheduled report-outs/failure alerts belong in `#announcements` (`channel:1511152439859085463`). Active UsefulOps cron deliveries and failure alerts were rerouted from Brian's DM to `#announcements`; the 09:45 retry guard still keeps normal no-retry days silent.
- Smoke tests completed 2026-05-30: `start`, `checkpoint`, and `complete` wrote durable state to `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`; `scripts/operator_loop.py run --dry-run` selected the website handler, ran `npm run build`, marked the earlier failed manual run interrupted, and completed without publishing.
