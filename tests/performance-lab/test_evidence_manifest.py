from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from performance_lab.evidence import create_evidence_manifest, verify_evidence_manifest


REVISION = "a" * 40
CREATED = "2026-11-13T12:00:00Z"


@pytest.fixture
def keys():
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw" / "trial-001.txt").write_text("captured response\n", encoding="utf-8")
    (tmp_path / "report.json").write_text(json.dumps({"status": "NOT_VERIFIED"}), encoding="utf-8")
    return tmp_path


def make_manifest(root, keys):
    private_pem, _ = keys
    return create_evidence_manifest(
        evidence_root=root,
        revision=REVISION,
        signer_id="custodian-01",
        signer_role="evidence-custodian",
        artifacts=[
            {"path": "raw/trial-001.txt", "kind": "raw_trial_output"},
            {"path": "report.json", "kind": "comparison_report"},
        ],
        private_key_pem=private_pem,
        created_at=CREATED,
    )


def test_manifest_signs_and_verifies_revision_bound_artifacts(evidence_root, keys):
    _, public_pem = keys
    manifest = make_manifest(evidence_root, keys)
    assert verify_evidence_manifest(
        manifest,
        evidence_root=evidence_root,
        trusted_public_key_pem=public_pem,
        expected_revision=REVISION,
        expected_signer_id="custodian-01",
        expected_signer_role="evidence-custodian",
    ) == []


def test_manifest_rejects_wrong_revision(evidence_root, keys):
    _, public_pem = keys
    manifest = make_manifest(evidence_root, keys)
    errors = verify_evidence_manifest(
        manifest, evidence_root=evidence_root, trusted_public_key_pem=public_pem,
        expected_revision="b" * 40,
    )
    assert "manifest revision does not match the expected candidate revision" in errors


def test_manifest_rejects_tampered_artifact(evidence_root, keys):
    _, public_pem = keys
    manifest = make_manifest(evidence_root, keys)
    (evidence_root / "raw" / "trial-001.txt").write_text("altered response\n", encoding="utf-8")
    errors = verify_evidence_manifest(
        manifest, evidence_root=evidence_root, trusted_public_key_pem=public_pem,
        expected_revision=REVISION,
    )
    assert any("artifact SHA-256 mismatch" in error for error in errors)


def test_manifest_rejects_tampered_signed_payload(evidence_root, keys):
    _, public_pem = keys
    manifest = make_manifest(evidence_root, keys)
    manifest["signer"]["signer_id"] = "forged-custodian"
    errors = verify_evidence_manifest(
        manifest, evidence_root=evidence_root, trusted_public_key_pem=public_pem,
        expected_revision=REVISION,
    )
    assert "Ed25519 manifest signature is invalid" in errors


def test_manifest_rejects_untrusted_public_key(evidence_root, keys):
    manifest = make_manifest(evidence_root, keys)
    other_private = Ed25519PrivateKey.generate()
    other_public = other_private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    errors = verify_evidence_manifest(
        manifest, evidence_root=evidence_root, trusted_public_key_pem=other_public,
        expected_revision=REVISION,
    )
    assert any("fingerprint does not match" in error for error in errors)
    assert "Ed25519 manifest signature is invalid" in errors


def test_manifest_rejects_path_traversal(evidence_root, keys):
    private_pem, _ = keys
    with pytest.raises(ValueError, match="traversal-free"):
        create_evidence_manifest(
            evidence_root=evidence_root, revision=REVISION, signer_id="custodian-01",
            signer_role="evidence-custodian", artifacts=[{"path": "../outside.txt", "kind": "raw"}],
            private_key_pem=private_pem, created_at=CREATED,
        )


def test_manifest_rejects_duplicate_artifact_paths(evidence_root, keys):
    private_pem, _ = keys
    with pytest.raises(ValueError, match="Duplicate artifact path"):
        create_evidence_manifest(
            evidence_root=evidence_root, revision=REVISION, signer_id="custodian-01",
            signer_role="evidence-custodian",
            artifacts=[{"path": "report.json", "kind": "report"}, {"path": "report.json", "kind": "duplicate"}],
            private_key_pem=private_pem, created_at=CREATED,
        )


def test_manifest_rejects_symlink_escape(evidence_root, keys, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = evidence_root / "escape.txt"
    link.symlink_to(outside)
    private_pem, _ = keys
    with pytest.raises(ValueError, match="outside evidence root"):
        create_evidence_manifest(
            evidence_root=evidence_root, revision=REVISION, signer_id="custodian-01",
            signer_role="evidence-custodian", artifacts=[{"path": "escape.txt", "kind": "raw"}],
            private_key_pem=private_pem, created_at=CREATED,
        )
