const DEFAULT_REJECT_STATUS = 486;
const MAX_TIMESTAMP_SKEW_SECONDS = 300;
const DEFAULT_MODEL = "gpt-realtime-2";
const DEFAULT_VOICE = "cedar";
const DEFAULT_TEST_TARGET_SECONDS = 12 * 60;
const DEFAULT_TEST_HARD_CUTOFF_SECONDS = 15 * 60;
const CONTROL_QUEUE_DELAY_SECONDS = 1;
const DEFAULT_TIME_CHECK_SECONDS = 10 * 60;
const WRAP_GRACE_SECONDS = 30;
const POST_WRAP_HANGUP_GRACE_SECONDS = 90;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse({
        ok: true,
        service: "usefulops-realtime-webhook",
        mode: getCallHandlingMode(env),
      });
    }

    if (request.method !== "POST" || url.pathname !== "/openai/realtime/webhook") {
      return jsonResponse({ error: "not_found" }, 404);
    }

    const body = await request.text();

    try {
      await verifyOpenAIWebhook(body, request.headers, env.OPENAI_WEBHOOK_SECRET);
    } catch (error) {
      console.warn("OpenAI webhook signature verification failed", {
        message: error instanceof Error ? error.message : String(error),
      });
      return jsonResponse({ error: "invalid_signature" }, 400);
    }

    let event;
    try {
      event = JSON.parse(body);
    } catch {
      return jsonResponse({ error: "invalid_json" }, 400);
    }

    if (event?.type !== "realtime.call.incoming") {
      console.log("Ignoring non-call webhook event", {
        event_id: event?.id,
        event_type: event?.type,
      });
      return jsonResponse({ ok: true, ignored: true });
    }

    const callId = event?.data?.call_id;
    if (!callId || typeof callId !== "string") {
      return jsonResponse({ error: "missing_call_id" }, 400);
    }

    const mode = getCallHandlingMode(env);
    const callerPhone = extractCallerPhone(event?.data?.sip_headers);
    if (mode === "accept-test" && isAllowedTestCaller(callerPhone, env.ALLOWED_TEST_CALLERS)) {
      if (!env.CALL_CONTROL_QUEUE) {
        const statusCode = parseRejectStatus(env.REJECT_STATUS_CODE);
        const rejectResult = await rejectRealtimeCall(callId, statusCode, env.OPENAI_API_KEY);
        console.warn("Rejected UsefulOps realtime test call because call-control queue is missing", {
          event_id: event?.id,
          call_id: callId,
          caller_phone: callerPhone,
          openai_status: rejectResult.status,
        });
        return jsonResponse({
          ok: false,
          mode,
          error: "missing_call_control_queue",
          call_id: callId,
          caller_phone: callerPhone,
          openai_status: rejectResult.status,
        }, 503);
      }

      const hardCutoffSeconds = parsePositiveInt(
        env.TEST_HARD_CUTOFF_SECONDS,
        DEFAULT_TEST_HARD_CUTOFF_SECONDS,
      );
      const acceptPayload = buildAcceptPayload({
        callId,
        callerPhone,
        model: env.REALTIME_MODEL,
        voice: env.REALTIME_VOICE,
        testTargetSeconds: env.TEST_TARGET_SECONDS,
        testHardCutoffSeconds: hardCutoffSeconds,
      });
      await env.CALL_CONTROL_QUEUE.send({
        call_id: callId,
        caller_phone: callerPhone,
        target_seconds: parsePositiveInt(env.TEST_TARGET_SECONDS, DEFAULT_TEST_TARGET_SECONDS),
        hard_cutoff_seconds: hardCutoffSeconds,
      }, { delaySeconds: CONTROL_QUEUE_DELAY_SECONDS });
      const acceptResult = await acceptRealtimeCall(callId, acceptPayload, env.OPENAI_API_KEY);

      console.log("Accepted incoming UsefulOps realtime test call", {
        event_id: event?.id,
        call_id: callId,
        caller_phone: callerPhone,
        openai_status: acceptResult.status,
      });

      return jsonResponse({
        ok: acceptResult.ok,
        mode,
        call_id: callId,
        caller_phone: callerPhone,
        openai_status: acceptResult.status,
      }, acceptResult.ok ? 200 : 502);
    }

    const statusCode = parseRejectStatus(env.REJECT_STATUS_CODE);
    const rejectResult = await rejectRealtimeCall(callId, statusCode, env.OPENAI_API_KEY);

    console.log("Rejected incoming UsefulOps realtime call", {
      event_id: event?.id,
      call_id: callId,
      caller_phone: callerPhone,
      mode,
      status_code: statusCode,
      openai_status: rejectResult.status,
    });

    return jsonResponse({
      ok: rejectResult.ok,
      mode,
      call_id: callId,
      caller_phone: callerPhone,
      status_code: statusCode,
      openai_status: rejectResult.status,
    }, rejectResult.ok ? 200 : 502);
  },

  async queue(batch, env) {
    for (const message of batch.messages) {
      const body = message.body || {};
      const callId = body.call_id;
      if (!callId || typeof callId !== "string") {
        console.warn("Skipping call-control queue message with missing call id");
        continue;
      }

      await startRealtimeCallControl(
        callId,
        env.OPENAI_API_KEY,
        parsePositiveInt(body.target_seconds, DEFAULT_TEST_TARGET_SECONDS),
        parsePositiveInt(body.hard_cutoff_seconds, DEFAULT_TEST_HARD_CUTOFF_SECONDS),
      );
    }
  },
};

