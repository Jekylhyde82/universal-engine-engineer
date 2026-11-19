import { createInterface } from "node:readline";

/**
 * Local terminal consent surface for a supervised single-user prototype.
 * It is deliberately explicit and fails closed. Production deployments should
 * replace or wrap it with an authenticated, accessible, auditable consent UI.
 */
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
      detail = "Application: " + String(request.application_origin || "unknown") +
        "\nSession: " + String(request.session_id || "unknown");
    } else if (request.purpose === "VISUAL_FRAME_CAPTURE") {
      heading = "Allow V.I.S.I.O.N. to capture a visual screenshot?";
      detail = "WARNING: the screenshot is NOT REDACTED and may contain sensitive information. " +
        "The adapter does not persist it; downstream handling remains the caller's responsibility.\n" +
        "Application: " + String(request.application_origin || "unknown");
    } else if (request.purpose === "EXECUTE_ACTION") {
      heading = "Allow D.D. to execute this supervised browser action?";
      detail = [
        "Action: " + String(request.action_type || "unknown"),
        "Action ID: " + String(request.action_id || "unknown"),
        "Application: " + String(request.application_origin || "unknown"),
        "Destination: " + String(request.destination_url || "not provided"),
        "Action digest: " + String(request.action_digest || "not provided"),
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
