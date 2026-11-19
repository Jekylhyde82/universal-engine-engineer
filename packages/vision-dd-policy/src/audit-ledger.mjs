import { createHash, randomUUID } from "node:crypto";
import { mkdir, lstat, readFile, open, truncate, unlink } from "node:fs/promises";
import { dirname } from "node:path";

const ZERO_HASH = "0".repeat(64);
const RECORD_KEYS = new Set(["sequence", "occurred_at", "event", "previous_hash", "hash"]);

function plainObject(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function canonicalize(value, depth = 0) {
  if (depth > 16) throw new TypeError("Maximum audit event nesting depth exceeded.");
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return JSON.stringify(value);
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("Audit events cannot contain non-finite numbers.");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    if (value.length > 256) throw new TypeError("Audit event array is too large.");
    return "[" + value.map((item) => canonicalize(item, depth + 1)).join(",") + "]";
  }
  if (!plainObject(value)) throw new TypeError("Audit event must contain plain JSON values.");
  const keys = Object.keys(value).sort();
  if (keys.length > 128 || keys.some((key) => ["__proto__", "prototype", "constructor"].includes(key))) {
    throw new TypeError("Audit event contains too many or unsafe object keys.");
  }
  return "{" + keys.map((key) =>
    JSON.stringify(key) + ":" + canonicalize(value[key], depth + 1)
  ).join(",") + "}";
}

function hashRecord(body) {
  return "sha256:" + createHash("sha256").update(canonicalize(body), "utf8").digest("hex");
}

function assertRecord(record, expectedSequence, previousHash) {
  if (!plainObject(record) || Object.keys(record).length !== RECORD_KEYS.size ||
      Object.keys(record).some((key) => !RECORD_KEYS.has(key))) {
    throw new Error("Audit ledger record schema is corrupt.");
  }
  if (record.sequence !== expectedSequence ||
      typeof record.occurred_at !== "string" ||
      !Number.isFinite(Date.parse(record.occurred_at)) ||
      record.previous_hash !== previousHash ||
      typeof record.hash !== "string" ||
      !/^sha256:[a-f0-9]{64}$/.test(record.hash) ||
      !plainObject(record.event)) {
    throw new Error("Audit ledger sequence or hash chain is corrupt.");
  }
  const body = {
    sequence: record.sequence,
    occurred_at: record.occurred_at,
    event: record.event,
    previous_hash: record.previous_hash,
  };
  if (hashRecord(body) !== record.hash) throw new Error("Audit ledger record hash mismatch.");
}

export class FileActionAuditLedger {
  constructor(path, {
    lockTimeoutMs = 2_000,
    retryMs = 10,
    clock = Date.now,
    maxLedgerBytes = 64 * 1024 * 1024,
    maxEventBytes = 16 * 1024,
  } = {}) {
    if (typeof path !== "string" || !path.trim() ||
        !Number.isSafeInteger(lockTimeoutMs) || lockTimeoutMs < 1 ||
        !Number.isSafeInteger(retryMs) || retryMs < 1 ||
        typeof clock !== "function" ||
        !Number.isSafeInteger(maxLedgerBytes) || maxLedgerBytes < 128 ||
        !Number.isSafeInteger(maxEventBytes) || maxEventBytes < 128 ||
        maxEventBytes > maxLedgerBytes) {
      throw new TypeError("Audit ledger configuration is invalid.");
    }
    this.path = path;
    this.lockPath = path + ".lock";
    this.lockTimeoutMs = lockTimeoutMs;
    this.retryMs = retryMs;
    this.clock = clock;
    this.maxLedgerBytes = maxLedgerBytes;
    this.maxEventBytes = maxEventBytes;
  }

