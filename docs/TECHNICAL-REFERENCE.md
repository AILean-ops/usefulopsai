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
- Calendar booking link added 2026-06-05: Rowan/UsefulOps Appointment Schedule URL is `https://calendar.app.google/j1pPihP5wcXVhhAo8`. Verified with `curl -I -L`: the short link redirects to Google Calendar Appointment Schedule and returns HTTP 200. Website phone-intake CTAs now use this direct booking link.

## Intake Form Internal Follow-Up Loop

- Script: `/Users/aileansolutions/usefulopsai/scripts/check_intake_responses.py`.
- Durable table: `intake_form_responses` in `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`; every recorded submission also writes an `action_log` row.
- Internal handling policy: the script records full response details locally and creates a high-priority `tasks` row for each new submission. Normal form submissions do not post Discord alerts. Email and phone remain in the local response record unless Rowan/Brian explicitly choose to surface them later.
- Existing Brian test response was marked as baseline on 2026-06-05 so future alerts only fire for new submissions.
- OpenClaw cron job `06b1222e-7b4a-4607-9ac7-2cd484bd3e55` (`UsefulOps intake form internal follow-up loop`) polls every 10 minutes in an isolated session with `delivery.mode=none`. New submissions are handled internally through SQLite/action-log/task state, not Discord lead alerts. Failure alerts still go to `#announcements` (`1511152439859085463`) with a 1-hour cooldown. Manual forced run on 2026-06-05 completed with `lastRunStatus=ok`.

## CRM v1

- CRM v1 source of truth: `/Users/aileansolutions/usefulopsai/local/data/usefulopsai.sqlite3`.
- CRM v1 documentation: `/Users/aileansolutions/usefulopsai/docs/CRM-V1.md`.
- Schema tables added 2026-06-15: `crm_leads`, `crm_source_submissions`, `crm_stage_history`, `crm_touchpoints`, `crm_opportunities`, and `crm_integrity_checks`.
- Shared helper: `/Users/aileansolutions/usefulopsai/scripts/usefulops_common.py` function `upsert_crm_lead(...)`.
- Integrity checker: `/Users/aileansolutions/usefulopsai/scripts/crm_integrity_check.py`; run with `--backfill` to create CRM rows for existing `intake_form_responses`.
- AIPromotionGuy.com Web3Forms watcher `/Users/aileansolutions/.openclaw/workspace/scripts/watch_aipromotion_web3forms.py` now writes both legacy intake/task/prospect/contact rows and CRM rows.
- UsefulOpsAI.com Google Form checker `/Users/aileansolutions/usefulopsai/scripts/check_intake_responses.py` now writes both legacy intake/task rows and CRM rows.
- Verification on 2026-06-15: `scripts/crm_integrity_check.py --backfill` returned `ok=true` with 3 source submissions, 2 deduped CRM leads, 0 missing CRM submissions, 0 missing follow-up tasks, and 0 duplicate emails. `scripts/build_dashboard.py` rebuilt the private dashboard with CRM metrics.

## Realtime Phone Webhook

