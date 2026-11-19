import { createHash } from "node:crypto";

const RISK_CLASSES = new Set(["R0", "R1", "R2", "R3", "R4"]);
const REQUEST_KEYS = new Set([
  "schema_version", "task_id", "action_id", "actor_id", "target_application",
  "target_session_id", "action_type", "parameters", "requested_at", "expires_at",
]);
const APPROVAL_KEYS = new Set([
  "action_digest", "task_id", "actor_id", "target_application", "target_session_id",
  "approved_by", "issued_at", "expires_at", "nonce", "signature",
]);

function isPlainObject(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function assertExactKeys(value, allowed, label) {
  if (!isPlainObject(value)) throw new TypeError(label + " must be a plain object.");
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new TypeError(label + " contains an unknown field.");
  }
}

function canonicalize(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return JSON.stringify(value);
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("Non-finite numbers are not permitted.");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return "[" + value.map(canonicalize).join(",") + "]";
  if (!isPlainObject(value)) throw new TypeError("Only plain JSON values are permitted.");
  const keys = Object.keys(value).sort();
  if (keys.some((key) => ["__proto__", "prototype", "constructor"].includes(key))) {
    throw new TypeError("Unsafe object key.");
  }
  return "{" + keys.map((key) => JSON.stringify(key) + ":" + canonicalize(value[key])).join(",") + "}";
}

function requiredString(value, label, max = 256) {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > max) {
    throw new TypeError(label + " is invalid.");
  }
}

function parseTime(value, label) {
  if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) {
    throw new TypeError(label + " must be a valid timestamp.");
  }
  return Date.parse(value);
}

function deny(reason) {
  return Object.freeze({ decision: "DENY", reason });
}

export function computeActionDigest(request) {
  assertExactKeys(request, REQUEST_KEYS, "Action request");
  const payload = {
    schema_version: request.schema_version,
    task_id: request.task_id,
    action_id: request.action_id,
    actor_id: request.actor_id,
    target_application: request.target_application,
    target_session_id: request.target_session_id,
    action_type: request.action_type,
    parameters: request.parameters,
  };
  return "sha256:" + createHash("sha256").update(canonicalize(payload), "utf8").digest("hex");
}

/**
 * Deterministic policy evaluation only. ELIGIBLE_FOR_GRANT is not an execution
 * credential: a separately authenticated grant issuer and executor must still
 * enforce the decision and bind a one-use grant to the exact action.
 *
 * For R2/R3, verifyApproval must verify a cryptographic signature against a
 * trusted approver key and consumeApprovalNonce must atomically persist the
 * nonce in a durable replay-protection store. Missing callbacks fail closed.
 */
