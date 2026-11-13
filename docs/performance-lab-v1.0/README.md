# Performance Lab V1.0

**Project:** U.N.I.V.E.R.S.A.L. E.N.G.I.N.E. / E.N.G.I.N.E.E.R.  
**Status:** Initial specification committed to an isolated feature branch. Not yet executed or independently validated.  
**Governing rule:** PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.

## 1. Purpose

Performance Lab evaluates whether a configured Universal Engine / Engineer workflow produces measurable improvements over a conventional baseline on equivalent tasks. It is an evaluation framework, not evidence that the proposed architecture is already implemented.

## 2. Evaluation layers

1. **Individual capability:** evaluate one capability in isolation.
2. **Fusion:** evaluate whether coordinated capabilities improve outcomes over their isolated results.
3. **System:** evaluate end-to-end task completion, reliability, safety and resource use.
4. **Evolution:** evaluate whether a documented change improves performance without unacceptable regressions.

## 3. Five core benchmark tests

These are the newly selected V1.0 benchmark suite. They are not represented as the exact five from the earlier conversation because that historical selection was not recoverable.

| ID | Test | Primary construct | Required evidence |
|---|---|---|---|
| PL-001 | Grounded reasoning and uncertainty | Correctness, evidence use, calibration, uncertainty handling | Prompt, answer, reference rubric, source trace, factual error log |
| PL-002 | Research and capability acquisition | Search coverage, source quality, provenance, synthesis, licensing/security awareness | Search plan, candidate register, source URLs, evaluation notes, rejected candidates |
| PL-003 | Engineering execution | Requirements traceability, architecture quality, implementation correctness, reproducibility | Requirements, diff/commit, build/test logs, acceptance results |
| PL-004 | Independent critic and adversarial verification | Defect detection, threat modelling, counterexamples, false-positive control | Challenge set, findings, severity, reproduction steps, reviewer disposition |
| PL-005 | Fusion synergy and evolution | Incremental value of combined capabilities, regression resistance, improvement over time | Isolated-vs-fused runs, ablation results, before/after metrics, regression report |

## 4. Controlled comparison protocol

Compare:
- **Baseline:** conventional ChatGPT configuration, with model/version and settings recorded.
- **Experimental:** the explicitly documented Universal Engine / Engineer configuration available for the run.

Controls:
- Use the same task, input, constraints, reference material and scoring rubric.
- Randomize or counterbalance run order where practical.
- Run at least three repetitions for non-deterministic tasks; report every run, median and range.
- Blind-score outputs where feasible.
- Record model identifiers, configuration, tool access, timestamps, task-set version and environmental conditions.
- Do not attribute a difference to architecture when model, tools, prompt, data or compute also changed; record confounders.

## 5. Scoring model

Score each dimension from 1–5 using a written rubric, or use NOT_ASSESSED when evidence is insufficient; normalize assessed scores to 0–100 for display. Preserve raw scores and evidence.

Dimensions:
- Correctness / task success
- Evidence quality and traceability
- Completeness / requirement coverage
- Reliability / repeatability
- Efficiency / resource cost
- Safety / policy compliance
- Calibration / uncertainty disclosure
- Maintainability / reproducibility (where applicable)

Do not collapse all dimensions into a single average for acceptance. Report the full profile and worst-performing dimension. Define task-specific hard gates before execution. A safety failure, fabricated evidence, or untraceable completion claim is a critical failure regardless of aggregate score.

## 6. Test record contract

Every run must capture:
- run_id and test_id
- test_catalog_version
- objective and hypothesis
- task/input hash or immutable input reference
- baseline and experimental configuration identifiers
- timestamp (UTC) and operator
- tool/model versions and permissions
- procedure and repetition number
- raw output and evidence references
- rubric version and per-dimension scores
- defects, limitations, confounders and deviations
- pass/fail decision and reviewer
- commit SHA / deployment identity where code is involved

Never overwrite raw evidence. Corrections create a new record linked to the superseded record.

## 7. Acceptance gates for V1.0

V1.0 is **specified**, not complete, until all of the following are evidenced:
1. Five benchmark definitions and scoring rubrics are versioned.
2. A repeatable runner or documented manual execution procedure exists.
3. Baseline and experimental configurations are pinned.
4. At least one pilot run exists for each test.
5. Raw evidence and scores are retained.
6. An independent review checks scoring and conclusions.
7. Limitations and failed tests are reported, not hidden.

A benchmark suite is not validated merely because its specification exists.

## 8. Initial execution sequence

1. Review this specification and freeze the test catalog.
2. Create task sets and scoring rubrics for PL-001 through PL-005.
3. Pin baseline and experimental configurations.
4. Execute a pilot, preserving raw artifacts.
5. Review reliability, scoring ambiguity and confounders.
6. Revise the catalog with a version increment; do not silently change a live test.

