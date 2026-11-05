# Universal Capability Evaluation Engine — Specification

**Specification ID:** UCEE-SPEC-001  
**Version:** 0.1.0  
**Status:** Proposed specification; not implemented  
**Applies to:** U.N.I.V.E.R.S.A.L. E.N.G.I.N.E. / E.N.G.I.N.E.E.R., including applicable UMICs, AFIs, Engines and subordinate components.

## 1. Purpose

Define a repeatable, evidence-led process for discovering, screening, evaluating, proving and recommending capabilities from external projects or internally developed work.

The Evaluation Engine is a decision-support and evidence-orchestration capability. It does not grant itself authority to install software, import code, change production systems, grant permissions or approve high-impact actions.

## 2. Governing invariants

1. **PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**
2. A repository, package, model, service or demonstration is a candidate source—not a capability proof.
3. Popularity, stars, marketing claims and aggregate scores cannot override a failed mandatory gate.
4. Preserve source identity, provenance, licence obligations, component boundaries and provider replaceability.
5. No external code executes during source discovery or static evaluation.
6. Untrusted workloads run only in an explicitly approved isolated environment with least privilege.
7. Human approval is required before code import, dependency installation, credential access, production changes, data migration or other designated high-impact actions.
8. Every decision records evidence, its origin, observation time, evaluator, limitations and reproducible test instructions.
9. A capability is not considered operational merely because a design is approved, code is written, or a test passes in a mock environment.
10. Evaluation and improvement must not weaken security, reliability, correctness or governance to increase speed.

## 3. Evaluation lifecycle

| Stage | Name | Required output |
|---|---|---|
| E0 | Discover | Candidate identity and reason for discovery |
| E1 | Source verification | Canonical URL, owner, repository, immutable commit/release reference and retrieval timestamp |
| E2 | Provenance and licence | Exact licence evidence, dependency/asset inventory, notices and distribution/service boundaries |
| E3 | Maintenance and compatibility | Release/commit signals, supported runtimes, API stability, advisories and compatibility findings |
| E4 | Security and governance | Threat model, permissions, data flows, sandbox/network/secrets controls and negative-test plan |
| E5 | Resource and deployment | CPU, memory, storage, latency, network, hosting, offline and target-device constraints |
| E6 | Proof of capability | Isolated, reproducible tests against measurable acceptance criteria, including negative tests |
| E7 | Integration decision | Explicit decision, rationale, scope, reviewer, conditions, rollback and expiry/review date |
| E8 | Implementation verification | Exact deployed identity/configuration, integration tests, security/reliability/performance results, independent review and mirror-parity evidence |

A candidate may be rejected or deferred at any stage. Later stages must not be represented as passed when earlier mandatory evidence is missing.

## 4. Mandatory gates and hard stops

The existing UCA-REG-001 gates G0–G7 remain authoritative. This specification adds execution discipline to those gates; it does not silently replace or waive them.

The following conditions block approval:

- Source identity cannot be pinned or provenance cannot be established.
- Licence, dependency, model, dataset or asset obligations are unresolved for the intended use.
- A critical security issue, uncontrolled privilege path or inadequate isolation remains open.
- Required runtime, hosting or resource constraints are incompatible with the target.
- Acceptance criteria cannot be reproduced or material negative tests fail.
- Rollback, data handling or provider replacement cannot be adequately explained.
- Required independent review or evidence is absent.

A blocked or failed gate cannot be offset by strong scores elsewhere.

## 5. Scoring policy

Score each dimension from 1 to 5 only when supporting evidence exists:

- capability value;
- maturity and maintenance;
- integration fit;
- security and governance fit;
- licence and distribution fit;
- resource and deployment fit;
- proof quality and reproducibility.

Use `NOT_ASSESSED` when evidence is insufficient. Do not convert missing evidence into a neutral score. Do not calculate a single average that conceals a critical weakness. Scores prioritise investigation; they do not grant approval.

For each score, record the evidence references, evaluator, observation date, confidence and known uncertainty.

## 6. Decision states

Use these states as distinct, non-interchangeable claims:

- `DISCOVERED`
- `SCREENING`
- `EVIDENCE_INCOMPLETE`
- `EVALUATION_IN_PROGRESS`
- `PROOF_READY`
- `PROOF_FAILED`
- `APPROVED_FOR_ADAPTER_DESIGN`
- `APPROVED_FOR_IMPLEMENTATION`
- `IMPLEMENTED`
- `TESTED`
- `INDEPENDENTLY_VERIFIED`
- `OPERATIONAL`
- `REJECTED`
- `DEFERRED`
- `BLOCKED`
- `DEPRECATED`

A state transition requires its defined evidence and an auditable decision record. Approval is not implementation; implementation is not testing; testing is not independent verification; verification is scoped to the tested version and environment.

## 7. Proof-of-capability test contract

Every proof plan must state:

- the capability claim being tested;
- the exact candidate commit/package/model/service version;
- test environment and resource limits;
- prerequisites and permitted network/data access;
- measurable acceptance criteria and thresholds;
- positive, negative, boundary and failure-recovery tests;
- expected outputs and machine-readable result format;
- reproducibility instructions and test-data provenance;
- known limitations and untested conditions;
- evidence artifact locations and content hashes, where available.

Mocks may validate an adapter contract but cannot prove live provider behavior. A benchmark must identify hardware, configuration, workload, sample size and measurement method.

## 8. Approval and authority boundaries

The Evaluation Engine may collect evidence, run approved isolated tests, calculate dimension scores and recommend a disposition. It may not self-approve an integration or expand its own permissions.

Approval records must identify the authorised human reviewer or governance authority, approved scope, conditions, timestamp and review/expiry date. Changes to source revision, licence, dependency set, permissions, data flows or deployment environment trigger re-evaluation of affected gates.

## 9. Evidence record minimum

Every evaluation record must include:

- unique evaluation ID and candidate record ID;
- canonical source and immutable source revision;
- evaluation start/completion timestamps;
- gate-by-gate status and evidence references;
- dimension scores or `NOT_ASSESSED`;
- test plan, environment, results and failures;
- decision, rationale, reviewer and approval scope;
- limitations, residual risks, rollback and next actions;
- evidence provenance and integrity metadata.

Evidence references must resolve to retained artifacts or stable source locations. A URL alone is not proof that its content was inspected at the stated time.

## 10. Initial proof sequence

Do not evaluate the entire P1 queue simultaneously. Select one narrow vertical slice at a time.

Recommended first slice: **policy decision and execution isolation** (OPA + gVisor) because the architecture needs enforcement boundaries before granting agent workloads broader tool or code-execution capability.

The proof must establish the distinct roles: policy decision versus actual enforcement, and workload isolation versus application-level authorization. It must test fail-closed behavior, denied actions, allowed actions, escape/privilege assumptions, network restrictions, resource limits and audit evidence. gVisor suitability must be assessed on a supported remote host; direct deployment on the user's Android phone is not assumed.

Second slice: **agent harness and orchestration** (DeepAgents + LangGraph), evaluated as potentially complementary layers rather than presumed interchangeable products. Test state persistence/recovery, delegation boundaries, human approval, tool permission enforcement, interruption handling and reproducible task outcomes.

These are proposed evaluation sequences, not integration approvals.

## 11. Completion criteria for this specification

This specification is complete as a design artifact only when its record format, gate mappings, decision transitions and proof contract have been reviewed. It is not an implemented evaluator, policy enforcement point, sandbox, benchmark suite or operational service.

## 12. Governing directive

**Build for capability today. Design for possibilities tomorrow. Engineer for evolution indefinitely.**
