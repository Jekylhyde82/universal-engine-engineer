import { computeActionDigest } from "./policy.mjs";
import { transitionActionState } from "./action-state.mjs";

function requiredFunction(value, label) {
  if (typeof value !== "function") throw new TypeError(label + " is required.");
}

function abortReason(signal) {
  return typeof signal?.reason === "string" && signal.reason.trim()
    ? signal.reason.slice(0, 160)
    : "ACTION_CANCELLED_BEFORE_EXECUTION";
}

function auditError(error, state, execution, executionAttempted) {
  const wrapped = new Error("Durable audit append failed; action lifecycle cannot be trusted.");
  wrapped.code = "AUDIT_UNAVAILABLE";
  wrapped.lastKnownState = state;
  wrapped.safeToRetry = executionAttempted !== true;
  wrapped.execution = execution;
  wrapped.cause = error;
  return wrapped;
}

/**
 * Orchestrate one governed action without allowing the planner to grant itself
 * authority. Policy grant, executor and independent verifier are separate
 * injected authorities. appendAudit must durably commit each event before the
 * next state/action proceeds.
 *
 * AbortSignal cancellation is honoured only before execution begins. Once an
 * executor may have caused a side effect, cancellation never converts the
 * outcome to CANCELLED and never triggers an automatic retry; reconciliation
 * and independent verification remain mandatory.
 */
