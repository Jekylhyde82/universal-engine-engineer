# Performance Lab adversarial audit — 2026-11-10

## Scope and assurance level

Reviewed the V1.0 catalogue, pilot fixtures, scoring rubric, schemas, capture runner, report generator, tests and CI workflow on the isolated implementation branch. This is an internal engineering audit, not an independent third-party review or a model-quality evaluation.

## Findings and dispositions

### A-01 — PL-005 multi-arm synergy protocol
**Severity: Critical for synergy claims.**
**Implementation disposition: Remediated in harness; experimental evidence outstanding.**

The original two-arm runner could not capture the required baseline, isolated specialist and fused comparisons. The runner now requires PL-005 to provide exactly eleven arms: baseline, specialist_1 through specialist_9, and fused. Each arm has its own configuration object and at least three supplied repetitions. The report compares fused against the strongest baseline/isolated-specialist comparator only when every comparator is scored and assessed-weight coverage matches.

**Remaining acceptance work:** identify the exact specialist/version in each configuration, execute all arms on the same task and rubric, collect latency/resource costs and ablation evidence, and obtain independent scoring. A descriptive score delta is not proof of synergy.

### A-02 — PL-001 reference fixture incomplete
**Severity: High for correctness scoring.**
**Implementation disposition: Remediated as a self-contained fictional fixture.**

PL-001 now includes a self-contained fictional Northstar Edge Gateway source packet: five explicit supported facts and two explicitly unsupported assertions. It warns against inferring encrypted throughput from interface line rates and requires evidence for certification and performance claims.

**Remaining acceptance work:** use a blinded answer key for independent scoring and ensure reviewers apply the same reference checks.

### A-03 — Partial benchmark batches
**Severity: High for dataset integrity.**
**Implementation disposition: Remediated in harness.**

The runner preflights all five test payloads, required arm keys, configuration objects and requested non-empty repetitions before writing any record. An automated regression test confirms a missing PL-005 arm leaves no partial output directory.

### A-04 — Configuration and output integrity
**Severity: High for reproducibility.**
**Implementation disposition: Remediated for tamper detection.**

Run records bind the fixed pilot input, canonicalized configuration and raw output with SHA-256 hashes. Validation and report generation recompute those hashes. This detects content alteration but does not authenticate model identity, operator identity, reviewer identity or the source system.

### A-05 — Benchmark asset schema coverage
**Severity: Medium.**
**Implementation disposition: Remediated in harness.**

Dedicated JSON Schemas now validate the test catalogue, pilot cases and scoring rubric. The run-record schema is separately meta-validated. Cross-file checks enforce exact test IDs, matching catalogue/case versions, unique test and dimension IDs, and rubric weights totaling 100.

### A-06 — Hard-gate semantics and reviewer provenance
**Severity: High for acceptance decisions.**
**Implementation disposition: Partially remediated in harness; independent evidence still outstanding.**

Hard gates now require explicit tri-state values: pass, fail or not_assessed. Four mandatory gates are required on every record. A PASS decision requires reviewer identity, a review reference and every mandatory gate explicitly marked pass. A FAIL decision requires reviewer identity, a review reference and at least one failed gate. Missing or unassessed gates cannot silently count as passing.

**Remaining acceptance work:** verify reviewer independence and the referenced evidence outside the capture process. The runner still cannot authenticate a reviewer or independently observe the underlying system.

## Current disposition

- Asset schemas and cross-file invariants: implemented.
- PL-001 self-contained reference fixture: implemented.
- PL-005 eleven-arm capture and strongest-comparator reporting: implemented.
- Partial-batch prevention and regression test: implemented.
- Input/configuration/output hash verification: implemented.
- Explicit tri-state hard gates and review-reference requirements: implemented.
- Latest CI: pending for the newest commits; update this disposition only after the matching head commit passes.
- Actual baseline/specialist/fused trials: not executed.
- Independent scoring and third-party adversarial review: not completed.
- Fusion synergy or model improvement: not demonstrated.
- Operational approval: not granted.

No benchmark result, synergy claim, model improvement claim or operational claim should be made until the relevant trials are executed and independently reviewed.


## Verification addendum — 2026-11-13

### A-07 — Report repetition and dimension comparability

**Disposition: Remediated in the report generator; regression-tested on the current PR head.**

