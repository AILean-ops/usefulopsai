# UsefulOps AI Operating Checklist

## Operating Doctrine

UsefulOps must be run as a business operating system, not as a sequence of clever conversations.

- Turn reasoning into rails: cron jobs, SQLite tasks, scripts, action_log rows, dashboard metrics, and follow-up triggers.
- Do not claim a dated plan is real until the trigger exists or the task state is durable.
- Every loop should have: objective, authority check, next action, decision rule, owner script/job, measurement, and next checkpoint.
- Prefer one small external experiment that is logged and measured over more internal preparation.
- Brian is a sounding board and boundary-setter, not the day-to-day operator. Ask him only when the authority envelope or safety boundary requires it.
- When a job cannot act, it must record the blocker precisely and create or recommend the next durable step.

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
- If a strategy decision creates dated follow-up work, create or verify the cron/task/checkpoint before reporting it as the plan.
- Check pending high-priority tasks in the local database.
- Keep `docs/STARTUP-TASKS.md` aligned with any durable startup tasks Brian should know about.
- Move the UsefulOps AI launch website forward until the public placeholder is replaced.
- Prioritize the UsefulOps AI operating dashboard until Brian has a reliable view of progress.
- Prefer direct Stripe API/webhook revenue tracking over polling Brian's personal inbox.

## Nightly Self-Improvement

- Run `scripts/nightly_self_improvement.py` as the nightly bounded self-improvement loop.
- Review both action efficacy and operating-system efficacy.
- Add at most one improvement task per nightly run.
- Do not let self-improvement displace customer acquisition, delivery, or revenue work; improvement must serve those outcomes.
- Do not create recursive chains of self-improvement tasks. If an improvement task proposes another improvement task, require it to name the business metric it improves.
- Keep runtime bounded and quiet unless the run creates a task, finds a blocker, or changes a durable artifact.

## Before Any Client Delivery

- Confirm scope.
- Confirm client facts.
- Confirm human-review boundaries.
- Confirm no sensitive data leak.
- Confirm deliverable quality.
- Log delivery.

## When A Prospect Wants A Call

- Follow `docs/REPLY-HANDLING.md`.
- Prefer async workflow-audit outline first when that can answer the question.
- If the prospect is qualified and wants a meeting, treat it as buying intent.
- Keep first calls to 15 minutes and one concrete workflow.
- Do not imply live human attendance unless a real attendance path exists.
- If Brian is needed for the call, create a prep packet before asking him to attend.
- Do not book Brian unless he has explicitly accepted the time or delegated scheduling authority for that specific case.

## Kill Switch

If Brian says `Sauron business freeze`, stop all UsefulOps AI outreach, spend, external replies, autonomous tasks, and non-essential sandbox actions until Brian explicitly resumes.
