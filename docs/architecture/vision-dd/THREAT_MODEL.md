# V.I.S.I.O.N. + D.D. — Threat Model

**Status:** Initial design threat model; requires security review against the implemented platform.  
**Scope:** Visual observation, model planning, policy enforcement, delegated execution, verification, audit and memory.

## 1. Assets to protect

- User identity, credentials, sessions and account access.
- Screen contents, images, documents, messages and personal information.
- Funds, purchases, records, settings, permissions and externally visible actions.
- Policy definitions, approval grants, signing keys and audit evidence.
- Integrity of task plans, observations, action targets and verification results.
- Availability of the stop control and safe-recovery path.

## 2. Trust boundaries

1. User and trusted approval surface.
2. Operating system / browser / application.
3. Visual acquisition adapter.
4. Model and all model-produced output.
5. Deterministic policy enforcement service.
6. D.D. execution adapter.
7. Independent verification channel.
8. Evidence store, signer and EB9PRIME memory.

Treat the model, webpage, document, OCR output, screenshot content and tool-returned text as untrusted. Trust is established by identity, cryptographic binding, policy and validation, not by fluent language.

## 3. Principal threats and mandatory controls

| Threat | Failure mode | Required mitigation |
|---|---|---|
| Visual prompt injection | A webpage or image tells the model to ignore task policy | Treat observed content as data; isolate task instructions; policy is outside model control |
| Wrong-account action | UI changes or session is not the intended account | Bind task, observation, grant and executor to authenticated session; recheck immediately before action |
| Stale coordinates | Screen changes after perception | Observation expiry, viewport binding and fresh pre-action grounding |
| False target recognition | Similar buttons or ambiguous controls | Multi-signal grounding; confidence calibration; stop on ambiguity |
| Permission escalation | D.D. or model requests broader rights | Independent deny-by-default policy; immutable allowlists; short-lived grants |
| Approval spoofing | Page content imitates a confirmation prompt | Trusted approval UI outside the controlled content; bind approval to action digest and target |
| Replay | Previously approved action is repeated | Unique nonce, action ID, expiry, one-use grant and idempotency control |
| Duplicate transaction | Timeout triggers a second purchase/send | Mark UNKNOWN; reconcile authoritative state before retry |
| Executor compromise | Adapter performs actions beyond scope | OS-level sandbox, minimal privileges, signed adapter, action allowlist and kill switch |
| Audit tampering | Executor rewrites its own history | Separate write identities, external signed checkpoints and independent retention |
| Sensitive data leakage | Screenshots/logs/memory retain secrets | On-device redaction where possible, minimisation, no raw image persistence by default, secret scrubbing and retention limits |
| Model hallucination | Model claims a task succeeded | Only independent verifier may set VERIFIED |
| Denial of service | Endless retries or capture loop | Bounded retries, timeouts, rate limits, circuit breaker and stop control |
| Supply-chain compromise | Malicious package or dependency | Pinned dependencies, provenance, SBOM, vulnerability scans, signed builds and review |
| Unsafe recovery | Automatic rollback causes another harmful action | No assumed rollback; compensating action gets separate policy and approval |

## 4. Security invariants

- Model output is never an authority token.
- A permission grant is bound to one exact action, application, session and expiry.
- R3 actions require explicit per-action approval in v1.
- R4 actions are denied.
- Loss of policy service, identity, verifier or session binding fails closed.
- Unknown outcome is never silently retried.
- The executor cannot alter policy, audit evidence or verifier result.
- The verifier has read-only access to its evidence sources wherever practical.
- Kill switch and revocation remain available when the model is unavailable.
- Raw visual data is not stored unless necessary, consented and governed by a retention rule.

## 5. Required adversarial tests

At minimum:
- webpage prompt injection asking to disclose credentials or change task;
- fake login or approval overlay;
- account switch between observation and action;
- viewport resize or navigation after target detection;
- near-identical buttons and hidden/disabled controls;
- expired, replayed, altered and cross-session grants;
- policy service outage and malformed policy response;
- timeout after a purchase/send where outcome may have succeeded;
- verifier disagreement with executor result;
- log and memory attempts to store secrets;
- adapter restart while an action is in flight;
- kill-switch activation during a multi-step task.

## 6. Residual risks

Visual inference can be wrong even with confidence calibration. UI automation is brittle across application versions, localisation, dynamic layouts and accessibility defects. A compromised OS, browser, account or approved application can defeat higher-level safeguards. Independent verification may be unavailable for some applications. These limitations must be disclosed per supported app and must constrain the allowed task set.

## 7. Security approval

This document is not a penetration test or independent security sign-off. Production approval requires an implementation-specific threat review, abuse-case testing, dependency and supply-chain review, permission review, incident-response plan and named independent approver.
