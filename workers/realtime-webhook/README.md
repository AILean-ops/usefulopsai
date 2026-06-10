# UsefulOps Realtime Webhook

Cloudflare Worker for OpenAI Realtime SIP incoming-call webhooks.

The default mode is reject-only. It verifies OpenAI webhook signatures, inspects `realtime.call.incoming` events, and rejects the call through the OpenAI Realtime Calls API.

The only answering mode currently implemented is `accept-test`, which is for Brian-approved internal testing. It accepts calls only from phone numbers listed in `ALLOWED_TEST_CALLERS`, configures a short Rowan Vale test intake prompt, hands call control to a Cloudflare Queue consumer, starts the first greeting over the Realtime WebSocket, and hangs up at the test hard cutoff.

## Routes

- `GET /health` - health check
- `POST /openai/realtime/webhook` - OpenAI webhook endpoint

## Secrets

Set these with Wrangler after Brian creates the OpenAI webhook and project API key:

```bash
npx wrangler secret put OPENAI_WEBHOOK_SECRET
npx wrangler secret put OPENAI_API_KEY
```

`OPENAI_WEBHOOK_SECRET` comes from the OpenAI dashboard after webhook creation.
`OPENAI_API_KEY` must be scoped to the UsefulOps AI project.

## Runtime Variables

Default reject-only behavior:

```toml
CALL_HANDLING_MODE = "reject-only"
REJECT_STATUS_CODE = "486"
```

Internal answer-test behavior, only after Brian approves the exact test config:

```toml
CALL_HANDLING_MODE = "accept-test"
ALLOWED_TEST_CALLERS = "+16025551212"
REALTIME_MODEL = "gpt-realtime-2"
REALTIME_VOICE = "cedar"
TEST_TARGET_SECONDS = "720"
TEST_HARD_CUTOFF_SECONDS = "870"

[[queues.producers]]
queue = "usefulops-realtime-call-control"
binding = "CALL_CONTROL_QUEUE"

[[queues.consumers]]
queue = "usefulops-realtime-call-control"
max_batch_size = 1
max_batch_timeout = 1
max_retries = 0
```

`ALLOWED_TEST_CALLERS` is a comma-separated allowlist. If it is missing, the inbound SIP `From` phone number does not match, or `CALL_CONTROL_QUEUE` is not bound, the Worker rejects the call even in `accept-test` mode.

Rowan voice selection:

- Primary Realtime phone voice: `cedar`
- Brian briefly tested `marin` but preferred Cedar for overall quality.
- Fallback if Cedar becomes a comprehension problem: `marin`
- Brian prefers OpenAI's `onyx` voice, but current OpenAI Realtime docs do not list `onyx` as a Realtime/SIP voice. Use `onyx` only if OpenAI adds Realtime support or the call path changes to a TTS surface that supports it.
- Set the voice before the first model audio response. OpenAI Realtime does not allow changing the voice after audio has been emitted in a session.

Current intake prompt posture:

- Rowan introduces himself as UsefulOps AI.
- Rowan explains the call is a focused 15-minute workflow-intake call.
- Rowan is explicit that the call is for understanding the pain-point process, not fixing the workflow live.
- Rowan asks only discovery questions about the workflow, handoffs, delays, duplicated work, systems, frequency, and business impact.
- Rowan should favor targeted clarifying questions over early summarizing so the caller feels heard and the written plan has useful detail.
- Adaptive question map: monthly volume/frequency, request/order/job sources, who handles each step, current tools, where information gets lost, prioritization, employee instructions/details, post-completion steps, invoice timing, payment collection, estimate follow-up, review requests, maintenance reminders, budget tolerance, staff tech comfort, success definition, and the most painful problem right now.
- Rowan does not estimate elapsed time from the prompt. The Queue controller queues the friendly time check and wrap-up instructions on actual timers, then sends them only at a natural turn boundary.
- Around 10 minutes, the controller queues one friendly time check that the call is on track.
- Around 12 minutes, the controller queues a clean final wrap-up: summarize, set expectation for follow-up email, thank the caller, say bye, and stop.
- After the target wrap-up grace period, the controller hangs up so the caller does not have to initiate the end of the call.
- Rowan closes by summarizing what he heard and setting up a written follow-up plan.
- Any mention of deeper workflow/process improvement help or monthly support should be soft and informational, not pushy. Example: "If the plan looks useful, I can also help with more in-depth workflow and process improvement needs, or support this kind of work on a monthly basis."

Create the queue only after Brian approves the exact activation:

```bash
npx wrangler queues create usefulops-realtime-call-control
```

Why Queue: OpenAI's SIP guide expects a long-lived WebSocket controller after `accept`. Normal Worker `waitUntil()` is cancelled after about 30 seconds after response return, which caused the first test call to die at 3:15. Cloudflare Queue consumers have a documented 15-minute wall-time limit, matching the UsefulOps phone-intake cap better than request `waitUntil()`.

## Deploy

```bash
cd /Users/aileansolutions/usefulopsai/workers/realtime-webhook
npm install
npm test
npm run deploy
```

Expected deployed URL:

```text
https://usefulops-realtime-webhook.<cloudflare-workers-subdomain>.workers.dev/openai/realtime/webhook
```

Do not enable accept-call behavior, voice configuration, agent instructions, tools, call transfer, or production routing without Brian's explicit approval on the exact configuration.
