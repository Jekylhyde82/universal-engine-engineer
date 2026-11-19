import {
  createPrivateKey,
  createPublicKey,
  randomUUID,
  sign,
  verify,
} from "node:crypto";
import { computeActionDigest } from "./policy.mjs";

const MAX_GRANT_TTL_MS = 30_000;
const PAYLOAD_KEYS = [
  "schema_version", "grant_id", "policy_version", "action_digest",
  "task_id", "action_id", "actor_id", "target_application",
  "target_session_id", "risk_class", "issued_at", "expires_at",
];

function canonicalize(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return JSON.stringify(value);
  }
  if (typeof value === "number" && Number.isFinite(value)) return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(canonicalize).join(",") + "]";
  if (value && typeof value === "object" &&
      (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null)) {
    const keys = Object.keys(value).sort();
    if (keys.some((key) => ["__proto__", "prototype", "constructor"].includes(key))) {
      throw new TypeError("Unsafe payload key.");
    }
    return "{" + keys.map((key) => JSON.stringify(key) + ":" + canonicalize(value[key])).join(",") + "}";
  }
  throw new TypeError("Grant payload must contain plain JSON values.");
}

function validString(value, max = 256) {
  return typeof value === "string" && value.trim().length > 0 && value.length <= max;
}

function payloadBytes(payload) {
  return Buffer.from(canonicalize(payload), "utf8");
}

function fail(reason) {
  return Object.freeze({ valid: false, reason });
}

/**
 * Create a short-lived Ed25519 grant. The caller must be the authenticated
 * policy service and must pass its final policy decision, not a model proposal.
 */
export function createGrant({ request, decision, privateKeyPem, now = Date.now(), ttlMs = 15_000 }) {
  if (!decision || decision.decision !== "ELIGIBLE_FOR_GRANT") {
    throw new Error("A final eligible policy decision is required.");
  }
  if (!["R0", "R1", "R2", "R3"].includes(decision.risk_class)) {
    throw new Error("Risk class is not grantable.");
  }
  if (["R2", "R3"].includes(decision.risk_class) &&
      decision.reason !== "APPROVAL_VERIFIED_AND_CONSUMED") {
    throw new Error("Consequential actions require verified human approval.");
  }
  if (!Number.isSafeInteger(now) || !Number.isSafeInteger(ttlMs) ||
      ttlMs < 1 || ttlMs > MAX_GRANT_TTL_MS) {
    throw new TypeError("Invalid clock or grant lifetime.");
  }
  if (!validString(decision.policy_version, 80) ||
      !validString(decision.action_digest, 80) ||
      decision.action_digest !== computeActionDigest(request)) {
    throw new Error("Policy decision is not bound to this action.");
  }
  for (const field of [
    "task_id", "action_id", "actor_id", "target_application", "target_session_id",
  ]) {
    if (!validString(request?.[field])) throw new TypeError("Invalid request field: " + field);
  }
  const requestExpiry = Date.parse(request.expires_at);
  if (!Number.isFinite(requestExpiry) || requestExpiry <= now) {
    throw new Error("Action request is expired.");
  }
  const expiresAt = Math.min(now + ttlMs, requestExpiry);
  if (expiresAt <= now) throw new Error("Grant would already be expired.");

  const payload = Object.freeze({
    schema_version: "1.0.0",
    grant_id: randomUUID(),
    policy_version: decision.policy_version,
    action_digest: decision.action_digest,
    task_id: request.task_id,
    action_id: request.action_id,
    actor_id: request.actor_id,
    target_application: request.target_application,
    target_session_id: request.target_session_id,
    risk_class: decision.risk_class,
    issued_at: new Date(now).toISOString(),
    expires_at: new Date(expiresAt).toISOString(),
  });
  const key = createPrivateKey(privateKeyPem);
  if (key.asymmetricKeyType !== "ed25519") throw new TypeError("An Ed25519 private key is required.");
  const signature = sign(null, payloadBytes(payload), key).toString("base64url");
  return Object.freeze({ payload, signature });
}

/**
 * Verify grant signature, freshness and exact action scope, then atomically
 * consume the grant ID in a durable replay-protection store. Missing storage
 * fails closed. The executor must call this immediately before every action.
 */
export async function verifyGrant({
  grant,
  publicKeyPem,
  expectedRequest,
  expectedPolicyVersion,
  consumeGrantId,
  now = Date.now(),
}) {
  try {
    if (!grant || !grant.payload || !validString(grant.signature, 256)) return fail("GRANT_MALFORMED");
    const payload = grant.payload;
    const keys = Object.keys(payload).sort();
    if (keys.length !== PAYLOAD_KEYS.length ||
        keys.some((key, index) => key !== [...PAYLOAD_KEYS].sort()[index])) {
      return fail("GRANT_SCHEMA_INVALID");
    }
    for (const field of PAYLOAD_KEYS) {
      if (!validString(payload[field], field === "action_digest" ? 80 : 256)) {
        return fail("GRANT_FIELD_INVALID");
      }
    }
    if (!Number.isSafeInteger(now)) return fail("INVALID_CLOCK");
    const issuedAt = Date.parse(payload.issued_at);
    const expiresAt = Date.parse(payload.expires_at);
    if (!Number.isFinite(issuedAt) || !Number.isFinite(expiresAt) ||
        issuedAt > now + 5_000 || expiresAt <= now ||
        expiresAt <= issuedAt || expiresAt - issuedAt > MAX_GRANT_TTL_MS) {
      return fail("GRANT_EXPIRED_OR_INVALID_TIME");
    }
    if (payload.policy_version !== expectedPolicyVersion ||
        payload.action_digest !== computeActionDigest(expectedRequest) ||
        payload.task_id !== expectedRequest.task_id ||
        payload.action_id !== expectedRequest.action_id ||
        payload.actor_id !== expectedRequest.actor_id ||
        payload.target_application !== expectedRequest.target_application ||
        payload.target_session_id !== expectedRequest.target_session_id) {
      return fail("GRANT_SCOPE_MISMATCH");
    }
    const key = createPublicKey(publicKeyPem);
    if (key.asymmetricKeyType !== "ed25519") return fail("GRANT_KEY_TYPE_INVALID");
    const signatureBytes = Buffer.from(grant.signature, "base64url");
    if (!verify(null, payloadBytes(payload), key, signatureBytes)) return fail("GRANT_SIGNATURE_INVALID");
    if (typeof consumeGrantId !== "function") return fail("REPLAY_STORE_UNAVAILABLE");
    const consumed = await consumeGrantId(payload.grant_id);
    if (consumed !== true) return fail("GRANT_REPLAYED_OR_STORE_UNAVAILABLE");
    return Object.freeze({ valid: true, payload });
  } catch {
    return fail("GRANT_VALIDATION_FAILED");
  }
}
