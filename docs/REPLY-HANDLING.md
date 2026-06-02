# UsefulOps AI Reply Handling

UsefulOps should not force every buyer interaction through email, but it should protect time and avoid pretending Rowan can do live human calls without a real operating path.

## Default Response Mode

Use email-first selling for the first experiment.

Reasons:

- It keeps friction low for busy owner-led businesses.
- It preserves a written audit trail.
- It lets Rowan prepare better workflow observations than a rushed call.
- It avoids burning Brian's time on weak-fit prospects.

Email-first does not mean email-only. If a good prospect wants a call, treat that as buying intent.

## If A Prospect Asks For A Phone Call Or Online Meeting

Use this decision path:

1. Confirm fit and intent.
   - Is this a real business from the prospect list or a legitimate inbound lead?
   - Did they ask about a workflow, pricing, implementation, timeline, or a specific pain?
   - Are they asking for a real conversation rather than trying to sell to us?

2. Ask one short qualifying question by email if needed.
   - Example: "Happy to. Before we schedule, what repeat workflow would you most want to fix first: inquiry follow-up, appointment prep, admin summaries, or something else?"

3. Offer async first when appropriate.
   - Example: "I can either send a short workflow-audit outline by email, or if it is easier, we can do a 15-minute call."

4. If they still want a meeting and fit is credible, schedule a short discovery call.
   - Default length: 15 minutes.
   - Purpose: identify one workflow worth auditing, not perform broad AI consulting.
   - Require a specific agenda before booking.
   - Do not book open-ended "pick your brain" calls.

5. Protect the live-call boundary.
   - Rowan may prepare the agenda, questions, notes, proposal, and follow-up.
   - Do not imply a human live operator can attend unless a real attendance path exists.
   - If Brian's participation is required, do not book without confirming his availability and priority fit.
   - If Brian is the human for the call, prepare him thoroughly before he meets the prospect.

## Brian As The Live Human

Until UsefulOps has another real attendance path, Brian is the likely human for live calls or meetings.

That is a dependency, not a default entitlement. Do not spend Brian's calendar casually.

Before asking Brian to take a UsefulOps call, prepare a call packet with:

- Prospect/company summary.
- Why the prospect is qualified.
- Original outreach and reply thread summary.
- Public-source personalization basis.
- The workflow pain hypothesis.
- Recommended call objective.
- 15-minute agenda.
- Specific questions Brian should ask.
- Likely objections and suggested answers.
- What not to promise.
- Recommended next step if the call goes well.
- Draft follow-up email for after the call.
- Payment/scope path if the prospect wants to proceed.

Do not book Brian into a UsefulOps prospect call unless:

- The prospect is qualified under this document.
- Brian has the prep packet.
- Brian has explicitly accepted the time or has delegated scheduling authority for that specific case.
- The call is worth potentially interrupting higher-priority AI Lean Solutions or market-intelligence work.

## Meeting Qualification

Book or escalate only if at least one is true:

- Prospect describes a real workflow pain.
- Prospect asks about price, implementation, timeline, or scope.
- Prospect requests an audit or wants to see what UsefulOps would recommend.
- Prospect is clearly a strong target account with a concrete operational hypothesis.

Do not book if:

- They are selling a service to UsefulOps.
- They only ask vague questions that can be answered by email.
- They request free broad consulting without a concrete workflow.
- The request would expose customer/private data before scope and payment are clear.

## First-Call Agenda

Keep the first live discussion narrow:

1. What repeat workflow is wasting time?
2. Where does the work currently arrive: email, form, phone, spreadsheet, inbox, scheduling app?
3. What happens when it is missed or delayed?
4. What would a useful first draft/summary/reminder look like?
5. What system access would be needed for implementation?
6. Is the right next step a paid workflow audit, implementation sprint, or no-fit?

## After A Meeting Request

Always log:

- Prospect id or company.
- Request type.
- Qualification result.
- Whether the response was async outline, meeting offered, meeting booked, or no-fit.
- Next follow-up date.

Update the relevant `outreach_actions` row:

- `outcome = 'interested'` when interest is credible but no meeting is booked.
- `outcome = 'booked'` when a meeting is actually scheduled.
- `response_at` when the reply is received.

Create a task for the next action if it cannot be completed immediately.

## Operating Bias

Do not hide behind email if a qualified buyer wants a call. Also do not let calls become the business model.

The goal is to use calls sparingly to close trust gaps, then move quickly back to written scope, payment, and delivery.
