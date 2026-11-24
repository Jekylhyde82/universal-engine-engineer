# OMNISIGHT PRIME — Batched Implementation Work Plan

**Status:** Planned; no implementation completion is implied.  
**Parent specification:** `architecture/OMNISIGHT_PRIME_9_FOLD_OMNI_INTRINSIC_SPEC_v0.1.md`

## Parallel work packages

| Work package | Deliverable | Dependency | Exit evidence |
|---|---|---|---|
| WP-A Contracts | Versioned schemas and capability manifest | None | Schema validation fixtures and compatibility tests |
| WP-B Evidence Fabric | Evidence record model, digesting, append semantics | WP-A | Tamper, provenance, access and retention tests |
| WP-C World Model | Entity/assertion graph and temporal/spatial relations | WP-A, WP-B | Ground-truth graph fixtures and contradiction tests |
| WP-D Android acquisition | Consent-gated MediaProjection session and frame pipeline | WP-A | Device capture, revocation, lifecycle and resource tests |
| WP-E OCR/image adapters | OpenCV preprocessing and replaceable OCR adapters | WP-A, WP-D | OCR accuracy/geometry benchmark and provenance checks |
| WP-F AFI orchestration | Registry, policy dispatch, correlation and fusion | WP-A, WP-B | Multi-engine conflict and degraded-mode tests |
| WP-G Independent verification | Separate verifier contract and evidence reports | WP-A, WP-B, WP-F | Demonstrated independence and seeded-fault detection |
| WP-H Device/performance | OPPO A6 benchmark harness and workload policy | WP-D, WP-E | Peak RAM, latency, energy, thermal and offline reports |

## Batch execution strategy

- Run WP-A first because all packages depend on stable contracts.
- In parallel after WP-A: WP-B, WP-D and WP-G interface design.
- After WP-B: WP-C and WP-F can progress in parallel.
- WP-E follows the Android acquisition interface; WP-G integrates after AFI contracts stabilize.
- Run device benchmarks continuously from the first Android vertical slice.
- Integrate only reviewed changes with passing targeted tests; retain failed experiments and their evidence.

## First vertical slice acceptance

A user-authorised Android screen capture produces a frame; OpenCV prepares a derived image; an OCR adapter returns text and geometry; the system records source, transformation and observation evidence; AFI correlates the observation; the world model stores an evidence-linked assertion; an independent verifier checks fixture-grounded results.

## Release gate

No deployment or operational claim until target-device tests, privacy/security review, licence review, failure handling, rollback and independent verification are documented and approved.