- Worker source: `/Users/aileansolutions/usefulopsai/workers/realtime-webhook/`.
- Worker name: `usefulops-realtime-webhook`.
- UsefulOps test inbound phone number: `760-334-8960`.
- Webhook path: `/openai/realtime/webhook`.
- Health path: `/health`.
- Public Worker URL: `https://usefulops-realtime-webhook.brian-bricker.workers.dev`.
- Full OpenAI webhook URL: `https://usefulops-realtime-webhook.brian-bricker.workers.dev/openai/realtime/webhook`.
- Default mode as of 2026-06-05: reject-only. It verifies OpenAI webhook signatures, handles `realtime.call.incoming`, and rejects the incoming call through `POST /v1/realtime/calls/{call_id}/reject` with SIP status `486` by default.
- Test answer mode as of 2026-06-05: source code supports `CALL_HANDLING_MODE=accept-test`, but `wrangler.toml` keeps `CALL_HANDLING_MODE="reject-only"` by default. In `accept-test`, the Worker accepts only callers in comma-separated `ALLOWED_TEST_CALLERS`, configures a short Rowan Vale internal-test prompt with `gpt-realtime-2`, starts the first greeting through the Realtime WebSocket, and hangs up at `TEST_HARD_CUTOFF_SECONDS`. Without an allowlisted caller, it still rejects.
- The Worker does not attach tools, transfer calls, contact third parties, spend money, change production systems, or perform production customer answering. Brian must explicitly approve the exact runtime configuration before answer-test or any future production answering behavior is enabled.
- Required deploy secrets: `OPENAI_WEBHOOK_SECRET` from the UsefulOps AI OpenAI project webhook settings and a UsefulOps AI project-scoped `OPENAI_API_KEY`.
- Local ignored secret placeholder: `/Users/aileansolutions/usefulopsai/local/secrets/realtime-webhook.env` with mode `600`.
- Local test command: `cd /Users/aileansolutions/usefulopsai/workers/realtime-webhook && npm test`.
- 2026-06-05 verification: local signature verification test passed, `npx wrangler deploy --dry-run` passed, Worker deployed to Cloudflare with version ID `e7446a53-653b-4674-b8ca-97580c9450e8`, and `GET /health` returned HTTP 200 with `mode: reject-only`.
- 2026-06-05 secret/install verification: Brian saved the UsefulOps AI OpenAI webhook secret and project API key in `/Users/aileansolutions/usefulopsai/local/secrets/realtime-webhook.env`; Sauron uploaded them to Cloudflare Worker secrets `OPENAI_WEBHOOK_SECRET` and `OPENAI_API_KEY` without printing values. `npx wrangler secret list` shows both secret names. Unsigned webhook POST returns HTTP 400 `invalid_signature`; a locally signed non-call webhook returns HTTP 200 `{"ok":true,"ignored":true}`.
- 2026-06-05 live SIP test: after Brian saved Twilio SIP routing, Sauron ran `npx wrangler tail usefulops-realtime-webhook --format json`; Brian placed one test call; OpenAI sent `realtime.call.incoming` event `evt_6a227f42ad9081909132e60156793999` with call id `rtc_u0_DnJZq3HwghqGmgTNwVMlf`; Worker rejected the call with SIP status `486`; OpenAI reject endpoint returned HTTP `200`. This proves Twilio number -> Twilio SIP -> OpenAI SIP -> Cloudflare webhook -> OpenAI reject-call plumbing works end to end without answering.
- 2026-06-05 answer-test result: Brian approved `CALL_HANDLING_MODE=accept-test` for caller `+17075696515` with model `gpt-realtime-2`, target `480` seconds, hard cutoff `600` seconds. Calls from `+17075696515` to `760-334-8960` reached the Worker, OpenAI accept returned HTTP `200`, and Brian confirmed he was able to have a conversation with Rowan. During the test, Cloudflare cancelled the long `waitUntil` monitor after about 30 seconds, so the Worker-only design is adequate for a gated answering smoke test but not production-length monitoring or hard hangup enforcement. Production call control needs a Durable Object/control process or another long-lived control path.
- 2026-06-05 post-test safety reset: after the successful Rowan conversation, `wrangler.toml` was switched back to `CALL_HANDLING_MODE="reject-only"`, deployed as Worker version `6f94dc63-4e37-4a6f-996f-f6c9440b37d4`, and `/health` returned `mode: reject-only`.
- 2026-06-05 follow-up test result: Brian asked to reopen the same allowlisted test and keep it open until he says to stop. `CALL_HANDLING_MODE="accept-test"` was deployed for caller `+17075696515` only, as Worker version `5729fb04-dc00-4735-bc1c-25f9b7eb632d`. Brian reported the call died at 3:15 with Rowan stopping mid-sentence. Official OpenAI docs say Realtime sessions can last up to 60 minutes and show SIP call accept handing off to a separate long-lived WebSocket task, so the failure is treated as a control-channel architecture issue, not an OpenAI session maximum. After Brian asked to stop the test, `CALL_HANDLING_MODE="reject-only"` was deployed as Worker version `435afd92-4dde-485c-858c-4241a0afceed` and `/health` returned `mode: reject-only`.
- 2026-06-05 15-minute control design: normal Worker `waitUntil()` is not sufficient because Cloudflare cancels it about 30 seconds after the webhook response. The prepared local Worker code now requires a Cloudflare Queue binding before it will accept `accept-test` calls. Proposed queue: `usefulops-realtime-call-control`; producer/consumer binding `CALL_CONTROL_QUEUE`; consumer settings `max_batch_size=1`, `max_batch_timeout=1`, `max_retries=0`. Flow: webhook verifies OpenAI signature and caller allowlist, queues `{call_id, caller_phone, hard_cutoff_seconds}` with a 1-second delay, accepts the OpenAI SIP call, and a queue consumer owns the Realtime WebSocket for up to Cloudflare's documented 15-minute queue-consumer wall-time limit. Do not create the queue, add bindings, or deploy this answering architecture until Brian approves the exact activation.
- 2026-06-05 subscriber-call guardrail locked by Brian: once Rowan has paying monthly subscribers, a true long-lived call controller is mandatory before offering or relying on subscriber voice access. Do not route paid subscriber calls through the 15-minute Queue-consumer intake controller. Paid/subscriber calls may exceed 15 minutes and must use a separate long-lived controller capable of reliable 30-60 minute OpenAI Realtime WebSocket control, budget enforcement, notes/summaries, and clean hangup behavior. This is a paid-access reliability boundary, not an optimization.
- 2026-06-05 Rowan Realtime voice and intake prompt decision: official OpenAI docs were checked live and list current Realtime voices `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, `verse`, `marin`, and `cedar`, with `marin` and `cedar` recommended for best quality. Rowan's selected primary voice is `cedar`; fallback is `marin` if Cedar feels too formal after live listening. Voice must be set before first audio is emitted. Intake prompt posture: Rowan introduces UsefulOps AI, states the call is a focused 15-minute workflow-intake call because another call is scheduled afterward, explains the purpose is to understand the pain-point process rather than fix it live, asks only discovery questions about workflow/handoffs/systems/impact, gives a calm friendly time check around 10 minutes, gently steers toward wrap-up around 12 minutes, then closes with a summary and expectation of a written follow-up plan. Any mention of deeper workflow/process improvement help or monthly support should be soft and informational, not pushy.
- 2026-06-05 12-15 minute Queue test result: Brian approved exact Queue activation and called `760-334-8960` from allowlisted `+17075696515`. Queue `usefulops-realtime-call-control` was created with binding `CALL_CONTROL_QUEUE`, consumer settings `max_batch_size=1`, `max_batch_timeout=1`, `max_retries=0`, voice `cedar`, target `720` seconds, and hard cutoff `900` seconds. `accept-test` was deployed as Worker version `e28f02f8-0d72-46a6-9b57-a543ee103988`; `/health` returned `mode: accept-test`; OpenAI accepted call id `rtc_u2_DneVIyLR1kghdgOtGHBEr` with HTTP `200`. The Queue consumer held the Realtime control WebSocket for about `805` seconds, roughly `13:25`, and logged normal `response.done` events throughout, proving the Queue controller gets past the earlier 3:15 failure. After the test, Sauron stopped the local Wrangler tail, switched `wrangler.toml` back to `CALL_HANDLING_MODE="reject-only"`, reran `npm test`, deployed reject-only as Worker version `05a3d2d0-baca-4a0a-86ad-36e4031955d2`, and verified `/health` returned `mode: reject-only`.
- 2026-06-05 Brian assessment after 13-minute Queue test: Cedar was not always easy to understand, so the next test should use `marin`. Prompt timing behavior was poor because the model started saying time was almost up about 4 minutes into the call, repeated urgency with increasing pace, glitched around 8 minutes with 5-10 seconds of silence, and repeated the same wrap-up phrase several times near the end without cleanly closing. Local next-test change: set `REALTIME_VOICE="marin"`, remove self-estimated 10/12-minute reminders from the base prompt, tell Rowan not to estimate elapsed time, and move the time-check and wrap-up prompts into Queue-controller timers. Local tests pass. Live Worker remains reject-only until Brian approves another deploy/test.
- 2026-06-05 cost datapoint: Brian reported OpenAI charged about `$0.90` for the roughly 13-minute Cedar Queue test. Treat this as an observed single-call datapoint for rough intake-call estimating, not a stable price guarantee.
- 2026-06-05 second 12-15 minute Queue test result: Brian approved one more Brian-only test using `marin` and controller-timed 10/12 minute prompts. `accept-test` was deployed as Worker version `868c93c3-5d52-4f39-bef1-41946ccfa13e`; OpenAI accepted call id `rtc_u7_DnexEytEcItrQtD9XVPzx` with HTTP `200`; Queue logs showed normal `response.done` events until about `900` seconds. Brian reported the phone call lasted `15:30`. Cloudflare marked the Queue invocation `exceededCpu` at the hard cutoff, so the test proved the call can reach the full 15-minute window but exposed a cleanup/hangup issue at hard cutoff. After the test, Sauron switched back to `CALL_HANDLING_MODE="reject-only"`, reran `npm test`, deployed reject-only as Worker version `03591d16-a88a-4906-8636-6cd27bf39207`, verified `/health` returned `mode: reject-only`, and stopped the Wrangler tail.
- 2026-06-06 refinement after Brian's second-test assessment: Brian preferred OpenAI voice `onyx`, but official OpenAI docs checked on 2026-06-06 list `onyx` for TTS and not for Realtime/SIP. After comparing `marin` and `cedar`, Brian chose `cedar` as the Realtime phone default because quality matters and Cedar was better overall. Brian also reported longer post-user delays, 10/12-minute reminders interrupting him mid-sentence, and awkward end-call behavior where Rowan said it had enough for a plan but stayed silent and did not hang up. Local code now queues timed reminder/wrap instructions and flushes them only after Realtime turn-boundary events instead of forcing immediate `response.create`; final wrap-up wording now says the caller can expect a follow-up email later today, thanks them, says bye, and a controller-side hangup grace period ends the call. Local test suite passes. Live Worker remains reject-only until Brian approves another deploy/test.
- 2026-06-06 Rowan intake-question refinement: Brian preferred the first test's higher density of targeted questions because clarifying questions make customers feel heard and produce better follow-up plans. Local prompt now biases Rowan toward targeted clarifying questions over early summarizing and includes an adaptive intake map: monthly volume/frequency, request/order/job sources, owners for each step, current tools, where information gets lost, prioritization, employee instructions/details, post-completion steps, invoice timing, payment collection, estimate follow-up, review requests, maintenance reminders, budget tolerance, staff tech comfort, success definition, and most painful current problem. This is a question map, not a rigid script.
- Operating policy added 2026-06-05: initial phone intakes should be capped at 12-15 minutes. Longer calls are for paying monthly clients or separately approved deeper consults. UsefulOps AI does not offer video calls.
- 2026-06-08 Brian reminder: UsefulOps is actively working toward a telephone interface where Rowan can run intakes and consulting calls for clients. The public website already offers the Workflow Intake form and the 15-minute phone-intake booking link. If UsefulOps books any clients, paid users, meaningful intake calls, or client/revenue conversions, Brian wants to know ASAP.

## Booking / Client ASAP Alerts

- Script: `/Users/aileansolutions/usefulopsai/scripts/check_booking_client_alerts.py`.
- Local state: `/Users/aileansolutions/usefulopsai/local/state/booking_client_alert_state.json`.
- Signals checked: UsefulOps intake form responses, Rowan/UsefulOps Google Calendar events over the next 60 days, Stripe revenue sync, local `clients`, and local `revenue` rows.
- First run on 2026-06-08 saw only the existing Brian test intake (`Testing This Form Inc.`), 0 relevant calendar booking events, 0 clients, and 0 revenue rows; that baseline is now marked seen.
- OpenClaw cron job `26702ac4-ec84-4ad8-8ae1-4bcf1520d0e0` (`UsefulOps booking/client ASAP alert watcher`) runs every 10 minutes with `delivery.mode=none`; it posts to UsefulOps `#announcements` only when the script returns new alerts, and failure alerts also go to `#announcements`.
- Durable task: `task-20260608-client-booking-alerts` tracks Brian's instruction to alert him quickly when UsefulOps bookings/client conversions happen.

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
- Dashboard LaunchAgent source: `/Users/aileansolutions/usefulopsai/scripts/com.aileansolutions.usefulops-dashboard.plist`.
- Installed Dashboard LaunchAgent: `/Users/aileansolutions/Library/LaunchAgents/com.aileansolutions.usefulops-dashboard.plist`.
- Dashboard logs: `/Users/aileansolutions/usefulopsai/local/logs/dashboard-server.log`; errors: `/Users/aileansolutions/usefulopsai/local/logs/dashboard-server.err`.
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
- 2026-06-03 reliability fix: added and installed `com.aileansolutions.usefulops-dashboard` LaunchAgent with `RunAtLoad` and `KeepAlive` because the dashboard server was down when Brian tried to open it. Verified `/health`, `/api/dashboard`, and `POST /api/refresh` after install.
- 2026-06-05 budget fix: Google Workspace `$8.60/month` row `expense-google-workspace-20260602` is an approved UsefulOps commitment and must count in `Budget used`. `scripts/build_dashboard.py` now upserts this known recurring commitment as `status='approved'` before computing metrics. Rebuilt dashboard snapshot `dash-20260606T032910Z-51aee61b`; exported JSON showed `budget_used_cents=860` and HTML showed `$8.60 / $100.00`.

