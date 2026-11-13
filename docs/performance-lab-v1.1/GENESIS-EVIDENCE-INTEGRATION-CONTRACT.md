# Performance Lab evidence integration contract — draft 0.1

## Status

**Proposed; not approved for production use.** This document defines a controlled integration boundary between the Python Performance Lab and the GENESIS Performance Lab. It does not merge their experimental protocols, scoring scales, or acceptance authorities.

## 1. Experimental protocols remain separate

The two laboratories answer different experimental questions and must remain protocol adapters over any future shared evidence infrastructure.

### Python Performance Lab

- PL-001 through PL-004 use baseline versus experimental conditions.
- PL-005 is the specialist-fusion experiment.
- PL-005 has exactly eleven arms: `baseline`, `specialist_1` through `specialist_9`, and `fused`.
- The current protocol requires at least three supplied repetitions per arm. At the minimum, PL-005 therefore requires 33 captured run records (11 arms × 3 repetitions).
- The Python rubric is version 1.0.0, scored 1–5, with a documented normalization to 0–100. Weighted scores are descriptive; hard gates remain independent.

### GENESIS Performance Lab

- Protocol 1.5 specifies five cases (P01–P05), two paired conditions (baseline and architecture-assisted), and three repetitions.
- Its planned matrix is 30 trials (5 × 2 × 3), not eleven arms.
- It requires trial-execution context metadata, blinded trial labels, scorer/reviewer separation, calibration evidence, and an Ed25519-signed evidence manifest bound to a candidate revision.
- Its rubric uses a 0–5 scale with eight dimensions. Its scoring semantics must not be silently converted to the Python 1–5 scale.

**Critical distinction:** eleven arms are eleven experimental configurations, not eleven engines or eleven architecture layers. The Python PL-005 protocol must not be substituted for the GENESIS paired-comparison protocol, or vice versa.

## 2. Shared evidence envelope — proposed

A future shared evidence core may standardise the transport and integrity envelope while leaving protocol-specific requirements to versioned adapters.

Minimum shared fields:

- evidence schema identifier and version;
- protocol identifier and protocol version;
- experiment, case, run, condition/arm, and repetition identifiers;
- UTC capture timestamp and accountable operator;
- subject/model/build identity and immutable configuration reference;
- canonical input reference and SHA-256;
- raw output artifact reference and SHA-256;
- rubric identifier/version, original scale, dimension identifiers, and unmodified raw scores;
- hard-gate results with explicit `pass`, `fail`, or `not_assessed` states;
- limitations, confounders, deviations, and capture status;
- reviewer identity/attestation and independent review evidence reference;
- candidate revision or build identity where applicable.

The envelope must preserve original source records. Adapters may add derived fields, but must never overwrite or silently reinterpret original values.

## 3. GENESIS-specific provenance extension

The GENESIS adapter retains its stronger Protocol 1.5 controls:

- explicit Unpersonalized Temporary Chat declaration and context reference;
- capture timestamp, settings, tools used, and raw-response hash;
- canonical prompt hash and frozen architecture-instruction hash for assisted trials;
- unique blind trial identifiers;
- distinct scorer and adversarial reviewer identities;
- calibration status and calibration artifact references;
- signed evidence manifest with externally trusted Ed25519 public key, signer identity/role, candidate revision binding, artifact path containment, and artifact-byte hash verification.

A submitted declaration is not proof that a real operator selected the declared context. Independent inspection of the referenced capture evidence remains necessary. A signature proves possession of a signing key, not the human identity or independence of its holder unless the trust process binds those separately.

## 4. Python-specific requirements to close before parity

The Python harness currently has strong schema, hash, hard-gate, repetition, and PL-005 dimension-comparability checks. The following are separate remaining controls:

1. Preflight every fully constructed run record against the schema before writing any output file.
2. Enforce test-to-condition compatibility in the common record validator used by both `validate` and `report`.
3. Reject score keys that are not identifiers in the versioned Python rubric.
4. Add trial-execution provenance, blind assessor separation, immutable raw-artifact references, and signed revision-bound manifests in a new run-record protocol version.
5. Validate specialist and fused configuration identity, including exact specialist/version references and an auditable fused composition. Configuration objects being present is not proof of isolation or fusion.
6. Add explicit resource measurements (latency, token/resource use, and cost) before making efficiency or synergy claims.

Items 1–3 are the scope of the current hardening branch. Items 4–6 require a separately versioned protocol change; they must not be smuggled into schema version 1.0.0.

## 5. Scoring interoperability

Do not average raw scores from different rubrics or scales.

- Preserve Python's 1–5 raw score and its rubric-defined normalization.
- Preserve GENESIS's 0–5 raw score and its rubric-defined anchors.
- A future common reporting view may display normalized values only when it also displays the source rubric/version, original raw score, transformation formula, and mapping version.
- Human governance approval is required before any cross-rubric mapping is used for acceptance decisions.
- A weighted aggregate never overrides a failed or unassessed mandatory hard gate.

## 6. Fusion-synergy acceptance logic

The Python PL-005 report may calculate a descriptive fused-versus-strongest-comparator delta only when all eleven arms meet the repetition gate and have the exact same assessed rubric-dimension identity set.

That delta alone is not synergy evidence. A defensible synergy conclusion additionally requires:

- the same task/input and scoring protocol across arms;
- independently verifiable specialist identities and isolated configurations;
- an auditable fused configuration showing which specialists were included and how;
- blinded independent scoring and adversarial review;
- per-dimension regressions and critical-failure analysis;
- ablation evidence to estimate each specialist's contribution;
- latency, resource, and cost measurements;
- repeated results and disclosed confounders;
- revision-bound raw artifacts and independent evidence verification.

A fused system that scores higher but incurs disproportionate cost, introduces critical failures, or fails ablation tests must not be described as a successful synergy result.

## 7. Required negative tests for eventual parity

- Missing or malformed trial-execution metadata.
- Raw-output or artifact hash mismatch.
- Invalid Ed25519 signature, wrong trusted-key fingerprint, or signer mismatch.
- Candidate revision mismatch.
- Absolute path, parent traversal, symlink escape, missing artifact, or duplicate artifact path.
- Duplicate trial IDs, blind labels, or case/condition/repetition combinations.
- Missing arm, incomplete repetitions, or inconsistent dimension identities.
- Unknown rubric dimension identifier or unapproved score-scale mapping.
- Scorer/reviewer identity collision or missing calibration evidence.
- Specialist configuration duplication, missing specialist version, or fused configuration that does not enumerate its components.
- Late invalid record in a batch must leave no partial dataset.

## 8. Governance and integration sequence

1. Land the current Python harness hardening in a separate draft PR after CI passes.
2. Approve this evidence contract and assign protocol owners.
3. Create a new, versioned shared evidence-envelope schema; do not break existing records.
4. Implement Python and GENESIS adapters independently.
5. Add cross-adapter contract and adversarial tests.
6. Execute authentic trials and independent scoring under each protocol.
7. Verify manifests and artifacts independently.
8. Submit a separate human release decision.

Discovery or test success does not automatically approve integration. The lifecycle is: Discovered → Proposed → Under Evaluation → Approved → Integrated / Rejected / Retired.

## 9. Current non-claims

At the time of this draft:

- Python PR #11 is draft and unmerged.
- GENESIS PR #22 is draft and unmerged.
- The Python CI pass verifies the harness revision only.
- GENESIS's 30-row trial matrix is planned evidence, not completed trials.
- No authentic Python PL-005 eleven-arm trial set has been established.
- No independent calibration/scoring, measured improvement, fusion synergy, or operational approval is established.

**PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**
