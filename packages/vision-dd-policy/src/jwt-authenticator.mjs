import { createPublicKey, verify } from "node:crypto";

const MAX_TOKEN_BYTES = 16 * 1024;
const MAX_JWKS_BYTES = 64 * 1024;
const MAX_JWKS_KEYS = 32;
const MAX_KID_LENGTH = 128;
const HEADER_KEYS = new Set(["alg", "kid", "typ"]);
const PRIVATE_JWK_FIELDS = ["d", "p", "q", "dp", "dq", "qi", "oth"];

function plainObject(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function decodeSegment(segment, maxBytes, label) {
  if (typeof segment !== "string" || segment.length === 0 ||
      segment.length > maxBytes * 2 || !/^[A-Za-z0-9_-]+$/.test(segment)) {
    throw new Error(label + " encoding is invalid.");
  }
  const bytes = Buffer.from(segment, "base64url");
  if (bytes.length > maxBytes || bytes.toString("base64url") !== segment) {
    throw new Error(label + " encoding is non-canonical or oversized.");
  }
  return bytes;
}

function parseJsonSegment(segment, maxBytes, label) {
  const bytes = decodeSegment(segment, maxBytes, label);
  let value;
  try { value = JSON.parse(bytes.toString("utf8")); }
  catch { throw new Error(label + " JSON is invalid."); }
  if (!plainObject(value)) throw new Error(label + " must be a JSON object.");
  return value;
}

function validText(value, maxLength) {
  return typeof value === "string" && value.trim().length > 0 &&
    value.length <= maxLength && !/[\u0000-\u001f\u007f]/.test(value);
}

function validateConfig({ issuer, audience, jwksUrl, clock, cacheTtlMs, maxTokenAgeMs, fetchImpl }) {
  if (!validText(issuer, 512) || !validText(audience, 256) ||
      typeof jwksUrl !== "string" || typeof clock !== "function" ||
      !Number.isSafeInteger(cacheTtlMs) || cacheTtlMs < 1_000 || cacheTtlMs > 900_000 ||
      !Number.isSafeInteger(maxTokenAgeMs) || maxTokenAgeMs < 1_000 || maxTokenAgeMs > 3_600_000 ||
      (fetchImpl !== undefined && typeof fetchImpl !== "function")) {
    throw new TypeError("JWT authenticator configuration is invalid.");
  }
  const issuerUrl = new URL(issuer);
  const jwks = new URL(jwksUrl);
  if (issuerUrl.protocol !== "https:" || issuerUrl.username || issuerUrl.password ||
      issuerUrl.search || issuerUrl.hash || jwks.protocol !== "https:" ||
      jwks.username || jwks.password || jwks.hash) {
    throw new TypeError("Issuer and JWKS endpoints must be fixed HTTPS URLs without credentials or fragments.");
  }
  return { issuer, jwksUrl: jwks.href, fetchImpl: fetchImpl ?? globalThis.fetch };
}

async function readBoundedResponse(response) {
  if (response.body?.getReader) {
    const reader = response.body.getReader();
    const chunks = [];
    let size = 0;
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > MAX_JWKS_BYTES) {
          await reader.cancel();
          throw new Error("JWKS response exceeds its size limit.");
        }
        chunks.push(Buffer.from(value));
      }
    } finally {
      reader.releaseLock();
    }
    return Buffer.concat(chunks, size);
  }
  const body = Buffer.from(await response.arrayBuffer());
  if (body.byteLength > MAX_JWKS_BYTES) throw new Error("JWKS response exceeds its size limit.");
  return body;
}

function importJwksKeys(document) {
  if (!plainObject(document) || !Array.isArray(document.keys) ||
      document.keys.length < 1 || document.keys.length > MAX_JWKS_KEYS) {
    throw new Error("JWKS document schema is invalid.");
  }
  const keys = new Map();
  for (const jwk of document.keys) {
    if (!plainObject(jwk) || jwk.kty !== "RSA" ||
        !validText(jwk.kid, MAX_KID_LENGTH) ||
        (jwk.alg !== undefined && jwk.alg !== "RS256") ||
        (jwk.use !== undefined && jwk.use !== "sig") ||
        (jwk.key_ops !== undefined && (!Array.isArray(jwk.key_ops) || !jwk.key_ops.includes("verify"))) ||
        PRIVATE_JWK_FIELDS.some((field) => Object.hasOwn(jwk, field)) ||
        typeof jwk.n !== "string" || typeof jwk.e !== "string") {
      throw new Error("JWKS contains an invalid or non-public signing key.");
    }
    if (keys.has(jwk.kid)) throw new Error("JWKS contains duplicate key identifiers.");
    const key = createPublicKey({ key: jwk, format: "jwk" });
    const modulusLength = key.asymmetricKeyDetails?.modulusLength;
    if (key.asymmetricKeyType !== "rsa" || !Number.isSafeInteger(modulusLength) || modulusLength < 2048) {
      throw new Error("JWKS signing key must be RSA-2048 or stronger.");
    }
    keys.set(jwk.kid, key);
  }
  return keys;
}

/**
 * Create a provider-configured RS256 JWT bearer authenticator.
 *
 * The caller must configure the exact issuer, audience and fixed HTTPS JWKS
 * endpoint for the selected identity provider. This module verifies tokens;
 * it does not provision identities, decide application roles or replace
 * provider-side MFA, account lifecycle or device posture controls.
 */
