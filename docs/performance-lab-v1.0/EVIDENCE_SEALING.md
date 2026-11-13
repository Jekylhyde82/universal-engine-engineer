# Python Performance Lab — Evidence Sealing

## Purpose

The evidence-sealing commands create and verify an Ed25519-signed manifest over explicitly listed evidence files. The manifest binds the artifact hashes and signer attestation to one exact 40-character Git commit SHA.

This is a provenance primitive. It does not authenticate a human identity by itself, prove that a capture was genuinely performed in an isolated context, or certify benchmark quality.

## Required inputs

- A frozen candidate commit SHA. Do not change the candidate source after choosing this revision.
- An evidence root containing the raw captures, run records, reports, and other evidence to be sealed.
- An artifact-list JSON file containing relative paths and artifact kinds.
- An Ed25519 private key supplied through a protected signing environment.
- The corresponding trusted public key supplied independently to verifiers.

Example artifact list:

```json
[
  {"path": "raw/PL-001-baseline-r1.txt", "kind": "raw_trial_output"},
  {"path": "records/PL-001-baseline-r1.json", "kind": "run_record"},
  {"path": "reports/comparison.md", "kind": "comparison_report"}
]
```

All paths are relative to the evidence root. Absolute paths, parent-directory traversal, symlink escapes, and duplicate artifact paths are rejected.

## Seal evidence

Keep the private key outside the repository and evidence directory. On POSIX systems, the CLI rejects private-key files accessible to group or other users; set restrictive permissions such as mode 0600.

```bash
chmod 600 /secure/keys/performance-lab-ed25519-private.pem

performance-lab seal \
  --evidence-root artifacts/performance-lab \
  --artifacts-json artifacts/performance-lab/artifacts.json \
  --revision <FROZEN_40_CHARACTER_COMMIT_SHA> \
  --signer-id <TRUSTED_SIGNER_ID> \
  --signer-role evidence-custodian \
  --private-key /secure/keys/performance-lab-ed25519-private.pem \
  --out /secure/evidence/performance-lab-manifest.json
```

The output manifest should be retained outside the candidate source tree (for example, as a protected CI artifact or in an evidence store). Do not commit the private key. Avoid committing the manifest into the source revision it signs: doing so changes the candidate commit and breaks revision binding.

## Verify evidence

The verifier must obtain the trusted public key independently of the manifest.

```bash
performance-lab verify-manifest \
  --evidence-root artifacts/performance-lab \
  --manifest /secure/evidence/performance-lab-manifest.json \
  --revision <SAME_FROZEN_40_CHARACTER_COMMIT_SHA> \
  --public-key /secure/keys/performance-lab-ed25519-public.pem \
  --expected-signer-id <TRUSTED_SIGNER_ID> \
  --expected-signer-role evidence-custodian
```

Verification fails closed for schema errors, invalid signatures, public-key fingerprint mismatch, unexpected revision, signer ID/role mismatch, missing or altered artifacts, duplicate paths, traversal, or symlink escape.

## Automatic capture-batch sealing

The public `performance-lab run` command now requires a frozen candidate revision and protected Ed25519 signing inputs. After validating the full supplied batch and writing its run records, it creates a signed manifest over every generated run-record file. It refuses to start if the private-key file is group/other accessible on POSIX systems. If sealing fails after capture, it reports `CAPTURE_UNSEALED` and the report command will reject the records until they are correctly sealed.

Required capture options:

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

The command binds every generated record to the supplied candidate revision and writes `evidence-manifest.json` under the evidence root by default. The supplied responses remain operator-provided; the runner does not invoke a model or independently establish that the outputs are authentic.

## Report-time enforcement

The public `performance-lab report` command now requires all of the following:

- `--evidence-root`: the evidence directory containing the records.
- `--manifest`: the signed manifest to verify.
- `--revision`: the exact candidate commit SHA.
- `--public-key`: an independently trusted Ed25519 public key.

The report command verifies the manifest signature, external key fingerprint, expected revision, optional externally expected signer identity/role, and every listed artifact byte. It then requires every input run-record file to appear in the verified manifest with kind `run_record`, and requires every record's `commit_sha` to equal the expected candidate revision. Missing or unsealed records fail closed before a report is written.

