# Ninefold Master Register Index

**Document ID:** UEE-REG-001  
**Version:** 1.0.0  
**Date:** 2026-11-15  
**Status:** Baseline and reconciliation in progress

## Governing principle

**We build capabilities, not illusions. We measure results, not intentions.**

The architecture is governed through nine independent, versioned and cross-referenced registers. Every entry requires a stable ID, canonical name, accountable owner, purpose, provenance, version, lifecycle status, last-verified timestamp, evidence references, dependencies, related-register references, known gaps and next action. Missing entries must not be invented to satisfy a target count.

## Canonical nine-register index

| ID | Register | Target / accounting rule | Baseline status |
|---|---|---|---|
| R01 | Major Division Register | 9 major divisions | Target retained; complete source-backed inventory requires reconciliation. |
| R02 | System Register | 90 systems | 60 named entries are documented in the recovered blueprint; 30 positions remain undefined/unverified. |
| R03 | Architecture Register | 184 architecture records | Target retained; complete 184-entry inventory not yet evidenced. |
| R04 | Responsibility Layer Register | 18 layers | Target retained; complete ownership and authority mapping requires reconciliation. |
| R05 | Intelligence Register | No fixed count | Inventory intelligence functions and distinguish conceptual labels from implemented capability. |
| R06 | Capability Register | No fixed count | Inventory reusable capabilities with contracts, dependencies, maturity and evidence. |
| R07 | Lifecycle & Governance Register | Controlled lifecycle | Record discovery, proposal, evaluation, approval, integration, rejection, deferral, retirement and rollback. |
| R08 | Evidence & Verification Register | Evidence-backed | Store tests, audits and independent verification; prohibit self-certification. |
| R09 | Cross-reference & Traceability Register | Referential integrity | Link all register records, source artefacts, decisions, tests and versions. |

## Count separation

These quantities describe different architectural dimensions and must not be conflated:

- **90 Systems** is the System Register target.
- **184 Architecture records** is the Architecture Register target, not 184 additional systems.
- **18 Responsibility Layers** describe accountability and authority, not 18 systems or agents.
- **90 Core Nodes** is a separate dual-ninefold structural design count; it does not replace the System Register.
- **81 coordination relationships** are matrix relationships, not additional nodes, systems or executable agents.
- The recovered **60-system list** is a baseline only. The remaining 30 system records require source-backed identification and approval; no speculative names are to be added.

## Capability maturity and lifecycle

Capability maturity is recorded as distinct evidence states:

- `DECLARED`: named in architecture or a capability profile only.
- `IMPLEMENTED`: an inspectable implementation artefact exists.
- `TESTED`: tests have run with recorded scope, environment, versions and results.
- `VERIFIED`: independent evidence confirms defined acceptance criteria.

Lifecycle states are:

`DISCOVERED → PROPOSED → UNDER_EVALUATION → APPROVED → INTEGRATED`

Alternative outcomes: `REJECTED`, `DEFERRED`, `RETIRED`.

Discovery is not approval; approval is not implementation; implementation is not testing; testing is not independent verification.

## Initial R06 capability entry

**CAP-UPSTREAM-001 — Continuous Upstream-Change Intelligence & Audit**

- **Purpose:** Detect beneficial upstream improvements and breaking changes, security advisories, deprecations, API/schema/protocol changes, CI/toolchain changes and support lifecycle changes.
- **Status:** SPECIFIED — NOT VERIFIED.
- **Cadence:** Weekly, through the existing weekly capability-discovery automation.
- **Inputs:** Repository default branch and relevant active PR branches; manifests, lockfiles, dependency graphs, CI workflows, build images, source references, APIs and authoritative upstream releases/advisories.
- **Outputs:** Dated repository and dependency inventory; verified upstream findings; impact analysis; evidence links; risk-ranked recommendations; test and rollback requirements; prior-baseline comparison; explicit evidence gaps.
- **Guardrails:** Read-only. No automatic installation, upgrade, source mutation, merge, approval, production change or privilege expansion.
- **Planned-only watchlist:** LangGraph, llama.cpp, LlamaIndex, Qdrant, Promptfoo, DeepEval, OpenHands, SWE-agent and Goose. This list does not assert that these projects are installed.
- **Acceptance:** Demonstrated recurring runs, source-backed actual dependency inventory, improvement and breaking/security test coverage, baseline comparison, planned-versus-installed distinction, and independent verification.

Specification: [CAP-UPSTREAM-001](../capabilities/upstream-change-audit-spec.md)

## Repository evidence boundary — 2026-11-15

The connected repository default branch `main` exposed only `README.md` in its recursive tree during inspection. There are open draft PR branches containing additional engineering artefacts, including PR #9 (Universal Capability Acquisition Register), PR #13 (Performance Lab hardening/evidence contract) and this stacked PR #14. The default-branch snapshot must not be mistaken for the complete state of all open work.

The 90-System, 184-Architecture and 18-Responsibility-Layer targets are not marked complete by this index. The 60 recovered system entries remain a reconciliation baseline. No 90-system deployment or 90-Core-Node deployment is claimed.

## Verification checklist

1. Stable IDs are unique and schema-valid.
2. Counts reconcile without double-counting systems, architecture records, layers, nodes or relationships.
3. Every entry has provenance and an accountable owner.
4. Status labels are supported by inspectable implementation and test evidence.
5. Dependencies and external interfaces are versioned.
6. Cross-register references resolve and are not stale.
7. Security, permissions, rollback and lifecycle controls are explicit.
8. Independent reviewers can reproduce material findings.
9. Claims link to evidence rather than intentions.