export async function verifyOpenAIWebhook(payload, headers, secret) {
  if (!secret) {
    throw new Error("OPENAI_WEBHOOK_SECRET is not configured");
  }

  const webhookId = headers.get("webhook-id");
  const webhookTimestamp = headers.get("webhook-timestamp");
  const webhookSignature = headers.get("webhook-signature");

  if (!webhookId || !webhookTimestamp || !webhookSignature) {
    throw new Error("required webhook signature headers are missing");
  }

  const timestamp = Number.parseInt(webhookTimestamp, 10);
  if (!Number.isFinite(timestamp)) {
    throw new Error("invalid webhook timestamp");
  }

  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - timestamp) > MAX_TIMESTAMP_SKEW_SECONDS) {
    throw new Error("webhook timestamp is outside tolerance");
  }

  const signedContent = `${webhookId}.${webhookTimestamp}.${payload}`;
  const expectedSignature = await hmacSha256Base64(secret, signedContent);
  const suppliedSignatures = parseSignatureHeader(webhookSignature);

  if (!suppliedSignatures.some((signature) => timingSafeEqual(signature, expectedSignature))) {
    throw new Error("signature mismatch");
  }
}

export function parseSignatureHeader(headerValue) {
  return headerValue
    .split(/\s+/)
    .map((part) => part.trim())
    .filter((part) => part.startsWith("v1,") || part.startsWith("v1="))
    .map((part) => part.slice(3))
    .filter(Boolean);
}

export async function hmacSha256Base64(secret, message) {
  const keyBytes = decodeWebhookSecret(secret);
  const key = await crypto.subtle.importKey(
    "raw",
    keyBytes,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  return arrayBufferToBase64(signature);
}

function decodeWebhookSecret(secret) {
  const normalized = secret.startsWith("whsec_") ? secret.slice("whsec_".length) : secret;
  try {
    return base64ToUint8Array(normalized);
  } catch {
    return new TextEncoder().encode(secret);
  }
}

function parseRejectStatus(value) {
  if (!value) {
    return DEFAULT_REJECT_STATUS;
  }
  const parsed = Number.parseInt(value, 10);
  if (Number.isInteger(parsed) && parsed >= 400 && parsed <= 699) {
    return parsed;
  }
  return DEFAULT_REJECT_STATUS;
}

function getCallHandlingMode(env) {
  return env.CALL_HANDLING_MODE === "accept-test" ? "accept-test" : "reject-only";
}

export function extractCallerPhone(sipHeaders) {
  if (!Array.isArray(sipHeaders)) {
    return null;
  }

  const from = sipHeaders.find((header) => String(header?.name || "").toLowerCase() === "from");
  const value = String(from?.value || "");
  const sipMatch = value.match(/sip:([^@;>\s]+)/i);
  const candidate = sipMatch ? sipMatch[1] : value;
  const normalized = normalizePhone(candidate);
  return normalized.replace(/\D/g, "").length >= 8 ? normalized : null;
}

export function normalizePhone(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) {
    return "";
  }
  const hasPlus = trimmed.startsWith("+");
  const digits = trimmed.replace(/\D/g, "");
  return digits ? `${hasPlus ? "+" : ""}${digits}` : "";
}

