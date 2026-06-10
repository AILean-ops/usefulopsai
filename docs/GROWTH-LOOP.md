# UsefulOps AI Growth Loop

UsefulOps must improve by running measurable experiments, not by accumulating setup work.

## Prime Directive

Reasoning is valuable only when it drives real operating motion. Every UsefulOps strategy conclusion must become at least one durable artifact:

- a SQLite task, experiment, growth batch, action_log entry, or learning_log entry;
- a cron job or other scheduled trigger;
- a script-owned workflow that can be rerun;
- a dashboard metric or review checkpoint.

If none of those exists, the conclusion is not yet an operating plan.

## Loop

1. **Run**
   - Send or prepare a defined batch with a clear hypothesis.
   - Keep niche, offer angle, subject pattern, CTA, and batch size explicit.
   - Create the next trigger before declaring the run plan complete.

2. **Measure**
   - Track drafts, sends, replies, positive replies, opt-outs, booked calls, paid customers, and revenue.
   - Store batch and review records in SQLite.

3. **Diagnose**
   - Execution gap: drafts exist but sends do not.
   - Message/list gap: sends exist but replies do not.
   - Offer gap: replies exist but positive replies do not.
   - Conversion gap: positive replies exist but no booked/paid outcome.
   - Scale winners: conversion/revenue signal exists.

4. **Adjust**
   - Change one or two variables at a time.
   - Preserve the current winner until evidence says otherwise.

5. **Repeat**
   - Strategy review creates the next concrete task automatically.
   - The dashboard surfaces the latest diagnosis, recommendation, and learning log.
   - No loop is complete until the next action is owned by a script, task, or scheduled job.

## Anti-Simulation Rules

- Do not count drafts, plans, docs, or recommendations as business progress unless they unblock or trigger real action.
- Do not say "we will" unless there is a durable mechanism that will.
- Do not wait for Brian on routine UsefulOps choices inside the authority envelope.
- If blocked, log the blocker, narrow it, and schedule the next attempt or escalation.
- Keep batch sizes small enough to protect reputation but large enough to create evidence.

## Nightly Self-Improvement Loop

UsefulOps runs a bounded self-improvement loop nightly.

Purpose:

- Evaluate whether previous business actions worked.
- Evaluate whether Rowan/Sauron's operating system failed, stalled, over-prepared, or left plans without triggers.
- Ask what would make the initiative more effective overall, not only what the last experiment proved.
- Add at most one concrete improvement task to the build plan.
- Rebuild the private dashboard so Brian can inspect current state.

Governor:

- No prospect contact.
- No spend.
- No customer/client system access.
- No OpenClaw gateway disruption.
- One new improvement task maximum per run.
- If blocked, record the blocker and next durable step instead of looping.
- Improvement tasks must connect to business outcomes: replies, booked calls, revenue, deliverability, trust, clarity, conversion, or reduced execution risk.

## Commands

```bash
scripts/strategy_review.py
scripts/nightly_self_improvement.py
scripts/build_dashboard.py
```

## Current First Diagnosis

As of 2026-05-30, UsefulOps has 12 prepared draft outreach records and zero sends. The strategy loop correctly diagnosed an execution gap and queued the next task:

`Execute first controlled outreach batch`

No emails were sent by the strategy review.

## First Controlled Outreach Decision

As of 2026-05-31, the execution path for the first controlled outreach batch is **direct send**, not mailbox drafts.

Rationale:

- The authority envelope allows direct prospect contact.
- The outreach compliance checklist allows direct email outreach when suppression, personalization, opt-out language, and logging checks pass.
- The UsefulOps Gmail account is authorized through GOG.
- A GOG dry-run and `scripts/send_outreach_batch.py --limit 2 --dry-run` both passed without sending real email.

Fallback:

- If Tuesday preflight fails, send 0 and record the blocker.
- Do not create mailbox drafts as a softer substitute unless the blocker specifically requires human mailbox inspection.

## Result Categories And Copy Quality

As of 2026-06-03, outreach results are tracked separately from row status:

- `undeliverable` means a hard delivery failure or confirmed bad address.
- `delivery_delayed` means Gmail or the recipient server is still retrying; do not suppress unless a final failure arrives.
- `sent`, `reply`, `positive_reply`, `opt_out`, `booked`, and `paid` remain outcome categories for funnel review.

The first 5-send UsefulOps batch produced one hard bounce and one temporary delay. The hard bounce is suppressed and counted as a `deliverability_gap`; the temporary delay is visible but not treated as a dead address yet.

Drafts also receive a `quality_score` and `quality_notes`. The send script blocks low-scoring drafts before external send, and the nightly self-improvement loop prioritizes rewriting jargon-heavy or robotic drafts before scaling.
