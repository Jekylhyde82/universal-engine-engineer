import { openEvidenceStream } from "./evidence.mjs";
import {
  executeCanonicalFusionCommand,
  FUSION_FUNCTION_ID,
  FUSION_FUNCTION_VERSION,
} from "./fusion-function.mjs";

const instanceId = process.env.NINEFOLD_INSTANCE_ID;
const evidencePath = process.env.NINEFOLD_EVIDENCE_PATH;
const policyVersion = process.env.NINEFOLD_POLICY_VERSION;

if (!/^UMIC-0[1-9]$/.test(instanceId ?? "") || !evidencePath || !policyVersion) {
  process.stderr.write("Invalid scoped instance process configuration.\n");
  process.exit(70);
}

const state = new Map();
let evidence;
let closing = false;

async function send(message) {
  if (typeof process.send !== "function" || !process.connected) return;
  await new Promise((resolve, reject) => {
    process.send(message, (error) => error ? reject(error) : resolve());
  });
}

async function handle(message) {
  if (!message || typeof message !== "object" || message.instanceId !== instanceId) {
    throw new Error("Request instance scope mismatch.");
  }

  const { requestId, command } = message;
  if (!command || typeof command.type !== "string") throw new TypeError("Malformed command.");

  if (command.type === "evidence.list") {
    return { events: evidence.events };
  }

  if (command.type === "audit.marker") {
    const event = await evidence.append(command.eventType, command.details ?? {});
    return { sequence: event.sequence, hash: event.hash };
  }

  if (command.type === "shutdown") {
    if (!closing) {
      closing = true;
      await evidence.append("INSTANCE_STOPPING", { reason: "supervised_shutdown" });
      await evidence.close();
    }
    return { status: "STOPPING" };
  }

  const execution = executeCanonicalFusionCommand({
    command,
    state,
    instanceId,
    policyVersion,
  });
  let event;
  if (execution.commit) {
    await evidence.append("COMMAND_PREPARED", execution.evidenceDetails);
    execution.commit();
    try {
      event = await evidence.append("COMMAND_COMMITTED", execution.evidenceDetails);
    } catch (error) {
      execution.rollback();
      throw error;
    }
  } else {
    event = await evidence.append("COMMAND_" + command.type.toUpperCase(), execution.evidenceDetails);
  }
  return {
    ...execution.result,
    evidenceSequence: event.sequence,
    evidenceHash: event.hash,
    requestId,
  };
}

async function main() {
  evidence = await openEvidenceStream({
    filePath: evidencePath,
    instanceId,
    functionVersion: FUSION_FUNCTION_VERSION,
    policyVersion,
  });
  await evidence.append("INSTANCE_STARTED", { pid: process.pid });
  await send({
    type: "ready",
    instanceId,
    pid: process.pid,
    fusionFunctionId: FUSION_FUNCTION_ID,
    fusionFunctionVersion: FUSION_FUNCTION_VERSION,
    policyVersion,
  });
}

process.on("message", async (message) => {
  if (closing) return;
  try {
    const result = await handle(message);
    await send({ type: "response", requestId: message.requestId, ok: true, result });
    if (message.command?.type === "shutdown") process.exit(0);
  } catch (error) {
    try {
      await evidence?.append("COMMAND_REJECTED", {
        requestId: message?.requestId ?? null,
        reason: error?.message ?? "unknown_error",
      });
    } catch {
      // An evidence failure is fail-closed: do not claim the command succeeded.
    }
    try {
      await send({
        type: "response",
        requestId: message?.requestId,
        ok: false,
        error: error?.message ?? "Instance command failed.",
      });
    } catch {
      process.exit(71);
    }
  }
});

main().catch((error) => {
  const reason = error?.message ?? "Instance startup failed.";
  process.stderr.write((error?.stack ?? String(error)) + "\n");
  if (typeof process.send === "function" && process.connected) {
    process.send({ type: "startup-error", instanceId, error: reason }, () => process.exit(72));
  } else {
    process.exit(72);
  }
});
