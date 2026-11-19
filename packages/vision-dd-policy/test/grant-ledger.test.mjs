import test from "node:test";
import assert from "node:assert/strict";
import { chmod, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { generateKeyPairSync } from "node:crypto";
import { computeActionDigest } from "../src/policy.mjs";
import { createGrant, verifyGrant } from "../src/grant.mjs";
import { FileNonceLedger } from "../src/nonce-ledger.mjs";

const now = Date.parse("2026-11-19T03:00:00.000Z");
const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const publicKeyPem = publicKey.export({ type: "spki", format: "pem" });
const privateKeyPem = privateKey.export({ type: "pkcs8", format: "pem" });

function action(overrides = {}) {
  return {
    schema_version: "1.0.0",
    task_id: "task-1",
    action_id: "action-1",
    actor_id: "user-1",
    target_application: "https://example.test",
    target_session_id: "session-1",
    action_type: "navigate",
    parameters: { url: "https://example.test/help" },
    requested_at: new Date(now - 1000).toISOString(),
    expires_at: new Date(now + 20_000).toISOString(),
    ...overrides,
  };
}

function decision(request) {
  return {
    decision: "ELIGIBLE_FOR_GRANT",
    policy_version: "policy-7",
    risk_class: "R1",
    action_digest: computeActionDigest(request),
  };
}

async function withTempDir(fn) {
  const directory = await mkdtemp(join(tmpdir(), "vision-dd-ledger-"));
  try { await fn(directory); } finally { await rm(directory, { recursive: true, force: true }); }
}

test("grant is signed and bound to exact action, actor, app, session and policy", async () => {
  const request = action();
  const grant = createGrant({
    request,
    decision: decision(request),
    privateKeyPem,
    now,
    ttlMs: 10_000,
  });
  const result = await verifyGrant({
    grant, publicKeyPem, expectedRequest: request,
    expectedPolicyVersion: "policy-7", now: now + 1,
    consumeGrantId: async () => true,
  });
  assert.equal(result.valid, true, result.reason);
  assert.equal(result.payload.action_digest, computeActionDigest(request));
});

test("grant signature tampering is rejected", async () => {
  const request = action();
  const grant = createGrant({ request, decision: decision(request), privateKeyPem, now });
  const tampered = { ...grant, payload: { ...grant.payload, target_session_id: "other" } };
  assert.equal((await verifyGrant({ grant: tampered, publicKeyPem, expectedRequest: request, expectedPolicyVersion: "policy-7", now })).valid, false);
});

test("grant for another action or policy is rejected", async () => {
  const request = action();
  const grant = createGrant({ request, decision: decision(request), privateKeyPem, now });
  assert.equal((await verifyGrant({
    grant, publicKeyPem, expectedRequest: action({ action_id: "different-action" }),
    expectedPolicyVersion: "policy-7", now,
  })).valid, false);
  assert.equal((await verifyGrant({
    grant, publicKeyPem, expectedRequest: request,
    expectedPolicyVersion: "policy-8", now,
  })).valid, false);
});

test("expired grant is rejected", async () => {
  const request = action();
  const grant = createGrant({ request, decision: decision(request), privateKeyPem, now, ttlMs: 1000 });
  assert.equal((await verifyGrant({
    grant, publicKeyPem, expectedRequest: request,
    expectedPolicyVersion: "policy-7", now: now + 1000,
  })).valid, false);
});

test("grant cannot be issued from a non-eligible policy decision", () => {
  const request = action();
  assert.throws(() => createGrant({
    request, decision: { ...decision(request), decision: "REQUIRE_APPROVAL" },
    privateKeyPem, now,
  }));
});

test("grant nonce is consumed once through the durable ledger", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileNonceLedger(join(directory, "nonces.jsonl"));
    assert.equal(await ledger.consume("nonce-1"), true);
    assert.equal(await ledger.consume("nonce-1"), false);
    assert.equal(await ledger.consume("nonce-2"), true);
  });
});

test("nonce ledger survives process-style reconstruction", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "nonces.jsonl");
    assert.equal(await new FileNonceLedger(path).consume("nonce-1"), true);
    assert.equal(await new FileNonceLedger(path).consume("nonce-1"), false);
  });
});

test("concurrent nonce consumption has exactly one winner", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileNonceLedger(join(directory, "nonces.jsonl"));
    const results = await Promise.all(Array.from({ length: 8 }, () => ledger.consume("same-nonce")));
    assert.equal(results.filter(Boolean).length, 1);
  });
});

test("partial final ledger write is recovered without accepting an incomplete nonce", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "nonces.jsonl");
    const ledger = new FileNonceLedger(path);
    assert.equal(await ledger.consume("complete"), true);
    const before = await readFile(path, "utf8");
    const { appendFile } = await import("node:fs/promises");
    await appendFile(path, '{"partial":');
    assert.equal(await ledger.consume("next"), true);
    const after = await readFile(path, "utf8");
    assert.ok(after.startsWith(before));
    assert.ok(after.endsWith("\n"));
    assert.equal(await new FileNonceLedger(path).consume("next"), false);
  });
});

test("tampered complete ledger record fails closed", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "nonces.jsonl");
    const ledger = new FileNonceLedger(path);
    await ledger.consume("nonce-1");
    const { writeFile } = await import("node:fs/promises");
    await writeFile(path, '{"nonce":"forged","timestamp":1,"previous_hash":"bad","hash":"bad"}\n');
    await assert.rejects(() => ledger.consume("nonce-2"), /integrity/i);
  });
});

test("grant replay protection fails closed when the replay store is missing", async () => {
  const request = action();
  const grant = createGrant({ request, decision: decision(request), privateKeyPem, now });
  const result = await verifyGrant({
    grant, publicKeyPem, expectedRequest: request,
    expectedPolicyVersion: "policy-7", now,
  });
  assert.equal(result.valid, false);
  assert.equal(result.reason, "REPLAY_STORE_UNAVAILABLE");
});

test("a valid grant can be consumed only once", async () => {
  const request = action();
  const grant = createGrant({ request, decision: decision(request), privateKeyPem, now });
  const consumed = new Set();
  const consumeGrantId = async (id) => {
    if (consumed.has(id)) return false;
    consumed.add(id);
    return true;
  };
  const first = await verifyGrant({
    grant, publicKeyPem, expectedRequest: request,
    expectedPolicyVersion: "policy-7", now, consumeGrantId,
  });
  const second = await verifyGrant({
    grant, publicKeyPem, expectedRequest: request,
    expectedPolicyVersion: "policy-7", now, consumeGrantId,
  });
  assert.equal(first.valid, true);
  assert.equal(second.valid, false);
  assert.equal(second.reason, "GRANT_REPLAYED_OR_STORE_UNAVAILABLE");
});

test("consequential grant cannot be issued without verified human approval", () => {
  const request = action();
  assert.throws(() => createGrant({
    request,
    decision: { ...decision(request), risk_class: "R3", reason: "ALLOWLISTED_LOW_RISK_ACTION" },
    privateKeyPem, now,
  }), /human approval/i);
});

test("nonce ledger refuses directories with group or world permissions", async () => {
  await withTempDir(async (directory) => {
    await chmod(directory, 0o755);
    const ledger = new FileNonceLedger(join(directory, "nonces.jsonl"));
    await assert.rejects(() => ledger.consume("nonce-1"), /private 0700/i);
  });
});

test("nonce ledger fails closed before exceeding its configured size limit", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileNonceLedger(join(directory, "nonces.jsonl"), { maxLedgerBytes: 128 });
    await assert.rejects(() => ledger.consume("nonce-1"), /size limit/i);
  });
});
