# UsefulOps AI Operating Checklist

## Before Any External Action

- Confirm action fits the current authority envelope.
- Confirm market-intelligence tasks are not being degraded.
- Check suppression list.
- Check approval state.
- Log planned action.
- Use approved identity and sender.
- Avoid unsupported claims.
- Avoid sensitive data unless explicitly approved.

## Before Any Spend

- Confirm vendor.
- Confirm amount.
- Confirm one-time vs. recurring.
- Confirm approved budget.
- Confirm payment path.
- Log planned spend.

## Startup Review

- Run the local orchestrator with `scripts/operator_loop.py run` for UsefulOps cron work; do not let detached Codex sessions own the whole loop.
- Keep Codex use bounded to orchestrator-controlled substeps with explicit timeout, scope, and no external action unless a deterministic handler performs it.
- Let the orchestrator start, checkpoint, complete, or fail the operator run; do not do that bookkeeping by hand during cron runs.
- Check pending high-priority tasks in the local database.
- Keep `docs/STARTUP-TASKS.md` aligned with any durable startup tasks Brian should know about.
- Move the UsefulOps AI launch website forward until the public placeholder is replaced.
- Prioritize the UsefulOps AI operating dashboard until Brian has a reliable view of progress.
- Prefer direct Stripe API/webhook revenue tracking over polling Brian's personal inbox.

## Before Any Client Delivery

- Confirm scope.
- Confirm client facts.
- Confirm human-review boundaries.
- Confirm no sensitive data leak.
- Confirm deliverable quality.
- Log delivery.

## Kill Switch

If Brian says `Sauron business freeze`, stop all UsefulOps AI outreach, spend, external replies, autonomous tasks, and non-essential sandbox actions until Brian explicitly resumes.
