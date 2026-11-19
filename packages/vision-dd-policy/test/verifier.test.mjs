import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { signReadback, verifyNavigationReadback } from "../src/verifier.mjs";

const now = Date.parse("2026-11-19T03:00:00.000Z");
const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const publicKeyPem = publicKey.export({ type: "spki", format: "pem" });
const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" });
const request = {
  schema_version: "1.0.0",
  task_id: "task-1",
  action_id: "action-1",
  actor_id: "user-1",
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
  executor: "playwright-supervised-browser",
  execution_state: "AWAITING_VERIFICATION",
  completed_at: new Date(now - 500).toISOString(),
};

function evidence(overrides = {}) {
  const payload = {
    schema_version: "1.0.0",
    evidence_id: "evidence-1",
    action_id: "action-1",
    session_id: "session-1",
    observed_url: "https://example.test/help",
    observed_at: new Date(now - 100).toISOString(),
    verifier_id: "independent-readonly-verifier",
    source_adapter: "separate-browser-observer",
    evidence_method: "READ_ONLY_BROWSER_SESSION_QUERY",
    ...overrides,
  };
  return signReadback({ payload, privateKeyPem });
}

test("independently signed readback verifies the requested navigation", () => {
  const result = verifyNavigationReadback({
    execution, request, readback: evidence(), verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "VERIFIED");
});

test("signed readback of a different URL is not verified", () => {
  const result = verifyNavigationReadback({
    execution, request, readback: evidence({ observed_url: "https://example.test/login" }),
    verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "NOT_VERIFIED");
});

test("stale readback is UNKNOWN", () => {
  const result = verifyNavigationReadback({
    execution, request,
    readback: evidence({ observed_at: new Date(now - 20_000).toISOString() }),
    verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "UNKNOWN");
});

test("executor cannot verify its own execution", () => {
  const result = verifyNavigationReadback({
    execution, request,
    readback: evidence({
      verifier_id: "independent-readonly-verifier",
      source_adapter: "playwright-supervised-browser",
    }),
    verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "UNKNOWN");
});

test("tampered readback signature is UNKNOWN", () => {
  const valid = evidence();
  const tampered = { ...valid, payload: { ...valid.payload, observed_url: "https://example.test/evil" } };
  const result = verifyNavigationReadback({
    execution, request, readback: tampered, verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "UNKNOWN");
});

test("readback for another action or session is UNKNOWN", () => {
  const result = verifyNavigationReadback({
    execution, request,
    readback: evidence({ action_id: "other-action" }),
    verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "UNKNOWN");
});

test("missing readback is UNKNOWN", () => {
  const result = verifyNavigationReadback({
    execution, request, readback: null, verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "UNKNOWN");
});

test("readback cannot verify a URL outside the approved application origin", () => {
  const result = verifyNavigationReadback({
    execution, request: { ...request, target_application: "https://other.test" },
    readback: evidence(), verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "UNKNOWN");
});

test("oversized evidence fields and signatures are rejected", () => {
  const valid = evidence();
  const oversized = {
    ...valid,
    payload: { ...valid.payload, observed_url: "https://example.test/" + "x".repeat(3000) },
  };
  const result = verifyNavigationReadback({
    execution, request, readback: oversized, verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(result.state, "UNKNOWN");
  const hugeSignature = verifyNavigationReadback({
    execution, request, readback: { ...valid, signature: "x".repeat(3000) },
    verifierPublicKeyPem: publicKeyPem,
    expectedVerifierId: "independent-readonly-verifier", now,
  });
  assert.equal(hugeSignature.state, "UNKNOWN");
});
