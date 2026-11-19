import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { createBrowserAdapter } from "../src/browser-adapter.mjs";
import { computeActionDigest } from "../src/policy.mjs";
import { createGrant } from "../src/grant.mjs";

const now = Date.parse("2026-11-19T03:00:00.000Z");
const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const publicKeyPem = publicKey.export({ type: "spki", format: "pem" });
const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" });

function fakePage(initialUrl = "https://example.test/start") {
  let currentUrl = initialUrl;
  const calls = [];
  const state = {};
  return {
    calls,
    state,
    route: async (_pattern, handler) => { state.routeHandler = handler; },
    url: () => currentUrl,
    viewportSize: () => ({ width: 1280, height: 720 }),
    evaluate: async () => ({
      title: "Test page",
      elements: [{ role: "link", label: "Help", x: 10, y: 20, width: 40, height: 20, disabled: false }],
    }),
    screenshot: async () => Buffer.from("test-png"),
    goto: async (url, options) => {
      calls.push({ url, options });
      if (state.gotoGate) await state.gotoGate;
      currentUrl = url;
      return { status: () => 200 };
    },
  };
}

async function observedAdapter(page, overrides = {}) {
  const adapter = createBrowserAdapter({
    page,
    sessionId: "browser-session-1",
    allowedOrigins: ["https://example.test"],
    publicKeyPem,
    policyVersion: "policy-7",
    grantNonceLedger: { consume: async () => true },
    clock: () => now,
    ...overrides,
  });
  const observation = await adapter.observe({ userConsent: true });
  return { adapter, observation };
}

function makeNavigateRequest(observationId, overrides = {}) {
  const request = {
    schema_version: "1.0.0",
    task_id: "task-1",
    action_id: "action-1",
    actor_id: "user-1",
    target_application: "https://example.test",
    target_session_id: "browser-session-1",
    action_type: "navigate",
    parameters: { url: "https://example.test/help" },
    requested_at: new Date(now - 1000).toISOString(),
    expires_at: new Date(now + 10_000).toISOString(),
    observation_id: observationId,
    ...overrides,
  };
  return request;
}

function makeGrant(request) {
  return createGrant({
    request,
    decision: {
      decision: "ELIGIBLE_FOR_GRANT",
      reason: "ALLOWLISTED_LOW_RISK_ACTION",
      policy_version: "policy-7",
      risk_class: "R1",
      action_digest: computeActionDigest(request),
    },
    privateKeyPem,
    now,
    ttlMs: 5000,
  });
}

test("observation requires explicit user consent", async () => {
  const adapter = createBrowserAdapter({
    page: fakePage(), sessionId: "browser-session-1",
    allowedOrigins: ["https://example.test"],
    publicKeyPem, policyVersion: "policy-7",
    grantNonceLedger: { consume: async () => true }, clock: () => now,
  });
  await assert.rejects(() => adapter.observe({ userConsent: false }), /consent/i);
});

test("observation is provenance-bound, time-limited and excludes raw form values", async () => {
  const page = fakePage();
  const { observation } = await observedAdapter(page);
  assert.equal(observation.source_session_id, "browser-session-1");
  assert.equal(observation.application_identity, "https://example.test");
  assert.ok(observation.observation_id);
  assert.ok(observation.content_digest.startsWith("sha256:"));
  assert.equal(observation.detected_elements.length, 1);
  assert.equal(Object.hasOwn(observation.detected_elements[0], "value"), false);
  assert.ok(observation.expiry_at);
  assert.equal(observation.redaction_applied, false);
});

test("visual frame is captured only with separate explicit visual consent", async () => {
  const page = fakePage();
  const { adapter } = await observedAdapter(page);
  await assert.rejects(() => adapter.observe({
    userConsent: true, includeScreenshot: true, visualConsent: false,
  }), /visual consent/i);
  const observation = await adapter.observe({
    userConsent: true, includeScreenshot: true, visualConsent: true,
  });
  assert.equal(observation.visual_frame.mime_type, "image/png");
  assert.equal(observation.visual_frame.data_base64, Buffer.from("test-png").toString("base64"));
});