export async function runGovernedAction({
  request,
  requestGrant,
  executor,
  verifyOutcome,
  appendAudit,
  approval = null,
  clock = Date.now,
  signal = null,
}) {
  requiredFunction(requestGrant, "requestGrant");
  requiredFunction(executor?.execute, "executor.execute");
  requiredFunction(verifyOutcome, "verifyOutcome");
  requiredFunction(appendAudit, "appendAudit");
  requiredFunction(clock, "clock");
  if (signal !== null && (typeof signal !== "object" ||
      typeof signal.aborted !== "boolean" ||
      typeof signal.addEventListener !== "function")) {
    throw new TypeError("signal must be an AbortSignal when supplied.");
  }

  const actionDigest = computeActionDigest(request);
  const initialTime = clock();
  if (!Number.isSafeInteger(initialTime)) throw new TypeError("Clock is invalid.");

  let state = "PROPOSED";
  let execution = null;
  let executionAttempted = false;
  let verification = null;
  const history = [];

  async function append(event) {
    try {
      const result = await appendAudit(Object.freeze(event));
      if (result === false) throw new Error("Audit store rejected the event.");
    } catch (error) {
      if (error?.code === "ACTION_ID_ALREADY_CLAIMED") {
        error.safeToRetry = false;
        error.lastKnownState = state;
        error.execution = execution;
        try {
          await appendAudit({
            event_type: "ACTION_DUPLICATE_REJECTED",
            task_id: request.task_id,
            action_id: request.action_id,
            actor_id: request.actor_id,
            reason: "ACTION_ID_ALREADY_CLAIMED",
            occurred_at: new Date(clock()).toISOString(),
          });
        } catch {
          // Preserve the original duplicate-claim refusal; never execute.
        }
        throw error;
      }
      throw auditError(error, state, execution, executionAttempted);
    }
  }

  await append({
    event_type: "ACTION_PROPOSED",
    task_id: request.task_id,
    action_id: request.action_id,
    actor_id: request.actor_id,
    target_application: request.target_application,
    action_digest: actionDigest,
    occurred_at: new Date(initialTime).toISOString(),
  });

  async function record(nextState, actor, evidence = {}) {
    const previousState = state;
    const transition = transitionActionState(previousState, nextState, actor, evidence);
    const timestamp = clock();
    if (!Number.isSafeInteger(timestamp)) throw new TypeError("Clock is invalid.");
    await append({
      event_type: "ACTION_STATE_TRANSITION",
      task_id: request.task_id,
      action_id: request.action_id,
      from_state: previousState,
      to_state: transition.state,
      actor,
      evidence: transition.evidence,
      occurred_at: new Date(timestamp).toISOString(),
    });
    state = transition.state;
    history.push(Object.freeze({
      from_state: previousState,
      to_state: state,
      actor,
      evidence: transition.evidence,
    }));
  }

  async function cancelBeforeExecution() {
    await record("CANCELLED", "system", { reason: abortReason(signal) });
    return Object.freeze({ state, execution, verification, history });
  }

  await record("POLICY_CHECK", "orchestrator");
  if (signal?.aborted) return cancelBeforeExecution();

  let policyResult;
  try {
    policyResult = await requestGrant({ request, approval, actionDigest, signal });
  } catch {
    if (signal?.aborted) return cancelBeforeExecution();
    await record("DENIED", "policy", { reason: "POLICY_SERVICE_UNAVAILABLE" });
    return Object.freeze({ state, execution, verification, history });
  }

  if (signal?.aborted) return cancelBeforeExecution();

  if (policyResult?.decision === "DENY") {
    await record("DENIED", "policy", {
      reason: typeof policyResult.reason === "string" ? policyResult.reason : "POLICY_DENIED",
    });
    return Object.freeze({ state, execution, verification, history });
  }
  if (policyResult?.decision === "REQUIRE_APPROVAL") {
    await record("AWAITING_APPROVAL", "policy", {
      reason: typeof policyResult.reason === "string" ? policyResult.reason : "HUMAN_APPROVAL_REQUIRED",
    });
    return Object.freeze({ state, execution, verification, history });
  }

  const grant = policyResult?.grant;
  const grantId = grant?.payload?.grant_id;
  if (policyResult?.decision !== "GRANT_ISSUED" ||
      typeof grantId !== "string" || !grantId.trim() ||
      typeof grant.signature !== "string" || !grant.signature.trim()) {
    await record("DENIED", "policy", { reason: "INVALID_POLICY_GRANT_RESPONSE" });
    return Object.freeze({ state, execution, verification, history });
  }

  await record("GRANTED", "policy", { grantReference: grantId });
  if (signal?.aborted) return cancelBeforeExecution();
  await record("EXECUTING", "executor");

  executionAttempted = true;
  try {
    execution = await executor.execute({ request, grant, signal });
  } catch {
    // An exception or timeout cannot prove that the executor caused no side
    // effect. Preserve uncertainty and require explicit reconciliation.
    await record("UNKNOWN", "system", { reason: "EXECUTOR_EXCEPTION_OUTCOME_UNKNOWN" });
    return Object.freeze({ state, execution, verification, history });
  }

  if (!execution || execution.action_id !== request.action_id ||
      typeof execution.execution_id !== "string" ||
      !["AWAITING_VERIFICATION", "UNKNOWN"].includes(execution.execution_state)) {
    await record("UNKNOWN", "system", { reason: "EXECUTOR_RESULT_INVALID" });
    return Object.freeze({ state, execution, verification, history });
  }

  if (execution.execution_state === "UNKNOWN") {
    await record("UNKNOWN", "executor", { reason: "EXECUTION_OUTCOME_UNKNOWN" });
    await record("VERIFYING", "reconciler", {
      reconciliationReference: execution.execution_id,
    });
  } else {
    await record("VERIFYING", "executor", {
      executionReference: execution.execution_id,
    });
  }

  try {
    verification = await verifyOutcome({ request, execution, grant, signal });
  } catch {
    verification = { state: "UNKNOWN", reason: "VERIFIER_UNAVAILABLE" };
  }

  if (verification?.state === "VERIFIED" &&
      typeof verification.evidence_id === "string" && verification.evidence_id.trim()) {
    await record("VERIFIED", "verifier", {
      verificationEvidence: verification.evidence_id,
    });
  } else if (verification?.state === "NOT_VERIFIED") {
    await record("FAILED", "verifier", {
      reason: typeof verification.reason === "string" ? verification.reason : "POSTCONDITION_NOT_VERIFIED",
    });
  } else {
    await record("UNKNOWN", "verifier", {
      reason: typeof verification?.reason === "string" ? verification.reason : "VERIFICATION_UNAVAILABLE_OR_INVALID",
    });
  }

  return Object.freeze({ state, execution, verification, history });
}