## Growth Loop

- Operating doc: `/Users/aileansolutions/usefulopsai/docs/GROWTH-LOOP.md`.
- Review script: `/Users/aileansolutions/usefulopsai/scripts/strategy_review.py`.
- Nightly self-improvement script: `/Users/aileansolutions/usefulopsai/scripts/nightly_self_improvement.py`.
- Durable tables: `growth_batches`, `growth_batch_items`, `strategy_reviews`, and `learning_log`.
- Purpose: automatically measure the funnel, diagnose the current bottleneck, record a lesson, and queue the next concrete high-priority task.
- Diagnoses currently encoded: `execution_gap`, `deliverability_gap`, `draft_quality_gap`, `message_or_list_gap`, `offer_gap`, `conversion_gap`, and `scale_winners`.
- 2026-05-30 first review: `strategy-review-20260530T225139Z-de38bfe1` diagnosed an `execution_gap` because UsefulOps had 12 draft outreach rows and 0 sends. It queued task `task-growth-loop-next-action` titled `Execute first controlled outreach batch`. No emails were sent.
- 2026-05-31 nightly self-improvement loop added: the script runs strategy review, reviews operator/system improvement opportunities, creates at most one improvement task, writes `learning_log` and `action_log`, rebuilds the private dashboard, and exits. It never sends outreach, spends money, accesses customer systems, or changes OpenClaw gateway state.
- 2026-06-03 result-quality loop added: `outreach_actions` now stores `result_category`, `result_recorded_at`, `quality_score`, and `quality_notes`. The strategy loop counts `undeliverable` and `delivery_delayed` separately from opt-outs, and the nightly self-improvement loop prioritizes hard-bounce cleanup and human-readability review before scaling outreach.
- OpenClaw cron job `9defe561-8895-485b-944b-5110a9734db5` (`UsefulOps nightly self-improvement loop`) runs daily at `22:30 America/Los_Angeles`. It executes only `scripts/nightly_self_improvement.py` and reports the JSON summary to Discord `#announcements` (`channel:1511152439859085463`) in the UsefulOps AI category.

