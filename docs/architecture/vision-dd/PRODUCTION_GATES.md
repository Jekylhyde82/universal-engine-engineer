# V.I.S.I.O.N. + D.D. — Production Gates and Acceptance Tests

**Status:** Proposed release criteria; no tests claimed as executed.  
**Release posture:** NO-GO until all applicable gates pass with evidence.

## 1. Nine acceptance groups

| # | Acceptance group | Minimum pass criteria | Evidence |
|---:|---|---|---|
| 1 | Visual observation | Correct source/session/viewport binding; capture timestamps; uncertainty and expiry; stale-frame rejection | Automated adapter tests and labelled evaluation set |
| 2 | Context and identity | Correct app, account/session and target identification; account-switch detection | Adversarial integration tests |
| 3 | Grounding and uncertainty | Multi-signal target grounding; calibrated thresholds; ambiguity and occlusion stop | Precision/recall, false-target and abstention report |
| 4 | Planning | Typed plans with preconditions, postconditions, risk class and bounded scope | Schema tests and plan evaluation |
| 5 | Policy and approval | Deny-by-default; action/session/digest-bound one-use grants; revocation; R3 approval; R4 denial | Policy unit tests, bypass tests and approval audit |
| 6 | Execution | Only allowlisted actions; fresh pre-action checks; no arbitrary commands; bounded timeouts | Adapter conformance and sandbox tests |
| 7 | Failure and recovery | No blind retry of non-idempotent actions; UNKNOWN reconciliation; bounded recovery | Fault injection and duplicate-action tests |
| 8 | Independent verification | Verifier can disagree with executor; VERIFIED only on sufficient independent evidence | End-to-end evidence tests and reviewer report |
| 9 | Memory, audit and operations | Provenance, minimised retention, tamper-evident evidence, monitoring, kill switch, backup/restore and rollback rehearsal | Audit, privacy, resilience and operational test reports |

Passing a group requires evidence for the actual release commit and configuration. A design review or mock-only test is insufficient.

## 2. Mandatory CI checks

- Schema validation and backward-compatibility tests.
- Unit tests for policy, grants, state machine, idempotency and redaction.
- Adapter contract tests with deterministic fixtures.
- Static analysis, lint, type checking and formatting.
- Dependency and licence review; vulnerability scanning and SBOM generation.
- Secret scanning and forbidden-permission/configuration checks.
- Prompt-injection and adversarial evaluation suite.
- Build reproducibility and artifact provenance.
- Coverage of critical policy branches, failure paths and denied actions.
- Test reports linked to exact commit SHA and dependency lockfile.

CI green is necessary but not sufficient for production.

## 3. Release gates

### Gate A — Design approval
- Scope and first platform fixed.
- Interface contracts and register references reviewed.
- Threat model and privacy impact reviewed.
- Data retention and consent requirements approved.

### Gate B — Implementation complete
- Runtime components and adapters implemented.
- Policy enforcement independent from model.
- Action ledger and verifier implemented.
- Stop, revoke and safe-shutdown paths implemented.

### Gate C — Verification complete
- Nine acceptance groups pass.
- Adversarial and fault-injection tests pass.
- No unresolved critical/high security findings.
- Independent reviewer verifies evidence and limitations.
- Supported app/platform matrix published.

### Gate D — Staging readiness
- Secrets provisioned outside source control.
- Identity and device/session binding active.
- Monitoring, alerting, incident response and rollback configured.
- Backup/restore and recovery rehearsal complete.
- Live tests limited to a non-production account and low-risk actions.

### Gate E — Production authorisation
- Explicit accountable owner and independent security approval.
- Final commit and artifact digests recorded.
- All blocking issues closed or formally accepted with documented risk owner.
- Release is limited to the tested platform/app/action allowlist.
- Human confirmation remains mandatory for R3 actions.
- Rollback and kill switch tested on the production configuration.

## 4. Release-blocking conditions

Any of the following is an automatic NO-GO:
- missing or bypassable policy enforcement;
- unbound or reusable approval grant;
- ability for the model to mint its own authority;
- stale or ambiguous target can still execute;
- executor can run arbitrary commands;
- non-idempotent action is retried after unknown outcome;
- verifier trusts only executor assertion;
- raw secrets appear in logs, screenshots or memory;
- no working stop/revoke control;
- no evidence for the actual release commit;
- unresolved critical/high security issue without a formally approved exception.

## 5. Operational readiness checklist

- [ ] Supported platform, app and action allowlist published.
- [ ] User consent and OS permissions documented.
- [ ] Least-privilege identity and session binding tested.
- [ ] Policy and approval service health monitored.
- [ ] Action ledger access controls and external checkpoints configured.
- [ ] Privacy redaction and retention tested.
- [ ] Rate limits, timeouts, circuit breakers and bounded retries configured.
- [ ] Kill switch, session revoke and adapter disablement tested.
- [ ] Incident response, evidence preservation and notification process documented.
- [ ] Backup, restore, continuity and recovery objectives measured.
- [ ] Rollback rehearsal passed.
- [ ] Independent security review and production approval recorded.

## 6. Evidence record template

For every release candidate record:
- repository, branch, commit SHA and artifact digest;
- runtime, adapter, model and policy versions;
- supported OS/device/app versions;
- exact test commands and workflow run URLs;
- test counts, failures, skips and coverage;
- security scan, SBOM and licence results;
- adversarial and fault-injection outcomes;
- staging results and redacted operational evidence;
- independent verifier and security approver;
- residual risks, expiry/review date and rollback reference.

## 7. Current decision

**NO-GO — real-browser-tested prototype, not production ready.**

This branch now includes executable policy evaluation, Ed25519 grant primitives, a single-host nonce ledger, an HTTP grant service, a consent-gated Playwright-compatible browser adapter and a signed readback verification primitive. The latest recorded test run reported 69 passing tests at commit `75ff874873ed1784009a5ea06c076ea51546a70a`. Two integration tests launch real Chromium against a temporary local fixture and validate a signed allowlisted navigation plus an external-redirect block. The tests do not establish a production browser host, user/device identity provider, trusted consent/approval UX, independent verifier provider, physical device operation or production deployment readiness.

The following release blockers remain: production OS-level network egress isolation (including WebRTC/UDP); production identity and trusted consent/approval providers; secure key provisioning/rotation; independently operated read-only verifier; externally signed audit checkpoints, protected backup/restore and retention; calibrated visual model and privacy redaction; Android companion and device validation; AFI PRIME and EB9PRIME runtime integration; adversarial and fault-injection campaigns; monitoring, incident response, rollback and independent security approval. CodeQL static analysis is configured, but its first result must be reviewed before release.

No live screen/camera/device access is enabled by this repository work. The adapter must not be wired to a live user session or used for consequential actions until the relevant gates are implemented and independently approved.
