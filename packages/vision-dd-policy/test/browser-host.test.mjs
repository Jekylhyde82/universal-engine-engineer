import test from "node:test";
import assert from "node:assert/strict";
import { createServer as createHttpServer } from "node:http";
import { mkdtemp, lstat, rm } from "node:fs/promises";
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
    response.end("<!doctype html><title>host fixture</title><p>Ready</p>");
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const origin = "http://127.0.0.1:" + server.address().port;
  const pair = generateKeyPairSync("ed25519");
  const publicKeyPem = pair.publicKey.export({ type: "spki", format: "pem" });
  let host;
  try {
    host = await launchBrowserHost({
      profileRoot: root,
      allowedOrigins: [origin],
      publicKeyPem,
      policyVersion: "host-policy",
      grantNonceLedger: { consume: async () => true },
      requestConsent: async () => true,
      headless: true,
    });
    const profilePath = host.profilePath;
    assert.equal((await lstat(profilePath)).isDirectory(), true);
    assert.equal(host.context.serviceWorkers().length, 0);
    await host.page.goto(origin);
    const observation = await host.adapter.observe();
    assert.equal(observation.application_identity, origin);
    await host.page.evaluate(() => window.open("https://evil.test/popup", "_blank"));
    await new Promise((resolve) => setTimeout(resolve, 100));
    assert.equal(host.context.pages().length, 1);
    await host.close();
    host = null;
    await assert.rejects(() => lstat(profilePath), { code: "ENOENT" });
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
      allowedOrigins: ["https://example.test"],
      publicKeyPem,
      policyVersion: "host-policy",
      grantNonceLedger: { consume: async () => true },
    }), /consent/i);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
