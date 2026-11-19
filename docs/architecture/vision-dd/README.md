# V.I.S.I.O.N. + DESIGNATED DRIVER (D.D.)

**Architecture status:** Design specification proposed; not implemented or activated.  
**Target authority:** NINEFOLD INTRINSIC  
**Constituent identities:** V.I.S.I.O.N., DESIGNATED DRIVER (D.D.), AFI PRIME  
**Governed memory relationship:** EB9PRIME  
**Review standard:** GENIUS ENGINEER CRITIC PRIME

## Purpose

Define a safe, testable architecture for visual perception and delegated computer interaction. V.I.S.I.O.N. interprets authorised visual inputs. AFI PRIME reasons over observations and task context. D.D. executes only explicitly authorised, bounded actions. An independent verifier checks outcomes. EB9PRIME may retain appropriately minimised, evidence-backed learning.

This specification does not claim that any of these capabilities are currently running.

## Documents

- [Technical specification](TECHNICAL_SPEC.md) — component boundaries, data flow, contracts and lifecycle.
- [Threat model](THREAT_MODEL.md) — trust boundaries, abuse cases and required mitigations.
- [Production gates](PRODUCTION_GATES.md) — nine acceptance groups, release gates and go/no-go criteria.

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

## Current implementation status

| Layer | Status |
|---|---|
| Architecture specification | Proposed in this branch |
| Threat model | Proposed in this branch |
| Acceptance criteria | Proposed in this branch |
| V.I.S.I.O.N. runtime | Not implemented |
| D.D. executor | Not implemented |
| AFI PRIME runtime integration | Not implemented |
| Independent policy enforcement | Not implemented |
| Independent outcome verifier | Not implemented |
| EB9PRIME governed persistence | Not implemented |
| Device / desktop adapters | Not implemented |
| CI, security and integration evidence | Not yet produced |
| Production deployment | Not approved |

## Decision

This specification is a prerequisite for implementation, not a production approval. All unresolved design choices and release blockers must remain visible until supported by code, tests and independent evidence.