The report now requires at least the greater of three repetitions or the catalogue protocol minimum for every condition. Repetition numbers must be distinct; duplicate repetition identifiers fail the gate. PL-005 comparison requires the exact same assessed rubric-dimension identity set across baseline, all nine isolated specialist arms, and fused. Equal aggregate weight coverage is not accepted as equivalent evidence. Missing arms and underfilled arms fail closed as NOT_VERIFIED; mismatched dimensions are NOT_COMPARABLE. A descriptive score delta is explicitly not a synergy claim.

Dedicated regression tests cover:
- fewer than three repetitions;
- duplicate repetition numbers;
- equal total dimension weight with different dimension identities;
- matching dimension identities; and
- a missing PL-005 arm.

**Exact verification evidence:** GitHub Actions run 43408768028 completed successfully on commit `ae5589d6f6ea51cb69c359307867805ed462edcc`. Dependency installation, `performance-lab validate --records tests/performance-lab`, and `pytest -q` all passed. This is harness verification only, not benchmark evidence.

### A-08 — GENESIS evidence-protocol parity

**Disposition: Partially aligned; full provenance parity is outstanding.**

The separate GENESIS Performance Lab in `Jekylhyde82/7282ALLSPARXPRIME`, PR #22, head `9541042f909e1e1f52eb49f1f96f2062d553f42d`, establishes a stronger evidence protocol than the Python Performance Lab currently enforces. Its inspected Protocol 1.5 runbook and runner include:
- a 20-column trial matrix with explicit Unpersonalized Temporary Chat confirmation, context/capture metadata, canonical prompt hashes, and architecture-instruction hashes;
- blind labels and separation of subject, scorer, and adversarial reviewer;
- recomputation of raw-response hashes;
- an Ed25519-signed evidence manifest bound to an exact candidate revision, trusted-key fingerprint, relative artifact paths, and verified artifact bytes; and
- fail-closed pair eligibility and calibration/governance requirements.

The Python Performance Lab currently validates supplied outputs, fixed pilot-input/configuration/output hashes, reviewer-supplied scores, hard gates, repetition sufficiency, and report comparability. It does **not** yet enforce equivalent per-trial context-isolation metadata, blind assessor separation, retained raw-artifact references, signed revision-bound evidence manifests, or independent identity-to-key trust.

Therefore, the Python report repair is verified, but full GENESIS evidence-protocol parity is **not** achieved. Do not describe the two labs as having equivalent provenance assurance.

**Next alignment work (separate controlled change):**
1. Define a Python run-record protocol revision with explicit trial-execution metadata and immutable raw-artifact references.
2. Define a blind trial matrix and enforce exact case/condition/repetition coverage and assessor separation.
3. Add a signed evidence-manifest format bound to the candidate revision and verify actual artifact bytes against an externally supplied trusted public key.
4. Map the Python rubric and hard-gate semantics to GENESIS without silently changing existing score meaning; version any mapping and require human approval.
5. Add negative tests for missing metadata, hash mismatch, invalid signatures, revision mismatch, path traversal, duplicate artifacts, and assessor conflicts.
6. Keep all actual trials, calibration, independent scoring, and release approval as separate evidence gates.

## Current disposition — 2026-11-13

- Python reporting repetition, dimension-identity, partial-dimension, and invalid test/condition defects: remediated and regression-tested.
- Exact latest code/test CI: passed on `155725c5f30c964ddde321ede870f33480224a56` (run 43409092478).
- Python capture/report harness: verified by automated checks only.
- GENESIS evidence-protocol parity: partial; explicit gap register recorded above.
- Authentic model trials, independent scoring, calibration, third-party review, measured improvement/synergy, and operational approval: not established.

The Python PR remains draft and unmerged. No merge, deployment, benchmark-quality, synergy, or operational-readiness claim is authorized by this CI result.


### A-09 — Partial dimension coverage and invalid test/condition combinations

**Disposition: Remediated in the report generator; regression-tested.**

A further review found two ways malformed records could weaken report interpretation:
- A rubric dimension could be scored in only some repetitions yet still be counted as assessed for the whole condition.
- A schema-valid condition could be attached to a test for which that condition is not part of the protocol, then be silently omitted from the report's expected condition groups.

The report now counts a dimension as assessed only when every record in that condition has a valid integer score for it (booleans are excluded). It also rejects test/condition combinations that do not belong to the test protocol rather than silently ignoring them. Regression tests cover partial dimension coverage and invalid condition/test pairings.

