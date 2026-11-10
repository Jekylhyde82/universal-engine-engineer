# Performance Lab adversarial audit — 2026-11-10

## Scope

Reviewed the V1.0 test catalogue, pilot cases, scoring rubric, run-record schema, capture runner, unit tests and CI workflow on the isolated implementation branch. This is an internal design/code audit, not an independent third-party security review.

## Findings

### A-01 — PL-005 does not operationalize its own synergy protocol
**Severity: Critical for synergy claims.**

The pilot case explicitly requires baseline, each specialist separately, and fused workflow. The current runner only supports `baseline` and `experimental` conditions. Therefore it cannot capture the full comparator set needed to establish incremental fusion benefit or ablation delta. No synergy conclusion is supportable from the current two-arm capture model.

**Required remediation:** introduce an explicit multi-arm experiment schema (baseline, each named specialist, fused), require identical task/rubric and configuration provenance across arms, and report fused performance against the strongest relevant comparator. Until then, mark PL-005 synergy evaluation NOT ASSESSED.

### A-02 — PL-001 lacks its actual reference brief
**Severity: High for correctness scoring.**

The pilot input describes five supported and two unsupported claims, but does not provide the brief or authoritative reference facts. Reviewers cannot consistently score correctness or verify unsupported claims from the fixture alone.

**Required remediation:** add a versioned, self-contained reference brief and answer key with five supported facts, two unsupported assertions, and explicit evidence mapping. Keep the answer key unavailable to the responding condition if blind scoring is intended.

### A-03 — Capture could write partial benchmark batches
**Severity: High for dataset integrity.**

Previously, the runner wrote records while iterating through tests. If a later test lacked repetitions, earlier records remained on disk and could be mistaken for a complete batch.

**Remediation applied:** runner now preflights the exact five-test payload, both conditions, configuration objects and all requested non-empty repetitions before creating records. Invalid input exits before writing any record.

### A-04 — Model configuration was not integrity-bound
**Severity: High for reproducibility.**

The original record stored configuration as mutable JSON without a corresponding digest.

**Remediation applied:** records now require a SHA-256 digest of canonicalized configuration JSON, and validation recomputes it. Raw-output and pilot-input hashes are also recomputed during validation/reporting. These hashes detect content changes; they do not authenticate the operator, model provider, or reviewer.

### A-05 — Asset validation is not full schema validation
**Severity: Medium.**

The validator checks the run-record schema and selected catalogue invariants, but the catalogue, pilot-case and rubric JSON documents do not each have dedicated JSON Schemas. Structural mistakes outside the currently checked fields could pass CI.

**Required remediation:** add schemas for all three assets, validate cross-file IDs and rubric dimension IDs, and test malformed/duplicate entries.

### A-06 — Hard-gate semantics depend on reviewer-supplied booleans
**Severity: High for acceptance decisions.**

The runner counts explicit false values, but a missing gate or a caller-supplied true value is not independent proof that the gate passed.

**Required remediation:** define required gate keys per test, require reviewer identity and evidence references for each decision, and keep unverified/missing gates in NOT_ASSESSED rather than treating absence as pass.

## Current disposition

- Harness CI: passed on the latest validated code commit only when the corresponding workflow run is green.
- PL-001 correctness reference fixture: incomplete.
- PL-005 multi-arm synergy protocol: incomplete.
- Independent scoring and adversarial review: not completed.
- Operational approval: not granted.

No benchmark result, synergy claim, model improvement claim or operational claim should be made until the relevant findings are remediated and evidence is independently reviewed.
