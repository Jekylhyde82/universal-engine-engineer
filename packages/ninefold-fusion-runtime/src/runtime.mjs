import { fork } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const WORKER_PATH = fileURLToPath(new URL("./instance-worker.mjs", import.meta.url));
const INSTANCE_IDS = Array.from({ length: 9 }, (_, index) => "UMIC-" + String(index + 1).padStart(2, "0"));

export class NinefoldFusionRuntime {
  static async create({
    evidenceRoot,
    policyVersion = "NINEFOLD-POLICY-POC-1",
    authorizeCrossInstance,
    requestTimeoutMs = 3_000,
    testMode = false,
  }) {
    if (typeof evidenceRoot !== "string" || evidenceRoot.length === 0) {
      throw new TypeError("A dedicated evidenceRoot directory is required.");
    }
    if (typeof policyVersion !== "string" || policyVersion.length === 0) {
      throw new TypeError("A shared policyVersion is required.");
    }
    await mkdir(evidenceRoot, { recursive: true, mode: 0o700 });
    const runtime = new NinefoldFusionRuntime({
      evidenceRoot,
      policyVersion,
      authorizeCrossInstance,
      requestTimeoutMs,
      testMode,
    });
    await runtime.start();
    return runtime;
  }

  constructor(options) {
    this.options = options;
    this.instances = new Map();
    this.closed = false;
  }

  async start() {
    try {
      await Promise.all(INSTANCE_IDS.map((instanceId) => this.startInstance(instanceId)));
    } catch (error) {
      await this.close();
      throw error;
    }
  }

  async startInstance(instanceId) {
    const evidencePath = join(this.options.evidenceRoot, "EVIDENCE-" + instanceId + ".jsonl");
    const child = fork(WORKER_PATH, [], {
      env: {
        ...process.env,
        NINEFOLD_INSTANCE_ID: instanceId,
        NINEFOLD_EVIDENCE_PATH: evidencePath,
        NINEFOLD_POLICY_VERSION: this.options.policyVersion,
      },
      stdio: ["ignore", "ignore", "ignore", "ipc"],
      execArgv: [],
    });

    const entry = {
      instanceId,
      child,
      pid: null,
      status: "STARTING",
      pending: new Map(),
      nextRequest: 1,
      intentionalStop: false,
      evidencePath,
    };
    this.instances.set(instanceId, entry);

    child.on("message", (message) => {
      if (message?.type === "ready") {
        entry.pid = message.pid;
        entry.status = "READY";
        entry.fusionFunctionVersion = message.fusionFunctionVersion;
        entry.fusionFunctionId = message.fusionFunctionId;
        entry.readyResolve?.(message);
        return;
      }
      if (message?.type !== "response") return;
      const pending = entry.pending.get(message.requestId);
      if (!pending) return;
      clearTimeout(pending.timer);
      entry.pending.delete(message.requestId);
      if (message.ok) pending.resolve(message.result);
      else pending.reject(new Error(message.error ?? "Instance command rejected."));
    });

    child.on("error", (error) => {
      entry.status = "FAULTED";
      entry.readyReject?.(error);
      this.rejectPending(entry, new Error("Instance process error: " + error.message));
    });

    child.on("exit", (code, signal) => {
      entry.status = entry.intentionalStop ? "STOPPED" : "FAULTED";
      this.rejectPending(entry, new Error("Instance " + instanceId + " exited (" + code + ", " + signal + ")."));
      entry.exitResolve?.({ code, signal, status: entry.status });
    });

    const readyPromise = new Promise((resolve, reject) => {
      entry.readyResolve = resolve;
      entry.readyReject = reject;
    });
    const readyTimer = setTimeout(() => {
      entry.readyReject?.(new Error("Instance " + instanceId + " startup timed out."));
      child.kill("SIGKILL");
    }, this.options.requestTimeoutMs);

    try {
      await readyPromise;
    } finally {
      clearTimeout(readyTimer);
      entry.readyResolve = null;
      entry.readyReject = null;
    }
  }

