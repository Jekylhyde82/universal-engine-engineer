# OMNISIGHT PRIME — Evidence Ledger Prototype

**Status:** Executable reference vertical slice; not production-ready.

## What this delivers

- Standard-library Python implementation; no third-party runtime dependencies.
- SHA-256 digest of supplied media bytes; raw media is not persisted.
- Canonical JSON evidence records with source, timestamp, producer/version, epistemic status, limitations and verification reference.
- Atomic SQLite append with a previous-record hash link.
- SQLite update/delete triggers as an accidental-mutation guard.
- Separate read-only verification function that recomputes every record digest and chain link.
- Tests for valid writes, chain continuity, digest stability, required verification references, timestamp validation, mutation blocking, tamper detection and externally retained checkpoint rollback detection.

## Run

From this directory's parent:

\`\`\`sh
PYTHONPATH=runtime python -m unittest discover -s runtime/omnisight_evidence/tests -v
\`\`\`

Python 3.10+ is required. The implementation uses only the Python standard library.

## Deliberate boundaries

- The ledger stores metadata and a digest, not screenshots or camera media.
- It does not capture a screen or camera, perform OCR, classify images, or infer a world model.
- A \`verification_ref\` is a reference string; this prototype does not authenticate the verifier or prove that verification occurred.
- The verifier detects edits and broken links among records still present. An externally retained checkpoint can detect truncation before its recorded sequence and replacement of its prefix. The checkpoint is not signed; its destination must be separately access-controlled and independently retained. It does not protect against an attacker who can replace both database and checkpoint.
- SQLite triggers are defence-in-depth against accidental writes, not a security boundary against a privileged database editor.
- No encryption, Android permission integration, remote sync, retention scheduler, multi-process stress test or production hardening is included.

## Next integration steps

1. Bind the record shape to the published observation-envelope schema.
2. Harden checkpoint storage with authenticated signatures, key management, rotation and independent retention.
3. Add authenticated verifier identities and signed verification statements.
4. Integrate consent-gated Android acquisition without bypassing OS controls.
5. Add OCR/specialist outputs as separate, provenance-linked observations.
6. Benchmark and threat-test on target hardware before production acceptance.
