import assert from "node:assert/strict";
import {
  buildAcceptPayload,
  extractCallerPhone,
  hmacSha256Base64,
  isAllowedTestCaller,
  parseSignatureHeader,
  verifyOpenAIWebhook,
} from "../src/index.js";

const secret = "whsec_" + btoa("local-test-secret");
const payload = JSON.stringify({
  object: "event",
  id: "evt_test",
  type: "realtime.call.incoming",
  created_at: Math.floor(Date.now() / 1000),
  data: { call_id: "call_test" },
});
const webhookId = "wh_test";
const webhookTimestamp = String(Math.floor(Date.now() / 1000));
const signedContent = `${webhookId}.${webhookTimestamp}.${payload}`;
const signature = await hmacSha256Base64(secret, signedContent);

assert.deepEqual(parseSignatureHeader(`v1,${signature}`), [signature]);
assert.deepEqual(parseSignatureHeader(`v1=${signature}`), [signature]);

await verifyOpenAIWebhook(
  payload,
  new Headers({
    "webhook-id": webhookId,
    "webhook-timestamp": webhookTimestamp,
    "webhook-signature": `v1,${signature}`,
  }),
  secret,
);

await assert.rejects(
  verifyOpenAIWebhook(
    payload,
    new Headers({
      "webhook-id": webhookId,
      "webhook-timestamp": webhookTimestamp,
      "webhook-signature": "v1,bad",
    }),
    secret,
  ),
  /signature mismatch/,
);

assert.equal(extractCallerPhone([
  { name: "From", value: "sip:+16025551212@sip.example.com" },
  { name: "To", value: "sip:+18005551212@sip.example.com" },
]), "+16025551212");
assert.equal(extractCallerPhone([{ name: "from", value: "\"Brian\" <sip:602-555-1212@sip.example.com>" }]), "6025551212");
assert.equal(extractCallerPhone([{ name: "To", value: "sip:+18005551212@sip.example.com" }]), null);

assert.equal(isAllowedTestCaller("+16025551212", "+16025551212,+14805550000"), true);
assert.equal(isAllowedTestCaller("+16025551212", "+14805550000"), false);
assert.equal(isAllowedTestCaller(null, "+16025551212"), false);

const acceptPayload = buildAcceptPayload({
  callId: "rtc_test",
  callerPhone: "+16025551212",
  model: undefined,
  testTargetSeconds: "480",
  testHardCutoffSeconds: "600",
});
assert.equal(acceptPayload.type, "realtime");
assert.equal(acceptPayload.model, "gpt-realtime-2");
assert.equal(acceptPayload.reasoning.effort, "low");
assert.match(acceptPayload.instructions, /Rowan Vale/);
assert.match(acceptPayload.instructions, /rtc_test/);
assert.match(acceptPayload.instructions, /8 minutes/);
assert.match(acceptPayload.instructions, /not to fix it live/);
assert.match(acceptPayload.instructions, /Do not estimate elapsed time/);
assert.match(acceptPayload.instructions, /call controller/);
assert.equal(acceptPayload.audio.input.turn_detection.type, "server_vad");
assert.equal(acceptPayload.audio.output.voice, "cedar");

const defaultDurationPayload = buildAcceptPayload({
  callId: "rtc_default",
  callerPhone: "+16025551212",
  voice: "marin",
});
assert.match(defaultDurationPayload.instructions, /12 minutes/);
assert.match(defaultDurationPayload.instructions, /15 minutes/);
assert.equal(defaultDurationPayload.audio.output.voice, "marin");

console.log("signature verification tests passed");
