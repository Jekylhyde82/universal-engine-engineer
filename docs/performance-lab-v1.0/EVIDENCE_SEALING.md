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

## Current integration boundary

The commands are available and CI-tested. The existing capture and report commands do not yet automatically create a manifest, require one before report generation, or prove that submitted trial-context metadata is authentic. Treat a successful manifest verification as evidence-integrity verification only—not as proof of model quality, evaluator independence, or production readiness.
