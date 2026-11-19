import test from "node:test";
import assert from "node:assert/strict";
import { isTerminalActionState, transitionActionState } from "../src/action-state.mjs";

test("only orchestrator advances a proposed task into policy evaluation", () => {
  assert.equal(transitionActionState("PROPOSED", "POLICY_CHECK", "orchestrator").state, "POLICY_CHECK");
  assert.throws(() => transitionActionState("PROPOSED", "POLICY_CHECK", "model"));
});

test("policy service alone can grant, and a grant reference is mandatory", () => {
  assert.throws(() => transitionActionState("POLICY_CHECK", "GRANTED", "policy"));
  assert.equal(
    transitionActionState("POLICY_CHECK", "GRANTED", "policy", { grantReference: "grant-1" }).state,
    "GRANTED",
  );
  assert.throws(() => transitionActionState("POLICY_CHECK", "GRANTED", "executor", { grantReference: "grant-1" }));
});

test("system can durably cancel an action while policy evaluation is pending", () => {
  const result = transitionActionState("POLICY_CHECK", "CANCELLED", "system", {
    reason: "ACTION_CANCELLED_BEFORE_EXECUTION",
  });
  assert.equal(result.state, "CANCELLED");
  assert.equal(isTerminalActionState(result.state), true);
  assert.throws(() => transitionActionState("POLICY_CHECK", "CANCELLED", "executor", {
    reason: "ACTION_CANCELLED_BEFORE_EXECUTION",
  }));
});

test("executor cannot mark an action verified", () => {
  assert.throws(() => transitionActionState("VERIFYING", "VERIFIED", "executor", { verificationEvidence: "evidence-1" }));
});

test("only verifier can mark an action verified and evidence is mandatory", () => {
  assert.throws(() => transitionActionState("VERIFYING", "VERIFIED", "verifier"));
  const result = transitionActionState("VERIFYING", "VERIFIED", "verifier", { verificationEvidence: "evidence-1" });
  assert.equal(result.state, "VERIFIED");
  assert.equal(isTerminalActionState(result.state), true);
});

test("unknown outcome cannot be retried directly", () => {
  assert.throws(() => transitionActionState("UNKNOWN", "EXECUTING", "executor"));
  assert.equal(
    transitionActionState("UNKNOWN", "VERIFYING", "reconciler", { reconciliationReference: "readback-1" }).state,
    "VERIFYING",
  );
});

test("terminal states cannot transition", () => {
  assert.throws(() => transitionActionState("VERIFIED", "EXECUTING", "executor"));
  assert.equal(isTerminalActionState("DENIED"), true);
});

test("denial and failure require an auditable reason", () => {
  assert.throws(() => transitionActionState("POLICY_CHECK", "DENIED", "policy"));
  assert.equal(transitionActionState("POLICY_CHECK", "DENIED", "policy", { reason: "NOT_ALLOWED" }).state, "DENIED");
});
