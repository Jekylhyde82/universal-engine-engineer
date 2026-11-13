"""Revision-bound Ed25519 evidence manifests for the Python Performance Lab.

Private signing keys are supplied by the caller and must be managed outside the
repository (for example, in a hardware-backed or CI secret store). Verification
trusts only the public key supplied by the caller; a manifest cannot nominate
its own trust root.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = Path(__file__).with_name("evidence-manifest.schema.json")
BENCHMARK_ID = "UNIVERSAL-ENGINE-PERFORMANCE-LAB-001"
ROLES = {"evidence-custodian", "independent-reviewer", "release-approver"}


def canonical_json(value: dict[str, Any]) -> bytes:
    """Return the deterministic UTF-8 representation covered by the signature."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_private_key(value: str | bytes) -> Ed25519PrivateKey:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    key = serialization.load_pem_private_key(raw, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Evidence manifest signing requires an Ed25519 private key")
    return key


def _load_public_key(value: str | bytes) -> Ed25519PublicKey:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    key = serialization.load_pem_public_key(raw)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("Evidence manifest verification requires an Ed25519 public key")
    return key


def _safe_artifact(root: Path, relative_path: str) -> Path:
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute() or not relative_path or "\\\\" in relative_path or ".." in candidate.parts:
        raise ValueError(f"Artifact path must be relative and traversal-free: {relative_path!r}")
    resolved_root = root.resolve(strict=True)
    resolved = (resolved_root / Path(*candidate.parts)).resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Artifact resolves outside evidence root: {relative_path!r}") from exc
    if not resolved.is_file():
        raise ValueError(f"Artifact is not a regular file: {relative_path!r}")
    return resolved


def _public_key_fingerprint(key: Ed25519PublicKey) -> str:
    der = key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return sha256_bytes(der)


def validate_manifest_schema(manifest: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in validator.iter_errors(manifest)
    ]


def create_evidence_manifest(
    *,
    evidence_root: str | Path,
    revision: str,
    signer_id: str,
    signer_role: str,
    artifacts: list[dict[str, str]],
    private_key_pem: str | bytes,
    created_at: str,
) -> dict[str, Any]:
    """Hash listed evidence files and sign a manifest bound to one 40-char revision."""
    if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        raise ValueError("revision must be a 40-character lowercase Git commit SHA")
    if signer_role not in ROLES or not signer_id.strip():
        raise ValueError("A non-empty signer ID and an allowed signer role are required")
    root = Path(evidence_root)
    entries = []
    seen: set[str] = set()
    for item in artifacts:
        relative = item["path"]
        if relative in seen:
            raise ValueError(f"Duplicate artifact path: {relative}")
        seen.add(relative)
        resolved = _safe_artifact(root, relative)
        entries.append({
            "path": relative,
            "kind": item["kind"],
            "sha256": sha256_bytes(resolved.read_bytes()),
        })
    payload = {
        "schema_version": "1.0",
        "benchmark_id": BENCHMARK_ID,
        "revision": revision,
        "created_at": created_at,
        "signer": {"signer_id": signer_id, "role": signer_role},
        "artifacts": entries,
    }
    problems = validate_manifest_schema({
        **payload,
        "signature": {
            "algorithm": "Ed25519",
            "public_key_sha256": "0" * 64,
            "value": base64.b64encode(b"0" * 64).decode("ascii"),
        },
    })
    if problems:
        raise ValueError("Invalid evidence manifest payload: " + "; ".join(problems))
    private_key = _load_private_key(private_key_pem)
    public_key = private_key.public_key()
    signature = private_key.sign(canonical_json(payload))
    return {
        **payload,
        "signature": {
            "algorithm": "Ed25519",
            "public_key_sha256": _public_key_fingerprint(public_key),
            "value": base64.b64encode(signature).decode("ascii"),
        },
    }


def verify_evidence_manifest(
    manifest: dict[str, Any],
    *,
    evidence_root: str | Path,
    trusted_public_key_pem: str | bytes,
    expected_revision: str,
    expected_signer_id: str | None = None,
    expected_signer_role: str | None = None,
) -> list[str]:
    """Verify schema, signature, external trust, revision binding and artifact bytes."""
    errors = validate_manifest_schema(manifest)
    if errors:
        return errors
    if manifest["revision"] != expected_revision:
        errors.append("manifest revision does not match the expected candidate revision")
    if expected_signer_id and manifest["signer"]["signer_id"] != expected_signer_id:
        errors.append("manifest signer ID does not match the externally trusted signer identity")
    if expected_signer_role and manifest["signer"]["role"] != expected_signer_role:
        errors.append("manifest signer role does not match the required role")
    try:
        public_key = _load_public_key(trusted_public_key_pem)
    except (TypeError, ValueError):
        return errors + ["trusted public key is invalid or is not Ed25519"]
    if _public_key_fingerprint(public_key) != manifest["signature"]["public_key_sha256"]:
        errors.append("manifest signing key fingerprint does not match the externally supplied trusted public key")
    signed_payload = {key: value for key, value in manifest.items() if key != "signature"}
    try:
        signature = base64.b64decode(manifest["signature"]["value"], validate=True)
        public_key.verify(signature, canonical_json(signed_payload))
    except Exception:
        errors.append("Ed25519 manifest signature is invalid")
    root = Path(evidence_root)
    seen: set[str] = set()
    for artifact in manifest["artifacts"]:
        relative = artifact["path"]
        if relative in seen:
            errors.append(f"duplicate artifact path: {relative}")
            continue
        seen.add(relative)
        try:
            actual_path = _safe_artifact(root, relative)
            actual_hash = sha256_bytes(actual_path.read_bytes())
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        if actual_hash != artifact["sha256"]:
            errors.append(f"artifact SHA-256 mismatch: {relative}")
    return errors