export async function evaluateAction({
  request,
  policy,
  approval = null,
  verifyApproval,
  consumeApprovalNonce,
  now = Date.now(),
}) {
  try {
    assertExactKeys(request, REQUEST_KEYS, "Action request");
    requiredString(request.schema_version, "schema_version", 32);
    requiredString(request.task_id, "task_id");
    requiredString(request.action_id, "action_id");
    requiredString(request.actor_id, "actor_id");
    requiredString(request.target_application, "target_application");
    requiredString(request.target_session_id, "target_session_id");
    requiredString(request.action_type, "action_type", 128);
    if (!isPlainObject(request.parameters)) throw new TypeError("parameters must be a plain object.");
    const requestedAt = parseTime(request.requested_at, "requested_at");
    const expiresAt = parseTime(request.expires_at, "expires_at");
    if (!Number.isFinite(now)) return deny("INVALID_CLOCK");
    if (requestedAt > now + 30_000) return deny("REQUEST_FROM_FUTURE");
    if (expiresAt <= now || expiresAt <= requestedAt) return deny("REQUEST_EXPIRED");
    if (!isPlainObject(policy) || typeof policy.version !== "string" ||
        !Array.isArray(policy.allowedApplications) || !isPlainObject(policy.actionRisk) ||
        !Number.isSafeInteger(policy.maxRequestTtlMs) || policy.maxRequestTtlMs < 1 ||
        !Number.isSafeInteger(policy.maxApprovalTtlMs) || policy.maxApprovalTtlMs < 1) {
      return deny("POLICY_CONFIGURATION_INVALID");
    }
    if (expiresAt - requestedAt > policy.maxRequestTtlMs) return deny("REQUEST_TTL_EXCEEDED");
    if (!policy.allowedApplications.includes(request.target_application)) {
      return deny("APPLICATION_NOT_ALLOWLISTED");
    }
    const risk = policy.actionRisk[request.action_type];
    if (!RISK_CLASSES.has(risk)) return deny("ACTION_NOT_CLASSIFIED_OR_NOT_ALLOWLISTED");
    if (risk === "R4") return deny("PROHIBITED_ACTION");

    const actionDigest = computeActionDigest(request);
    const approvalRequired = risk === "R2" || risk === "R3";
    if (!approvalRequired) {
      return Object.freeze({
        decision: "ELIGIBLE_FOR_GRANT",
        reason: "ALLOWLISTED_LOW_RISK_ACTION",
        policy_version: policy.version,
        risk_class: risk,
        action_digest: actionDigest,
      });
    }

    if (!approval) {
      return Object.freeze({
        decision: "REQUIRE_APPROVAL",
        reason: "HUMAN_APPROVAL_REQUIRED",
        policy_version: policy.version,
        risk_class: risk,
        action_digest: actionDigest,
      });
    }

    assertExactKeys(approval, APPROVAL_KEYS, "Approval");
    requiredString(approval.action_digest, "approval.action_digest", 80);
    requiredString(approval.task_id, "approval.task_id");
    requiredString(approval.actor_id, "approval.actor_id");
    requiredString(approval.target_application, "approval.target_application");
    requiredString(approval.target_session_id, "approval.target_session_id");
    requiredString(approval.approved_by, "approval.approved_by");
    requiredString(approval.nonce, "approval.nonce", 256);
    requiredString(approval.signature, "approval.signature", 4096);

    const approvalIssuedAt = parseTime(approval.issued_at, "approval.issued_at");
    const approvalExpiresAt = parseTime(approval.expires_at, "approval.expires_at");
    if (approvalIssuedAt > now + 30_000 || approvalExpiresAt <= now ||
        approvalExpiresAt <= approvalIssuedAt ||
        approvalExpiresAt - approvalIssuedAt > policy.maxApprovalTtlMs) {
      return deny("APPROVAL_EXPIRED_OR_INVALID_TIME");
    }
    if (approval.action_digest !== actionDigest ||
        approval.task_id !== request.task_id ||
        approval.actor_id !== request.actor_id ||
        approval.target_application !== request.target_application ||
        approval.target_session_id !== request.target_session_id) {
      return deny("APPROVAL_SCOPE_MISMATCH");
    }
    if (typeof verifyApproval !== "function" || typeof consumeApprovalNonce !== "function") {
      return deny("APPROVAL_VERIFICATION_UNAVAILABLE");
    }
    const signatureValid = await verifyApproval(approval);
    if (signatureValid !== true) return deny("APPROVAL_SIGNATURE_INVALID");
    const nonceConsumed = await consumeApprovalNonce(approval.nonce);
    if (nonceConsumed !== true) return deny("APPROVAL_NONCE_REPLAYED");

    return Object.freeze({
      decision: "ELIGIBLE_FOR_GRANT",
      reason: "APPROVAL_VERIFIED_AND_CONSUMED",
      policy_version: policy.version,
      risk_class: risk,
      action_digest: actionDigest,
      approval_reference: approval.nonce,
    });
  } catch (error) {
    return deny("INVALID_REQUEST: " + (error instanceof Error ? error.message : "unknown error"));
  }
}
