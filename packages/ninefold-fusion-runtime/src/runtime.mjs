import { fork } from "node:child_process";
import { randomUUID } from "node:crypto";
import { chmod, mkdir, open, unlink } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const WORKER_PATH = fileURLToPath(new URL("./instance-worker.mjs", import.meta.url));
const INSTANCE_IDS = Array.from({ length: 9 }, (_, index) => "UMIC-" + String(index + 1).padStart(2, "0"));

const CHILD_ENV_ALLOWLIST = ["PATH", "HOME", "TMPDIR", "TEMP", "SystemRoot", "WINDIR", "LANG", "LC_ALL"];

export function buildWorkerEnvironment(source = process.env) {
  return Object.fromEntries(
    CHILD_ENV_ALLOWLIST
      .filter((key) => typeof source[key] === "string")
      .map((key) => [key, source[key]]),
  );
}

export class NinefoldFusionRuntime {
  static async create({
    evidenceRoot,
    runtimeId = "default",
    policyVersion = "NINEFOLD-POLICY-POC-1",
    authorizeInstanceAccess,
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
    if (typeof runtimeId !== "string" || !/^[a-zA-Z0-9_-]{1,64}$/.test(runtimeId)) {
      throw new TypeError("runtimeId must be 1–64 safe alphanumeric, underscore or hyphen characters.");
    }
    await mkdir(evidenceRoot, { recursive: true, mode: 0o700 });
    const runtimeBase = join(evidenceRoot, ".ninefold-fusion-runtime");
    const runEvidenceRoot = join(runtimeBase, runtimeId);
    await mkdir(runEvidenceRoot, { recursive: true, mode: 0o700 });
    await chmod(runtimeBase, 0o700);
    await chmod(runEvidenceRoot, 0o700);
    const lockPath = join(runtimeBase, runtimeId + ".lock");
    let lockHandle;
    try {
      lockHandle = await open(lockPath, "wx", 0o600);
      await lockHandle.writeFile(JSON.stringify({ pid: process.pid, runtimeId, startedAt: new Date().toISOString() }) + "\n");
      await lockHandle.sync();
    } catch (error) {
      if (lockHandle) {
        await lockHandle.close().catch(() => {});
        await unlink(lockPath).catch(() => {});
      }
      if (error?.code === "EEXIST") throw new Error("Runtime evidence namespace is already in use or has a stale lock.");
      throw error;
    }
    const runtime = new NinefoldFusionRuntime({
      evidenceRoot: runEvidenceRoot,
      runtimeId,
      lockPath,
      lockHandle,
      policyVersion,
      authorizeInstanceAccess,
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
        ...buildWorkerEnvironment(),
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
      if (message?.type === "startup-error") {
        entry.readyReject?.(new Error("Instance " + instanceId + " startup failed: " + message.error));
        return;
      }
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
      const exitError = new Error("Instance " + instanceId + " exited (" + code + ", " + signal + ").");
      entry.readyReject?.(exitError);
      this.rejectPending(entry, exitError);
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

  async #request(instanceId, command) {
    if (this.closed) throw new Error("Runtime is closed.");
    const entry = this.instances.get(instanceId);
    if (!entry || entry.status !== "READY" || !entry.child.connected) {
      throw new Error("Instance " + instanceId + " is not READY.");
    }

    if (entry.pending.size >= 64) throw new Error("Instance request concurrency limit reached.");
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

  async openScope({ actorId, instanceId }) {
    if (typeof actorId !== "string" || actorId.length === 0) {
      throw new TypeError("An authenticated actor identity is required.");
    }
    const authorize = this.options.authorizeInstanceAccess;
    const allowed = typeof authorize === "function" && await authorize({
      actorId,
      instanceId,
      resource: "UMIC_INSTANCE_SCOPE",
      policyVersion: this.options.policyVersion,
    }) === true;
    if (!allowed) throw new Error("Instance scope denied by shared governance.");

    return Object.freeze({
      instanceId,
      health: () => this.#request(instanceId, { type: "health" }),
      writeState: (key, value) => this.#request(instanceId, { type: "state.write", key, value }),
      readState: (key) => this.#request(instanceId, { type: "state.read", key }),
      getEvidence: () => this.#request(instanceId, { type: "evidence.list" }),
    });
  }

  async crossInstanceRead({ actorId, sourceInstanceId, destinationInstanceId, key, purpose }) {
    if (sourceInstanceId === destinationInstanceId) throw new Error("Cross-instance access requires two different instances.");
    if (typeof key !== "string" || key.length < 1 || key.length > 128) throw new TypeError("Cross-instance state key is invalid.");
    if (purpose !== undefined && (typeof purpose !== "string" || purpose.length > 256)) throw new TypeError("Cross-instance purpose is invalid.");
    const authorize = this.options.authorizeCrossInstance;
    let allowed = false;
    if (typeof authorize === "function" && typeof actorId === "string" && actorId.length > 0) {
      allowed = await authorize({
        actorId,
        sourceInstanceId,
        destinationInstanceId,
        resource: "state.read",
        key,
        purpose,
        policyVersion: this.options.policyVersion,
      }) === true;
    }

    await this.#request(sourceInstanceId, {
      type: "audit.marker",
      eventType: allowed ? "CROSS_INSTANCE_ACCESS_REQUESTED" : "CROSS_INSTANCE_ACCESS_DENIED",
      details: { sourceInstanceId, destinationInstanceId, resource: "state.read", key, purpose: purpose ?? null },
    });

    if (!allowed) throw new Error("Cross-instance access denied by shared governance.");

    await this.#request(destinationInstanceId, {
      type: "audit.marker",
      eventType: "CROSS_INSTANCE_ACCESS_AUTHORISED",
      details: { sourceInstanceId, destinationInstanceId, resource: "state.read", key, purpose: purpose ?? null },
    });
    return this.#request(destinationInstanceId, { type: "state.read", key });
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

  waitForExit(entry) {
    if (entry.child.exitCode !== null || entry.child.signalCode !== null) {
      return Promise.resolve({ code: entry.child.exitCode, signal: entry.child.signalCode, status: entry.status });
    }
    return new Promise((resolve) => { entry.exitResolve = resolve; });
  }

  async injectFaultForTest(instanceId) {
    if (!this.options.testMode) throw new Error("Fault injection is disabled outside test mode.");
    const entry = this.instances.get(instanceId);
    if (!entry || entry.status !== "READY") throw new Error("Instance is not READY.");
    const exited = this.waitForExit(entry);
    entry.child.kill("SIGKILL");
    return exited;
  }

  async close() {
    if (this.closed) return;
    this.closed = true;
    const entries = [...this.instances.values()];
    try {
      await Promise.all(entries.map(async (entry) => {
        const exited = this.waitForExit(entry);
        if (entry.status !== "READY") {
          if (entry.child.exitCode === null && entry.child.signalCode === null) entry.child.kill("SIGKILL");
          await exited;
          return;
        }
        entry.intentionalStop = true;
        try {
          await this.requestDuringClose(entry, { type: "shutdown" });
        } catch {
          entry.child.kill("SIGKILL");
        }
        await exited;
      }));
    } finally {
      if (this.options.lockHandle) {
        await this.options.lockHandle.close();
        this.options.lockHandle = null;
        await unlink(this.options.lockPath).catch((error) => {
          if (error?.code !== "ENOENT") throw error;
        });
      }
    }
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
