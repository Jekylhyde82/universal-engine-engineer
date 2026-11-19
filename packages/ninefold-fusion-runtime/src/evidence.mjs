import { createHash } from "node:crypto";
import { chmod, mkdir, open, readFile } from "node:fs/promises";
import { dirname } from "node:path";

const ZERO_HASH = "0".repeat(64);

export function hashEvidencePayload(payload) {
  return createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}

export function verifyEvidenceEvents(events, expectedInstanceId) {
  let previousHash = ZERO_HASH;
  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];
    const { hash, ...payload } = event;
    if (event.sequence !== index + 1) throw new Error("Evidence sequence gap.");
    if (event.instanceId !== expectedInstanceId) throw new Error("Evidence instance identity mismatch.");
    if (event.previousHash !== previousHash) throw new Error("Evidence chain link mismatch.");
    if (hashEvidencePayload(payload) !== hash) throw new Error("Evidence digest mismatch.");
    previousHash = hash;
  }
  return { valid: true, eventCount: events.length, headHash: previousHash };
}

export async function openEvidenceStream({ filePath, instanceId, functionVersion, policyVersion }) {
  await mkdir(dirname(filePath), { recursive: true, mode: 0o700 });
  await chmod(dirname(filePath), 0o700);
  const handle = await open(filePath, "a+", 0o600);
  await chmod(filePath, 0o600);

  const existing = await readFile(filePath, "utf8");
  const events = existing.trim() ? existing.trimEnd().split("\n").map((line) => JSON.parse(line)) : [];
  const verified = verifyEvidenceEvents(events, instanceId);
  for (const event of events) {
    if (event.functionVersion !== functionVersion || event.policyVersion !== policyVersion) {
      await handle.close();
      throw new Error("Evidence stream version mismatch.");
    }
  }

  let previousHash = verified.headHash;

  return {
    get events() {
      return events.map((event) => ({ ...event }));
    },
    async append(eventType, details = {}) {
      const payload = {
        sequence: events.length + 1,
        instanceId,
        functionVersion,
        policyVersion,
        occurredAt: new Date().toISOString(),
        eventType,
        details,
        previousHash,
      };
      const event = { ...payload, hash: hashEvidencePayload(payload) };
      await handle.write(JSON.stringify(event) + "\n");
      await handle.sync();
      events.push(event);
      previousHash = event.hash;
      return { ...event };
    },
    async close() {
      await handle.sync();
      await handle.close();
    },
  };
}