Example:

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

The capture command automatically seals generated run-record files after freezing the candidate revision. The operator must separately retain raw captures and list them as additional artifacts when they are stored outside the generated run records. The manifest must cover every run-record file used by the report and all retained raw capture artifacts required for independent review.

This enforcement verifies integrity and revision binding; it does not prove that a capture was genuinely performed in an isolated context, authenticate a real-world human identity, establish evaluator independence, or certify benchmark quality. Trial-context metadata and assessor separation remain separate acceptance gates.


## Trial-execution provenance and assessor separation

Every Python run record now requires a GENESIS-aligned `trial_execution` object:

- unique trial ID and blind label;
- explicit Unpersonalized Temporary Chat confirmation;
- context type/reference and capture timestamp;
- model label, settings and tools used;
- retained capture reference;
- canonical prompt SHA-256 and raw-response SHA-256;
- architecture-instruction SHA-256 for non-baseline conditions.

The runner recomputes the canonical prompt and raw-response hashes and rejects mismatches. Capture preflight requires unique trial IDs and blind labels across the batch and refuses to proceed without the explicit isolation confirmation.

Every record also requires separate `assessor` and `adversarial_review` attestations. Both must attest blinded condition and independence; the scorer/assessor and adversarial reviewer IDs must differ. A PASS decision requires every recorded adversarial check to explicitly PASS. These are structured attestations and consistency gates—not cryptographic proof of human identity, actual blinding, evaluator independence, or a genuinely Unpersonalized session. Those controls still require independent governance and evidence.

Example metadata (illustrative only; never submit as an actual trial without real capture evidence):

```json
{
  "trial_execution": {
    "trial_id": "TRIAL-001",
    "blind_label": "BLIND-001",
    "unpersonalized_confirmed": true,
    "context_type": "Unpersonalized Temporary Chat",
    "context_reference": "operator-generated-context-reference",
    "captured_at": "2026-11-14T00:00:00Z",
    "model_label": "record the exact visible model label",
    "settings": "record actual settings",
    "tools_used": "none",
    "capture_reference": "reference-to-retained-raw-capture",
    "canonical_prompt_sha256": "64-character-prompt-hash",
    "raw_response_sha256": "64-character-response-hash",
    "architecture_instruction_sha256": "64-character-hash-for-non-baseline"
  },
  "assessor": {
    "assessor_id": "independent-blind-scorer",
    "blinded_condition": true,
    "independent": true
  },
  "adversarial_review": {
    "reviewer_id": "separate-independent-reviewer",
    "blinded_condition": true,
    "independent": true,
    "checks": [
      {"check_id": "CHECK-001", "outcome": "pass", "finding": "Evidence-backed finding."}
    ]
  }
}
```


## Calibrated evaluator provenance and score rationales

Every record also requires an `assessment` object with separate scorer and adversarial-evaluator identities, provider, model, version, instruction SHA-256, calibration status `PASS`, calibration reference, and calibration artifact SHA-256. The evaluator configurations must not collapse to the same provider/model/version tuple. A non-empty rationale is mandatory for every score key, and rationales must cover exactly the scored dimensions.

The capture runner now requires each calibration reference to resolve to a retained file inside the evidence root and verifies its bytes against the declared SHA-256 before writing any run records. It includes both calibration artifacts in the signed evidence manifest. The report command requires each scorer/reviewer calibration reference and declared hash to match a calibration_reference entry in the independently verified manifest. This establishes artifact integrity and linkage, not calibration quality or evaluator competence. Calibration PASS must still be backed by an independently reviewed calibration package; do not treat a signed file alone as proof of calibration.


## Frozen evaluator protocol across fusion arms

The PL-005 report gate compares evaluator signatures across all eleven arms and all repetitions. The scorer signature and adversarial-evaluator signature must each remain identical across evaluator ID, provider, model, version, instruction hash, calibration reference and calibration hash. Any drift blocks the fusion comparison, even if all individual records otherwise pass their schema and evidence gates.
