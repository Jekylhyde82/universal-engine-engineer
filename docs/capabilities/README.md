# Universal Capability Acquisition Register

**Register ID:** UCA-REG-001  
**Version:** 0.1.0  
**Research baseline:** 2026-11-06  
**Status:** Research baseline — candidates are not approved integrations.

## Purpose

A continuously extensible, evidence-backed register of repositories and other sources that may supply capabilities to the U.N.I.V.E.R.S.A.L. E.N.G.I.N.E. / E.N.G.I.N.E.E.R. It is a candidate backlog, not an integration approval, security clearance, legal opinion, or proof that a capability works in our environment.

## Governing rules

- **PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**
- Preserve each provider's identity, responsibilities, licence obligations and governance boundaries.
- Prefer provider-neutral adapters and replaceable integrations over wholesale repository imports.
- Discover capability gaps and methods; do not optimise for repository counts.
- Popularity, stars, demos and maintainer claims are not proof of suitability.
- Enforce permissions and isolation outside the model. Human approval is required for defined high-impact actions.
- Accepted capabilities require reproducible proof, provenance, rollback and source/operational mirror parity.

## Register contents

The machine-readable record is [universal-capability-acquisition-register.json](./universal-capability-acquisition-register.json). It contains candidate records, source links, initial licence leads, provisional priorities, risks, evaluation gates and next actions.

### Initial P1 evaluation queue

| Candidate | Proposed role | Why evaluate |
|---|---|---|
| DeepAgents + LangGraph | Agent harness + orchestration | Planning, delegation and durable state; evaluate as complementary layers |
| OpenHands Software Agent SDK | Software engineering agent | Controlled codebase work and isolated workspaces |
| Browser Use + Playwright MCP | Browser agent + deterministic browser control | Complementary high-level and structured browser interaction |
| Kestra | Workflow orchestration | Durable, scheduled and event-driven automation |
| Activepieces Community Edition | Service connectors | Broad integration ecosystem; separate commercial feature boundary |
| Cognee | Memory and knowledge graph | Persistent, structured knowledge and retrieval |
| OPA + gVisor | Policy decision + workload isolation | Governance and execution containment outside the model |
| Promptfoo + DeepEval + Langfuse | Adversarial testing + metrics + tracing | Distinct evaluation and observability responsibilities |

These are evaluation priorities, not integration approvals. The initial queue must be narrowed through compatibility, licence, maintenance, security and resource reviews.

## Candidate groups

1. Agent planning and orchestration.
2. Software engineering agents.
3. Browser and computer automation.
4. Workflow automation and service integrations.
5. Persistent memory and knowledge graphs.
6. Policy, authorization and sandboxed execution.
7. Evaluation, observability and red-team testing.
8. Local inference, document retrieval and vector storage.

## Mandatory evaluation gates

| Gate | Required evidence |
|---|---|
| G0 — Source identity | Canonical repository, pinned commit/release, retrieval date |
| G1 — Licence and provenance | Root/nested licences, dependency and asset inventory, hosted/enterprise boundary |
| G2 — Maintenance and compatibility | Release/commit health, security advisories, supported runtimes, API stability |
| G3 — Security and governance | Threat model, prompt-injection tests, least privilege, sandbox/network/secrets controls |
| G4 — Resource and deployment | CPU/RAM/storage/latency/network benchmarks, hosting and offline behavior |
| G5 — Proof of capability | Acceptance criteria, isolated reproducible tests, negative tests and limitations |
| G6 — Integration approval | Narrow adapter contract, replaceability, rollback and data migration plan |
| G7 — Operational verification | Deployed identity, integration/security/reliability/performance tests, independent review, mirror parity |

**A failure at a critical licence, security, maintenance or resource gate blocks approval.** Do not hide a weak dimension in an average score.

## Status vocabulary

DISCOVERED → TRIAGE_REQUIRED → EVALUATION_IN_PROGRESS → PROOF_OF_CAPABILITY_REQUIRED → APPROVED_FOR_ADAPTER_DESIGN → APPROVED_FOR_IMPLEMENTATION → IMPLEMENTED → TESTED → INDEPENDENTLY_VERIFIED → OPERATIONAL.

Alternative terminal/holding states: REJECTED, DEFERRED, BLOCKED.

Approval is not implementation. Implementation is not testing. Testing is not independent verification. Verification is not proof of operational suitability outside the tested environment.

## First engineering actions

1. Pin upstream commit/release identities for P1 candidates.
2. Complete exact-revision licence and dependency inventory before importing or distributing code.
3. Define provider-neutral contracts for agent runtime, tool gateway, memory, workflow execution, policy enforcement and evidence.
4. Build isolated proof-of-capability benchmarks for each P1 vertical slice.
5. Integrate one narrow capability at a time; preserve rollback and provider replacement.
6. Keep this register distinct from the existing six-source reconnaissance PR unless deliberate consolidation is reviewed.

## Current non-claims

- No candidate is installed or integrated by this register.
- No candidate has passed a security audit or operational benchmark.
- Licence labels are preliminary research leads, not legal clearance.
- No upstream test suites were executed during register creation.
- Priority labels indicate proposed evaluation order only.

## Design invariant

**Build for capability today. Design for possibilities tomorrow. Engineer for evolution indefinitely.**
