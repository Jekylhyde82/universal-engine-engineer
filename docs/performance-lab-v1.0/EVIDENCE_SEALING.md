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

The capture command still does not automatically seal evidence. The operator must retain the raw captures and run records, prepare an artifact list, and seal them after freezing the candidate revision. The manifest must cover every run-record file used by the report; raw captures should also be listed as separate artifacts when retained separately.

This enforcement verifies integrity and revision binding; it does not prove that a capture was genuinely performed in an isolated context, authenticate a real-world human identity, establish evaluator independence, or certify benchmark quality. Trial-context metadata and assessor separation remain separate acceptance gates.
