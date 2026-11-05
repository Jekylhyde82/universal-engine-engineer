# SYPHON Full Gateway and Evidence Checkpoints — Preserved Snapshot

**Disposition:** PRESERVED / QUARANTINED / NOT INTEGRATED  
**Source repository:** https://github.com/Jekylhyde82/7282ALLSPARXPRIME  
**Source branch:** `allsparx/universal-core-integration`  
**Source commit:** `91f0680f4d6828bf4374423a7abc49e7c0a28509`  
**Related source work:** [PR #15](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/15), [PR #19](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/19)  
**Licence:** MIT; shared source notice at `../syphon-provider-foundation/LICENSE.source`.

## Preserved contents

- `workers/allsparx-gateway/src/index.js`: full Cloudflare AI gateway, provider routing, Turnstile checks, request limits, rate limiter/spend budget boundaries and protected evidence export.
- `workers/allsparx-gateway/src/evidence-ledger.js`: exact worker-local evidence ledger dependency (also preserved in the evidence/pipeline package).
- `workers/allsparx-gateway/README.md`, `package.json`, `wrangler.toml`: worker build and deployment context.
- `scripts/evidence-checkpoint.mjs`: offline checkpoint creation.
- `scripts/sign-evidence-checkpoint.mjs`: offline Ed25519 signing.
- `scripts/verify-evidence-checkpoint.mjs`: checkpoint verification.
- `tests/allsparx-gateway.test.mjs`: gateway, budget, evidence and request-boundary tests.
- Source assurance/dependency workflows, pipeline/deployment/security documentation and the dependency-remediation ledger.

## Engineering value

The gateway combines bounded request/response handling, exact-origin CORS, Turnstile verification, per-IP rate limiting, per-attempt spend reservations, explicit provider selection/fallback, evidence-before-provider execution and a protected bounded evidence export.

The checkpoint scripts provide a starting point for separating evidence generation from offline signing and verification. The nine-stage assurance and dependency-remediation documentation provides useful source material for a controlled release process.

## Review findings and limitations

- This is a product-specific anonymous assistant gateway, not a generic Universal Engine gateway. It is tied to Cloudflare Durable Objects, Turnstile, provider-specific API formats, product task contracts and CloudCredits/ALLSPARX identifiers.
- The gateway source accepts `ollama` in request validation but its configured provider list and provider-call implementation only contain OpenAI, Anthropic and Google. An explicit Ollama request therefore resolves to no configured provider. Do not advertise Ollama support from this snapshot.
- Spend reservations are not actual provider usage settlement or billing reconciliation. The source PR #15 explicitly lists settlement/reconciliation as outstanding.
- The evidence export bearer token is a sensitive operational secret. The source PR #15 lists edge access restriction, secret provisioning, external immutable retention, independent signer operation, key custody/rotation/revocation, checkpoint distribution and recovery exercises as outstanding.
- A hash chain within the same administrative boundary is not independent tamper protection.
- The source PR #19 reports successful workflow automation but deliberately holds at Stage 9. Its source workflow success is not production approval.
- No live Cloudflare deployment, live provider request, billing settlement, external checkpoint verification or independent security approval is established by this snapshot.
- Source docs and product identifiers are preserved as legacy reference material. They must be reconciled with the current UNIVERSAL ENGINE / ENGINEER architecture and naming rules before any reuse.

Do not deploy, activate nested workflows, expose the evidence export route or treat the package as production-ready. Keep it isolated until a target-specific threat model, configuration, cost controls, security review, tests, rollback plan and independent verification are complete.
