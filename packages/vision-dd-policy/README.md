# V.I.S.I.O.N. / D.D. Policy and Supervised Browser Prototype

Dependency-free Node.js reference package for deterministic policy evaluation, signed execution grants, local replay protection, a policy HTTP service, supervised browser observation/navigation and signed readback verification.

## Status

**Prototype / integration slice. Not production approved.**

## Implemented in this branch

- Deterministic deny-by-default action policy evaluation.
- R0–R4 classification from trusted server-side policy configuration.
- Policy-version-bound, action-digest-bound human approval checks.
- Ed25519 short-lived grant signing and verification.
- Grant scope binding to actor, task, action, application and session.
- Local append-only hash-chained nonce ledger with exclusive locking, fsync, partial-tail recovery, restrictive permission checks and a configurable size limit.
- Authenticated policy-grant HTTP service with mandatory injected authentication and approval-verification functions.
- Consent-provider-gated Playwright page adapter for bounded semantic observation and optional screenshot capture.
- Strict browser request-origin allowlisting, stale-observation rejection, one-action-at-a-time execution, stop control and navigation-only action support.
- Signed readback verifier that refuses to trust the executor's own assertion.
- Automated Node.js tests in GitHub Actions, including real Chromium integration tests against a local fixture and CodeQL static analysis.

## Validation evidence

The latest recorded policy workflow reported **69 tests passed, 0 failed** at commit `75ff874873ed1784009a5ea06c076ea51546a70a`. This includes two real Chromium integration tests against a temporary local fixture. The browser integration suite verifies a signed allowlisted navigation and blocks a redirect to an unapproved origin.

## Important limitations

This is not a complete runtime or production security boundary.

- No production identity provider or real user/device authentication adapter is included. The HTTP service requires an injected authenticator.
- Human approval signature verification is injected; tests use fakes. No trusted approval UI or production key-management/rotation service is included.
- The local nonce ledger is single-host replay protection. Its hash chain is not independently tamper-proof; production audit evidence needs externally anchored checkpoints, backup and restore procedures.
- No production deployment, staging environment, operational monitoring, incident response or independent penetration test is included.
- The browser adapter accepts a Playwright-compatible page supplied by a trusted host. CI launches real Chromium for integration tests, but a production browser host/launcher, isolated persistent profile management and trusted user-facing consent UI are not yet implemented.
- The adapter currently supports navigation only. It does not implement generic clicks, form submissions, typing, file access or arbitrary desktop control.
- DOM labels are untrusted page data. A trusted consent-provider callback is mandatory for observation, screenshot capture and action execution. Screenshot capture requires separate visual consent and is not redacted; the adapter does not persist screenshots. The production host must create a dedicated browser context with `serviceWorkers: "block"` and a private isolated profile.
- The signed readback verifier is a verification primitive. A separate authenticated read-only verifier process/provider is not yet implemented.
- No Android app, MediaProjection/accessibility service, AFI PRIME runtime integration or EB9PRIME governed persistence runtime is included.

## Local supervised browser host

Requires Node.js 22 or later and the pinned Playwright dependency. The host launches a fresh Chromium profile, blocks service workers, disables downloads/extensions, applies the origin allowlist, and deletes the temporary profile on close by default.

The consent provider must be a trusted UI surface separate from the page being controlled. A terminal prompt provider is included for local single-user development; it requires typing `YES` and warns that screenshots are not redacted.

The host is a library API, not an unattended service. It requires an initial allowlisted URL and obtains separate consent before opening it. It does not expose the raw Playwright page or browser context to the caller; status is available through a read-only summary. It still requires a trusted policy public key and a durable grant replay ledger supplied by the caller.

```js
import { join } from "node:path";
import { homedir } from "node:os";
import {
  FileNonceLedger,
  createTerminalConsentProvider,
  launchBrowserHost,
} from "@ninefold/vision-dd-policy";

const consent = createTerminalConsentProvider();
const host = await launchBrowserHost({
  profileRoot: join(homedir(), ".ninefold", "vision-dd-profiles"),
  initialUrl: "https://example.test",
  allowedOrigins: ["https://example.test"],
  publicKeyPem: process.env.VISION_DD_POLICY_PUBLIC_KEY,
  policyVersion: "policy-1",
  grantNonceLedger: new FileNonceLedger(
    join(homedir(), ".ninefold", "vision-dd-grants.jsonl")
  ),
  requestConsent: consent.requestConsent,
  headless: false,
});

try {
  const observation = await host.adapter.observe();
  // Pass the observation to an authorised perception workflow.
  // D.D. still requires a signed grant for each navigation.
} finally {
  await host.close();
  consent.close();
}
```

The example is a local integration pattern, not a production deployment recipe. Do not put private signing keys in the browser host; the policy service retains the private key and the browser host receives only the trusted public key.

## Run tests

Requires Node.js 22 or later.

```sh
npm install
npx playwright install chromium
npm run check
npm test
```

## Decision semantics

- `DENY`: malformed, out-of-scope, prohibited or unevaluable request.
- `REQUIRE_APPROVAL`: human approval is required.
- `ELIGIBLE_FOR_GRANT`: deterministic checks passed. This is not an execution credential.
- A grant is a short-lived signed capability. D.D. must verify it against a trusted public key and consume its grant ID through a durable replay store immediately before execution.
- A navigation executor returns `AWAITING_VERIFICATION` or `UNKNOWN`; it never declares its own action verified.
