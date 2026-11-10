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