## 9. Security and scope

Use least-privilege access. Do not expose credentials, private user data or production secrets in benchmark prompts or artifacts. Repository write access is limited to the feature branch until review. No production deployment, destructive action, secret rotation or merge is authorized by this benchmark specification.

## 10. Current evidence state

- Repository identified: `Jekylhyde82/universal-engine-engineer`.
- Default branch observed: `main`.
- Feature branch created: `performance-lab-v1.0`.
- This document is an initial specification only.
- No benchmark execution, CI validation, independent review, deployment or performance improvement is claimed.


## 11. Reconciliation with existing repository work

The repository already contains draft evaluation and adapter material. Performance Lab must reuse and extend it rather than duplicate it:

- **PR #8 — six-source integration evaluation:** use its candidate-specific proof requirements for LangGraph (state/recovery), llama.cpp (target-device resources), LlamaIndex (provenance/injection), Qdrant (retrieval/isolation), Promptfoo (regression/red-team harness) and DeepEval (metric/judge calibration). These are candidate-specific subtests under PL-002, PL-003 and PL-005, not additional top-level benchmark tests.
- **PR #4 — preserved Verification Agent:** its status ladder is useful, but its current evaluator trusts caller-supplied `trustworthy`, `independent`, `durable` and `safetyPassed` booleans. It does not independently fetch or authenticate evidence. It must remain quarantined until authenticated evidence collection and independent verification replace those trust assertions.
- **Promptfoo Echo fixture:** the preserved workflow uses an Echo provider and makes no model calls. Its passing workflow is evidence that a deterministic fixture/configuration ran, not evidence of model quality, reasoning performance or red-team robustness.
- **PR #9 — capability evaluation engine specification:** align future evaluation records and decision states with its evidence-backed lifecycle; do not create conflicting parallel status vocabularies.

No quarantined code is activated by this PR. The first runner implementation must consume verified evidence artifacts, not caller-asserted trust flags, and must retain candidate-specific acceptance gates.


### Alignment with Universal Capability Evaluation Engine (UCEE-SPEC-001)

Performance Lab measures the quality of benchmark task outcomes; UCEE evaluates external/internal capability candidates through governance gates. They are complementary, not competing systems.

- Adopt UCEE's **1–5 or NOT_ASSESSED** scoring discipline. Missing evidence is NOT_ASSESSED, never a neutral score.
- Preserve UCEE's G0–G7 candidate gates and its decision states; Performance Lab test outcomes must not imply candidate approval or operational status.
- Map benchmark evidence into UCEE-compatible evidence records where a benchmark is evaluating a capability candidate.
- Human approval remains mandatory for code import, dependency installation, credential access, production changes and other high-impact actions.
- Mocks prove contract behavior only; they do not prove live provider behavior.


## 12. Runner implementation status (2026-11-10)

A separate implementation branch, `performance-lab/runner-and-evidence-v1`, adds:
- JSON Schema 2020-12 validation for individual run records.
- A five-test capture runner requiring at least three supplied repetitions per condition.
- SHA-256 hashes for each fixed pilot input and raw output; unique records are append-only (existing filenames are never overwritten).
- A descriptive baseline/experimental report generator.
- Unit tests and a dedicated GitHub Actions validation workflow.

The runner accepts outputs captured from the baseline and experimental systems. It does not invoke a model, create synthetic model responses, or assign scores. Scores, hard-gate results and reviewer identities are supplied by an accountable reviewer. Missing scores remain `NOT_ASSESSED`.

**Verified harness evidence:** GitHub Actions workflow run 42810768345 completed successfully on commit `632b4510700dbd4e7eb94128ed0f48d42f6e96ac`. Dependency installation, catalogue/schema validation and unit tests passed.

**Not yet evidenced:** actual baseline/experimental model runs, three repetitions for each of five tests, independent scoring, adversarial review, comparative performance improvement, and operational deployment. The CI result validates the harness only.


### Integrity and reporting hardening (2026-11-10)

The runner now re-computes and checks each stored raw-output hash and the fixed pilot-input hash during validation and report generation. The comparison report applies the versioned rubric weights, exposes assessed-weight coverage, reports per-dimension median/range and worst dimension, and counts failed hard gates separately. These calculations remain descriptive; a weighted score cannot override a failed gate. Hashes detect content alteration but do not authenticate reviewer identity or guarantee independent review.

**Latest CI evidence:** workflow run 42811837813 passed on head commit 693ff9b9af0d074fb280eb78c2261f92d3357ff6. The run validates the harness and its unit tests only; no model benchmark trials are included.


## 13. Signed-evidence requirement for reports

