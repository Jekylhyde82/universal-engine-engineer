# V.I.S.I.O.N. + D.D. production-readiness implementation plan

**Date:** 2026-11-19  
**Parent:** NINEFOLD INTRINSIC  
**Delivery status:** Active implementation; production remains NO-GO.

## Current implementation checkpoint (2026-11-19)

Implemented in the feature branch:
- Deterministic deny-by-default policy evaluation and guarded action-state transitions.
- Ed25519 action-bound grants with policy version, actor, task, action, application and session binding.
- Single-host hash-chained nonce ledger with locking, fsync, restrictive permissions, bounded capacity and fail-closed recovery.
- HTTP policy-grant service with injected authentication and approval-verification dependencies.
- Trusted-consent-provider-gated browser observation, optional separately consented screenshot capture and navigation-only D.D. execution.
- Isolated Chromium host with fresh private profile, service workers blocked, downloads/extensions disabled, external popups closed and raw browser handles withheld from the caller.
- Terminal consent provider with explicit YES confirmation and terminal-output sanitization.
- Signed independent readback verification primitive.
- Governed action orchestrator that separates policy, executor and verifier roles and refuses to proceed when an audit append fails.
- Local append-only hash-chained action audit ledger with locking, fsync, partial-tail recovery, canonical-record enforcement, restrictive permissions, bounded capacity and atomic duplicate action-ID prevention.
- Real Chromium CI integration tests plus JavaScript syntax checks and CodeQL workflow.

Latest verified real-browser CI run on commit `e1b913aaa294242aa5c936e897038d22c111829f`: **114 tests passed, 0 failed, 0 skipped**, including two real Chromium integration tests against a temporary local fixture. CodeQL also passed on that exact commit (workflow runs `44458441606` and `44458441678`).

Still not production-ready: real identity provider, trusted approval-signature provider/key lifecycle, independent read-only verifier process, calibrated vision model, screenshot redaction, durable externally anchored action audit ledger, AFI PRIME/EB9PRIME runtime integration, Android implementation, deployment/operations and independent security approval.

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
- The policy package remains a prototype despite the local replay ledger and signed grant primitives: production identity, approval/key management, independent verifier provider, externally anchored audit evidence and operational review remain outstanding.

## Implementation sequence

### P0 — Correct the policy boundary
1. **Implemented:** test-first Ed25519 grant signing and verification bound to action digest, policy version, actor, application, session, expiry and unique grant ID.
2. **Implemented as a single-host prototype:** crash-recoverable append-only nonce ledger with fail-closed behavior, restrictive permissions, locking and capacity bounds.
3. **Implemented:** tests for signature tampering, scope mismatch, expiry, replay, corrupted/truncated ledger, concurrent nonce consumption and restart recovery.
4. **Implemented:** policy HTTP service interface; production identity and approval providers remain injected integration work. The executor cannot mint grants.

### P1 — Supervised browser adapter
1. **Implemented in the reference package:** strict action request validation and action digests bound to V.I.S.I.O.N. observation IDs.
2. **Implemented and real-Chromium-tested:** isolated Chromium host, origin allowlist, session binding, fresh observation, request interception, blocked external redirects, private per-run profile, service-worker blocking and popup closure.
3. **Implemented:** navigation only. Text entry, clicks and form interactions remain disabled.
4. **Implemented:** stop switch, action serialization, bounded observation/navigation timeouts and no-blind-retry UNKNOWN state. Production session revocation remains outstanding.
5. Consequential actions remain disabled pending trusted approval UX, policy grants and independent verification.

### P2 — Independent verification and evidence
1. **Partially implemented:** signed readback verification primitive rejects executor self-verification, stale evidence, scope mismatch and invalid signatures. A separate authenticated read-only verifier provider remains outstanding.
2. Local nonce replay and action audit ledgers are implemented. External signed integrity checkpoints, protected backup/restore, retention/access controls and screenshot redaction remain outstanding.
3. **Partially implemented:** executor reports AWAITING_VERIFICATION or UNKNOWN; reconciliation workflow and durable recovery evidence remain outstanding.
4. Initial adversarial tests cover stale observations, origin changes/redirects, popup blocking, approval/grant replay and signature tampering. Visual prompt injection, account/session switching and broader fault-injection campaigns remain outstanding.

### P3 — Operational readiness
1. **Partially implemented:** JavaScript syntax checks and CodeQL workflow are configured. Dependency/license scanning, secret scanning, SBOM and coverage thresholds remain outstanding.
2. Reproducible release build and artifact provenance remain outstanding.
3. Staging, monitoring, incident response, backup/restore and rollback/kill-switch rehearsals remain outstanding.
4. Independent code/security review against the exact release commit remains outstanding.
5. Production remains NO-GO until every applicable acceptance group and release gate has evidence.

### P4 — Android and broader integration
1. Reuse the existing `android/uaie-client-v0.1` native Kotlin intake/control-terminal branch (PR #20) as the future mobile companion foundation; it currently has no screen capture or accessibility automation.
2. Add explicit MediaProjection/accessibility consent and persistent user-visible operation indicators only in a separate Android feature branch.
3. Test on the supported OPPO/ColorOS/Android matrix; no accessibility permission is requested before its feature is ready.
4. Integrate AFI PRIME and EB9PRIME through versioned, least-privilege interfaces and reconcile the Node action-policy contract with the existing Python runtime policy engine.
5. Keep Android production release separate from browser release until its own gates pass.

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
