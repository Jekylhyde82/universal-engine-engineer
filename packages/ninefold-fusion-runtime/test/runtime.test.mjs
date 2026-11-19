import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { NinefoldFusionRuntime, buildWorkerEnvironment } from "../src/runtime.mjs";
import { verifyEvidenceEvents } from "../src/evidence.mjs";

async function withRuntime(options, fn) {
  const root = await mkdtemp(join(tmpdir(), "ninefold-runtime-"));
  const runtime = await NinefoldFusionRuntime.create({
    evidenceRoot: root,
    policyVersion: "POLICY-TEST-1",
    requestTimeoutMs: 4_000,
    authorizeInstanceAccess: async ({ actorId, instanceId }) => actorId === instanceId,
    ...options,
  });
  try {
    await fn(runtime, root);
  } finally {
    await runtime.close();
    await rm(root, { recursive: true, force: true });
  }
}

const scope = (runtime, instanceId) =>
  runtime.openScope({ actorId: instanceId, instanceId });

test("child instances receive an allowlisted environment without parent secrets or Node injection flags", () => {
  const childEnv = buildWorkerEnvironment({
    PATH: "/usr/bin",
    HOME: "/tmp",
    API_TOKEN: "must-not-propagate",
    DATABASE_URL: "must-not-propagate",
    NODE_OPTIONS: "--require=unexpected.js",
    NINEFOLD_PARENT_SECRET: "must-not-propagate",
  });
  assert.deepEqual(childEnv, { PATH: "/usr/bin", HOME: "/tmp" });
  assert.equal("API_TOKEN" in childEnv, false);
  assert.equal("DATABASE_URL" in childEnv, false);
  assert.equal("NODE_OPTIONS" in childEnv, false);
});

test("starts nine process-isolated instances using one shared AFI PRIME function version", async () => {
  await withRuntime({}, async (runtime) => {
    const statuses = runtime.getStatuses();
    assert.equal(statuses.length, 9);
    assert.equal(new Set(statuses.map((item) => item.pid)).size, 9);
    assert.ok(statuses.every((item) => item.status === "READY"));
    const health = await Promise.all(statuses.map(async (item) => (await scope(runtime, item.instanceId)).health()));
    assert.ok(health.every((item) => item.fusionFunctionId === "UNIFIED FUSION SYNERGY — AFI PRIME"));
    assert.equal(new Set(health.map((item) => item.fusionFunctionVersion)).size, 1);
  });
});

test("shared governance does not grant an actor another instance's scope", async () => {
  await withRuntime({}, async (runtime) => {
    await assert.rejects(
      runtime.openScope({ actorId: "UMIC-01", instanceId: "UMIC-02" }),
      /Instance scope denied by shared governance/,
    );
  });
});

test("state written in one instance is not visible in another instance", async () => {
  await withRuntime({}, async (runtime) => {
    const one = await scope(runtime, "UMIC-01");
    const two = await scope(runtime, "UMIC-02");
    await one.writeState("private-key", { value: "domain-one" });
    const same = await one.readState("private-key");
    const other = await two.readState("private-key");
    assert.equal(same.found, true);
    assert.deepEqual(same.value, { value: "domain-one" });
    assert.equal(other.found, false);
  });
});

test("each instance maintains a distinct verifiable append-only evidence stream", async () => {
  await withRuntime({}, async (runtime, root) => {
    const oneScope = await scope(runtime, "UMIC-01");
    const twoScope = await scope(runtime, "UMIC-02");
    await oneScope.health();
    await twoScope.health();
    const one = await oneScope.getEvidence();
    const two = await twoScope.getEvidence();
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
    const source = await scope(runtime, "UMIC-01");
    const destination = await scope(runtime, "UMIC-02");
    await destination.writeState("shared-candidate", "secret");
    await assert.rejects(
      runtime.crossInstanceRead({
        actorId: "UMIC-01",
        sourceInstanceId: "UMIC-01",
        destinationInstanceId: "UMIC-02",
        key: "shared-candidate",
        purpose: "test",
      }),
      /denied by shared governance/,
    );
    const sourceEvidence = await source.getEvidence();
    assert.ok(sourceEvidence.events.some((event) => event.eventType === "CROSS_INSTANCE_ACCESS_DENIED"));
  });
});

test("cross-instance access requires and records an explicit governance decision", async () => {
  await withRuntime({
    authorizeCrossInstance: async (request) =>
      request.actorId === "UMIC-01" &&
      request.sourceInstanceId === "UMIC-01" &&
      request.destinationInstanceId === "UMIC-02" &&
      request.resource === "state.read" &&
      request.purpose === "approved-test",
  }, async (runtime) => {
    const source = await scope(runtime, "UMIC-01");
    const destination = await scope(runtime, "UMIC-02");
    await destination.writeState("approved-value", "visible-by-explicit-contract");
    const result = await runtime.crossInstanceRead({
      actorId: "UMIC-01",
      sourceInstanceId: "UMIC-01",
      destinationInstanceId: "UMIC-02",
      key: "approved-value",
      purpose: "approved-test",
    });
    assert.equal(result.found, true);
    assert.equal(result.value, "visible-by-explicit-contract");
    const sourceEvidence = await source.getEvidence();
    const destinationEvidence = await destination.getEvidence();
    assert.ok(sourceEvidence.events.some((event) => event.eventType === "CROSS_INSTANCE_ACCESS_REQUESTED"));
    assert.ok(destinationEvidence.events.some((event) => event.eventType === "CROSS_INSTANCE_ACCESS_AUTHORISED"));
  });
});

test("one instance process fault does not prevent peer instances from operating", async () => {
  await withRuntime({ testMode: true }, async (runtime) => {
    const failedScope = await scope(runtime, "UMIC-03");
    const peerScope = await scope(runtime, "UMIC-04");
    const otherPeerScope = await scope(runtime, "UMIC-09");
    const fault = await runtime.injectFaultForTest("UMIC-03");
    assert.equal(fault.status, "FAULTED");
    await assert.rejects(failedScope.health(), /not READY/);
    const peer = await peerScope.health();
    const otherPeer = await otherPeerScope.health();
    assert.equal(peer.status, "READY");
    assert.equal(otherPeer.status, "READY");
    assert.equal(runtime.getStatuses().filter((item) => item.status === "READY").length, 8);
  });
});

test("evidence tampering is detected when an instance restarts", async () => {
  const root = await mkdtemp(join(tmpdir(), "ninefold-tamper-"));
  const runtime = await NinefoldFusionRuntime.create({
    evidenceRoot: root,
    policyVersion: "POLICY-TEST-1",
    authorizeInstanceAccess: async ({ actorId, instanceId }) => actorId === instanceId,
  });
  const one = await scope(runtime, "UMIC-01");
  await one.health();
  await runtime.close();
  const path = join(root, "EVIDENCE-UMIC-01.jsonl");
  const contents = await readFile(path, "utf8");
  await writeFile(path, contents.replace("INSTANCE_STARTED", "INSTANCE_TAMPERED"));
  await assert.rejects(
    NinefoldFusionRuntime.create({ evidenceRoot: root, policyVersion: "POLICY-TEST-1" }),
    /Evidence digest mismatch/,
  );
  await rm(root, { recursive: true, force: true });
});