  rejectPending(entry, error) {
    for (const pending of entry.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    entry.pending.clear();
  }

  async request(instanceId, command) {
    if (this.closed) throw new Error("Runtime is closed.");
    const entry = this.instances.get(instanceId);
    if (!entry || entry.status !== "READY" || !entry.child.connected) {
      throw new Error("Instance " + instanceId + " is not READY.");
    }

    const requestId = instanceId + "-" + entry.nextRequest++ + "-" + randomUUID();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        entry.pending.delete(requestId);
        entry.status = "FAULTED";
        entry.child.kill("SIGKILL");
        reject(new Error("Instance " + instanceId + " request timed out; outcome is UNKNOWN."));
      }, this.options.requestTimeoutMs);
      entry.pending.set(requestId, { resolve, reject, timer });
      entry.child.send({ requestId, instanceId, command }, (error) => {
        if (!error) return;
        clearTimeout(timer);
        entry.pending.delete(requestId);
        reject(error);
      });
    });
  }

  async health(instanceId) {
    return this.request(instanceId, { type: "health" });
  }

  async writeState(instanceId, key, value) {
    return this.request(instanceId, { type: "state.write", key, value });
  }

  async readState(instanceId, key) {
    return this.request(instanceId, { type: "state.read", key });
  }

  async getEvidence(instanceId) {
    return this.request(instanceId, { type: "evidence.list" });
  }

  async crossInstanceRead({ sourceInstanceId, destinationInstanceId, key, purpose }) {
    if (sourceInstanceId === destinationInstanceId) throw new Error("Cross-instance access requires two different instances.");
    const authorize = this.options.authorizeCrossInstance;
    let allowed = false;
    if (typeof authorize === "function") {
      allowed = await authorize({
        sourceInstanceId,
        destinationInstanceId,
        resource: "state.read",
        key,
        purpose,
        policyVersion: this.options.policyVersion,
      }) === true;
    }

    await this.request(sourceInstanceId, {
      type: "audit.marker",
      eventType: allowed ? "CROSS_INSTANCE_ACCESS_REQUESTED" : "CROSS_INSTANCE_ACCESS_DENIED",
      details: { sourceInstanceId, destinationInstanceId, resource: "state.read", key, purpose: purpose ?? null },
    });

    if (!allowed) throw new Error("Cross-instance access denied by shared governance.");

    await this.request(destinationInstanceId, {
      type: "audit.marker",
      eventType: "CROSS_INSTANCE_ACCESS_AUTHORISED",
      details: { sourceInstanceId, destinationInstanceId, resource: "state.read", key, purpose: purpose ?? null },
    });
    return this.readState(destinationInstanceId, key);
  }

  getStatuses() {
    return INSTANCE_IDS.map((instanceId) => {
      const entry = this.instances.get(instanceId);
      return {
        instanceId,
        pid: entry?.pid ?? null,
        status: entry?.status ?? "MISSING",
        fusionFunctionVersion: entry?.fusionFunctionVersion ?? null,
        evidencePath: entry?.evidencePath ?? null,
      };
    });
  }

  async injectFaultForTest(instanceId) {
    if (!this.options.testMode) throw new Error("Fault injection is disabled outside test mode.");
    const entry = this.instances.get(instanceId);
    if (!entry || entry.status !== "READY") throw new Error("Instance is not READY.");
    const exited = new Promise((resolve) => { entry.exitResolve = resolve; });
    entry.child.kill("SIGKILL");
    return exited;
  }

  async close() {
    if (this.closed) return;
    this.closed = true;
    const entries = [...this.instances.values()];
    await Promise.all(entries.map(async (entry) => {
      if (entry.status !== "READY") {
        if (entry.child.exitCode === null && entry.child.signalCode === null) entry.child.kill("SIGKILL");
        return;
      }
      entry.intentionalStop = true;
      try {
        await this.requestDuringClose(entry, { type: "shutdown" });
      } catch {
        entry.child.kill("SIGKILL");
      }
    }));
  }

  async requestDuringClose(entry, command) {
    const requestId = entry.instanceId + "-shutdown-" + randomUUID();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        entry.pending.delete(requestId);
        reject(new Error("Instance shutdown timed out."));
      }, this.options.requestTimeoutMs);
      entry.pending.set(requestId, { resolve, reject, timer });
      entry.child.send({ requestId, instanceId: entry.instanceId, command }, (error) => {
        if (!error) return;
        clearTimeout(timer);
        entry.pending.delete(requestId);
        reject(error);
      });
    });
  }
}
