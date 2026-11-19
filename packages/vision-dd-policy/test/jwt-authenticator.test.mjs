import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import { createJwtBearerAuthenticator } from "../src/jwt-authenticator.mjs";

const now = Date.parse("2026-11-19T04:00:00.000Z");
const issuer = "https://identity.example";
const audience = "ninefold-vision-dd";
const { publicKey, privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const { privateKey: otherPrivateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const jwk = {
  ...publicKey.export({ format: "jwk" }),
  kid: "key-1",
  use: "sig",
  alg: "RS256",
  key_ops: ["verify"],
};

function encode(value) {
  return Buffer.from(JSON.stringify(value), "utf8").toString("base64url");
}

function makeToken({
  claims = {},
  key = privateKey,
  header = { alg: "RS256", kid: "key-1", typ: "JWT" },
} = {}) {
  const payload = {
    iss: issuer,
    aud: audience,
    sub: "user-17",
    iat: Math.floor(now / 1000) - 30,
    exp: Math.floor(now / 1000) + 300,
    ...claims,
  };
  const input = encode(header) + "." + encode(payload);
  return input + "." + sign("RSA-SHA256", Buffer.from(input, "ascii"), key).toString("base64url");
}

function createAuthenticator({ keys = [jwk], fetchImpl, clock = () => now } = {}) {
  const fetcher = fetchImpl ?? (async (_url, options) => {
    assert.equal(options.redirect, "error");
    return new Response(JSON.stringify({ keys }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });
  return createJwtBearerAuthenticator({
    issuer,
    audience,
    jwksUrl: "https://identity.example/.well-known/jwks.json",
    clock,
    fetchImpl: fetcher,
  });
}

function request(token) {
  return { headers: { authorization: "Bearer " + token } };
}

test("valid RS256 bearer token maps to issuer-scoped actor identity", async () => {
  const authenticate = createAuthenticator();
  const actor = await authenticate(request(makeToken()));
  assert.equal(actor.actorId, issuer + "|user-17");
  assert.equal(actor.issuer, issuer);
  assert.equal(actor.subject, "user-17");
  assert.equal(actor.audience, audience);
});

test("issuer matching is exact and does not silently append a slash", async () => {
  const authenticate = createAuthenticator();
  const actor = await authenticate(request(makeToken({ claims: { iss: issuer + "/" } })));
  assert.equal(actor, null);
});

test("wrong audience, expired token, stale token and future-issued token are rejected", async () => {
  const authenticate = createAuthenticator();
  const cases = [
    { aud: "another-app" },
    { exp: Math.floor(now / 1000) - 1 },
    { iat: Math.floor(now / 1000) - 2_000 },
    { iat: Math.floor(now / 1000) + 60 },
  ];
  for (const claims of cases) {
    assert.equal(await authenticate(request(makeToken({ claims }))), null);
  }
});

test("multi-audience token requires the configured authorized party", async () => {
  const authenticate = createAuthenticator();
  assert.equal(await authenticate(request(makeToken({
    claims: { aud: [audience, "another-app"] },
  }))), null);
  assert.ok(await authenticate(request(makeToken({
    claims: { aud: [audience, "another-app"], azp: audience },
  }))));
});

test("unsupported algorithms and untrusted JWT header key references are rejected", async () => {
  const authenticate = createAuthenticator();
  assert.equal(await authenticate(request(makeToken({ header: { alg: "none", kid: "key-1" } }))), null);
  assert.equal(await authenticate(request(makeToken({
    header: { alg: "RS256", kid: "key-1", jku: "https://attacker.example/jwks.json" },
  }))), null);
});

test("signature from a different key is rejected", async () => {
  const authenticate = createAuthenticator();
  assert.equal(await authenticate(request(makeToken({ key: otherPrivateKey }))), null);
});

test("malformed bearer headers and malformed compact tokens are rejected", async () => {
  const authenticate = createAuthenticator();
  for (const authorization of ["Basic abc", "Bearer", "Bearer a.b", "Bearer " + "x".repeat(20_000)]) {
    assert.equal(await authenticate({ headers: { authorization } }), null);
  }
});

test("JWKS response must be HTTPS JSON with public RSA keys", async () => {
  assert.throws(() => createJwtBearerAuthenticator({
    issuer, audience, jwksUrl: "http://identity.example/jwks",
  }), /HTTPS/i);
  const privateJwk = { ...jwk, d: "must-not-be-published" };
  const authenticate = createAuthenticator({ keys: [privateJwk] });
  assert.equal(await authenticate(request(makeToken())), null);
});

test("unknown key IDs trigger at most one refresh per cooldown window", async () => {
  let calls = 0;
  const authenticate = createAuthenticator({
    fetchImpl: async () => {
      calls += 1;
      return new Response(JSON.stringify({ keys: [jwk] }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  });
  await authenticate(request(makeToken()));
  const unknown = makeToken({ header: { alg: "RS256", kid: "random-kid", typ: "JWT" } });
  assert.equal(await authenticate(request(unknown)), null);
  assert.equal(await authenticate(request(unknown)), null);
  assert.equal(calls, 2);
});

test("JWKS fetch failures fail authentication closed", async () => {
  const authenticate = createAuthenticator({
    fetchImpl: async () => new Response("unavailable", { status: 503 }),
  });
  assert.equal(await authenticate(request(makeToken())), null);
});
