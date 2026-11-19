import test from "node:test";
import assert from "node:assert/strict";
import { runGovernedAction } from "../src/orchestrator.mjs";

const request = {
  schema_version: "1.0.0",
  task_id: "task-1",
  action_id: "action-1",
  actor_id: "user-1",
  target_application: "https://example.test",
  target_session_id: "session-1",
  action_type: "navigate",
  parameters: { url: "https://example.test/help" },
  requested_at: "2026-11-19T02:59:00.000Z",
  expires_at: "2026-11-19T03:01:00.000Z",
  observation_id: "observation-1",
};

function dependencies(overrides = {}) {
  const events = [];
  let executions = 0;
  return {
    events,
    get executions() { return executions; },
    options: {
      request,
      requestGrant: async () => ({
        decision: "GRANT_ISSUED",
        grant: { payload: { grant_id: "grant-1" }, signature: "signed" },
      }),
      executor: {
        execute: async () => {
          executions += 1;
          return {
            execution_id: "execution-1",
            action_id: "action-1",
            execution_state: "AWAITING_VERIFICATION",
            verified: false,
          };
        },
      },
      verifyOutcome: async () => ({
        state: "VERIFIED",
        evidence_id: "evidence-1",
      }),
      appendAudit: async (event) => { events.push(event); },
      ...overrides,
    },
  };
}

test("policy denial stops before execution and is audited", async () => {
  const d = dependencies({
    requestGrant: async () => ({ decision: "DENY", reason: "NOT_ALLOWED" }),
  });
  const result = await runGovernedAction(d.options);
  assert.equal(result.state, "DENIED");
  assert.equal(d.executions, 0);
  assert.ok(d.events.some((event) => event.to_state === "DENIED"));
});

test("approval requirement stops before execution", async () => {
  const d = dependencies({
    requestGrant: async () => ({ decision: "REQUIRE_APPROVAL", reason: "HUMAN_APPROVAL_REQUIRED" }),
  });
  const result = await runGovernedAction(d.options);
  assert.equal(result.state, "AWAITING_APPROVAL");
  assert.equal(d.executions, 0);
});

test("grant, execution and independent verification complete the governed lifecycle", async () => {
  const d = dependencies();
  const result = await runGovernedAction(d.options);
  assert.equal(result.state, "VERIFIED");
  assert.equal(result.execution.verified, false);
  assert.equal(result.verification.state, "VERIFIED");
  assert.equal(d.executions, 1);
  assert.deepEqual(
    d.events.map((event) => event.to_state).filter(Boolean),
    ["POLICY_CHECK", "GRANTED", "EXECUTING", "VERIFYING", "VERIFIED"],
  );
});

test("executor UNKNOWN outcome is reconciled before verification", async () => {
  const d = dependencies({
    executor: {
      execute: async () => ({
        execution_id: "execution-unknown",
        action_id: "action-1",
        execution_state: "UNKNOWN",
        verified: false,
      }),
    },
    verifyOutcome: async () => ({ state: "UNKNOWN", reason: "READBACK_UNAVAILABLE" }),
  });
  const result = await runGovernedAction(d.options);
  assert.equal(result.state, "UNKNOWN");
  assert.ok(d.events.some((event) => event.actor === "reconciler"));
});

test("independent verifier NOT_VERIFIED is not converted into success", async () => {
  const d = dependencies({
    verifyOutcome: async () => ({ state: "NOT_VERIFIED", reason: "DESTINATION_MISMATCH" }),
  });
  const result = await runGovernedAction(d.options);
  assert.equal(result.state, "FAILED");
  assert.notEqual(result.state, "VERIFIED");
});

test("malformed grant response fails closed before execution", async () => {
  const d = dependencies({
    requestGrant: async () => ({ decision: "GRANT_ISSUED" }),
  });
  const result = await runGovernedAction(d.options);
  assert.equal(result.state, "DENIED");
  assert.equal(d.executions, 0);
});

test("audit failure before execution prevents the action", async () => {
  const d = dependencies({
    appendAudit: async () => { throw new Error("disk unavailable"); },
  });
  await assert.rejects(() => runGovernedAction(d.options), (error) => {
    assert.equal(error.code, "AUDIT_UNAVAILABLE");
    assert.equal(error.safeToRetry, true);
    assert.equal(error.execution, null);
    return true;
  });
  assert.equal(d.executions, 0);
});

test("audit failure after execution returns an explicit unsafe-to-retry error", async () => {
  let writes = 0;
  const d = dependencies({
    appendAudit: async () => {
      writes += 1;
      if (writes === 5) throw new Error("disk unavailable after action");
    },
  });
  await assert.rejects(() => runGovernedAction(d.options), (error) => {
    assert.equal(error.code, "AUDIT_UNAVAILABLE");
    assert.equal(error.safeToRetry, false);
    assert.ok(error.execution);
    return true;
  });
  assert.equal(d.executions, 1);
});
