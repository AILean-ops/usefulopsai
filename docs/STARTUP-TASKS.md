# UsefulOps AI Startup Tasks

These are the operating tasks that should remain visible at startup until they are complete.

## High Priority

- **Replace UsefulOps AI placeholder website with launch site**
  - Status: completed 2026-05-30
  - Database task: `task-20260529-website-launch-build`
  - Goal: turn the live placeholder at `https://usefulopsai.com/` into a credible launch site for UsefulOps AI.
  - Initial scope: practical small-business AI workflow positioning, audit/sprint/support offers, clear boundaries, payment-link CTA path, privacy-friendly contact path, and non-weird Rowan Vale identity.
  - Guardrails: do not publish misleading claims, fake customer proof, guaranteed outcomes, unsupported compliance promises, or Sauron/internal persona references.
  - Cron rule: completed by the local orchestrator; future daily runs should move to the next high-priority task.

- **Build UsefulOps AI operating dashboard**
  - Status: completed 2026-05-30
  - Database task: `task-20260529-usefulops-dashboard`
  - Goal: give Brian a clear, regularly refreshed view of UsefulOps AI progress.
  - Data sources: local SQLite operating database first; Stripe API/webhook data once credentials are configured.
  - Initial metrics: gross revenue, MRR, tax reserve estimate, UsefulOps retained earnings, Brian/AI Lean Solutions share, operator discretion pool, monthly budget used/remaining, active prospects, cold contacts sent, replies, customers, deliverables, tasks, and recent action log.
  - Privacy rule: do not publish private prospect/customer detail, secrets, payment credentials, or inbox content to a public dashboard.
  - Result: private local dashboard export created at `local/exports/usefulops-dashboard.html`; latest snapshot is recorded in SQLite `dashboard_snapshots`.

- **Integrate Stripe API/webhooks for revenue tracking**
  - Status: completed 2026-05-30
  - Database task: `task-20260529-stripe-api-integration`
  - Decision: use Stripe API/webhooks rather than polling Brian's personal email for payment messages.
  - Current access: restricted live key stored privately in `local/secrets/stripe.env`; smoke test can read payment links, checkout sessions, customers, and subscriptions.
  - Later need from Brian: webhook signing secret when the dashboard grows from polling/smoke tests into event-driven sync.
  - Storage rule: no Stripe secret keys in Git, docs, website files, or plaintext committed files.
  - Result: read-only Stripe sync added and run. It records sync history in `stripe_sync_runs`, upserts payment links, and records paid checkout revenue when present.

- **Add deterministic orchestrator handlers for dashboard, Stripe, compliance, and prospect prep**
  - Status: completed 2026-05-30
  - Database task: `task-20260530-orchestrator-handlers`
  - Result: `scripts/operator_loop.py run` can now handle dashboard build, Stripe sync, outreach compliance, and prospect prep through bounded local scripts instead of free-form detached Codex work.

- **Complete UsefulOps outreach compliance and suppression process**
  - Status: completed 2026-05-30
  - Database task: `task-20260530-outreach-compliance`
  - Result: compliance checklist added at `docs/OUTREACH-COMPLIANCE.md`. No outreach was sent.

- **Prepare first UsefulOps prospect batch**
  - Status: completed 2026-05-30
  - Database task: `task-20260530-first-prospect-batch`
  - Result: five named public-prospect records were seeded in SQLite with public-source URLs, operating hypotheses, offer fit, and next actions. They are research-ready, not send-ready.

## Recorded Partnership Terms

- Friendly competition: first business to reach `$14k MRR` gets one year of bragging rights.
- Early UsefulOps revenue waterfall: reserve 30% for taxes, reimburse direct costs, then split remaining profit 50% to Brian/AI Lean Solutions and 50% to UsefulOps growth/discretion until UsefulOps reaches $2k/month gross for two consecutive months.
- Later default waterfall: reserve 30% for taxes, reimburse direct costs, then split remaining profit 40% to Brian/AI Lean Solutions, 40% to UsefulOps retained earnings, and 20% to operator discretion, subject to future agreement.