**Exact verification evidence:** GitHub Actions run 43409092478 passed on code-and-test commit `155725c5f30c964ddde321ede870f33480224a56`: https://github.com/Jekylhyde82/universal-engine-engineer/actions/runs/43409092478. Dependency installation, asset/record validation, and `pytest -q` all passed.

The previous failed test run 43408980584 was investigated. The implementation behavior was correct; the test asserted an internal diagnostic string instead of the report's stable tabular output. The test was corrected to assert the actual fused-condition dimension and coverage row. The final exact code/test revision then passed.



### A-10 — Python Ed25519 evidence-manifest foundation

**Disposition: Implemented as a reusable API and schema; CI verification pending; runner integration outstanding.**

The Python branch now adds a strict evidence-manifest JSON Schema and a reusable Python API for deterministic canonical JSON, SHA-256 artifact hashing, Ed25519 signing, trusted-public-key verification, key-fingerprint checking, expected-revision checking, optional externally expected signer identity/role checks, duplicate-path rejection, traversal rejection, symlink-escape rejection, and artifact-byte revalidation. The API is exported from the package. A cryptography runtime dependency and positive/negative tests have also been added.

Tests cover valid signing and verification, tampered payloads, wrong revisions, untrusted keys, artifact tampering, duplicate paths, path traversal, and symlink escape.

**Important limitations:** this is a manifest primitive, not yet end-to-end provenance parity. The existing performance-lab run and report commands do not yet automatically create or require a signed manifest. The Python run-record schema still does not enforce GENESIS-equivalent trial context metadata, blind labels, scorer/adversarial-reviewer separation, or raw-artifact capture references. Signer identity remains an externally supplied assertion associated with a trusted key; the API does not independently prove a real-world person's identity. Private keys must remain outside the repository and be supplied by a protected signing environment.

**Acceptance work remaining:**
1. Pass CI on the exact branch head containing this change.
2. Integrate manifest creation/verification into a dedicated evidence-seal command without exposing private keys in logs or run records.
3. Add a versioned trial-execution schema and blind trial matrix with exact case/condition/repetition coverage.
4. Preserve raw captures as separate immutable artifacts and require manifest references before a report can claim sealed evidence.
5. Add end-to-end tests proving the CLI fails closed on absent, invalid, stale-revision, or artifact-mismatched manifests.
6. Independently review rubric mapping before changing score semantics.

## Current disposition — 2026-11-13

- Python reporting repetition, dimension-identity, partial-dimension, and invalid test/condition defects: implemented and regression-tested.
- Earlier Python code/test revision 155725c5f30c964ddde321ede870f33480224a56 passed in GitHub Actions run 43409092478.
- Python Ed25519 manifest foundation: committed; latest-head CI pending.
- GENESIS current candidate PR #22 head 9541042f909e1e1f52eb49f1f96f2062d553f42d passed CI in run 42846696349 on that exact head.
- Authentic GENESIS trials: 0/30; complete eligible pairs: 0/15, per PR #22 evidence report.
- Python/GENESIS full provenance parity: not achieved.
- Independent scoring, calibration, third-party review, measured improvement/synergy, and operational approval: not established.

Both pull requests remain draft and unmerged. No merge, deployment, benchmark-quality, synergy, or operational-readiness claim is authorized by these harness checks.


### A-11 — Evidence-manifest command-line integration

**Disposition: Implemented and CI-verified on exact commit 80bbd3b60ad4797577d19c754c3856d9d935b42e.**

The Python CLI now exposes `performance-lab seal` and `performance-lab verify-manifest`. Sealing reads an explicit artifact-list JSON file, requires a protected Ed25519 private-key PEM file (on POSIX, group/other permissions are rejected), creates a revision-bound manifest, and writes it atomically. Verification requires an externally supplied public key and exact candidate revision, with optional expected signer ID and role. It fails closed on malformed manifests, invalid signatures, trust-key mismatch, artifact mismatch, or revision mismatch.

**Exact CI evidence:** GitHub Actions run 43429608408 passed on commit 80bbd3b60ad4797577d19c754c3856d9d935b42e. Dependency installation and the Performance Lab validation command passed; pytest reported 25 passed, 0 failed. This verifies the manifest primitive and CLI tests, not authentic benchmark execution or independent identity verification.

