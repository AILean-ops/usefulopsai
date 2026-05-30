# UsefulOps AI Growth Loop

UsefulOps must improve by running measurable experiments, not by accumulating setup work.

## Loop

1. **Run**
   - Send or prepare a defined batch with a clear hypothesis.
   - Keep niche, offer angle, subject pattern, CTA, and batch size explicit.

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

## Commands

```bash
scripts/strategy_review.py
scripts/build_dashboard.py
```

## Current First Diagnosis

As of 2026-05-30, UsefulOps has 12 prepared draft outreach records and zero sends. The strategy loop correctly diagnosed an execution gap and queued the next task:

`Execute first controlled outreach batch`

No emails were sent by the strategy review.
