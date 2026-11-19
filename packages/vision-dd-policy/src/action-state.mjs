const TERMINAL_STATES = new Set(["VERIFIED", "DENIED", "CANCELLED", "EXPIRED", "FAILED"]);

const TRANSITIONS = {
  PROPOSED: { POLICY_CHECK: new Set(["orchestrator"]), CANCELLED: new Set(["human"]) },
  POLICY_CHECK: {
    AWAITING_APPROVAL: new Set(["policy"]),
    GRANTED: new Set(["policy"]),
    DENIED: new Set(["policy"]),
    EXPIRED: new Set(["system"]),
  },
  AWAITING_APPROVAL: {
    GRANTED: new Set(["policy"]),
    DENIED: new Set(["policy"]),
    CANCELLED: new Set(["human"]),
    EXPIRED: new Set(["system"]),
  },
  GRANTED: {
    EXECUTING: new Set(["executor"]),
    CANCELLED: new Set(["human", "policy"]),
    EXPIRED: new Set(["system"]),
  },
  EXECUTING: {
    VERIFYING: new Set(["executor"]),
    UNKNOWN: new Set(["executor", "system"]),
    FAILED: new Set(["executor", "system"]),
  },
  VERIFYING: {
    VERIFIED: new Set(["verifier"]),
    FAILED: new Set(["verifier", "system"]),
    UNKNOWN: new Set(["verifier", "system"]),
  },
  UNKNOWN: {
    VERIFYING: new Set(["reconciler"]),
    RECOVERY_REQUIRED: new Set(["reconciler", "system"]),
  },
  RECOVERY_REQUIRED: {
    VERIFYING: new Set(["reconciler"]),
    FAILED: new Set(["reconciler", "verifier"]),
    CANCELLED: new Set(["human"]),
  },
};

function requiredReference(value, label) {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > 512) {
    throw new TypeError(label + " is required.");
  }
}

/**
 * Pure transition guard. The caller must authenticate actor identity and
 * independently validate grant/evidence references before calling this.
 */
export function transitionActionState(currentState, nextState, actor, evidence = {}) {
  if (TERMINAL_STATES.has(currentState)) {
    throw new Error("Terminal action states cannot transition.");
  }
  if (typeof actor !== "string" || !actor.trim()) {
    throw new TypeError("An authenticated actor role is required.");
  }
  const allowedActors = TRANSITIONS[currentState]?.[nextState];
  if (!allowedActors || !allowedActors.has(actor)) {
    throw new Error("Transition is not permitted for this state and actor.");
  }
  if (nextState === "GRANTED") requiredReference(evidence.grantReference, "grantReference");
  if (nextState === "VERIFYING") requiredReference(evidence.executionReference ?? evidence.reconciliationReference, "executionReference");
  if (nextState === "VERIFIED") requiredReference(evidence.verificationEvidence, "verificationEvidence");
  if (["DENIED", "FAILED", "UNKNOWN", "RECOVERY_REQUIRED"].includes(nextState)) {
    requiredReference(evidence.reason, "reason");
  }
  return Object.freeze({
    state: nextState,
    actor,
    evidence: Object.freeze({ ...evidence }),
  });
}

export function isTerminalActionState(state) {
  return TERMINAL_STATES.has(state);
}
