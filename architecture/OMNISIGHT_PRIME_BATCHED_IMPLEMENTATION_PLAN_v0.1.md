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


## Additional work package — security and privacy

| Work package | Deliverable | Dependency | Exit evidence |
|---|---|---|---|
| WP-I Security/privacy | Threat model, consent and permission design, untrusted-input isolation, storage/retention controls, supply-chain assurance | Initial design can proceed independently; implementation gates apply to WP-B through WP-G | Threat review, abuse-case tests, privacy lifecycle evidence and independent security acceptance |

WP-I design baseline is recorded in `architecture/OMNISIGHT_PRIME_SECURITY_PRIVACY_THREAT_MODEL_v0.1.md`. It is proposed for review and does not represent implemented controls.

## Execution status snapshot — 2026-11-25

| Work package | Current state | Evidence / remaining gate |
|---|---|---|
| WP-A Contracts | CONTRACT BASELINE VERIFIED | Capability-manifest and observation-envelope Draft 2020-12 schemas; GitHub Actions run 45480218880 passed all 15 schema/contract tests on the PR merge ref containing head 921c40fa0de2dab63afceaf1b40eb32122c661b1. Runtime compatibility and downstream contract integration remain. |
| WP-B Evidence Fabric | NOT STARTED | Record model, storage, digest chain, retention and tamper tests remain. |
| WP-C World Model | NOT STARTED | Typed entity/assertion model, temporal relations and contradiction handling remain. |
| WP-D Android acquisition | NOT STARTED | Consent-gated MediaProjection implementation and device verification remain. |
| WP-E OCR/image adapters | NOT STARTED | Adapter implementation and labelled accuracy/geometry benchmark remain. |
| WP-F AFI orchestration | DESIGN INTERFACE PENDING | Must bind to the repository's canonical AFI PRIME and existing nine-instance runtime; do not create a competing fusion authority. |
| WP-G Independent verification | DESIGN INTERFACE PENDING | Must preserve separation from producers and return UNKNOWN when evidence is absent or unverifiable. |
| WP-H Device/performance | NOT STARTED | Target-device measurement required; no performance assumptions are accepted as results. |
| WP-I Security/privacy | DESIGN BASELINE DELIVERED | Threat model v0.1 committed; review and all implementation/abuse-case gates remain. |

The current branch is a design-and-contract increment, not a runnable OMNISIGHT runtime. Keep the PR in draft until contract CI has run on the exact head, architecture and security reviews are complete, and implementation changes are separately tested.


### WP-A verification evidence

- GitHub Actions run [45480218880](https://github.com/Jekylhyde82/universal-engine-engineer/actions/runs/45480218880): SUCCESS.
- 15 tests passed, 0 failed, using Python 3.12.16 and `jsonschema[format]==4.23.0`.
- PR head under test: `921c40fa0de2dab63afceaf1b40eb32122c661b1`; CI checked out merge ref `9a7f1adff742f2c262b2344c8b740a97b842b80d`.
- This closes the initial schema-definition and fixture-validation gate only. It does not establish runtime, security, device, model-quality or production acceptance.
