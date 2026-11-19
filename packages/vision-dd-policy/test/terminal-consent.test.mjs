import test from "node:test";
import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import { createTerminalConsentProvider } from "../src/terminal-consent.mjs";

async function ask(provider, input, request) {
  const pending = provider.requestConsent(request);
  input.write("YES\n");
  return pending;
}

test("terminal consent provider requires an explicit exact YES response", async () => {
  const input = new PassThrough();
  const output = new PassThrough();
  const provider = createTerminalConsentProvider({ input, output });
  try {
    assert.equal(await ask(provider, input, {
      purpose: "OBSERVE", session_id: "session-1",
      application_origin: "https://example.test",
    }), true);
    const denied = provider.requestConsent({
      purpose: "EXECUTE_ACTION", session_id: "session-1",
      application_origin: "https://example.test", action_id: "action-1",
      action_type: "navigate", action_digest: "sha256:abc",
      destination_url: "https://example.test/help",
    });
    input.write("yes\n");
    assert.equal(await denied, false);
  } finally {
    provider.close();
    input.destroy();
    output.destroy();
  }
});

test("terminal visual consent warns that screenshot content is not redacted", async () => {
  const input = new PassThrough();
  const output = new PassThrough();
  const provider = createTerminalConsentProvider({ input, output });
  try {
    const pending = provider.requestConsent({
      purpose: "VISUAL_FRAME_CAPTURE", session_id: "session-1",
      application_origin: "https://example.test",
    });
    input.write("NO\n");
    assert.equal(await pending, false);
    const text = output.read()?.toString() || "";
    assert.match(text, /not redacted/i);
    assert.match(text, /sensitive/i);
  } finally {
    provider.close();
    input.destroy();
    output.destroy();
  }
});

test("unknown consent purpose is denied without prompting", async () => {
  const input = new PassThrough();
  const output = new PassThrough();
  const provider = createTerminalConsentProvider({ input, output });
  try {
    assert.equal(await provider.requestConsent({ purpose: "UNKNOWN" }), false);
  } finally {
    provider.close();
    input.destroy();
    output.destroy();
  }
});
