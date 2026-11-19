# V.I.S.I.O.N. + D.D. production-readiness implementation plan

**Date:** 2026-11-19  
**Parent:** NINEFOLD INTRINSIC  
**Delivery status:** Active implementation plan; not a release approval.

## Delivery objective

Turn the current V.I.S.I.O.N. + DESIGNATED DRIVER specification and policy prototype into a narrowly scoped, supervised, auditable application workflow. The first supported execution surface is a dedicated desktop Chromium session; Android is a subsequent adapter because it requires a native application, explicit OS permissions, device-specific validation and a separate release process.

Preserve distinct responsibilities:
- V.I.S.I.O.N. observes and grounds current UI state.
- AFI PRIME proposes typed plans; it is not a policy authority.
- The policy service authenticates, evaluates, approves and issues narrowly scoped grants.
- D.D. executes one allowlisted action at a time.
- An independent verifier determines whether the requested postcondition actually occurred.
- EB9PRIME receives only minimised, provenance-bearing, verified learning records under retention controls.

## Approaches considered

1. **Unrestricted general desktop automation:** rejected. It expands the attack surface, makes target grounding and policy enforcement difficult, and contradicts the approved R0–R4 model.
2. **Supervised browser automation with a dedicated isolated Chromium profile:** selected. It gives a bounded first platform, supports deterministic test fixtures, allows domain/session scoping, and can be extended without granting arbitrary desktop or shell access.
3. **Native Android accessibility/screen-capture service first:** deferred. It is the user's eventual mobile interaction target, but it requires Android Studio/SDK, signing, OS permission UX, device testing and a separate application release. It is not a safe substitute for the initial browser runtime.

## Scope and constraints

- First release supports only explicitly allowlisted browser origins and a small typed action set.
- R0 observation and R1 reversible navigation are the initial automatic scope.
- R2 requires a trusted, per-action approval; R3 requires explicit per-action approval and remains disabled by default in v1; R4 is always denied.
- No arbitrary shell, terminal, file-system or code execution.
- No background capture, covert monitoring, credential handling, financial actions, publication, deletion or legal acceptance.
- The browser adapter must run in an isolated, dedicated profile and bind each action to a live session and fresh observation.
- No user device is accessed or activated by this repository change.
- No credentials, private keys, approval secrets or personal data may be committed.
- The policy package is a prototype until persistent replay protection, authenticated identity, grant issuance, executor enforcement and independent verification are implemented and reviewed.

## Implementation sequence

### P0 — Correct the policy boundary
1. Add test-first Ed25519 grant signing and verification bound to action digest, policy version, actor, application, session, expiry and unique grant ID.
2. Add a durable, crash-recoverable, append-only grant/nonce ledger with fail-closed behavior; document single-host filesystem assumptions and operational recovery.
3. Add tests for signature tampering, scope mismatch, expiry, replay, corrupted/truncated ledger, concurrent nonce consumption and restart recovery.
4. Expose only a minimal policy service interface; do not let the executor call the model or mint grants.

### P1 — Supervised browser adapter
1. Add typed observation and action schemas; reject unknown fields and stale observations.
2. Add an isolated Chromium adapter with origin allowlists, session binding, fresh-target checks and a strict action allowlist.
3. Begin with observation, navigation to allowlisted origins and safe text entry into non-sensitive test fixtures.
4. Add a global stop, session revoke, bounded timeouts and no-blind-retry semantics.
5. Do not enable arbitrary click, form submission or consequential actions until risk/approval enforcement and verifier evidence are complete.

### P2 — Independent verification and evidence
1. Add a verifier interface that obtains fresh state independently of the executor success flag.
2. Add an append-only task/action evidence ledger with redaction, integrity checks and retention policy.
3. Ensure uncertain external outcomes become UNKNOWN and require reconciliation.
4. Add adversarial tests for visual prompt injection, stale frames, origin changes, account/session changes, approval replay and duplicate actions.

### P3 — Operational readiness
1. Add lint, type/schema validation, coverage, dependency/license scanning, secret scanning and SBOM generation.
2. Add reproducible build and artifact provenance.
3. Add staging deployment instructions, monitoring, incident response, backup/restore and rollback/kill-switch rehearsals.
4. Obtain independent code/security review against the exact release commit.
5. Keep production NO-GO until every applicable acceptance group and release gate has evidence.

### P4 — Android and broader integration
1. Build a native Android companion with explicit MediaProjection/accessibility consent and persistent user-visible operation indicators.
2. Test on the supported OPPO/ColorOS/Android matrix; no accessibility permission is requested before its feature is ready.
3. Integrate AFI PRIME and EB9PRIME through versioned, least-privilege interfaces.
4. Keep Android production release separate from browser release until its own gates pass.

## Acceptance criteria

- No grant can be forged, altered, replayed or reused for a different task/action/session/policy.
- Missing identity, clock, ledger, policy, grant or evidence fails closed.
- D.D. cannot execute without a valid short-lived grant and a fresh target observation.
- V.I.S.I.O.N. output is observation-only and never interpreted as authority.
- The verifier can return NOT_VERIFIED or UNKNOWN even when the executor reports success.
- No raw screen content or secrets are written to durable memory by default.
- Every consequential operation has attributable approval and audit evidence.
- CI evidence is tied to the exact PR head SHA.
- All nine acceptance groups and release gates in PRODUCTION_GATES.md are satisfied before production approval.

## Explicit non-claims

A green unit-test workflow is not a working device integration, penetration test, staging deployment, independent security review or production approval. This plan authorises implementation work in the feature branch only; it does not authorise enabling live capture or unattended execution.
