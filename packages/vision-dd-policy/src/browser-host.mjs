import { mkdir, lstat, rm } from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import { chromium } from "playwright";
import { createBrowserAdapter } from "./browser-adapter.mjs";

/**
 * Launch a dedicated persistent Chromium context for supervised automation.
 * A fresh profile is created for each host instance; by default it is deleted
 * after the browser closes. The caller must supply a trusted consent provider,
 * production public key and durable grant replay ledger.
 */
export async function launchBrowserHost({
  profileRoot,
  initialUrl,
  allowedOrigins,
  publicKeyPem,
  policyVersion,
  grantNonceLedger,
  requestConsent,
  headless = false,
  deleteProfileOnClose = true,
  browserType = chromium,
  clock = Date.now,
}) {
  if (typeof profileRoot !== "string" || !isAbsolute(profileRoot) ||
      typeof initialUrl !== "string" || !Array.isArray(allowedOrigins) || allowedOrigins.length === 0 ||
      typeof publicKeyPem !== "string" || typeof policyVersion !== "string" ||
      !grantNonceLedger || typeof grantNonceLedger.consume !== "function" ||
      typeof requestConsent !== "function" || typeof headless !== "boolean" ||
      typeof deleteProfileOnClose !== "boolean" ||
      !browserType || typeof browserType.launchPersistentContext !== "function" ||
      typeof clock !== "function") {
    throw new TypeError("Browser host requires an absolute private profile root, allowlist, grant ledger and consent provider.");
  }

  const root = resolve(profileRoot);
  await mkdir(root, { recursive: true, mode: 0o700 });
  const rootInfo = await lstat(root);
  if (!rootInfo.isDirectory() || rootInfo.isSymbolicLink()) {
    throw new Error("Browser profile root must be a real directory.");
  }
  if (process.platform !== "win32" && (rootInfo.mode & 0o077) !== 0) {
    throw new Error("Browser profile root must be private to the current OS user.");
  }

  const initial = new URL(initialUrl);
  const allowedOriginSet = new Set(allowedOrigins.map((value) => new URL(value).origin));
  if (initial.username || initial.password || initial.search || initial.hash ||
      !allowedOriginSet.has(initial.origin) ||
      !["https:", "http:"].includes(initial.protocol) ||
      (initial.protocol === "http:" && !["localhost", "127.0.0.1", "[::1]"].includes(initial.hostname))) {
    throw new Error("Initial browser URL must use an allowlisted HTTPS origin (or loopback HTTP).");
  }

  const profilePath = join(root, "profile-" + randomUUID());
  await mkdir(profilePath, { mode: 0o700 });
  let context;
  try {
    context = await browserType.launchPersistentContext(profilePath, {
      headless,
      serviceWorkers: "block",
      acceptDownloads: false,
      bypassCSP: false,
      ignoreHTTPSErrors: false,
      permissions: [],
      args: [
        "--disable-extensions",
        "--no-first-run",
        "--disable-sync",
        "--disable-background-networking",
      ],
    });
    const pages = context.pages();
    const page = pages[0] || await context.newPage();
    for (const extraPage of pages.slice(1)) await extraPage.close();
    let blockedPopupCount = pages.length - 1;
    context.on("page", (newPage) => {
      if (newPage !== page) {
        blockedPopupCount += 1;
        void newPage.close().catch(() => {});
      }
    });
    const sessionId = randomUUID();
    const adapter = createBrowserAdapter({
      page,
      context,
      sessionId,
      allowedOrigins,
      publicKeyPem,
      policyVersion,
      grantNonceLedger,
      requestConsent,
      clock,
    });
    const initialConsent = await requestConsent({
      purpose: "OPEN_INITIAL_URL",
      session_id: sessionId,
      application_origin: initial.origin,
      destination_url: initial.origin + initial.pathname,
    });
    if (initialConsent !== true) throw new Error("Trusted consent was not granted for the initial browser navigation.");
    await page.goto(initial.href, { waitUntil: "domcontentloaded", timeout: 15_000 });
    let closed = false;
    return Object.freeze({
      adapter,
      getStatus() {
        return Object.freeze({
          page_count: context.pages().length,
          service_worker_count: context.serviceWorkers().length,
          blocked_popup_count: blockedPopupCount,
          stopped: adapter.stopped,
        });
      },
      stop() {
        adapter.stop();
      },
      async close() {
        if (closed) return;
        closed = true;
        adapter.stop();
        try {
          await context.close();
        } finally {
          if (deleteProfileOnClose) {
            await rm(profilePath, { recursive: true, force: true });
          }
        }
      },
    });
  } catch (error) {
    if (context) await context.close().catch(() => {});
    if (deleteProfileOnClose) await rm(profilePath, { recursive: true, force: true }).catch(() => {});
    throw error;
  }
}