**Remaining parity gaps:** trial-execution metadata and blind matrix are not yet enforced in Python run records; the existing capture command does not automatically produce a manifest or raw artifact inventory; reports do not yet require a verified manifest before rendering. These are the next implementation gates.


### A-12 — Cross-platform artifact-path hardening and final CLI regression

**Disposition: Implemented and CI-verified on exact code/test commit a8c6c242b16229a1818b0f7098dbf35cde32d6f2.**

Artifact path validation now rejects backslash-containing paths as non-canonical, in addition to absolute paths, parent traversal, symlink escapes, and resolved paths outside the evidence root. Regression coverage includes POSIX traversal, Windows-style traversal/drive paths, symlink escape, duplicate paths, artifact tampering, and signature/revision/trust-key failures.

GitHub Actions run 43429912937 passed on the exact code/test commit a8c6c242b16229a1818b0f7098dbf35cde32d6f2. Dependency installation and benchmark asset/record validation passed; pytest reported 25 passed, 0 failed.

The evidence-sealing usage guide is in docs/performance-lab-v1.0/EVIDENCE_SEALING.md. The manifest API and CLI are verified, but automatic capture sealing, report-time manifest enforcement, trial-context schema parity, blind-assessor separation, and authentic experimental evidence remain outstanding.


### A-13 — Fail-closed report eligibility for mandatory hard gates

**Disposition: Implemented and CI-verified on exact code/test commit `f850cc8417518a71b2a26e3322b5b24ddc273d3c`.**

A report-integrity review found that the report displayed mandatory hard-gate failures but could still calculate weighted scores and a PL-005 fused-versus-comparator delta when a record had failed or unassessed gates. This could allow a failed gate to appear alongside a comparative score, contrary to the stated fail-closed policy.

The report generator now:
- exposes a separate evidence-gate status for every test/condition row;
- withholds weighted scores unless every record in that condition has an explicit `pass` decision and every mandatory hard gate is explicitly `pass`;
- blocks the PL-005 fusion comparison if any of its eleven arms contains a failed or unassessed hard gate or lacks an explicit PASS decision; and
- preserves hard-gate failure and unassessed counts in the report.

Regression tests cover both failed and unassessed mandatory gates. Synthetic comparison fixtures now explicitly mark their gates and review decisions as passing; these remain synthetic software tests, not benchmark evidence.

**Verification history:** the first implementation run (43456877582) exposed one stale test assertion that did not include the new evidence-gate column; 26 tests passed and one assertion failed. The assertion was corrected without weakening the implementation. GitHub Actions run 43456996213 then completed successfully on exact commit `f850cc8417518a71b2a26e3322b5b24ddc273d3c`: asset/record validation passed and pytest reported **27 passed, 0 failed**.

This verifies report eligibility logic only. It does not close the separate GENESIS provenance-parity gaps: automatic capture sealing, report-time signed-manifest enforcement, trial-context/isolation metadata, blind-label and assessor separation, or independent identity-to-key verification. Authentic trials and independent release approval remain outstanding.


### A-14 — Report-time signed-manifest enforcement

**Disposition: Implemented; exact-head CI verification pending.**

The public `performance-lab report` CLI previously accepted records and generated a comparison report without requiring the signed evidence-manifest verification command to have been run. This left a gap between the available Ed25519 manifest primitive and the ordinary reporting path.

The report CLI now requires an evidence root, manifest, expected 40-character candidate revision, and independently supplied trusted public key. Before reading records for comparison it:
- verifies the manifest schema and Ed25519 signature;
- verifies the public-key fingerprint against the external trust key;
- verifies the exact expected candidate revision and optional externally expected signer ID/role;
- re-hashes every listed artifact from disk;
- requires every input run-record file to be listed in the verified manifest as kind `run_record`; and
- requires each included run record's `commit_sha` to equal the expected candidate revision.

Missing, unsealed, altered, stale-revision, or incorrectly signed evidence fails closed before report output is written. Unit tests cover a valid signed-manifest report path and rejection of a run record omitted from the manifest.

**Scope limitation:** this does not automatically seal captures at capture time. Operators must freeze the candidate revision, retain raw captures and run records, list the evidence artifacts, and seal them with a protected private key. The report gate verifies integrity and revision binding, not real-world identity, actual isolation, assessor independence, or benchmark quality.

**Verification:** implementation and regression tests committed on the PR branch; exact-head CI result must be inspected before this finding can be marked CI-verified. The PR remains draft and unmerged.
