import test from "node:test";
import assert from "node:assert/strict";
import { computeActionDigest, evaluateAction } from "../src/policy.mjs";

const now = Date.parse("2026-11-19T03:00:00.000Z");
const policy = {
  version: "0.1.0",
  maxRequestTtlMs: 60_000,
  maxApprovalTtlMs: 30_000,
  allowedApplications: ["com.example.test"],
  actionRisk: {
    inspect_screen: "R0",
    open_tab: "R1",
    save_draft: "R2",
    submit_purchase: "R3",
    delete_account: "R4",
  },
};
function request(action_type = "inspect_screen", overrides = {}) {
  return {
    schema_version: "1.0.0",
    task_id: "task-1",
    action_id: "action-1",
    actor_id: "user-1",
    target_application: "com.example.test",
    target_session_id: "session-1",
    action_type,
    parameters: { destination: "safe-example" },
    requested_at: new Date(now - 1_000).toISOString(),
    expires_at: new Date(now + 30_000).toISOString(),
    ...overrides,
  };
}
function approvalFor(action, overrides = {}) {
  return {
    action_digest: computeActionDigest(action),
    task_id: action.task_id,
    actor_id: action.actor_id,
    target_application: action.target_application,
    target_session_id: action.target_session_id,
    approved_by: "human-approver-1",
    issued_at: new Date(now - 500).toISOString(),
    expires_at: new Date(now + 10_000).toISOString(),
    nonce: "nonce-unique-1",
    signature: "test-signature",
    ...overrides,
  };
}

test("allowlisted R0 observation is eligible for grant issuance, not direct execution", async () => {
  const result = await evaluateAction({ request: request(), policy, now });
  assert.equal(result.decision, "ELIGIBLE_FOR_GRANT");
  assert.equal(result.risk_class, "R0");
});

test("unknown action is denied", async () => {
  const result = await evaluateAction({ request: request("run_shell"), policy, now });
  assert.equal(result.decision, "DENY");
});

test("R4 prohibited action is denied", async () => {
  const result = await evaluateAction({ request: request("delete_account"), policy, now });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "PROHIBITED_ACTION");
});

test("R2 and R3 require human approval", async () => {
  for (const actionType of ["save_draft", "submit_purchase"]) {
    const result = await evaluateAction({ request: request(actionType), policy, now });
    assert.equal(result.decision, "REQUIRE_APPROVAL");
  }
});

test("valid signed, scoped, one-use approval makes R3 eligible for grant issuance", async () => {
  const action = request("submit_purchase");
  const approval = approvalFor(action);
  const consumed = new Set();
  const result = await evaluateAction({
    request: action,
    policy,
    approval,
    now,
    verifyApproval: async (value) => value.signature === "test-signature",
    consumeApprovalNonce: async (nonce) => {
      if (consumed.has(nonce)) return false;
      consumed.add(nonce);
      return true;
    },
  });
  assert.equal(result.decision, "ELIGIBLE_FOR_GRANT");
  assert.equal(result.reason, "APPROVAL_VERIFIED_AND_CONSUMED");
});

test("approval cannot be replayed", async () => {
  const action = request("submit_purchase");
  const approval = approvalFor(action);
  const consumed = new Set(["nonce-unique-1"]);
  const result = await evaluateAction({
    request: action,
    policy,
    approval,
    now,
    verifyApproval: async () => true,
    consumeApprovalNonce: async (nonce) => {
      if (consumed.has(nonce)) return false;
      consumed.add(nonce);
      return true;
    },
  });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "APPROVAL_NONCE_REPLAYED");
});

test("approval bound to another session is denied", async () => {
  const action = request("submit_purchase");
  const approval = approvalFor(action, { target_session_id: "different-session" });
  const result = await evaluateAction({
    request: action, policy, approval, now,
    verifyApproval: async () => true,
    consumeApprovalNonce: async () => true,
  });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "APPROVAL_SCOPE_MISMATCH");
});

test("missing cryptographic verifier or durable nonce consumer fails closed", async () => {
  const action = request("submit_purchase");
  const result = await evaluateAction({ request: action, policy, approval: approvalFor(action), now });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "APPROVAL_VERIFICATION_UNAVAILABLE");
});

test("expired requests are denied", async () => {
  const action = request("inspect_screen", { expires_at: new Date(now - 1).toISOString() });
  const result = await evaluateAction({ request: action, policy, now });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "REQUEST_EXPIRED");
});

test("request TTL above policy limit is denied", async () => {
  const action = request("inspect_screen", {
    requested_at: new Date(now - 100_000).toISOString(),
    expires_at: new Date(now + 30_000).toISOString(),
  });
  const result = await evaluateAction({ request: action, policy, now });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "REQUEST_TTL_EXCEEDED");
});

test("application outside allowlist is denied", async () => {
  const result = await evaluateAction({
    request: request("inspect_screen", { target_application: "com.unknown.app" }),
    policy, now,
  });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "APPLICATION_NOT_ALLOWLISTED");
});

test("unknown request fields are denied", async () => {
  const result = await evaluateAction({
    request: request("inspect_screen", { execute_arbitrary_code: true }),
    policy, now,
  });
  assert.equal(result.decision, "DENY");
});

test("action digest is deterministic and changes when parameters change", () => {
  const first = request("save_draft");
  const second = request("save_draft", { parameters: { destination: "different" } });
  assert.equal(computeActionDigest(first), computeActionDigest({ ...first }));
  assert.notEqual(computeActionDigest(first), computeActionDigest(second));
});

test("invalid policy TTL configuration fails closed", async () => {
  const invalidPolicy = { ...policy, maxApprovalTtlMs: 0 };
  const result = await evaluateAction({ request: request(), policy: invalidPolicy, now });
  assert.equal(result.decision, "DENY");
  assert.equal(result.reason, "POLICY_CONFIGURATION_INVALID");
});