## Outreach Prep

- Compliance checklist: `/Users/aileansolutions/usefulopsai/docs/OUTREACH-COMPLIANCE.md`.
- Prep script: `/Users/aileansolutions/usefulopsai/scripts/prepare_outreach.py`.
- 2026-05-30 result: seeded five named public-prospect records with public URLs, operating hypotheses, offer fit, and next actions. They are research-ready only; no emails were sent and no contacts were created.
- Prospect records use `status='qualified_research_ready'` and still require final public contact-page verification, suppression checks, and draft quality review before any outreach.
- Prospecting pipeline script: `/Users/aileansolutions/usefulopsai/scripts/prospecting_pipeline.py`.
- 2026-05-30 prospecting-ready result: pipeline seeded 12 named public prospects, created 12 public-source contact records, checked suppressions, and created 12 unsent `outreach_actions` draft rows. No emails were sent and no Gmail drafts were created.
- Send script: `/Users/aileansolutions/usefulopsai/scripts/send_outreach_batch.py`.
- Shared outreach quality/result helpers: `/Users/aileansolutions/usefulopsai/scripts/usefulops_common.py`.
- 2026-05-31 direct-send path decision: for the first controlled outreach batch, direct Gmail send is the default because the UsefulOps authority envelope allows direct prospect contact and the compliance doc allows direct email outreach. Mailbox drafts are not the default fallback; if direct-send preflight fails, record a blocker and send 0.
- 2026-05-31 dry-run verification: `scripts/send_outreach_batch.py --limit 2 --dry-run` succeeded through GOG Gmail dry-run, selected two draft candidates, enforced suppression/opt-out preflight, wrote a dry-run `action_log`, and sent no emails.
- 2026-06-03 delivery/readability correction: the initial 5-send batch produced one hard bounce (`info@sapperhvac.com`) and one temporary delivery delay (`info@phoenixheatingcoolingauthority.com`). The hard bounce is recorded as `result_category='undeliverable'`, `outcome='undeliverable'`, and a suppression row; the delay is recorded as `result_category='delivery_delayed'` only. Pending drafts were rewritten for a less robotic, less jargon-heavy voice and now pass the pre-send quality threshold.
- 2026-06-08 UsefulOps-only separation correction: in UsefulOps channels, generic references to "batch", "outreach", "send", "prospects", or "pipeline" must be interpreted as UsefulOps AI unless Brian explicitly names the market-intelligence business. Same-day bounded send: `scripts/send_outreach_batch.py --limit 7 --dry-run` passed, then `scripts/send_outreach_batch.py --limit 7` sent 7 UsefulOps cold-initial emails from `rowan.vale@usefulopsai.com` with 0 skipped and 0 failed; dashboard snapshot `dash-20260608T163153Z-b21bf347` rebuilt afterward. OpenClaw cron job `996ef030-66d0-4f9d-96a5-1488c2fdb876` (`UsefulOps daily outbound batch rail`) runs daily at `10:05 America/Los_Angeles`; it sends up to 10 compliance-cleared UsefulOps draft outreach rows if available, otherwise runs `scripts/operator_loop.py run --trigger cron-1005-outbound-rail --objective "Prepare the next UsefulOps prospect/draft batch or revised outreach variant for revenue-generating outreach." --push` and reports to UsefulOps `#announcements`.
- 2026-06-10 revenue-bias correction: strategy review now tracks `unresolved_undeliverable` separately from total historical undeliverables. Already-suppressed hard bounces no longer keep the diagnosis stuck at `deliverability_gap`; when sent outreach has no replies and no draft queue, the next action becomes a verified outreach variant batch. Nightly self-improvement now creates `Prepare next UsefulOps verified outreach batch` instead of another cleanup task in that state. Operator loop now refuses to recycle the static seed-list script for verified/revised outreach tasks and records `live_research_required` so the gap is visible.
- 2026-06-10 one-shot revenue trigger: OpenClaw cron job `c59aaece-a3db-4aec-bab0-6279d4a0c90c` (`UsefulOps live-research outreach batch - 2026-06-11`) is scheduled for `2026-06-11 09:05 America/Los_Angeles`. It runs an isolated agent turn to check Rowan Gmail, live-research 5-8 owner-led service-business prospects, create verified drafts, dry-run `scripts/send_outreach_batch.py --limit 8`, send if inside the UsefulOps authority envelope, update SQLite/action logs, and report to UsefulOps `#announcements`.
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