export function createJwtBearerAuthenticator({
  issuer,
  audience,
  jwksUrl,
  clock = Date.now,
  cacheTtlMs = 300_000,
  maxTokenAgeMs = 900_000,
  fetchImpl,
}) {
  const config = validateConfig({ issuer, audience, jwksUrl, clock, cacheTtlMs, maxTokenAgeMs, fetchImpl });
  if (typeof config.fetchImpl !== "function") throw new TypeError("A fetch implementation is required.");

  let cachedKeys = new Map();
  let cacheExpiresAt = 0;
  let refreshPromise = null;
  let unknownKidRefreshAt = Number.NEGATIVE_INFINITY;

  async function refreshKeys() {
    if (refreshPromise) return refreshPromise;
    refreshPromise = (async () => {
      const response = await config.fetchImpl(config.jwksUrl, {
        method: "GET",
        headers: { accept: "application/json, application/jwk-set+json" },
        redirect: "error",
        signal: AbortSignal.timeout(3_000),
      });
      if (!response || response.ok !== true) throw new Error("JWKS provider unavailable.");
      const contentType = String(response.headers?.get?.("content-type") || "").split(";")[0].trim().toLowerCase();
      if (!["application/json", "application/jwk-set+json"].includes(contentType)) {
        throw new Error("JWKS provider returned an unsupported media type.");
      }
      const declaredLength = Number(response.headers?.get?.("content-length"));
      if (Number.isFinite(declaredLength) && declaredLength > MAX_JWKS_BYTES) {
        throw new Error("JWKS response exceeds its size limit.");
      }
      const body = await readBoundedResponse(response);
      const document = JSON.parse(body.toString("utf8"));
      const nextKeys = importJwksKeys(document);
      if (nextKeys.size === 0) throw new Error("JWKS contains no usable keys.");
      cachedKeys = nextKeys;
      const now = clock();
      if (!Number.isSafeInteger(now)) throw new Error("Clock unavailable.");
      cacheExpiresAt = now + cacheTtlMs;
    })();
    try { await refreshPromise; }
    finally { refreshPromise = null; }
  }

  async function getSigningKey(kid) {
    let now = clock();
    if (!Number.isSafeInteger(now)) throw new Error("Clock unavailable.");
    let refreshed = false;
    if (now >= cacheExpiresAt) {
      await refreshKeys();
      refreshed = true;
      now = clock();
      if (!Number.isSafeInteger(now)) throw new Error("Clock unavailable.");
    }
    let key = cachedKeys.get(kid);
    // Unknown key IDs are attacker-controlled input. Refresh at most once per
    // cooldown window so random kid values cannot force a JWKS fetch per token.
    if (!key && !refreshed && now - unknownKidRefreshAt >= 10_000) {
      unknownKidRefreshAt = now;
      await refreshKeys();
      key = cachedKeys.get(kid);
    }
    if (!key) throw new Error("JWT signing key is not trusted.");
    return key;
  }

  return async function authenticateActor(request) {
    try {
      const authorization = request?.headers?.authorization;
      if (typeof authorization !== "string" || authorization.length > MAX_TOKEN_BYTES + 16) return null;
      const match = /^Bearer ([A-Za-z0-9._~-]+)$/.exec(authorization);
      if (!match) return null;
      const token = match[1];
      if (Buffer.byteLength(token, "utf8") > MAX_TOKEN_BYTES) return null;
      const parts = token.split(".");
      if (parts.length !== 3) return null;

      const header = parseJsonSegment(parts[0], 2_048, "JWT header");
      if (Object.keys(header).some((key) => !HEADER_KEYS.has(key)) ||
          header.alg !== "RS256" || !validText(header.kid, MAX_KID_LENGTH) ||
          (header.typ !== undefined && header.typ !== "JWT")) return null;
      const claims = parseJsonSegment(parts[1], 8_192, "JWT claims");
      const signature = decodeSegment(parts[2], 2_048, "JWT signature");
      const key = await getSigningKey(header.kid);
      const signingInput = Buffer.from(parts[0] + "." + parts[1], "ascii");
      if (!verify("RSA-SHA256", signingInput, key, signature)) return null;

      const now = clock();
      if (!Number.isSafeInteger(now)) return null;
      const nowSeconds = Math.floor(now / 1000);
      const audienceMatches = claims.aud === config.audience ||
        (Array.isArray(claims.aud) && claims.aud.includes(config.audience));
      if (claims.iss !== config.issuer || !audienceMatches ||
          !validText(claims.sub, 256) ||
          !Number.isSafeInteger(claims.exp) || !Number.isSafeInteger(claims.iat) ||
          claims.exp <= nowSeconds || claims.iat > nowSeconds + 30 ||
          nowSeconds - claims.iat > maxTokenAgeMs / 1000 ||
          claims.exp <= claims.iat || claims.exp - claims.iat > 3_600) {
        return null;
      }
      if (claims.nbf !== undefined &&
          (!Number.isSafeInteger(claims.nbf) || claims.nbf > nowSeconds + 30)) return null;
      if (Array.isArray(claims.aud) && claims.aud.length > 1 && claims.azp !== config.audience) return null;

      return Object.freeze({
        actorId: config.issuer + "|" + claims.sub,
        issuer: config.issuer,
        subject: claims.sub,
        audience: config.audience,
        issuedAt: claims.iat,
        expiresAt: claims.exp,
      });
    } catch {
      return null;
    }
  };
}
