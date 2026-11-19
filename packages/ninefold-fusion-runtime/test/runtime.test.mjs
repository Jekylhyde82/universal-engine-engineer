import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { NinefoldFusionRuntime } from "../src/runtime.mjs";
import { verifyEvidenceEvents } from "../src/evidence.mjs";

async function withRuntime(options, fn) {
  const root = await mkdtemp(join(tmpdir(), "ninefold-runtime-"));
  const runtime = await NinefoldFusionRuntime.create({
    evidenceRoot: root,
    policyVersion: "POLICY-TEST-1",
    requestTimeoutMs: 4_000,
    ...options,
  });
  try {
    await fn(runtime, root);
  } finally {
    await runtime.close();
    await rm(root, { recursive: true, force: true });
  }
}

test("starts nine process-isolated instances using one shared AFI PRIME function version", async () => {
  await withRuntime({}, async (runtime) => {
    const statuses = runtime.getStatuses();
    assert.equal(statuses.length, 9);
    assert.equal(new Set(statuses.map((item) => item.pid)).size, 9);
    assert.ok(statuses.every((item) => item.status === "READY"));
    const health = await Promise.all(statuses.map((item) => runtime.health(item.instanceId)));
    assert.ok(health.every((item) => item.fusionFunctionId === "UNIFIED FUSION SYNERGY — AFI PRIME"));
    assert.equal(new Set(health.map((item) => item.fusionFunctionVersion)).size, 1);
  });
});

test("state written in one instance is not visible in another instance", async () => {
  await withRuntime({}, async (runtime) => {
    await runtime.writeState("UMIC-01", "private-key", { value: "domain-one" });
    const same = await runtime.readState("UMIC-01", "private-key");
    const other = await runtime.readState("UMIC-02", "private-key");
    assert.equal(same.found, true);
    assert.deepEqual(same.value, { value: "domain-one" });
    assert.equal(other.found, false);
  });
});

test("each instance maintains a distinct verifiable append-only evidence stream", async () => {
  await withRuntime({}, async (runtime, root) => {
    await runtime.health("UMIC-01");
    await runtime.health("UMIC-02");
    const one = await runtime.getEvidence("UMIC-01");
    const two = await runtime.getEvidence("UMIC-02");
    assert.notEqual(one.events[0].instanceId, two.events[0].instanceId);
    assert.notEqual(one.events[0].hash, two.events[0].hash);
    assert.equal(verifyEvidenceEvents(one.events, "UMIC-01").valid, true);
    assert.equal(verifyEvidenceEvents(two.events, "UMIC-02").valid, true);
    assert.notEqual(
      join(root, "EVIDENCE-UMIC-01.jsonl"),
      join(root, "EVIDENCE-UMIC-02.jsonl"),
    );
  });
});

test("cross-instance access is denied without an explicit governance authorisation", async () => {
  await withRuntime({}, async (runtime) => {
    await runtime.writeState("UMIC-02", "shared-candidate", "secret");
    await assert.rejects(
      runtime.crossInstanceRead({
        sourceInstanceId: "UMIC-01",
        destinationInstanceId: "UMIC-02",
        key: "shared-candidate",
        purpose: "test",
      }),
      /denied by shared governance/,
    );
    const sourceEvidence = await runtime.getEvidence("UMIC-01");
    assert.ok(sourceEvidence.events.some((event) => event.eventType === "CROSS_INSTANCE_ACCESS_DENIED"));
  });
});

test("cross-instance access requires and records an explicit governance decision", async () => {
  await withRuntime({
    authorizeCrossInstance: async (request) =>
      request.sourceInstanceId === "UMIC-01" &&
      request.destinationInstanceId === "UMIC-02" &&
      request.resource === "state.read" &&
      request.purpose === "approved-test",
  }, async (runtime) => {
    await runtime.writeState("UMIC-02", "approved-value", "visible-by-explicit-contract");
    const result = await runtime.crossInstanceRead({
      sourceInstanceId: "UMIC-01",
      destinationInstanceId: "UMIC-02",
      key: "approved-value",
      purpose: "approved-test",
    });
    assert.equal(result.found, true);
    assert.equal(result.value, "visible-by-explicit-contract");
    const source = await runtime.getEvidence("UMIC-01");
    const destination = await runtime.getEvidence("UMIC-02");
    assert.ok(source.events.some((event) => event.eventType === "CROSS_INSTANCE_ACCESS_REQUESTED"));
    assert.ok(destination.events.some((event) => event.eventType === "CROSS_INSTANCE_ACCESS_AUTHORISED"));
  });
});

test("one instance process fault does not prevent peer instances from operating", async () => {
  await withRuntime({ testMode: true }, async (runtime) => {
    const fault = await runtime.injectFaultForTest("UMIC-03");
    assert.equal(fault.status, "FAULTED");
    await assert.rejects(runtime.health("UMIC-03"), /not READY/);
    const peer = await runtime.health("UMIC-04");
    const otherPeer = await runtime.health("UMIC-09");
    assert.equal(peer.status, "READY");
    assert.equal(otherPeer.status, "READY");
    assert.equal(runtime.getStatuses().filter((item) => item.status === "READY").length, 8);
  });
});

test("evidence tampering is detected when an instance restarts", async () => {
  const root = await mkdtemp(join(tmpdir(), "ninefold-tamper-"));
  let runtime = await NinefoldFusionRuntime.create({ evidenceRoot: root, policyVersion: "POLICY-TEST-1" });
  await runtime.health("UMIC-01");
  await runtime.close();
  const path = join(root, "EVIDENCE-UMIC-01.jsonl");
  const contents = await readFile(path, "utf8");
  await (await import("node:fs/promises")).writeFile(path, contents.replace("INSTANCE_STARTED", "INSTANCE_TAMPERED"));
  await assert.rejects(
    NinefoldFusionRuntime.create({ evidenceRoot: root, policyVersion: "POLICY-TEST-1" }),
    /Evidence digest mismatch/,
  );
  await rm(root, { recursive: true, force: true });
});
