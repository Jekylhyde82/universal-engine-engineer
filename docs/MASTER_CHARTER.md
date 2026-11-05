# UNIVERSAL ENGINE / ENGINEER — MASTER CHARTER

**Status:** Approved design principles; implementation and verification remain separately gated.

## 1. Authority and purpose

This charter governs the single authoritative UNIVERSAL ENGINE / ENGINEER repository. It establishes architecture-wide constraints, traceability, and evidence requirements. It does not itself prove that any specified subsystem has been implemented.

The repository is the authoritative architecture source. Governed subprojects may retain separate deployment, data, security, and release boundaries while remaining traceable to this master.

## 2. Constitutional engineering rule

**PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**

Every material claim must identify its evidence and provenance. Status language must distinguish:
- proposed;
- design-approved;
- specified;
- implemented;
- integrated;
- tested;
- independently verified;
- released / operational.

Do not promote a status without its required evidence. Record failed tests, limitations, outstanding risks, and unknowns rather than hiding them.

## 3. Foundational architecture

The mandatory foundation is nine Unified Master Intelligence Cores (UMICs). Each UMIC retains its distinct Master Core, AFI, and Fusion Synergy responsibilities. Specialist cores, engines, and capabilities remain distinct even when fused or coordinated.

The ninefold architecture is governed consistently. No count, hierarchy, capability, or relationship is inferred merely from symmetry; it must be specified and registered.

## 4. Intrinsic integration invariant

Applicable capabilities and controls are intrinsic to the component that needs them, not optional add-ons. This includes, where applicable:
- GENESIS identity and lifecycle traceability;
- security, privacy, and least-privilege boundaries;
- governance, accountability, and bounded authority;
- provenance, evidence, testing, and verification;
- error handling, observability, recovery, and evolution;
- accessibility and user-facing safeguards.

Applicability must be reasoned and recorded. “Intrinsic” does not mean every component receives every feature regardless of relevance.

## 5. Fusion and governance

Fusion preserves constituent identity, responsibility, and boundaries. Coordination does not imply ownership or unrestricted control.

**FOUNDATIONAL AUTHORITY ≠ UNRESTRICTED AUTHORITY.** No master intelligence, fusion intelligence, critic, or governance function is an absolute authority. AGSO PRIME may coordinate foundational fusion standards without unilateral control. CRITIC may challenge and scrutinise authority without gaining unrestricted authority itself.

## 6. GENESIS and lifecycle

GENESIS identity and traceability are required for every applicable architecture element: systems, engines, cores, specialists, agents, modules, submodules, subsystems, components, frameworks, and architecture records.

Lifecycle changes must be versioned and traceable to decisions, owners, source commits, tests, and evidence.

## 7. Independent registers

Maintain four independent registers:
1. 9 Major Divisions;
2. 90 Systems;
3. 184 Architecture Entries;
4. 18 Responsibility Layers.

Preserve existing numbering. A cross-reference matrix connects entries across registers; it does not merge, renumber, evenly allocate, or assume one-to-one relationships.

## 8. Mirrored build and drift control

The source architecture and operational mirror must remain aligned in registry, version, documentation, tests, benchmarks, and evidence. Detect and report drift. A mirror is not considered equivalent merely because it has the same name or a recent sync timestamp.

## 9. Change and release gates

Every significant change should include:
- rationale and scope;
- affected register entries and dependencies;
- threat / risk assessment where relevant;
- implementation and rollback notes;
- automated tests and their results;
- provenance and commit identity;
- independent verification where the claim warrants it.

Security-sensitive changes fail closed. Secrets, private keys, access tokens, and credentials must never be committed.

## 10. Subprojects

Subprojects such as Discworld Pocket may be governed within this master repository while preserving their own domain rules, content provenance, deployment boundaries, and release criteria. Their inclusion in the architecture does not establish implementation or ownership of third-party content.

## 11. Evolution

The architecture may evolve through reviewed, evidence-backed changes. No constituent can bypass this charter by claiming greater intelligence, speed, capability, or foundational status.
