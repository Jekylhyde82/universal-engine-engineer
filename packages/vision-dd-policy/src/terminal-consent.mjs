import { createInterface } from "node:readline";

/**
 * Local terminal consent surface for a supervised single-user prototype.
 * It is deliberately explicit and fails closed. Production deployments should
 * replace or wrap it with an authenticated, accessible, auditable consent UI.
 */
function safeDisplay(value, maxLength = 256) {
  return String(value ?? "unknown")
    .replace(/[\\u0000-\\u001f\\u007f\\u001b]/g, " ")
    .slice(0, maxLength);
}

export function createTerminalConsentProvider({
  input = process.stdin,
  output = process.stdout,
} = {}) {
  const readline = createInterface({ input, output, terminal: Boolean(output.isTTY && input.isTTY) });
  let closed = false;

  async function requestConsent(request) {
    if (closed || !request || typeof request !== "object") return false;
    let heading;
    let detail;
    if (request.purpose === "OBSERVE") {
      heading = "Allow V.I.S.I.O.N. to inspect visible interface labels?";
      detail = "Application: " + safeDisplay(request.application_origin) +
        "\nSession: " + safeDisplay(request.session_id);
    } else if (request.purpose === "VISUAL_FRAME_CAPTURE") {
      heading = "Allow V.I.S.I.O.N. to capture a visual screenshot?";
      detail = "WARNING: the screenshot is NOT REDACTED and may contain sensitive information. " +
        "The adapter does not persist it; downstream handling remains the caller's responsibility.\n" +
        "Application: " + safeDisplay(request.application_origin);
    } else if (request.purpose === "EXECUTE_ACTION") {
      heading = "Allow D.D. to execute this supervised browser action?";
      detail = [
        "Action: " + safeDisplay(request.action_type),
        "Action ID: " + safeDisplay(request.action_id),
        "Application: " + safeDisplay(request.application_origin),
        "Destination: " + safeDisplay(request.destination_url),
        "Action digest: " + safeDisplay(request.action_digest),
        "Only the typed, policy-approved action is authorised.",
      ].join("\n");
    } else {
      return false;
    }

    output.write("\n=== NINEFOLD INTRINSIC — TRUSTED CONSENT ===\n");
    output.write(heading + "\n" + detail + "\n");
    output.write("Type YES exactly to approve; any other response denies.\n");
    const answer = await new Promise((resolve) => {
      readline.question("> ", (value) => resolve(value));
    });
    return answer.trim() === "YES";
  }

  return Object.freeze({
    requestConsent,
    close() {
      if (closed) return;
      closed = true;
      readline.close();
    },
  });
}
