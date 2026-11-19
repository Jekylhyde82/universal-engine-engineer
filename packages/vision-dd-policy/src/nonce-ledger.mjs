import { createHash } from "node:crypto";
import { open, mkdir, lstat, readFile, unlink } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";

const ZERO_HASH = "0".repeat(64);

function digest(nonce, timestamp, previousHash) {
  return createHash("sha256")
    .update(nonce + "\n" + timestamp + "\n" + previousHash, "utf8")
    .digest("hex");
}

function validateRecord(record, expectedPreviousHash) {
  if (!record || Object.keys(record).sort().join(",") !== "hash,nonce,previous_hash,timestamp" ||
      typeof record.nonce !== "string" ||
      !Number.isSafeInteger(record.timestamp) ||
      record.previous_hash !== expectedPreviousHash ||
      typeof record.hash !== "string" ||
      !/^[a-f0-9]{64}$/.test(record.hash) ||
      digest(record.nonce, record.timestamp, record.previous_hash) !== record.hash) {
    throw new Error("Nonce ledger integrity validation failed.");
  }
}

/**
 * Single-host durable replay ledger.
 *
 * Assumptions: the ledger directory is private to the service account and
 * resides on a local filesystem with atomic exclusive file creation and
 * fsync semantics. Stale locks fail closed and require operator recovery.
 * This hash chain detects accidental corruption but is NOT independently
 * tamper-proof; production audit checkpoints must be externally anchored.
 */
export class FileNonceLedger {
  constructor(path, { lockTimeoutMs = 2_000, retryMs = 10, clock = Date.now, maxLedgerBytes = 64 * 1024 * 1024 } = {}) {
    if (typeof path !== "string" || !path.trim()) throw new TypeError("Ledger path is required.");
    if (!Number.isSafeInteger(lockTimeoutMs) || lockTimeoutMs < 1 ||
        !Number.isSafeInteger(retryMs) || retryMs < 1 || typeof clock !== "function" ||
        !Number.isSafeInteger(maxLedgerBytes) || maxLedgerBytes < 128) {
      throw new TypeError("Invalid ledger options.");
    }
    this.path = resolve(path);
    this.lockPath = this.path + ".lock";
    this.lockTimeoutMs = lockTimeoutMs;
    this.retryMs = retryMs;
    this.clock = clock;
    this.maxLedgerBytes = maxLedgerBytes;
  }

  async #ensurePrivateDirectory() {
    const directory = dirname(this.path);
    await mkdir(directory, { recursive: true, mode: 0o700 });
    const info = await lstat(directory);
    if (!info.isDirectory() || info.isSymbolicLink() || (process.platform !== "win32" && (info.mode & 0o077) !== 0)) {
      throw new Error("Nonce ledger directory must be a private 0700 directory.");
    }
  }

  async #acquireLock() {
    const deadline = Date.now() + this.lockTimeoutMs;
    while (true) {
      let handle;
      try {
        handle = await open(this.lockPath, "wx", 0o600);
        await handle.writeFile(String(process.pid) + "\n");
        await handle.sync();
        return handle;
      } catch (error) {
        if (handle) {
          await handle.close().catch(() => {});
          await unlink(this.lockPath).catch(() => {});
        }
        if (error?.code !== "EEXIST") throw error;
        if (Date.now() >= deadline) {
          throw new Error("Nonce ledger lock unavailable; refusing to bypass replay protection.");
        }
        await delay(this.retryMs);
      }
    }
  }

  async #readAndRecover() {
    let bytes;
    try {
      const info = await lstat(this.path);
      if (!info.isFile() || info.isSymbolicLink() || (process.platform !== "win32" && (info.mode & 0o077) !== 0)) {
        throw new Error("Nonce ledger must be a private 0600 regular file, not a symlink.");
      }
      if (info.size > this.maxLedgerBytes) throw new Error("Nonce ledger size limit exceeded; refusing to disable replay protection.");
      bytes = await readFile(this.path);
    } catch (error) {
      if (error?.code === "ENOENT") return { records: [], previousHash: ZERO_HASH, size: 0 };
      throw error;
    }

    const lastNewline = bytes.lastIndexOf(0x0a);
    if (bytes.length > 0 && lastNewline !== bytes.length - 1) {
      const handle = await open(this.path, "r+");
      try {
        await handle.truncate(lastNewline + 1);
        await handle.sync();
      } finally {
        await handle.close();
      }
      bytes = bytes.subarray(0, lastNewline + 1);
    }
    const text = bytes.toString("utf8");
    const lines = text.length === 0 ? [] : text.slice(0, -1).split("\n");
    if (lines.some((line) => line.length === 0)) {
      throw new Error("Nonce ledger contains an unexpected blank record.");
    }
    const records = [];
    const seen = new Set();
    let previousHash = ZERO_HASH;
    for (const line of lines) {
      let record;
      try { record = JSON.parse(line); } catch {
        throw new Error("Nonce ledger contains an invalid complete record.");
      }
      if (JSON.stringify(record) !== line) {
        throw new Error("Nonce ledger record encoding is non-canonical.");
      }
      validateRecord(record, previousHash);
      if (seen.has(record.nonce)) throw new Error("Nonce ledger contains a duplicate nonce.");
      seen.add(record.nonce);
      records.push(record);
      previousHash = record.hash;
    }
    return { records, previousHash, size: bytes.length };
  }

  async consume(nonce) {
    if (typeof nonce !== "string" || nonce.trim().length === 0 || nonce.length > 256) {
      throw new TypeError("Nonce is invalid.");
    }
    await this.#ensurePrivateDirectory();
    const lock = await this.#acquireLock();
    try {
      const { records, previousHash, size } = await this.#readAndRecover();
      if (records.some((record) => record.nonce === nonce)) return false;
      const timestamp = this.clock();
      if (!Number.isSafeInteger(timestamp)) throw new Error("Ledger clock is invalid.");
      const record = {
        nonce,
        timestamp,
        previous_hash: previousHash,
        hash: digest(nonce, timestamp, previousHash),
      };
      const line = JSON.stringify(record) + "\n";
      if (size + Buffer.byteLength(line, "utf8") > this.maxLedgerBytes) {
        throw new Error("Nonce ledger size limit reached; refusing to bypass replay protection.");
      }
      const handle = await open(this.path, "a", 0o600);
      try {
        await handle.writeFile(line, "utf8");
        await handle.sync();
      } finally {
        await handle.close();
      }
      const directoryHandle = await open(dirname(this.path), "r");
      try { await directoryHandle.sync(); } finally { await directoryHandle.close(); }
      return true;
    } finally {
      await lock.close();
      await unlink(this.lockPath).catch(() => {});
    }
  }
}
