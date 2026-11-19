import test from "node:test";
import assert from "node:assert/strict";
import { createServer as createHttpServer } from "node:http";
import { generateKeyPairSync } from "node:crypto";
let chromium;
try { ({ chromium } = await import("playwright")); } catch { /* Optional outside CI. */ }
import { createBrowserAdapter } from "../src/browser-adapter.mjs";
import { computeActionDigest } from "../src/policy.mjs";
import { createGrant } from "../src/grant.mjs";

async function withBrowser(fn) {
  const server = createHttpServer((request, response) => {
    if (request.url === "/redirect") {
      response.writeHead(302, { location: "https://evil.test/redirected" });
      response.end();
      return;
    }
    const html = `<!doctype html><html><head><title>VISION DD fixture</title></head>
      <body><h1>Safe fixture</h1><label for="secret">Secret</label>
      <input id="secret" type="password" value="never-export-this-value">
      <a href="/done">Continue to safe page</a></body></html>`;
    response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    response.end(html);
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  const origin = "http://127.0.0.1:" + address.port;
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ serviceWorkers: "block" });
  try {
    const page = await context.newPage();
    await page.goto(origin + "/start");
    await fn({ page, origin, context });
  } finally {
    await context.close();
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

function keys() {
  const pair = generateKeyPairSync("ed25519");
  return {
    publicKeyPem: pair.publicKey.export({ type: "spki", format: "pem" }),
    privateKeyPem: pair.privateKey.export({ type: "pkcs8", format: "pem" }),
  };
}

function makeRequest({ origin, observationId, now, path = "/done" }) {
  return {
    schema_version: "1.0.0",
    task_id: "integration-task",
    action_id: "integration-action",
    actor_id: "integration-user",
    target_application: origin,
    target_session_id: "integration-session",
    action_type: "navigate",
    parameters: { url: origin + path },
    requested_at: new Date(now - 1000).toISOString(),
    expires_at: new Date(now + 15_000).toISOString(),
    observation_id: observationId,
  };
}

function makeGrant(request, privateKeyPem, now) {
  return createGrant({
    request,
    decision: {
      decision: "ELIGIBLE_FOR_GRANT",
      reason: "ALLOWLISTED_LOW_RISK_ACTION",
      policy_version: "integration-policy",
      risk_class: "R1",
      action_digest: computeActionDigest(request),
    },
    privateKeyPem,
    now,
    ttlMs: 10_000,
  });
}

test("real Chromium observes with consent and performs one signed allowlisted navigation", { skip: !chromium }, async () => {
  await withBrowser(async ({ page, origin, context }) => {
    const { publicKeyPem, privateKeyPem } = keys();
    const adapter = createBrowserAdapter({
      page,
      context,
      sessionId: "integration-session",
      allowedOrigins: [origin],
      publicKeyPem,
      policyVersion: "integration-policy",
      grantNonceLedger: { consume: async () => true },
      requestConsent: async () => true,
    });
    const observation = await adapter.observe({ includeScreenshot: true });
    assert.equal(observation.application_identity, origin);
    assert.equal(observation.visual_frame.mime_type, "image/png");
    assert.equal(JSON.stringify(observation).includes("never-export-this-value"), false);
    assert.equal(context.serviceWorkers().length, 0);
    const blockedSocketCode = await page.evaluate(() => new Promise((resolve) => {
      const socket = new WebSocket("wss://evil.test/socket");
      socket.addEventListener("close", (event) => resolve(event.code), { once: true });
      setTimeout(() => resolve(-2), 2000);
    }));
    assert.equal(blockedSocketCode, 1008);
    assert.equal(adapter.getStatus().blocked_websocket_requests, 1);

    const now = Date.now();
    const request = makeRequest({ origin, observationId: observation.observation_id, now });
    const grant = makeGrant(request, privateKeyPem, now);
    const result = await adapter.execute({ request, grant });
    assert.equal(result.execution_state, "AWAITING_VERIFICATION");
    assert.equal(result.verified, false);
    assert.equal(page.url(), origin + "/done");
  });
});

test("real Chromium blocks a redirect outside the configured origin allowlist", { skip: !chromium }, async () => {
  await withBrowser(async ({ page, origin, context }) => {
    const { publicKeyPem, privateKeyPem } = keys();
    const adapter = createBrowserAdapter({
      page,
      context,
      sessionId: "integration-session",
      allowedOrigins: [origin],
      publicKeyPem,
      policyVersion: "integration-policy",
      grantNonceLedger: { consume: async () => true },
      requestConsent: async () => true,
    });
    const observation = await adapter.observe();
    const now = Date.now();
    const request = makeRequest({
      origin, observationId: observation.observation_id, now, path: "/redirect",
    });
    const grant = makeGrant(request, privateKeyPem, now);
    const result = await adapter.execute({ request, grant, userConsent: true });
    assert.equal(result.execution_state, "UNKNOWN");
    assert.ok(adapter.getStatus().blocked_http_requests >= 1);
  });
});
