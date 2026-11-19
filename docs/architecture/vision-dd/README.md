# V.I.S.I.O.N. + DESIGNATED DRIVER (D.D.)

**Architecture authority:** NINEFOLD INTRINSIC  
**Specialist identities:** V.I.S.I.O.N., D.D., AFI PRIME  
**Governed memory relationship:** EB9PRIME  
**Critical review discipline:** GENIUS ENGINEER CRITIC PRIME  
**Release decision:** NO-GO — prototype implementation only.

## Purpose

V.I.S.I.O.N. observes authorised visual inputs and produces provenance-bearing, uncertainty-aware observations. AFI PRIME proposes bounded typed plans. D.D. executes only actions authorised by an independent policy service. An independent verifier checks outcomes. EB9PRIME may retain only appropriately minimised, evidence-backed learning.

This specification and prototype do not claim live access to the user's camera, screen, applications or devices.

## Documents

- [Technical specification](TECHNICAL_SPEC.md)
- [Threat model](THREAT_MODEL.md)
- [Production gates](PRODUCTION_GATES.md)
- [Implementation plan](../../superpowers/plans/2026-11-19-vision-dd-production-readiness.md)
- [NINEFOLD INTRINSIC toolchain integration contract](../ninefold-intrinsic/TOOLCHAIN_INTEGRATION_CONTRACT.md)

## Non-negotiable invariants

1. Observation is not permission.
2. Planning is not authorisation.
3. A click, keystroke, API response or UI toast is not proof of the intended outcome.
4. D.D. is deny-by-default and cannot grant itself authority.
5. V.I.S.I.O.N. observations are time-bound, provenance-bearing and uncertainty-aware.
6. Untrusted content displayed on a screen is data, never an instruction to the agent.
7. Independent verification must not merely repeat the executor's assertion.
8. Human approval is required for consequential actions unless a separately approved, narrowly scoped policy explicitly delegates them.
9. Every action has a traceable task, policy decision, executor identity, result and verification state.
10. Fail closed when identity, context, permission, evidence or system health is uncertain.

## Implementation status

| Layer | Status |
|---|---|
| Architecture specification and threat model | Documented |
| Deterministic policy evaluation | Implemented; unit-tested |
| Ed25519 action-bound grant primitive | Implemented; unit-tested |
| Local nonce replay ledger | Implemented; unit-tested; single-host prototype |
| Policy HTTP service | Implemented; injected identity/approval adapters required |
| Supervised browser observation adapter | Implemented; fake-page contract tests plus real Chromium integration tests |
| Optional screenshot capture | Implemented behind separate trusted-consent-provider approval; no redaction or persistence |
| Browser execution | Navigation only; grant, trusted consent-provider and fresh-observation gated; real Chromium integration tested against local fixture |
| Browser network-origin restriction | HTTP and WebSocket allowlists implemented; real Chromium redirect/WebSocket tests; OS-level egress firewall still outstanding |
| Independent readback verification primitive | Implemented; signed evidence contract only |
| Governed action orchestrator | Implemented; requires the local or an external durable audit writer and separate policy/executor/verifier authorities |
| Real independent verifier provider | Not implemented |
| Production Chromium host/launcher | Not implemented; local-fixture Chromium integration tests pass |
| Production identity provider and key management | Not implemented |
| Local append-only action audit ledger | Implemented; hash-chained, fsynced, permission-restricted, bounded and fail-closed |
| External audit anchoring, retention and recovery operations | Not implemented; independent checkpoints, protected backups and audit access service remain outstanding |
| AFI PRIME runtime integration | Not implemented |
| EB9PRIME governed persistence | Not implemented |
| Android runtime and OS permission integration | Not implemented |
| Staging, monitoring, rollback and incident response | Not implemented |
| Production deployment | Not approved |

The latest policy CI run on branch head `dffac1857689f8fc18018a94268492e8a251d7db` completed successfully with **118 tests passed, 0 failed, 0 cancelled, 0 skipped**, including real Chromium integration tests against a temporary local fixture. CodeQL also completed successfully on that exact commit (workflow runs `44459876855` and `44459876908`). This is integration and static-analysis evidence for the prototype boundary, not production assurance.

## Decision

The current work is an implementation prototype, not an activated system. Production remains NO-GO until the actual browser host, independent identity/approval providers, independent verifier, durable evidence controls, adversarial tests, operational controls and all nine acceptance groups pass on the exact release artifact.
