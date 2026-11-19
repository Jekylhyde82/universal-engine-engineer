import test from "node:test";
import assert from "node:assert/strict";
import { createServer as createHttpServer } from "node:http";
import { mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { generateKeyPairSync } from "node:crypto";
let chromium;
try { ({ chromium } = await import("playwright")); } catch { /* Optional outside CI. */ }
import { launchBrowserHost } from "../src/browser-host.mjs";

test("browser host launches isolated Chromium with service workers blocked and cleans its profile", { skip: !chromium }, async () => {
  const root = await mkdtemp(join(tmpdir(), "vision-dd-profile-root-"));
  const server = createHttpServer((_request, response) => {
    response.writeHead(200, { "content-type": "text/html" });
    response.end('<!doctype html><title>host fixture</title><p>Ready</p><script>window.open("https://evil.test/popup", "_blank")</script>');
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const origin = "http://127.0.0.1:" + server.address().port;
  const pair = generateKeyPairSync("ed25519");
  const publicKeyPem = pair.publicKey.export({ type: "spki", format: "pem" });
  let host;
  try {
    host = await launchBrowserHost({
      profileRoot: root,
      initialUrl: origin,
      allowedOrigins: [origin],
      publicKeyPem,
      policyVersion: "host-policy",
      grantNonceLedger: { consume: async () => true },
      requestConsent: async () => true,
      headless: true,
    });
    const profileEntries = await readdir(root);
    assert.equal(profileEntries.length, 1);
    assert.equal(host.getStatus().service_worker_count, 0);
    const observation = await host.adapter.observe();
    assert.equal(observation.application_identity, origin);
    await new Promise((resolve) => setTimeout(resolve, 100));
    assert.equal(host.getStatus().page_count, 1);
    assert.ok(host.getStatus().blocked_popup_count >= 1);
    assert.equal("page" in host, false);
    assert.equal("context" in host, false);
    await host.close();
    host = null;
    assert.deepEqual(await readdir(root), []);
  } finally {
    if (host) await host.close();
    await new Promise((resolve) => server.close(resolve));
    await rm(root, { recursive: true, force: true });
  }
});

test("browser host requires an explicit consent provider", async () => {
  const root = await mkdtemp(join(tmpdir(), "vision-dd-profile-root-"));
  const pair = generateKeyPairSync("ed25519");
  const publicKeyPem = pair.publicKey.export({ type: "spki", format: "pem" });
  try {
    await assert.rejects(() => launchBrowserHost({
      profileRoot: root,
      initialUrl: "https://example.test",
      allowedOrigins: ["https://example.test"],
      publicKeyPem,
      policyVersion: "host-policy",
      grantNonceLedger: { consume: async () => true },
    }), /consent/i);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("browser host rejects initial URLs with hidden query or fragment data", async () => {
  const root = await mkdtemp(join(tmpdir(), "vision-dd-profile-root-"));
  const pair = generateKeyPairSync("ed25519");
  const publicKeyPem = pair.publicKey.export({ type: "spki", format: "pem" });
  let launched = false;
  try {
    await assert.rejects(() => launchBrowserHost({
      profileRoot: root,
      initialUrl: "https://example.test/start?token=secret#fragment",
      allowedOrigins: ["https://example.test"],
      publicKeyPem,
      policyVersion: "host-policy",
      grantNonceLedger: { consume: async () => true },
      requestConsent: async () => true,
      browserType: {
        launchPersistentContext: async () => { launched = true; throw new Error("must not launch"); },
      },
    }), /allowlisted HTTPS origin/i);
    assert.equal(launched, false);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
