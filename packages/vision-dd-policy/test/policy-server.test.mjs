import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { createServer } from "../src/policy-server.mjs";
import { computeActionDigest } from "../src/policy.mjs";

const { privateKey } = generateKeyPairSync("ed25519");
const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" });
const policy = {
  version: "policy-7",
  maxRequestTtlMs: 60_000,
  maxApprovalTtlMs: 30_000,
  allowedApplications: ["https://example.test"],
  actionRisk: { navigate: "R1", save_draft: "R2", send_message: "R3", exfiltrate: "R4" },
};
const now = Date.now();

function request(action_type = "navigate", overrides = {}) {
  return {
    schema_version: "1.0.0",
    task_id: "task-1",
    action_id: "action-1",
    actor_id: "user-1",
    target_application: "https://example.test",
    target_session_id: "session-1",
    action_type,
    parameters: { url: "https://example.test/help" },
    requested_at: new Date(now - 1000).toISOString(),
    expires_at: new Date(now + 20_000).toISOString(),
    ...overrides,
  };
}

async function withServer(options, fn) {
  const server = createServer(options);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  try { await fn("http://127.0.0.1:" + address.port); }
  finally { await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve())); }
}

function baseOptions(overrides = {}) {
  const approvalNonces = new Set();
  return {
    policy,
    privateKeyPem,
    authenticateActor: async (req) => req.headers.authorization === "Bearer test-token"
      ? { actorId: "user-1" } : null,
    verifyApproval: async (approval) => approval.signature === "test-signature",
    approvalNonceLedger: {
      consume: async (nonce) => {
        if (approvalNonces.has(nonce)) return false;
        approvalNonces.add(nonce);
        return true;
      },
    },
    clock: () => now,
    ...overrides,
  };
}

test("unauthenticated grant request is rejected", async () => {
  await withServer(baseOptions(), async (url) => {
    const response = await fetch(url + "/v1/grants", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ action_request: request() }),
    });
    assert.equal(response.status, 401);
  });
});

test("authenticated low-risk request receives a signed, bounded grant", async () => {
  await withServer(baseOptions(), async (url) => {
    const response = await fetch(url + "/v1/grants", {
      method: "POST",
      headers: { authorization: "Bearer test-token", "content-type": "application/json" },
      body: JSON.stringify({ action_request: request() }),
    });
    assert.equal(response.status, 201);
    const body = await response.json();
    assert.ok(body.grant.payload.grant_id);
    assert.ok(body.grant.signature);
    assert.equal(body.grant.payload.actor_id, "user-1");
    assert.equal(body.grant.payload.target_session_id, "session-1");
  });
});

test("request cannot claim a different actor identity", async () => {
  await withServer(baseOptions(), async (url) => {
    const response = await fetch(url + "/v1/grants", {
      method: "POST",
      headers: { authorization: "Bearer test-token", "content-type": "application/json" },
      body: JSON.stringify({ action_request: request("navigate", { actor_id: "someone-else" }) }),
    });
    assert.equal(response.status, 403);
  });
});

test("unknown and prohibited actions are denied", async () => {
  await withServer(baseOptions(), async (url) => {
    for (const action_type of ["unknown_action", "exfiltrate"]) {
      const response = await fetch(url + "/v1/grants", {
        method: "POST",
        headers: { authorization: "Bearer test-token", "content-type": "application/json" },
        body: JSON.stringify({ action_request: request(action_type) }),
      });
      assert.equal(response.status, 403);
    }
  });
});

test("R2 action requires and validates a human approval", async () => {
  await withServer(baseOptions(), async (url) => {
    const action_request = request("save_draft");
    const missing = await fetch(url + "/v1/grants", {
      method: "POST",
      headers: { authorization: "Bearer test-token", "content-type": "application/json" },
      body: JSON.stringify({ action_request }),
    });
    assert.equal(missing.status, 409);
    const approval = {
      action_digest: computeActionDigest(action_request),
      policy_version: "policy-7",
      task_id: "task-1",
      actor_id: "user-1",
      target_application: "https://example.test",
      target_session_id: "session-1",
      approved_by: "human-1",
      issued_at: new Date(now - 100).toISOString(),
      expires_at: new Date(now + 5000).toISOString(),
      nonce: "approval-1",
      signature: "test-signature",
    };
    const response = await fetch(url + "/v1/grants", {
      method: "POST",
      headers: { authorization: "Bearer test-token", "content-type": "application/json" },
      body: JSON.stringify({ action_request, approval }),
    });
    assert.equal(response.status, 201);
    const body = await response.json();
    assert.equal(body.grant.payload.risk_class, "R2");
  });
});

test("unknown route and unsupported method are rejected", async () => {
  await withServer(baseOptions(), async (url) => {
    assert.equal((await fetch(url + "/unknown")).status, 404);
    assert.equal((await fetch(url + "/v1/grants")).status, 405);
  });
});

test("invalid JSON and oversized request bodies are rejected", async () => {
  await withServer(baseOptions({ maxBodyBytes: 64 }), async (url) => {
    const headers = { authorization: "Bearer test-token", "content-type": "application/json" };
    assert.equal((await fetch(url + "/v1/grants", { method: "POST", headers, body: "{" })).status, 400);
    assert.equal((await fetch(url + "/v1/grants", { method: "POST", headers, body: "x".repeat(100) })).status, 413);
  });
});

test("JSONP-like media types are not accepted as JSON", async () => {
  await withServer(baseOptions(), async (url) => {
    const response = await fetch(url + "/v1/grants", {
      method: "POST",
      headers: { authorization: "Bearer test-token", "content-type": "application/jsonp" },
      body: JSON.stringify({ action_request: request() }),
    });
    assert.equal(response.status, 415);
  });
});

test("policy service refuses to start without approval verification and durable nonce consumption", () => {
  const options = baseOptions();
  assert.throws(
    () => createServer({ ...options, verifyApproval: undefined }),
    /approval verification/i,
  );
  assert.throws(
    () => createServer({ ...options, approvalNonceLedger: undefined }),
    /nonce consumption/i,
  );
});

test("policy service refuses a non-Ed25519 grant signing key at startup", () => {
  const { privateKey: rsaPrivateKey } = generateKeyPairSync("rsa", {
    modulusLength: 2048,
  });
  const rsaPem = rsaPrivateKey.export({ type: "pkcs8", format: "pem" });
  assert.throws(
    () => createServer({ ...baseOptions(), privateKeyPem: rsaPem }),
    /Ed25519/i,
  );
});
