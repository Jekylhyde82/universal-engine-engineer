import { createServer as createHttpServer } from "node:http";
import { createPublicKey } from "node:crypto";
import { verifyNavigationReadback } from "./verifier.mjs";

const MAX_BODY_BYTES = 16_384;
const ALLOWED_KEYS = new Set(["request", "execution"]);

function send(response, status, payload) {
  const body = JSON.stringify(payload);
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
  });
  response.end(body);
}

async function readEnvelope(request) {
  const declared = Number(request.headers["content-length"]);
  if (Number.isFinite(declared) && declared > MAX_BODY_BYTES) {
    const error = new Error("BODY_TOO_LARGE");
    error.statusCode = 413;
    throw error;
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) {
      const error = new Error("BODY_TOO_LARGE");
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  let value;
  try {
    value = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    const error = new Error("INVALID_JSON");
    error.statusCode = 400;
    throw error;
  }
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).some((key) => !ALLOWED_KEYS.has(key)) ||
      !Object.hasOwn(value, "request") || !Object.hasOwn(value, "execution")) {
    const error = new Error("INVALID_ENVELOPE");
    error.statusCode = 400;
    throw error;
  }
  return value;
}

/**
 * Read-only verification service.
 *
 * The caller supplies only the action request and executor outcome. Evidence
 * is fetched by this service from a separately operated read-only provider;
 * caller-supplied evidence is rejected. The service has no signing key and
 * cannot issue execution grants.
 */
export function createVerifierServer({
  authenticateActor,
  readEvidence,
  evidenceProviderId,
  verifierPublicKeyPem,
  expectedVerifierId,
  clock = Date.now,
  maxEvidenceAgeMs = 5_000,
}) {
  if (typeof authenticateActor !== "function" ||
      typeof readEvidence !== "function" ||
      typeof evidenceProviderId !== "string" || !evidenceProviderId.trim() ||
      typeof verifierPublicKeyPem !== "string" || !verifierPublicKeyPem.trim() ||
      typeof expectedVerifierId !== "string" || !expectedVerifierId.trim() ||
      evidenceProviderId === expectedVerifierId ||
      typeof clock !== "function" ||
      !Number.isSafeInteger(maxEvidenceAgeMs) ||
      maxEvidenceAgeMs < 1 || maxEvidenceAgeMs > 60_000) {
    throw new TypeError("Verifier service requires separate authentication, evidence-provider and verifier identities, a trusted Ed25519 public key and bounded limits.");
  }
  let publicKey;
  try {
    publicKey = createPublicKey(verifierPublicKeyPem);
  } catch {
    throw new TypeError("Verifier public key is invalid.");
  }
  if (publicKey.asymmetricKeyType !== "ed25519") {
    throw new TypeError("Verifier service requires an Ed25519 public key.");
  }

  const server = createHttpServer(async (request, response) => {
    if (request.url === "/healthz" && request.method === "GET") {
      return send(response, 200, { status: "ok", mode: "read-only" });
    }
    if (request.url !== "/v1/verify") return send(response, 404, { error: "NOT_FOUND" });
    if (request.method !== "POST") return send(response, 405, { error: "METHOD_NOT_ALLOWED" });
    const mediaType = String(request.headers["content-type"] || "")
      .split(";")[0].trim().toLowerCase();
    if (mediaType !== "application/json") {
      return send(response, 415, { error: "UNSUPPORTED_MEDIA_TYPE" });
    }

    let actor;
    try { actor = await authenticateActor(request); }
    catch { return send(response, 503, { error: "IDENTITY_PROVIDER_UNAVAILABLE" }); }
    if (!actor || typeof actor.actorId !== "string" || !actor.actorId.trim()) {
      return send(response, 401, { error: "UNAUTHENTICATED" });
    }

    let envelope;
    try { envelope = await readEnvelope(request); }
    catch (error) {
      return send(response, error.statusCode || 400, {
        error: error.message === "BODY_TOO_LARGE" ? "BODY_TOO_LARGE" : "INVALID_REQUEST",
      });
    }
    const { request: actionRequest, execution } = envelope;
    if (!actionRequest || typeof actionRequest !== "object" || Array.isArray(actionRequest) ||
        !execution || typeof execution !== "object" || Array.isArray(execution) ||
        actionRequest.actor_id !== actor.actorId ||
        typeof actionRequest.action_id !== "string" ||
        execution.action_id !== actionRequest.action_id ||
        typeof actionRequest.target_session_id !== "string" ||
        typeof actionRequest.target_application !== "string") {
      return send(response, 403, { error: "ACTOR_OR_ACTION_SCOPE_MISMATCH" });
    }

    const now = clock();
    if (!Number.isSafeInteger(now)) return send(response, 503, { error: "CLOCK_UNAVAILABLE" });
    let evidence;
    try {
      evidence = await readEvidence(Object.freeze({
        actorId: actor.actorId,
        actionId: actionRequest.action_id,
        sessionId: actionRequest.target_session_id,
        targetApplication: actionRequest.target_application,
      }));
    } catch {
      return send(response, 200, { state: "UNKNOWN", reason: "INDEPENDENT_EVIDENCE_UNAVAILABLE" });
    }
    if (!evidence || evidence.providerId !== evidenceProviderId ||
        evidence.providerId === execution.executor ||
        !evidence.readback) {
      return send(response, 200, { state: "UNKNOWN", reason: "EVIDENCE_PROVIDER_PROVENANCE_INVALID" });
    }

    const result = verifyNavigationReadback({
      execution,
      request: actionRequest,
      readback: evidence.readback,
      verifierPublicKeyPem,
      expectedVerifierId,
      now,
      maxEvidenceAgeMs,
    });
    return send(response, 200, result);
  });

  server.requestTimeout = 5_000;
  server.headersTimeout = 6_000;
  server.keepAliveTimeout = 5_000;
  return server;
}
