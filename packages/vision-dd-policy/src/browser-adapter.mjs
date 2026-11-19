import { createHash, randomUUID } from "node:crypto";
import { verifyGrant } from "./grant.mjs";

const MAX_OBSERVATIONS = 32;
const MAX_ELEMENTS = 200;
const MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024;

function digest(value) {
  return "sha256:" + createHash("sha256").update(JSON.stringify(value), "utf8").digest("hex");
}

function normaliseOrigin(value) {
  const url = new URL(value);
  if (url.username || url.password || !["https:", "http:"].includes(url.protocol)) {
    throw new TypeError("Only credential-free HTTP(S) origins are permitted.");
  }
  if (url.protocol === "http:" && !["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) {
    throw new TypeError("Non-local browser origins must use HTTPS.");
  }
  return url.origin;
}

function safePageUrl(value, allowedOrigins) {
  let url;
  try { url = new URL(value); } catch { throw new Error("Browser URL is invalid."); }
  if (url.username || url.password || !allowedOrigins.has(url.origin)) {
    throw new Error("Browser origin is outside the allowlist.");
  }
  return url;
}

function publicUrl(url) {
  return url.origin + url.pathname;
}

function observationScript() {
  const candidates = Array.from(document.querySelectorAll(
    'button,a[href],input,textarea,select,[role="button"],[role="link"],[role="checkbox"],[role="radio"]'
  )).slice(0, 200);
  const visible = [];
  for (const element of candidates) {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    if (rect.width <= 0 || rect.height <= 0 || style.visibility === "hidden" ||
        style.display === "none" || Number(style.opacity) === 0) continue;
    const tag = element.tagName.toLowerCase();
    let role = element.getAttribute("role");
    if (!role) {
      if (tag === "button") role = "button";
      else if (tag === "a") role = "link";
      else if (tag === "textarea") role = "textbox";
      else if (tag === "select") role = "combobox";
      else if (tag === "input") {
        const type = (element.getAttribute("type") || "text").toLowerCase();
        role = ["button", "submit", "reset", "image"].includes(type) ? "button" :
          ["checkbox", "radio"].includes(type) ? type : "textbox";
      }
    }
    const labelledBy = element.getAttribute("aria-labelledby");
    const labelledText = labelledBy
      ? labelledBy.split(/\s+/).map((id) => document.getElementById(id)?.textContent || "").join(" ")
      : "";
    const labels = element.labels
      ? Array.from(element.labels).map((label) => label.textContent || "").join(" ")
      : "";
    const rawLabel = element.getAttribute("aria-label") || labelledText ||
      labels || element.getAttribute("title") || element.innerText || element.textContent || "";
    const label = String(rawLabel).replace(/\s+/g, " ").trim().slice(0, 160);
    visible.push({
      role: String(role || "unknown").slice(0, 32),
      label,
      x: Math.round(rect.x),
      y: Math.round(rect.y),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      disabled: Boolean(element.disabled || element.getAttribute("aria-disabled") === "true"),
      tag,
      input_type: tag === "input" ? (element.getAttribute("type") || "text").toLowerCase() : null,
    });
  }
  return {
    title: String(document.title || "").slice(0, 200),
    viewport: { width: window.innerWidth, height: window.innerHeight },
    elements: visible,
  };
}

/**
 * Supervised Playwright page adapter. It observes only after explicit consent,
 * exposes page labels as untrusted data, and initially permits navigation only.
 * It never performs generic clicks, form submission, shell execution or writes.
 */
export function createBrowserAdapter({
  page,
  sessionId,
  allowedOrigins,
  publicKeyPem,
  policyVersion,
  grantNonceLedger,
  clock = Date.now,
  observationTtlMs = 5_000,
  navigationTimeoutMs = 5_000,
}) {
  if (!page || typeof page.url !== "function" || typeof page.evaluate !== "function" ||
      typeof page.goto !== "function" || !Array.isArray(allowedOrigins) ||
      allowedOrigins.length === 0 || typeof sessionId !== "string" || !sessionId.trim() ||
      typeof publicKeyPem !== "string" || typeof policyVersion !== "string" ||
      typeof clock !== "function" || !Number.isSafeInteger(observationTtlMs) ||
      observationTtlMs < 100 || !Number.isSafeInteger(navigationTimeoutMs) ||
      navigationTimeoutMs < 100 || navigationTimeoutMs > 15_000) {
    throw new TypeError("Browser adapter configuration is incomplete or invalid.");
  }
  const origins = new Set(allowedOrigins.map(normaliseOrigin));
  const observations = new Map();
  let stopped = false;
  const routeReady = Promise.resolve(page.route("**/*", async (route) => {
    const rawUrl = route.request().url();
    if (rawUrl === "about:blank" || rawUrl.startsWith("data:") || rawUrl.startsWith("blob:")) {
      return route.continue();
    }
    try {
      safePageUrl(rawUrl, origins);
      return route.continue();
    } catch {
      return route.abort("blockedbyclient");
    }
  }));

  function purgeObservations(now) {
    for (const [id, item] of observations) {
      if (item.expiresAt <= now) observations.delete(id);
    }
    while (observations.size >= MAX_OBSERVATIONS) {
      observations.delete(observations.keys().next().value);
    }
  }

  async function observe({ userConsent = false, includeScreenshot = false, visualConsent = false } = {}) {
    if (stopped) throw new Error("Browser adapter is stopped.");
    if (userConsent !== true) throw new Error("Explicit user consent is required for observation.");
    if (includeScreenshot && visualConsent !== true) {
      throw new Error("Separate explicit visual consent is required for screenshot capture.");
    }
    await routeReady;
    const now = clock();
    if (!Number.isSafeInteger(now)) throw new Error("Clock unavailable.");
    const currentUrl = safePageUrl(page.url(), origins);
    const snapshot = await page.evaluate(observationScript);
    if (!snapshot || !Array.isArray(snapshot.elements)) {
      throw new Error("Browser observation could not be acquired.");
    }
    const elements = snapshot.elements.slice(0, MAX_ELEMENTS).map((element, index) => ({
      element_id: "element-" + index,
      role: String(element.role || "unknown").slice(0, 32),
      label: String(element.label || "").slice(0, 160),
      geometry: {
        x: Number(element.x) || 0,
        y: Number(element.y) || 0,
        width: Number(element.width) || 0,
        height: Number(element.height) || 0,
      },
      disabled: element.disabled === true,
      tag: String(element.tag || "unknown").slice(0, 16),
      input_type: element.input_type == null ? null : String(element.input_type).slice(0, 32),
      content_trust: "UNTRUSTED_PAGE_DATA",
    }));
    const visualFrame = includeScreenshot ? await page.screenshot({ type: "png" }) : null;
    if (visualFrame && visualFrame.length > MAX_SCREENSHOT_BYTES) {
      throw new Error("Visual frame exceeds the 5 MiB limit.");
    }
    const viewport = snapshot.viewport || page.viewportSize?.() || { width: 0, height: 0 };
    const frameDigest = visualFrame
      ? "sha256:" + createHash("sha256").update(visualFrame).digest("hex")
      : null;
    const observationId = randomUUID();
    const content = {
      title: String(snapshot.title || "").slice(0, 200),
      viewport,
      elements,
      visual_frame_digest: frameDigest,
      source_url: publicUrl(currentUrl),
    };
    const expiry = now + observationTtlMs;
    const observation = Object.freeze({
      schema_version: "1.0.0",
      observation_id: observationId,
      source_adapter: "playwright-supervised-browser",
      source_session_id: sessionId,
      captured_at: new Date(now).toISOString(),
      application_identity: currentUrl.origin,
      viewport_or_frame_id: String(viewport.width) + "x" + String(viewport.height),
      content_digest: digest(content),
      detected_elements: elements,
      confidence: null,
      uncertainty: "DOM_SEMANTIC_OBSERVATION; MODEL_CONFIDENCE_NOT_CALIBRATED",
      redaction_applied: false,
      expiry_at: new Date(expiry).toISOString(),
      ...(visualFrame ? {
        visual_frame: Object.freeze({
          mime_type: "image/png",
          digest: frameDigest,
          data_base64: visualFrame.toString("base64"),
          retention: "CALLER_CONTROLLED; NOT_PERSISTED_BY_ADAPTER",
        }),
      } : {}),
    });
    purgeObservations(now);
    observations.set(observationId, {
      publicObservation: observation,
      pageUrl: page.url(),
      expiresAt: expiry,
    });
    return observation;
  }

  async function execute({ request, grant, userConsent = false }) {
    if (stopped) throw new Error("Browser adapter is stopped.");
    await routeReady;
    if (userConsent !== true) throw new Error("Explicit user consent is required for execution.");
    if (!request || request.action_type !== "navigate") {
      throw new Error("Unsupported action; this adapter currently permits navigation only.");
    }
    if (!request.parameters || Object.keys(request.parameters).length !== 1 ||
        typeof request.parameters.url !== "string") {
      throw new Error("Navigation action parameters are invalid.");
    }
    if (request.target_session_id !== sessionId) throw new Error("Browser session mismatch.");
    const observation = observations.get(request.observation_id);
    const now = clock();
    if (!observation || observation.expiresAt <= now) {
      throw new Error("Visual observation is missing or stale.");
    }
    if (observation.publicObservation.application_identity !== request.target_application ||
        observation.publicObservation.source_session_id !== request.target_session_id ||
        page.url() !== observation.pageUrl) {
      throw new Error("Visual observation is stale or bound to another application/session.");
    }
    const destination = safePageUrl(request.parameters.url, origins);
    if (destination.origin !== request.target_application) {
      throw new Error("Navigation target does not match the approved application.");
    }
    if (stopped) throw new Error("Browser adapter is stopped.");

    const grantResult = await verifyGrant({
      grant,
      publicKeyPem,
      expectedRequest: request,
      expectedPolicyVersion: policyVersion,
      consumeGrantId: grantNonceLedger?.consume
        ? (id) => grantNonceLedger.consume(id)
        : undefined,
      now,
    });
    if (!grantResult.valid) throw new Error("Execution grant rejected: " + grantResult.reason);
    if (stopped || page.url() !== observation.pageUrl || observation.expiresAt <= clock()) {
      throw new Error("Browser context changed after grant validation; action stopped.");
    }

    try {
      const response = await page.goto(destination.href, {
        waitUntil: "domcontentloaded",
        timeout: navigationTimeoutMs,
      });
      return Object.freeze({
        execution_id: randomUUID(),
        action_id: request.action_id,
        executor: "playwright-supervised-browser",
        execution_state: "AWAITING_VERIFICATION",
        verified: false,
        response_status_telemetry: typeof response?.status === "function" ? response.status() : null,
        resulting_application: safePageUrl(page.url(), origins).origin,
        resulting_path: safePageUrl(page.url(), origins).pathname,
        completed_at: new Date(clock()).toISOString(),
        note: "Executor telemetry is not independent proof of the requested outcome.",
      });
    } catch {
      return Object.freeze({
        execution_id: randomUUID(),
        action_id: request.action_id,
        executor: "playwright-supervised-browser",
        execution_state: "UNKNOWN",
        verified: false,
        completed_at: new Date(clock()).toISOString(),
        note: "Navigation outcome is uncertain; do not retry until independently reconciled.",
      });
    }
  }

  return Object.freeze({
    observe,
    execute,
    stop() { stopped = true; observations.clear(); },
    get stopped() { return stopped; },
  });
}