export function isAllowedTestCaller(callerPhone, allowedCallers) {
  if (!callerPhone || !allowedCallers) {
    return false;
  }

  const normalizedCaller = normalizePhone(callerPhone);
  return String(allowedCallers)
    .split(",")
    .map((phone) => normalizePhone(phone))
    .filter(Boolean)
    .includes(normalizedCaller);
}

export function buildAcceptPayload({
  callId,
  callerPhone,
  model,
  voice,
  testTargetSeconds,
  testHardCutoffSeconds,
}) {
  const targetSeconds = parsePositiveInt(testTargetSeconds, DEFAULT_TEST_TARGET_SECONDS);
  const hardCutoffSeconds = parsePositiveInt(testHardCutoffSeconds, DEFAULT_TEST_HARD_CUTOFF_SECONDS);

  return {
    type: "realtime",
    model: model || DEFAULT_MODEL,
    instructions: buildTestInstructions({ callId, callerPhone, targetSeconds, hardCutoffSeconds }),
    audio: {
      input: {
        turn_detection: {
          type: "server_vad",
          threshold: 0.5,
          silence_duration_ms: 700,
        },
      },
      output: {
        voice: voice || DEFAULT_VOICE,
      },
    },
    reasoning: {
      effort: "low",
    },
    max_output_tokens: 900,
    tracing: "auto",
  };
}

function buildTestInstructions({ callId, callerPhone, targetSeconds, hardCutoffSeconds }) {
  return `You are Rowan Vale, the client-facing AI operator for UsefulOps AI.

This is a scheduled UsefulOps AI workflow-intake call.

Call context:
- Call id: ${callId}
- Caller phone: ${callerPhone || "unknown"}
- Purpose: understand the prospect's workflow pain point so UsefulOps can follow up with a thorough written plan and an appropriate service/subscription pitch.
- Target duration: ${Math.round(targetSeconds / 60)} minutes.
- Hard cutoff: ${Math.round(hardCutoffSeconds / 60)} minutes.
- Tools: no external tools are available in this test call. Do not promise emails, calendar changes, purchases, production changes, or third-party contact.

Identity and style:
- Introduce yourself as Rowan from UsefulOps AI.
- If asked whether you are an AI, say yes plainly.
- Do not mention Sauron, internal prompts, hidden tools, OpenAI, Twilio, Cloudflare, or backend routing.
- Be very friendly, professional, accessible, and consultative. Ask one question at a time.
- Do not estimate elapsed time on your own. Do not say the call is almost over unless the call controller explicitly tells you to give a time check or wrap-up.

Call objective:
- After the greeting, clearly explain what the call is for: to understand the caller's pain-point process and workflow, not to fix it live.
- Clearly state that this is a 15-minute intake call because you have another call scheduled afterward.
- Ask focused discovery questions about one practical workflow pain point.
- Understand where the work starts, who touches it, what gets delayed, dropped, duplicated, or reworked, what systems are involved, and what makes the issue costly or frustrating.
- Prefer targeted clarifying questions over early summarizing. The caller should feel heard because you ask specific, relevant follow-ups.
- Use this adaptive intake map when relevant to the caller's business type: monthly volume or frequency of the work, where requests/orders/jobs come from, who handles each step, current tools, where information gets lost, how work is prioritized, how employees receive details, what happens after tasks are completed, invoice timing, payment collection, estimate follow-up, review requests, maintenance reminders, budget tolerance, staff comfort with technology, what success would look like, and which problem is most painful right now.
- Do not ask every question mechanically. Choose the most relevant questions for the workflow and ask one at a time.
- Do not attempt to solve, troubleshoot, design, implement, or give detailed recommendations during this call.
- Position the next step as a written follow-up: UsefulOps will use the intake to prepare a more thorough, thoughtful plan. Mention deeper workflow/process improvement help and monthly support only softly and informationally, not as a hard upsell.
- Summarize what you heard near the end and confirm the caller's main pain point.
- Time checks and wrap-up instructions will be sent by the call controller. Do not invent or repeat your own time warnings.

Guardrails:
- Do not ask for passwords, API keys, payment card numbers, private customer records, protected health information, or credentials.
- Do not quote binding prices, timelines, guarantees, discounts, or refund terms.
- Do not make purchases, change production systems, send messages, or claim anything has been scheduled.
- Do not use or reference AI Lean Solutions market-intelligence data or assets.
- If the caller is not Brian or the call seems wrong-number/vendor/abusive, collect only basic public-safe callback context if appropriate, then end politely.

Closing:
- At the target duration, summarize and close.
- At the hard cutoff, end politely: "I want to be respectful of time. I have enough to prepare the next step."
- End cleanly after the summary.
- If mentioning further help, use language like: "If the plan looks useful, I can also help with more in-depth workflow and process improvement needs, or support this kind of work on a monthly basis."
- Time reminders should reassure the caller that the call is on track, not pressure them.
- Do not repeat the same time or wrap-up phrase. If you have already said you have enough information, summarize and close instead of saying it again.
- Do not overrun the intake call.`;
}

