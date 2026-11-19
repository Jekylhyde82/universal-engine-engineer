import { createPrivateKey, createPublicKey, sign, verify } from "node:crypto";

const READBACK_KEYS = [
  "schema_version", "evidence_id", "action_id", "session_id", "observed_url",
  "observed_at", "verifier_id", "source_adapter", "evidence_method",
];
const METHODS = new Set([
  "READ_ONLY_BROWSER_SESSION_QUERY",
  "AUTHORITATIVE_APPLICATION_STATE_API",
]);
const MAX_FIELD_LENGTHS = {
  schema_version: 32,
  evidence_id: 256,
  action_id: 256,
  session_id: 256,
  observed_url: 2048,
  observed_at: 64,
  verifier_id: 128,
  source_adapter: 128,
  evidence_method: 64,
};

function canonicalize(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return JSON.stringify(value);
  }
  if (typeof value === "number" && Number.isFinite(value)) return JSON.stringify(value);
  if (value && typeof value === "object" &&
      (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null)) {
    const keys = Object.keys(value).sort();
    return "{" + keys.map((key) => JSON.stringify(key) + ":" + canonicalize(value[key])).join(",") + "}";
  }
  throw new TypeError("Readback payload must contain plain JSON values.");
}

function bytes(payload) {
  return Buffer.from(canonicalize(payload), "utf8");
}

function unknown(reason) {
  return Object.freeze({ state: "UNKNOWN", reason });
}

function exactPayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) return false;
  const actual = Object.keys(payload).sort();
  const expected = [...READBACK_KEYS].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]) &&
    READBACK_KEYS.every((key) =>
      typeof payload[key] === "string" &&
      payload[key].trim().length > 0 &&
      payload[key].length <= MAX_FIELD_LENGTHS[key]
    );
}

/**
 * Sign a readback inside a separately authenticated, read-only verifier process.
 * The signing key must not be available to the D.D. executor.
 */
export function signReadback({ payload, privateKeyPem }) {
  if (!exactPayload(payload)) throw new TypeError("Readback payload schema is invalid.");
  const key = createPrivateKey(privateKeyPem);
  if (key.asymmetricKeyType !== "ed25519") throw new TypeError("An Ed25519 verifier key is required.");
  return Object.freeze({
    payload: Object.freeze({ ...payload }),
    signature: sign(null, bytes(payload), key).toString("base64url"),
  });
}

/**
 * Verify independently signed read-only evidence for a browser navigation.
 * The trusted verifier public key and verifier identity must be provisioned
 * out-of-band; the executor must never possess the matching private key.
 */
export function verifyNavigationReadback({
  execution,
  request,
  readback,
  verifierPublicKeyPem,
  expectedVerifierId,
  now = Date.now(),
  maxEvidenceAgeMs = 5_000,
}) {
  try {
    if (!execution || !request || !readback || !readback.payload ||
        typeof readback.signature !== "string" || readback.signature.length > 256) {
      return unknown("EVIDENCE_MISSING_OR_OVERSIZED");
    }
    if (!["AWAITING_VERIFICATION", "UNKNOWN"].includes(execution.execution_state) ||
        execution.action_id !== request.action_id ||
        request.action_type !== "navigate" ||
        typeof execution.executor !== "string" || execution.executor.length > 128 ||
        typeof execution.completed_at !== "string" || execution.completed_at.length > 64 ||
        typeof request.parameters?.url !== "string" || request.parameters.url.length > 2048 ||
        typeof expectedVerifierId !== "string" || !expectedVerifierId.trim() || expectedVerifierId.length > 128 ||
        typeof verifierPublicKeyPem !== "string" || verifierPublicKeyPem.length > 4096 ||
        !Number.isSafeInteger(now) ||
        !Number.isSafeInteger(maxEvidenceAgeMs) || maxEvidenceAgeMs < 1 || maxEvidenceAgeMs > 60_000) {
      return unknown("EXECUTION_OR_REQUEST_SCOPE_INVALID");
    }
    const payload = readback.payload;
    if (!exactPayload(payload) || payload.schema_version !== "1.0.0" ||
        !METHODS.has(payload.evidence_method)) return unknown("EVIDENCE_SCHEMA_INVALID");
    if (payload.action_id !== request.action_id ||
        payload.session_id !== request.target_session_id ||
        payload.verifier_id !== expectedVerifierId ||
        payload.source_adapter === execution.executor ||
        payload.verifier_id === execution.executor) {
      return unknown("EVIDENCE_PROVENANCE_OR_SCOPE_MISMATCH");
    }
    const completedAt = Date.parse(execution.completed_at);
    const observedAt = Date.parse(payload.observed_at);
    if (!Number.isFinite(completedAt) || !Number.isFinite(observedAt) ||
        observedAt < completedAt || observedAt > now + 5_000 ||
        now - observedAt > maxEvidenceAgeMs) {
      return unknown("EVIDENCE_STALE_OR_INVALID_TIME");
    }
    const expectedUrl = new URL(request.parameters?.url);
    const observedUrl = new URL(payload.observed_url);
    const localHttp = expectedUrl.protocol === "http:" &&
      ["localhost", "127.0.0.1", "[::1]"].includes(expectedUrl.hostname);
    if (expectedUrl.username || expectedUrl.password ||
        observedUrl.username || observedUrl.password ||
        (expectedUrl.protocol !== "https:" && !localHttp) ||
        expectedUrl.origin !== request.target_application ||
        observedUrl.origin !== expectedUrl.origin) {
      return unknown("EVIDENCE_URL_INVALID");
    }
    const key = createPublicKey(verifierPublicKeyPem);
    if (key.asymmetricKeyType !== "ed25519" ||
        !verify(null, bytes(payload), key, Buffer.from(readback.signature, "base64url"))) {
      return unknown("EVIDENCE_SIGNATURE_INVALID");
    }
    if (observedUrl.href !== expectedUrl.href) {
      return Object.freeze({
        state: "NOT_VERIFIED",
        reason: "OBSERVED_URL_DIFFERS_FROM_EXPECTED",
        evidence_id: payload.evidence_id,
        verifier_id: payload.verifier_id,
        verified_at: new Date(now).toISOString(),
      });
    }
    return Object.freeze({
      state: "VERIFIED",
      reason: "INDEPENDENT_SIGNED_READBACK_MATCHED",
      evidence_id: payload.evidence_id,
      verifier_id: payload.verifier_id,
      verified_at: new Date(now).toISOString(),
    });
  } catch {
    return unknown("EVIDENCE_VALIDATION_FAILED");
  }
}
