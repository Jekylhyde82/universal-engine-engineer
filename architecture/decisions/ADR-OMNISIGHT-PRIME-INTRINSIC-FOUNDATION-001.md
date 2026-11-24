# Architecture Decision Record — OMNISIGHT PRIME Intrinsic Foundation

**ID:** UEE-ADR-OMNI-001  
**Status:** Proposed for review  
**Date:** 2026-11-25  
**Related specification:** `architecture/OMNISIGHT_PRIME_9_FOLD_OMNI_INTRINSIC_SPEC_v0.1.md`

## Decision

Specify OMNISIGHT PRIME as the visual specialist capability within NINEFOLD INTRINSIC, with the existing canonical UNIFIED FUSION SYNERGY — AFI PRIME function intrinsic to its applicable capabilities and lifecycle controls.

The first implementation foundation is a shared, versioned contract model connecting:

1. Visual Evidence Fabric (source, observation, transformation, fusion, inference, verification and decision records).
2. Universal Visual World Model (evidence-linked entities, states, events, relations and assertions).
3. AFI orchestration (capability manifests, policy-filtered dispatch, correlation, conflict preservation and explicit degraded mode).

## Rationale

Starting with independent but interoperable contracts prevents early dependence on a specific OCR engine, VLM vendor, Android API wrapper or storage implementation. It also allows acquisition, evidence persistence, world-model logic and specialist adapters to be tested independently without weakening intrinsic integration.

## Decisions and constraints

- Reuse the existing canonical AFI PRIME identity; do not create a second fusion authority.
- Preserve nine scoped UMIC execution/state/evidence/fault-containment boundaries.
- Keep visual specialist identity distinct from the wider OMNI UNIVERSAL PERCEPTION INTELLIGENCE PRIME.
- Treat observations, interpretations, inferences and verified assertions as different epistemic states.
- Preserve disagreement and provenance through fusion.
- Default to deny for unregistered capabilities and unauthorised actions.
- Keep Android acquisition permission-gated and user-visible.
- Treat the 4 GB Android phone as a constrained endpoint until benchmarks prove otherwise.
- Keep model/runtime choices replaceable and licence-reviewed.
- No autonomous self-approval, unrestricted self-modification or unreviewed deployment.

## Consequences

Positive:
- Enables parallel work against stable contracts.
- Supports local-first and optional remote execution.
- Makes provenance and uncertainty available from the first vertical slice.
- Allows specialist engines to be replaced without rewriting the evidence model.

Costs and trade-offs:
- Contract/schema versioning and migration discipline are required.
- Evidence retention and privacy deletion require careful design.
- Multi-engine fusion adds latency and must be resource-budgeted.
- Independent verification needs a genuinely separate trust boundary.

## Deferred decisions

- Final 9 Major Division / 90 System / 184 Architecture Entry / 18 Responsibility Layer mappings.
- Exact Android minimum SDK and target SDK.
- OCR and VLM model selection.
- Durable evidence-artifact storage implementation.
- Remote inference provider and authentication architecture.
- Production identity, signing and external audit anchoring.

## Approval gate

This ADR remains proposed until reviewed against the master charter, canonical registers, security/privacy requirements and target-device constraints. Approval does not imply implementation.
