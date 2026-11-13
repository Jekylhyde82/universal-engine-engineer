# Python Performance Lab — Evidence provenance

**Status:** IMPLEMENTED IN THIS BRANCH; CI AND INDEPENDENT REVIEW REQUIRED. This does not make the lab operational.

## Scope

The provenance helper adds a GENESIS-aligned Ed25519 evidence-manifest layer. A manifest binds the benchmark identifier and exact candidate revision, UTC creation timestamp and signer role, relative artifact paths and SHA-256 digests, an Ed25519 signature over deterministic canonical JSON, and the signing public-key fingerprint.

The helper verifies the signature, expected candidate revision, independently supplied signer ID and required role, trusted public-key fingerprint, path containment, and actual bytes of every listed artifact. It rejects absolute paths, parent traversal, platform-specific path escapes, symlinks resolving outside the evidence root, missing files, and changed artifact bytes.

## Trust boundary — mandatory

The verifier must receive the trusted public key, expected signer ID, required role and candidate revision from an independently controlled trust record or release procedure. Do not obtain these values from the manifest being verified. Keep private keys outside the repository and evidence directory. A valid Ed25519 signature proves possession of the corresponding private key; it does not prove real-world identity, independent custody, truthful capture, or completeness of the evidence package.

The evidence custodian must not independently approve their own evidence. A reviewer independent of implementation and evidence collection must validate the key-to-person binding and inspect the package.

## Prepare a manifest payload

Create a JSON payload without a signature field. Each artifact digest must be SHA-256 of the exact retained bytes. This is a template only; replace every placeholder and never sign synthetic trial data.

```json
{
  "schema_version": "1.0",
  "benchmark_id": "PYTHON-PERFORMANCE-LAB-001",
  "revision": "REPLACE_WITH_EXACT_40_CHARACTER_COMMIT_SHA",
  "created_at": "2026-11-13T00:00:00Z",
  "signer": {"signer_id": "OUT_OF_BAND_CUSTODIAN_ID", "role": "evidence-custodian"},
  "artifacts": [{"path": "raw/PL-001-baseline-r1.txt", "kind": "raw-response", "sha256": "REPLACE_WITH_64_CHARACTER_SHA256"}]
}
```

## Commands

Install the project and dependencies:

```bash
python -m pip install -e ".[test]"
```

Sign the payload. The evidence root is explicit so signing checks every artifact path and byte digest before producing the signature:

```bash
performance-lab-provenance sign-manifest payload.json /secure/path/custodian-private-key.pem evidence/ signed-manifest.json
```

Verify using a separately provisioned trusted public key and independently supplied trust values:

```bash
performance-lab-provenance verify-manifest signed-manifest.json /secure/path/trusted-custodian-public-key.pem evidence/ <candidate-commit-sha> <trusted-signer-id> evidence-custodian
```

## Release integration still required

This helper does not yet establish full GENESIS parity. Remaining gates:
1. Add and validate run-record fields for blind trial labels, trial IDs, capture metadata, canonical prompt hashes, raw artifact references and model/tool configuration.
2. Enforce blinded assessor/reviewer separation and independently calibrated scoring.
3. Cross-check every run-record evidence reference against the signed manifest. The helper verifies manifest-listed files but does not yet prove manifest completeness against the run ledger.
4. Retain raw artifacts, calibration materials, reviewer statements, execution metadata and reports in the evidence package.
5. Obtain independent verification of the signed manifest and out-of-band key custody.
6. Execute authentic benchmark trials. CI and unit tests are not model-performance evidence.

**Release remains HOLD.** No benchmark trials, independent assessment, operational readiness, or fusion improvement are claimed by adding this helper.