test("browser observation refuses an origin outside the allowlist", async () => {
  const page = fakePage("https://evil.test/");
  const adapter = createBrowserAdapter({
    page, sessionId: "browser-session-1", allowedOrigins: ["https://example.test"],
    publicKeyPem, policyVersion: "policy-7",
    grantNonceLedger: { consume: async () => true }, clock: () => now,
  });
  await assert.rejects(() => adapter.observe({ userConsent: true }), /origin/i);
});

test("navigation refuses an origin outside the allowlist", async () => {
  const page = fakePage();
  const { adapter, observation } = await observedAdapter(page);
  const request = makeNavigateRequest(observation.observation_id, {
    parameters: { url: "https://evil.test/collect" },
  });
  await assert.rejects(() => adapter.execute({
    request, grant: makeGrant(request), userConsent: true,
  }), /origin/i);
  assert.equal(page.calls.length, 0);
});

test("navigation refuses stale observations before grant consumption", async () => {
  const page = fakePage();
  let consumed = 0;
  const { adapter, observation } = await observedAdapter(page, {
    grantNonceLedger: { consume: async () => { consumed += 1; return true; } },
  });
  const request = makeNavigateRequest(observation.observation_id);
  const grant = makeGrant(request);
  page.url = () => "https://example.test/changed";
  await assert.rejects(() => adapter.execute({ request, grant, userConsent: true }), /stale/i);
  assert.equal(consumed, 0);
});

test("navigation requires a valid signed grant and returns pending verification", async () => {
  const page = fakePage();
  const { adapter, observation } = await observedAdapter(page);
  const request = makeNavigateRequest(observation.observation_id);
  const result = await adapter.execute({
    request, grant: makeGrant(request), userConsent: true,
  });
  assert.equal(result.execution_state, "AWAITING_VERIFICATION");
  assert.equal(result.verified, false);
  assert.equal(page.calls.length, 1);
  assert.equal(page.calls[0].url, "https://example.test/help");
});

test("adapter refuses unsupported actions rather than performing generic clicks", async () => {
  const page = fakePage();
  const { adapter, observation } = await observedAdapter(page);
  const request = makeNavigateRequest(observation.observation_id, {
    action_type: "click",
    parameters: { target_element_id: "button-1" },
  });
  await assert.rejects(() => adapter.execute({
    request, grant: makeGrant(request), userConsent: true,
  }), /unsupported action/i);
  assert.equal(page.calls.length, 0);
});

test("adapter stop switch prevents further execution", async () => {
  const page = fakePage();
  const { adapter, observation } = await observedAdapter(page);
  adapter.stop();
  const request = makeNavigateRequest(observation.observation_id);
  await assert.rejects(() => adapter.execute({
    request, grant: makeGrant(request), userConsent: true,
  }), /stopped/i);
  assert.equal(page.calls.length, 0);
});

test("browser adapter blocks external origins at the network request boundary", async () => {
  const page = fakePage();
  await observedAdapter(page);
  let aborted = 0;
  let continued = 0;
  await page.state.routeHandler({
    request: () => ({ url: () => "https://evil.test/tracker.js" }),
    abort: async () => { aborted += 1; },
    continue: async () => { continued += 1; },
  });
  assert.equal(aborted, 1);
  assert.equal(continued, 0);
});

test("browser adapter serializes actions and rejects concurrent execution", async () => {
  const page = fakePage();
  const { adapter, observation } = await observedAdapter(page);
  let release;
  page.state.gotoGate = new Promise((resolve) => { release = resolve; });
  const request = makeNavigateRequest(observation.observation_id);
  const grant = makeGrant(request);
  const first = adapter.execute({ request, grant, userConsent: true });
  while (page.calls.length === 0) await new Promise((resolve) => setImmediate(resolve));
  await assert.rejects(
    () => adapter.execute({ request, grant, userConsent: true }),
    /already executing/i,
  );
  release();
  const result = await first;
  assert.equal(result.execution_state, "AWAITING_VERIFICATION");
});
