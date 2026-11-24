import tempfile
import unittest
from pathlib import Path

from omnisight_evidence import EvidenceStore
from omnisight_evidence.envelope import to_observation_envelope
from omnisight_evidence.world_model import WorldModel


class EnvelopeAndWorldModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = EvidenceStore(self.root / "evidence.sqlite3")
        self.record = self.store.append(
            source_id="screen-frame-1", media_type="image/png",
            payload=b"synthetic-frame", producer="vision-fixture",
            producer_version="0.1.0", epistemic_status="interpreted",
            observation={"entities": [{"label": "button", "text": "Save"}]},
            limitations=["synthetic fixture"],
            captured_at="2026-11-25T00:00:00Z",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_envelope_maps_digest_provenance_and_epistemic_state(self):
        envelope = to_observation_envelope(
            self.record, correlation_id="test-correlation",
            content_type="control", confidence={"value": 0.8, "meaning": "fixture score"},
        )
        self.assertEqual(envelope["source"]["media_digest"], "sha256:" + self.record.payload_sha256)
        self.assertEqual(envelope["producer"]["capability_id"], "vision-fixture")
        self.assertEqual(envelope["epistemic_status"], "interpreted")
        self.assertEqual(envelope["evidence_refs"], [self.record.record_id])
        self.assertNotIn("verification_ref", envelope)

    def test_envelope_does_not_upgrade_interpretation_to_verified(self):
        envelope = to_observation_envelope(self.record, correlation_id="corr")
        self.assertEqual(envelope["epistemic_status"], "interpreted")

    def test_world_assertion_requires_evidence_reference(self):
        model = WorldModel(self.root / "world.sqlite3", self.root / "evidence.sqlite3")
        assertion = model.add_assertion(
            subject_id="entity:button-1", predicate="has_label",
            object_value="Save", epistemic_status="interpreted",
            evidence_record_id=self.record.record_id,
        )
        self.assertEqual(assertion.evidence_record_id, self.record.record_id)
        self.assertEqual(len(model.list_assertions("entity:button-1")), 1)

    def test_verified_world_assertion_requires_verification_reference(self):
        model = WorldModel(self.root / "world.sqlite3", self.root / "evidence.sqlite3")
        with self.assertRaisesRegex(ValueError, "verification_ref"):
            model.add_assertion(
                subject_id="entity:button-1", predicate="has_label",
                object_value="Save", epistemic_status="verified",
                evidence_record_id=self.record.record_id,
            )

    def test_world_model_rejects_unknown_evidence_record(self):
        model = WorldModel(self.root / "world.sqlite3", self.root / "evidence.sqlite3")
        with self.assertRaisesRegex(ValueError, "does not exist"):
            model.add_assertion(subject_id="entity:1", predicate="label",
                object_value="unknown", epistemic_status="observed",
                evidence_record_id="missing-record")

    def test_world_model_preserves_conflicting_assertions(self):
        model = WorldModel(self.root / "world.sqlite3", self.root / "evidence.sqlite3")
        model.add_assertion(subject_id="entity:1", predicate="colour",
            object_value="red", epistemic_status="interpreted",
            evidence_record_id=self.record.record_id)
        model.add_assertion(subject_id="entity:1", predicate="colour",
            object_value="blue", epistemic_status="inferred",
            evidence_record_id=self.record.record_id)
        self.assertEqual(len(model.list_assertions("entity:1")), 2)


if __name__ == "__main__":
    unittest.main()
