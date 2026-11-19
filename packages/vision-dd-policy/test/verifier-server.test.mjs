import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { createVerifierServer } from "../src/verifier-server.mjs";
import { signReadback } from "../src/verifier.mjs";

const now = Date.parse("2026-11-19T03:00:00.000Z");
const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const publicKeyPem = publicKey.export({ type: "spki", format: "pem" });
const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" });
const actionRequest = {
  schema_version: "1.0.0",
  task_id: "task-1",
  action_id: "action-1",
  actor_id: "operator-1",
  target_application: "https://example.test",
  target_session_id: "session-1",
  action_type: "navigate",
  parameters: { url: "https://example.test/help" },
  requested_at: new Date(now - 1000).toISOString(),
  expires_at: new Date(now + 10_000).toISOString(),
  observation_id: "observation-1",
};
const execution = {
  action_id: "action-1",
  executor: "dd-browser-executor",
  execution_state: "AWAITING_VERIFICATION",
  completed_at: new Date(now - 500).toISOString(),
};
const readback = signReadback({
  payload: {
    schema_version: "1.0.0",
    evidence_id: "evidence-1",
    action_id: "action-1",
    session_id: "session-1",
    observed_url: "https://example.test/help",
    observed_at: new Date(now - 100).toISOString(),
    verifier_id: "independent-verifier",
    source_adapter: "read-only-browser-observer",
    evidence_method: "READ_ONLY_BROWSER_SESSION_QUERY",
  },
  privateKeyPem,
});

async function withServer(options, run) {
  const server = createVerifierServer({
    authenticateActor: async () => ({ actorId: "operator-1" }),
    readEvidence: async () => ({
      providerId: "separate-read-only-evidence-store",
      readback,
    }),
    evidenceProviderId: "separate-read-only-evidence-store",
    verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-verifier",
    clock: () => now,
    ...options,
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const address = server.address();
    await run(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise((resolve, reject) =>
      server.close((error) => error ? reject(error) : resolve()));
  }
}

async function post(baseUrl, body, headers = {}) {
  return fetch(`${baseUrl}/v1/verify`, {
    method: "POST",
    headers: { "content-type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
}

test("verifier fetches evidence independently and returns VERIFIED", async () => {
  let queried;
  await withServer({
    readEvidence: async (scope) => {
      queried = scope;
      return { providerId: "separate-read-only-evidence-store", readback };
    },
  }, async (url) => {
    const response = await post(url, { request: actionRequest, execution });
    assert.equal(response.status, 200);
    assert.equal((await response.json()).state, "VERIFIED");
    assert.equal(queried.actorId, "operator-1");
    assert.equal(queried.actionId, "action-1");
    assert.equal(queried.sessionId, "session-1");
  });
});

test("caller-supplied readback is rejected rather than trusted", async () => {
  await withServer({}, async (url) => {
    const response = await post(url, { request: actionRequest, execution, readback });
    assert.equal(response.status, 400);
    assert.equal((await response.json()).error, "INVALID_REQUEST");
  });
});

test("executor identity cannot be used as the evidence provider", async () => {
  await withServer({
    readEvidence: async () => ({ providerId: "dd-browser-executor", readback }),
  }, async (url) => {
    const response = await post(url, { request: actionRequest, execution });
    assert.equal((await response.json()).state, "UNKNOWN");
  });
});

test("evidence-provider failure returns UNKNOWN, never VERIFIED", async () => {
  await withServer({ readEvidence: async () => { throw new Error("offline"); } }, async (url) => {
    const response = await post(url, { request: actionRequest, execution });
    assert.equal((await response.json()).state, "UNKNOWN");
  });
});

test("actor mismatch is rejected", async () => {
  await withServer({}, async (url) => {
    const response = await post(url, {
      request: { ...actionRequest, actor_id: "another-operator" },
      execution,
    });
    assert.equal(response.status, 403);
  });
});

test("missing authentication is rejected", async () => {
  await withServer({ authenticateActor: async () => null }, async (url) => {
    const response = await post(url, { request: actionRequest, execution });
    assert.equal(response.status, 401);
  });
});

test("server refuses to start without a separate provider identity", () => {
  assert.throws(() => createVerifierServer({
    authenticateActor: async () => ({ actorId: "operator-1" }),
    readEvidence: async () => ({ providerId: "x", readback }),
    evidenceProviderId: "same",
    verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "same",
  }), /separate authentication, evidence-provider and verifier identities/);
});

test("read-only verifier exposes no grant or mutation endpoint", async () => {
  await withServer({}, async (url) => {
    const response = await fetch(`${url}/v1/grants`, { method: "POST" });
    assert.equal(response.status, 404);
  });
});
