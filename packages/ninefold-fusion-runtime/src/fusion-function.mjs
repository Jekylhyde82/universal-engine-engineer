export const FUSION_FUNCTION_ID = "UNIFIED FUSION SYNERGY — AFI PRIME";
export const FUSION_FUNCTION_VERSION = "0.1.0-poc";

const ALLOWED_COMMANDS = new Set(["health", "state.write", "state.read"]);
const MAX_STATE_ENTRIES = 1_024;
const MAX_STATE_BYTES = 1_048_576;

function validateKey(key) {
  if (typeof key !== "string" || key.length < 1 || key.length > 128) {
    throw new TypeError("State key must be a string between 1 and 128 characters.");
  }
}

function validateJsonValue(value) {
  const encoded = JSON.stringify(value);
  if (encoded === undefined || Buffer.byteLength(encoded) > 16_384) {
    throw new TypeError("State value must be JSON-serialisable and no larger than 16 KiB.");
  }
  return encoded;
}

/**
 * Deterministic proof function shared by all nine OS-process instances.
 * This is an orchestration/state-boundary proof, not an LLM or reasoning engine.
 */
export function executeCanonicalFusionCommand({ command, state, instanceId, policyVersion }) {
  if (!command || typeof command !== "object" || !ALLOWED_COMMANDS.has(command.type)) {
    throw new TypeError("Unsupported fusion command.");
  }

  if (command.type === "health") {
    return {
      instanceId,
      fusionFunctionId: FUSION_FUNCTION_ID,
      fusionFunctionVersion: FUSION_FUNCTION_VERSION,
      policyVersion,
      status: "READY",
    };
  }

  validateKey(command.key);

  if (command.type === "state.write") {
    const encoded = validateJsonValue(command.value);
    const hadKey = state.has(command.key);
    if (!hadKey && state.size >= MAX_STATE_ENTRIES) {
      throw new Error("Instance state entry limit reached.");
    }
    const currentBytes = [...state.values()].reduce(
      (total, item) => total + Buffer.byteLength(JSON.stringify(item)),
      0,
    );
    const previousBytes = hadKey
      ? Buffer.byteLength(JSON.stringify(state.get(command.key)))
      : 0;
    const nextBytes = currentBytes - previousBytes + Buffer.byteLength(encoded);
    if (nextBytes > MAX_STATE_BYTES) throw new Error("Instance state byte limit reached.");
    state.set(command.key, JSON.parse(encoded));
    return {
      instanceId,
      written: true,
      key: command.key,
      valueBytes: Buffer.byteLength(encoded),
    };
  }

  if (command.type === "state.read") {
    const found = state.has(command.key);
    return {
      instanceId,
      found,
      key: command.key,
      value: found ? state.get(command.key) : null,
    };
  }

  throw new TypeError("Unsupported fusion command.");
}
