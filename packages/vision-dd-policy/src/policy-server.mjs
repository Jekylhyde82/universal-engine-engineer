import { createServer as createHttpServer } from "node:http";
import { evaluateAction } from "./policy.mjs";
import { createGrant } from "./grant.mjs";

const OUTER_KEYS = new Set(["action_request", "approval"]);

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

async function readJson(request, maxBytes) {
  const declaredLength = Number(request.headers["content-length"]);
  if (Number.isFinite(declaredLength) && declaredLength > maxBytes) {
    const error = new Error("Request body too large.");
    error.statusCode = 413;
    throw error;
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > maxBytes) {
      const error = new Error("Request body too large.");
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  let parsed;
  try { parsed = JSON.parse(Buffer.concat(chunks).toString("utf8")); }
  catch {
    const error = new Error("Request body must be valid JSON.");
    error.statusCode = 400;
    throw error;
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed) ||
      Object.keys(parsed).some((key) => !OUTER_KEYS.has(key)) ||
      !Object.hasOwn(parsed, "action_request")) {
    const error = new Error("Request envelope is invalid.");
    error.statusCode = 400;
    throw error;
  }
  return parsed;
}

/**
 * Creates a policy grant HTTP service. Authentication, approval verification,
 * and durable approval nonce consumption are mandatory injected dependencies;
 * this module deliberately ships with no insecure development fallback.
 *
 * Bind the returned server to loopback or a separately protected private
 * network endpoint. Do not expose it directly to the public internet.
 */
export function createServer({
  policy,
  privateKeyPem,
  authenticateActor,
  verifyApproval,
  approvalNonceLedger,
  clock = Date.now,
  grantTtlMs = 15_000,
  maxBodyBytes = 32_768,
}) {
  if (!policy || typeof policy !== "object" ||
      typeof privateKeyPem !== "string" || !privateKeyPem.trim() ||
      typeof authenticateActor !== "function" ||
      typeof clock !== "function" ||
      !Number.isSafeInteger(maxBodyBytes) || maxBodyBytes < 256 ||
      !Number.isSafeInteger(grantTtlMs) || grantTtlMs < 1 || grantTtlMs > 30_000) {
    throw new TypeError("Policy service configuration is incomplete or invalid.");
  }

  const server = createHttpServer(async (request, response) => {
    if (request.url === "/healthz" && request.method === "GET") {
      return send(response, 200, { status: "ok" });
    }
    if (request.url !== "/v1/grants") return send(response, 404, { error: "NOT_FOUND" });
    if (request.method !== "POST") return send(response, 405, { error: "METHOD_NOT_ALLOWED" });
    if (!String(request.headers["content-type"] || "").toLowerCase().startsWith("application/json")) {
      return send(response, 415, { error: "UNSUPPORTED_MEDIA_TYPE" });
    }

    let actor;
    try { actor = await authenticateActor(request); }
    catch { return send(response, 503, { error: "IDENTITY_PROVIDER_UNAVAILABLE" }); }
    if (!actor || typeof actor.actorId !== "string" || !actor.actorId.trim()) {
      return send(response, 401, { error: "UNAUTHENTICATED" });
    }

    let envelope;
    try { envelope = await readJson(request, maxBodyBytes); }
    catch (error) {
      return send(response, error.statusCode || 400, {
        error: error.statusCode === 413 ? "BODY_TOO_LARGE" : "INVALID_REQUEST",
      });
    }

    const actionRequest = envelope.action_request;
    if (!actionRequest || typeof actionRequest !== "object" ||
        Array.isArray(actionRequest) || actionRequest.actor_id !== actor.actorId) {
      return send(response, 403, { error: "ACTOR_SCOPE_MISMATCH" });
    }

    const now = clock();
    if (!Number.isSafeInteger(now)) return send(response, 503, { error: "CLOCK_UNAVAILABLE" });

    let decision;
    try {
      decision = await evaluateAction({
        request: actionRequest,
        policy,
        approval: envelope.approval ?? null,
        verifyApproval,
        consumeApprovalNonce: approvalNonceLedger?.consume
          ? (nonce) => approvalNonceLedger.consume(nonce)
          : undefined,
        now,
      });
    } catch {
      return send(response, 503, { error: "POLICY_EVALUATION_UNAVAILABLE" });
    }

    if (decision.decision === "DENY") {
      return send(response, 403, { error: "POLICY_DENIED", reason: decision.reason });
    }
    if (decision.decision === "REQUIRE_APPROVAL") {
      return send(response, 409, {
        error: "HUMAN_APPROVAL_REQUIRED",
        policy_version: decision.policy_version,
        risk_class: decision.risk_class,
        action_digest: decision.action_digest,
      });
    }
    if (decision.decision !== "ELIGIBLE_FOR_GRANT") {
      return send(response, 503, { error: "POLICY_DECISION_INVALID" });
    }

    try {
      const grant = createGrant({
        request: actionRequest,
        decision,
        privateKeyPem,
        now,
        ttlMs: grantTtlMs,
      });
      return send(response, 201, {
        decision: "GRANT_ISSUED",
        policy_version: decision.policy_version,
        grant,
      });
    } catch {
      return send(response, 503, { error: "GRANT_ISSUANCE_FAILED" });
    }
  });

  server.requestTimeout = 5_000;
  server.headersTimeout = 6_000;
  server.keepAliveTimeout = 5_000;
  return server;
}
