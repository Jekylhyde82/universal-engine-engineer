"""Ed25519-signed, revision-bound evidence manifests for Performance Lab.

The trusted public key and signer identity must come from an independent
out-of-band trust record. A manifest never establishes its own trust anchor.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "evidence-manifest.schema.json"
HEX_40 = re.compile(r"^[a-f0-9]{40}$")


def canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _public_raw(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _artifact_path(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or not candidate.parts or any(part in ("", ".", "..") for part in candidate.parts):
        raise ValueError(f"artifact path must be a clean relative path: {relative!r}")
    if "\\" in relative or ":" in relative:
        raise ValueError(f"artifact path contains a platform-specific escape: {relative!r}")
    resolved_root = root.resolve(strict=True)
    resolved = (resolved_root / Path(*candidate.parts)).resolve(strict=True)
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise ValueError(f"artifact escapes evidence root or is not a file: {relative!r}")
    return resolved


def validate_manifest(manifest: dict) -> None:
    schema = _load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
                    key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        raise ValueError("; ".join(f"{list(e.absolute_path)}: {e.message}" for e in errors))


def _verify_artifact_bytes(manifest: dict, evidence_root: Path) -> None:
    for artifact in manifest["artifacts"]:
        path = _artifact_path(evidence_root, artifact["path"])
        digest = sha256_bytes(path.read_bytes())
        if digest != artifact["sha256"]:
            raise ValueError(f"SHA-256 mismatch for artifact: {artifact['path']}")


def sign_manifest(payload_path: Path, private_key_path: Path, evidence_root: Path, output_path: Path) -> dict:
    payload = _load_json(payload_path)
    if "signature" in payload:
        raise ValueError("payload must not contain a signature; signatures are generated here")
    validate_manifest({**payload, "signature": {
        "algorithm": "Ed25519", "public_key_sha256": "0" * 64, "value": "A" * 88
    }})
    _verify_artifact_bytes(payload, evidence_root)\n    private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("private key must be Ed25519 PEM")
    public_bytes = _public_raw(private_key.public_key())
    manifest = dict(payload)
    manifest["signature"] = {
        "algorithm": "Ed25519",
        "public_key_sha256": sha256_bytes(public_bytes),
        "value": base64.b64encode(private_key.sign(canonical_bytes(payload))).decode("ascii"),
    }
    validate_manifest(manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def verify_manifest(manifest_path: Path, public_key_path: Path, evidence_root: Path,
                    expected_revision: str, trusted_signer_id: str, required_role: str) -> dict:
    manifest = _load_json(manifest_path)
    validate_manifest(manifest)
    if not HEX_40.fullmatch(expected_revision) or manifest["revision"] != expected_revision:
        raise ValueError("manifest revision does not match the independently supplied candidate revision")
    if manifest["signer"]["signer_id"] != trusted_signer_id:
        raise ValueError("manifest signer ID does not match the out-of-band trust record")
    if manifest["signer"]["role"] != required_role:
        raise ValueError("manifest signer role does not match the required role")
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    if not isinstance(public_key, Ed25519PublicKey):
        raise ValueError("trusted public key must be Ed25519 PEM")
    public_bytes = _public_raw(public_key)
    fingerprint = sha256_bytes(public_bytes)
    if manifest["signature"]["public_key_sha256"] != fingerprint:
        raise ValueError("trusted public-key fingerprint mismatch")
    payload = {key: value for key, value in manifest.items() if key != "signature"}
    try:
        public_key.verify(base64.b64decode(manifest["signature"]["value"], validate=True),
                          canonical_bytes(payload))
    except Exception as exc:
        raise ValueError("Ed25519 signature verification failed") from exc
    _verify_artifact_bytes(manifest, evidence_root)
    return {"verified": True, "revision": expected_revision, "signer_id": trusted_signer_id,
            "role": required_role, "public_key_sha256": fingerprint,
            "artifacts_verified": len(manifest["artifacts"])}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="performance-lab-provenance")
    commands = parser.add_subparsers(dest="command", required=True)
    sign = commands.add_parser("sign-manifest")
    sign.add_argument("payload", type=Path)
    sign.add_argument("private_key", type=Path)
    sign.add_argument("output", type=Path)
    verify = commands.add_parser("verify-manifest")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("public_key", type=Path)
    verify.add_argument("evidence_root", type=Path)
    verify.add_argument("expected_revision")
    verify.add_argument("trusted_signer_id")
    verify.add_argument("required_role", choices=("evidence-custodian", "independent-reviewer", "release-approver"))
    args = parser.parse_args(argv)
    try:
        if args.command == "sign-manifest":
            result = sign_manifest(args.payload, args.private_key, args.evidence_root, args.output)
            print(f"Signed {len(result['artifacts'])} artifact(s); signer={result['signer']['signer_id']}; revision={result['revision']}")
        else:
            result = verify_manifest(args.manifest, args.public_key, args.evidence_root,
                                     args.expected_revision, args.trusted_signer_id, args.required_role)
            print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