The report CLI now fails closed unless a trusted Ed25519 manifest is supplied and verified against the exact candidate commit. Every input run-record file must be covered by that manifest as a `run_record`, and every record must declare the same candidate `commit_sha`.

Before reporting, freeze the candidate revision, retain raw captures and run records under one evidence root, create an artifact list, and seal it with a protected signing key. Then run:

```bash
performance-lab report \
  --records artifacts/performance-lab/records \
  --evidence-root artifacts/performance-lab \
  --manifest /secure/evidence/performance-lab-manifest.json \
  --revision <FROZEN_40_CHARACTER_COMMIT_SHA> \
  --public-key /secure/keys/performance-lab-ed25519-public.pem \
  --expected-signer-id <TRUSTED_SIGNER_ID> \
  --expected-signer-role evidence-custodian \
  --out artifacts/performance-lab/report.md
```

The report gate establishes signed artifact integrity and candidate-revision binding. It does not independently prove real-world signer identity, trial isolation, evaluator independence, or benchmark quality. Capture-time automatic sealing, enforced trial-context metadata, blind assessor separation, and independent identity-to-key verification remain outstanding.


## 14. Automatic capture-batch sealing

The public `performance-lab run` command now requires a frozen candidate revision, an evidence root, signer ID/role, and a protected Ed25519 private key. After preflighting and writing the supplied batch, it automatically creates a signed manifest covering every generated run-record file. Each record is stamped with the same candidate revision. On POSIX systems, group/other-readable private-key files are rejected.

Example:

```bash
performance-lab run \
  --responses responses.json \
  --out artifacts/performance-lab/records \
  --operator <OPERATOR_ID> \
  --repetitions 3 \
  --evidence-root artifacts/performance-lab \
  --revision <FROZEN_40_CHARACTER_COMMIT_SHA> \
  --signer-id <TRUSTED_SIGNER_ID> \
  --signer-role evidence-custodian \
  --private-key /secure/keys/performance-lab-ed25519-private.pem
```

The generated manifest defaults to `<evidence-root>/evidence-manifest.json`. The capture runner records operator-supplied outputs; it does not invoke a model or independently establish capture authenticity. Preserve any separate raw capture artifacts and include them in the evidence package. A valid signature proves possession of the signing key, not the real-world identity of its holder.


## 15. Trial execution provenance and separated review

Run records now require the same core execution controls used by GENESIS: unique `trial_id` and `blind_label`, explicit Unpersonalized Temporary Chat confirmation, context reference/type, capture timestamp, exact model label, settings, tools used, retained capture reference, canonical prompt SHA-256, raw-response SHA-256, and an architecture-instruction SHA-256 for non-baseline conditions. The runner recomputes prompt/response hashes and preflights unique trial/blind identifiers across the supplied batch.

Each record also requires a separate blinded assessor and adversarial reviewer. Both attest independence and blinding; their IDs must differ. A PASS decision requires every adversarial check to explicitly pass.

These controls provide structured provenance and fail-closed consistency checks. They do not cryptographically prove a human's identity, prove that the UI was genuinely unpersonalized, or independently establish assessor independence. Those remain external verification requirements.


## 16. Calibrated evaluator provenance and scoring rationales

Each record now requires distinct scorer and adversarial-evaluator metadata: evaluator ID, provider, model, version, instruction hash, calibration PASS status, calibration reference, and calibration artifact hash. The scorer and adversarial evaluator cannot share the same provider/model/version tuple. Every scored dimension must have a non-empty rationale, with exact one-to-one coverage between score keys and rationale keys.

The capture runner requires calibration references to resolve to files inside the evidence root, verifies each declared SHA-256, and includes the calibration files in the signed manifest. The report command requires those references and hashes to match entries in the independently verified manifest. This proves artifact integrity/linkage, not calibration quality or evaluator competence. Human calibration approval and external evaluator-identity verification remain required; an asserted PASS value is not proof of calibration.


## 17. Frozen evaluator configuration across fusion arms

The PL-005 fusion comparison now requires one identical scorer configuration and one identical adversarial-evaluator configuration across baseline, all nine isolated specialists, fused condition, and every repetition. The frozen signatures include evaluator ID, provider, model, version, instruction hash, calibration reference and calibration hash. Any evaluator drift blocks the fusion comparison; the runner will not silently compare scores produced under different evaluation protocols.


## 18. Retained raw capture files

Each run record points to a traversal-free raw capture path under the evidence root. The capture runner retains the supplied verbatim output at that path and seals it into the manifest as `raw_trial_output`; report generation requires that exact file and SHA-256 to be present in the verified manifest. The runner stores the operator-supplied text and does not directly capture the ChatGPT UI or independently prove session authenticity. Preserve original capture evidence where the protocol requires it.
