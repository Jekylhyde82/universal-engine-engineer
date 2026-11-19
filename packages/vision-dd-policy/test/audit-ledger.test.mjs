import test from "node:test";
import assert from "node:assert/strict";
import { chmod, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { FileActionAuditLedger } from "../src/audit-ledger.mjs";

async function withTempDir(fn) {
  const directory = await mkdtemp(join(tmpdir(), "vision-dd-audit-"));
  try { await fn(directory); }
  finally { await rm(directory, { recursive: true, force: true }); }
}

test("audit ledger appends and verifies a hash-chained event sequence", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileActionAuditLedger(join(directory, "events.jsonl"));
    const first = await ledger.append({ event_type: "ACTION_PROPOSED", action_id: "a-1" });
    const second = await ledger.append({ event_type: "ACTION_STATE_TRANSITION", action_id: "a-1", to_state: "POLICY_CHECK" });
    assert.equal(first.sequence, 1);
    assert.equal(second.sequence, 2);
    const result = await ledger.verifyIntegrity();
    assert.equal(result.valid, true);
    assert.equal(result.records, 2);
    assert.ok(result.head_hash.startsWith("sha256:"));
  });
});

test("audit ledger detects a modified complete record", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "events.jsonl");
    const ledger = new FileActionAuditLedger(path);
    await ledger.append({ event_type: "ACTION_PROPOSED", action_id: "a-1" });
    const bytes = await readFile(path, "utf8");
    await writeFile(path, bytes.replace("a-1", "a-2"), { mode: 0o600 });
    await assert.rejects(() => ledger.verifyIntegrity(), /corrupt|hash/i);
  });
});

test("audit ledger recovers an incomplete trailing record without accepting it", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "events.jsonl");
    const ledger = new FileActionAuditLedger(path);
    await ledger.append({ event_type: "ACTION_PROPOSED", action_id: "a-1" });
    await writeFile(path, (await readFile(path)) + '{"partial":', { mode: 0o600 });
    const recovered = await ledger.verifyIntegrity();
    assert.equal(recovered.records, 1);
    await ledger.append({ event_type: "ACTION_STATE_TRANSITION", action_id: "a-1", to_state: "POLICY_CHECK" });
    assert.equal((await ledger.verifyIntegrity()).records, 2);
  });
});

test("concurrent audit appends receive unique sequential positions", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileActionAuditLedger(join(directory, "events.jsonl"));
    const results = await Promise.all(
      Array.from({ length: 12 }, (_, index) => ledger.append({
        event_type: "ACTION_STATE_TRANSITION", action_id: "a-" + index,
      })),
    );
    assert.deepEqual(results.map((item) => item.sequence).sort((a, b) => a - b),
      Array.from({ length: 12 }, (_, index) => index + 1));
    assert.equal((await ledger.verifyIntegrity()).records, 12);
  });
});

test("audit ledger refuses insecure directory permissions", async () => {
  await withTempDir(async (directory) => {
    await chmod(directory, 0o755);
    const ledger = new FileActionAuditLedger(join(directory, "events.jsonl"));
    await assert.rejects(() => ledger.append({ event_type: "ACTION_PROPOSED" }), /private 0700/i);
  });
});

test("audit ledger enforces its configured storage limit before append", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileActionAuditLedger(join(directory, "events.jsonl"), { maxLedgerBytes: 128, maxEventBytes: 128 });
    await assert.rejects(
      () => ledger.append({ event_type: "ACTION_PROPOSED", action_id: "capacity-action", detail: "x".repeat(50) }),
      /size limit/i,
    );
  });
});

test("audit ledger rejects non-JSON and unsafe event values", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileActionAuditLedger(join(directory, "events.jsonl"));
    await assert.rejects(() => ledger.append({ event_type: "BAD", callback: () => true }), /JSON|plain/i);
    const unsafe = JSON.parse('{"event_type":"BAD","__proto__":{"polluted":true}}');
    await assert.rejects(() => ledger.append(unsafe), /unsafe|plain/i);
  });
});

test("audit ledger rejects blank complete records instead of silently skipping them", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "events.jsonl");
    const ledger = new FileActionAuditLedger(path);
    await ledger.append({ event_type: "ACTION_PROPOSED", action_id: "a-1" });
    const bytes = await readFile(path, "utf8");
    await writeFile(path, bytes.replaceAll("\n", "\n\n"));
    await assert.rejects(() => ledger.verifyIntegrity(), /blank record/i);
  });
});

test("audit ledger rejects non-canonical JSON record encodings", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "events.jsonl");
    const ledger = new FileActionAuditLedger(path);
    await ledger.append({ event_type: "ACTION_PROPOSED", action_id: "a-1" });
    const bytes = await readFile(path, "utf8");
    await writeFile(path, " " + bytes);
    await assert.rejects(() => ledger.verifyIntegrity(), /non-canonical/i);
  });
});

test("audit ledger fails closed on a pre-existing stale lock", async () => {
  await withTempDir(async (directory) => {
    const path = join(directory, "events.jsonl");
    await writeFile(path + ".lock", "stale-lock", { mode: 0o600 });
    const ledger = new FileActionAuditLedger(path, { lockTimeoutMs: 30, retryMs: 5 });
    await assert.rejects(() => ledger.append({ event_type: "ACTION_PROPOSED", action_id: "stale-lock-action" }), /lock timeout/i);
  });
});

test("audit ledger atomically refuses a duplicate action claim", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileActionAuditLedger(join(directory, "events.jsonl"));
    await ledger.append({
      event_type: "ACTION_PROPOSED", task_id: "task-1", action_id: "action-1",
    });
    await assert.rejects(
      () => ledger.append({
        event_type: "ACTION_PROPOSED", task_id: "task-1", action_id: "action-1",
      }),
      (error) => error.code === "ACTION_ID_ALREADY_CLAIMED",
    );
    assert.equal((await ledger.verifyIntegrity()).records, 1);
  });
});

test("audit ledger allows the same action ID under a different task ID", async () => {
  await withTempDir(async (directory) => {
    const ledger = new FileActionAuditLedger(join(directory, "events.jsonl"));
    await ledger.append({
      event_type: "ACTION_PROPOSED", task_id: "task-1", action_id: "action-1",
    });
    await ledger.append({
      event_type: "ACTION_PROPOSED", task_id: "task-2", action_id: "action-1",
    });
    assert.equal((await ledger.verifyIntegrity()).records, 2);
  });
});