  async #ensurePrivateDirectory() {
    const directory = dirname(this.path);
    await mkdir(directory, { recursive: true, mode: 0o700 });
    const info = await lstat(directory);
    if (!info.isDirectory() || info.isSymbolicLink() || (info.mode & 0o077) !== 0) {
      throw new Error("Audit ledger directory must be a private 0700 directory.");
    }
  }

  async #acquireLock() {
    const deadline = Date.now() + this.lockTimeoutMs;
    while (true) {
      try {
        const handle = await open(this.lockPath, "wx", 0o600);
        await handle.writeFile(JSON.stringify({ pid: process.pid, token: randomUUID() }), "utf8");
        await handle.sync();
        return handle;
      } catch (error) {
        if (error?.code !== "EEXIST") throw error;
        if (Date.now() >= deadline) {
          throw new Error("Audit ledger lock timeout; refusing concurrent or stale writes.");
        }
        await new Promise((resolve) => setTimeout(resolve, this.retryMs));
      }
    }
  }

  async #withLock(callback) {
    await this.#ensurePrivateDirectory();
    const lock = await this.#acquireLock();
    try {
      return await callback();
    } finally {
      await lock.close().catch(() => {});
      await unlink(this.lockPath).catch(() => {});
    }
  }

  async #readAndRecover() {
    let bytes;
    try {
      const info = await lstat(this.path);
      if (!info.isFile() || info.isSymbolicLink() || (info.mode & 0o077) !== 0) {
        throw new Error("Audit ledger must be a private 0600 regular file, not a symlink.");
      }
      if (info.size > this.maxLedgerBytes) {
        throw new Error("Audit ledger size limit exceeded; refusing to bypass evidence retention.");
      }
      bytes = await readFile(this.path);
    } catch (error) {
      if (error?.code === "ENOENT") return { records: 0, previousHash: ZERO_HASH, size: 0 };
      throw error;
    }

    if (bytes.length > 0 && bytes[bytes.length - 1] !== 0x0a) {
      const lastNewline = bytes.lastIndexOf(0x0a);
      const recoveredLength = lastNewline + 1;
      const handle = await open(this.path, "r+");
      try {
        await handle.truncate(recoveredLength);
        await handle.sync();
      } finally {
        await handle.close();
      }
      bytes = bytes.subarray(0, recoveredLength);
    }

    const lines = bytes.toString("utf8").split("\n").filter(Boolean);
    let previousHash = ZERO_HASH;
    let sequence = 0;
    for (const line of lines) {
      let record;
      try { record = JSON.parse(line); }
      catch { throw new Error("Audit ledger contains malformed JSON."); }
      sequence += 1;
      assertRecord(record, sequence, previousHash);
      previousHash = record.hash;
    }
    return { records: sequence, previousHash, size: bytes.length };
  }

  async append(event) {
    if (!plainObject(event)) throw new TypeError("Audit event must be a plain object.");
    const canonicalEvent = canonicalize(event);
    if (Buffer.byteLength(canonicalEvent, "utf8") > this.maxEventBytes) {
      throw new TypeError("Audit event exceeds its configured size limit.");
    }
    const safeEvent = JSON.parse(canonicalEvent);
    return this.#withLock(async () => {
      const { records, previousHash, size } = await this.#readAndRecover();
      const timestamp = this.clock();
      if (!Number.isSafeInteger(timestamp)) throw new TypeError("Audit ledger clock is invalid.");
      const body = {
        sequence: records + 1,
        occurred_at: new Date(timestamp).toISOString(),
        event: safeEvent,
        previous_hash: previousHash,
      };
      const record = { ...body, hash: hashRecord(body) };
      const line = JSON.stringify(record) + "\n";
      const lineBytes = Buffer.byteLength(line, "utf8");
      if (size + lineBytes > this.maxLedgerBytes) {
        throw new Error("Audit ledger size limit reached; refusing to drop evidence.");
      }
      const handle = await open(this.path, "a", 0o600);
      try {
        await handle.writeFile(line, "utf8");
        await handle.sync();
      } finally {
        await handle.close();
      }
      return Object.freeze({
        sequence: record.sequence,
        reference: "audit:" + record.sequence + ":" + record.hash,
        hash: record.hash,
      });
    });
  }

  async verifyIntegrity() {
    return this.#withLock(async () => {
      const result = await this.#readAndRecover();
      return Object.freeze({
        valid: true,
        records: result.records,
        head_hash: result.previousHash === ZERO_HASH ? null : result.previousHash,
        size_bytes: result.size,
      });
    });
  }
}
