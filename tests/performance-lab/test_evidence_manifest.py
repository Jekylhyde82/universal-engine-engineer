import base64
import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from performance_lab.provenance.evidence_manifest import sign_manifest, verify_manifest


def _keypair(tmp_path):
    private = Ed25519PrivateKey.generate()
    private_path = tmp_path / "private.pem"
    public_path = tmp_path / "public.pem"
    private_path.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public_path.write_bytes(private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    return private_path, public_path


def _payload(evidence):
    artifact = evidence / "raw.txt"
    artifact.write_text("verbatim captured evidence", encoding="utf-8")
    return {
        "schema_version": "1.0",
        "benchmark_id": "PYTHON-PERFORMANCE-LAB-001",
        "revision": "a" * 40,
        "created_at": "2026-11-13T00:00:00Z",
        "signer": {"signer_id": "custodian-test", "role": "evidence-custodian"},
        "artifacts": [{"path": "raw.txt", "kind": "raw-response",
                       "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}]
    }


def test_manifest_sign_and_verify_revision_key_and_artifact(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    private, public = _keypair(tmp_path)
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps(_payload(evidence)), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    sign_manifest(payload, private, evidence, manifest_path)
    result = verify_manifest(manifest_path, public, evidence, "a" * 40,
                             "custodian-test", "evidence-custodian")
    assert result["verified"] is True
    assert result["artifacts_verified"] == 1


def test_manifest_rejects_wrong_revision_and_signer(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    private, public = _keypair(tmp_path)
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps(_payload(evidence)), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    sign_manifest(payload, private, evidence, manifest)
    with pytest.raises(ValueError, match="revision"):
        verify_manifest(manifest, public, evidence, "b" * 40, "custodian-test", "evidence-custodian")
    with pytest.raises(ValueError, match="signer ID"):
        verify_manifest(manifest, public, evidence, "a" * 40, "someone-else", "evidence-custodian")


def test_manifest_rejects_artifact_tampering_and_path_escape(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    private, public = _keypair(tmp_path)
    payload_obj = _payload(evidence)
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps(payload_obj), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    sign_manifest(payload, private, manifest)
    (evidence / "raw.txt").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_manifest(manifest, public, evidence, "a" * 40, "custodian-test", "evidence-custodian")
    payload_obj["artifacts"][0]["path"] = "../outside.txt"
    payload.write_text(json.dumps(payload_obj), encoding="utf-8")
    with pytest.raises(ValueError, match="relative path"):
        sign_manifest(payload, private, manifest)


def test_manifest_rejects_modified_signed_payload(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    private, public = _keypair(tmp_path)
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps(_payload(evidence)), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    sign_manifest(payload, private, manifest)
    changed = json.loads(manifest.read_text(encoding="utf-8"))
    changed["signer"]["signer_id"] = "forged"
    manifest.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="signer ID"):
        verify_manifest(manifest, public, evidence, "a" * 40, "custodian-test", "evidence-custodian")