function parsePositiveInt(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

async function acceptRealtimeCall(callId, payload, apiKey) {
  if (!apiKey) {
    return { ok: false, status: 500 };
  }

  const response = await fetch(
    `https://api.openai.com/v1/realtime/calls/${encodeURIComponent(callId)}/accept`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );

  return { ok: response.ok, status: response.status };
}

async function startRealtimeCallControl(callId, apiKey, targetSeconds, hardCutoffSeconds) {
  if (!apiKey) {
    return;
  }

  try {
    const response = await fetch(
      `https://api.openai.com/v1/realtime?call_id=${encodeURIComponent(callId)}`,
      {
        headers: {
          Authorization: `Bearer ${apiKey}`,
          Upgrade: "websocket",
        },
      },
    );

    const websocket = response.webSocket;
    if (response.status !== 101 || !websocket) {
      console.warn("Realtime call control websocket upgrade failed", {
        call_id: callId,
        status: response.status,
      });
      return;
    }

    websocket.accept();
    websocket.send(JSON.stringify({
      type: "response.create",
      response: {
        instructions: "Greet the caller as Rowan from UsefulOps AI. Explain that this is a focused 15-minute workflow-intake call to understand their pain-point process, not to fix it live, because you will use the call to prepare a thoughtful written follow-up plan. Then ask what workflow or process is causing the most pain right now. Keep any mention of deeper help or monthly support soft and informational, not pushy. Do not estimate elapsed time or say the call is almost over unless a later controller message explicitly tells you to give a time check or wrap up.",
      },
    }));

    let userSpeaking = false;
    let responseActive = false;
    const pendingInstructions = [];

    const enqueueTimedCallInstruction = (instructions) => {
      pendingInstructions.push(instructions);
      flushTimedCallInstruction();
    };

    const flushTimedCallInstruction = () => {
      if (pendingInstructions.length === 0 || userSpeaking || responseActive) {
        return;
      }

      responseActive = true;
      sendTimedCallInstruction(websocket, pendingInstructions.shift());
    };

    websocket.addEventListener("message", (event) => {
      try {
        const realtimeEvent = JSON.parse(event.data);
        if (realtimeEvent?.type === "input_audio_buffer.speech_started") {
          userSpeaking = true;
        }
        if (realtimeEvent?.type === "input_audio_buffer.speech_stopped") {
          userSpeaking = false;
          setTimeout(flushTimedCallInstruction, 1000);
        }
        if (realtimeEvent?.type === "response.created") {
          responseActive = true;
        }
        if (realtimeEvent?.type === "response.done") {
          responseActive = false;
          flushTimedCallInstruction();
        }
        if ([
          "error",
          "response.done",
          "input_audio_buffer.speech_started",
          "input_audio_buffer.speech_stopped",
          "conversation.item.input_audio_transcription.completed",
        ].includes(realtimeEvent?.type)) {
          console.log("Realtime call event", {
            call_id: callId,
            event_type: realtimeEvent.type,
            event_id: realtimeEvent.event_id,
          });
        }
      } catch {
        // Avoid logging raw call content.
      }
    });

    await new Promise((resolve) => {
      const timers = [];
      const cleanupTimers = () => {
        for (const timer of timers) {
          clearTimeout(timer);
        }
      };

      const timeCheckSeconds = Math.max(
        60,
        Math.min(DEFAULT_TIME_CHECK_SECONDS, targetSeconds - 120),
      );
      if (timeCheckSeconds > 0 && timeCheckSeconds < hardCutoffSeconds) {
        timers.push(setTimeout(() => {
          enqueueTimedCallInstruction(
            "At your next natural turn, give exactly one brief, calm time check. Use wording like: 'Just a quick time check: we have a few minutes left, so I want to make sure I understand the most important part of this workflow.' Then continue with one useful discovery question. Do not repeat this time check.",
          );
        }, timeCheckSeconds * 1000));
      }

      const wrapSeconds = Math.min(targetSeconds, hardCutoffSeconds - WRAP_GRACE_SECONDS);
      if (wrapSeconds > timeCheckSeconds && wrapSeconds < hardCutoffSeconds) {
        timers.push(setTimeout(() => {
          enqueueTimedCallInstruction(
            "At your next natural turn, begin the final wrap-up. Briefly summarize the caller's workflow pain point, confirm the main issue, then say: 'I have what I need, so if there's nothing else, I hope you have a great day. You can expect a follow-up email from me later today. Thanks. Bye.' If you mention deeper workflow help or monthly support, make it soft and informational before that closing. Do not repeat 'we are short on time' or 'I have enough to put together a plan'. Do not go silent after saying you have enough; close the call.",
          );
        }, wrapSeconds * 1000));
      }

      let settled = false;
      const postWrapHangupSeconds = Math.min(
        targetSeconds + POST_WRAP_HANGUP_GRACE_SECONDS,
        hardCutoffSeconds - WRAP_GRACE_SECONDS,
      );
      if (postWrapHangupSeconds > wrapSeconds && postWrapHangupSeconds < hardCutoffSeconds) {
        timers.push(setTimeout(() => {
          void hangUpAndFinish("target wrap completed");
        }, postWrapHangupSeconds * 1000));
      }

      const timeout = setTimeout(() => {
        void hangUpAndFinish("test hard cutoff");
      }, hardCutoffSeconds * 1000);

      const finish = () => {
        if (settled) {
          return;
        }
        settled = true;
        cleanupTimers();
        clearTimeout(timeout);
        resolve();
      };

      async function hangUpAndFinish(reason) {
        if (settled) {
          return;
        }
        settled = true;
        try {
          await hangUpRealtimeCall(callId, apiKey);
        } finally {
          try {
            websocket.close(1000, reason);
          } catch {
            // Nothing useful to do during cleanup.
          }
          cleanupTimers();
          clearTimeout(timeout);
          resolve();
        }
      }

      websocket.addEventListener("close", finish, { once: true });
      websocket.addEventListener("error", finish, { once: true });
    });
  } catch (error) {
    console.warn("Realtime call control websocket failed", {
      call_id: callId,
      message: error instanceof Error ? error.message : String(error),
    });
  }
}

function sendTimedCallInstruction(websocket, instructions) {
  try {
    websocket.send(JSON.stringify({
      type: "response.create",
      response: { instructions },
    }));
  } catch {
    // The close/error handlers own cleanup if the call already ended.
  }
}

async function hangUpRealtimeCall(callId, apiKey) {
  const response = await fetch(
    `https://api.openai.com/v1/realtime/calls/${encodeURIComponent(callId)}/hangup`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    },
  );
  return { ok: response.ok, status: response.status };
}

async function rejectRealtimeCall(callId, statusCode, apiKey) {
  if (!apiKey) {
    return { ok: false, status: 500 };
  }

  const response = await fetch(
    `https://api.openai.com/v1/realtime/calls/${encodeURIComponent(callId)}/reject`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status_code: statusCode }),
    },
  );

  return { ok: response.ok, status: response.status };
}

function timingSafeEqual(a, b) {
  const left = new TextEncoder().encode(a);
  const right = new TextEncoder().encode(b);

  if (left.length !== right.length) {
    return false;
  }

  let result = 0;
  for (let index = 0; index < left.length; index += 1) {
    result |= left[index] ^ right[index];
  }
  return result === 0;
}

function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

function base64ToUint8Array(value) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
