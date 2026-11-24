import sqlite3
import tempfile
import unittest
from pathlib import Path

from omnisight_evidence import EvidenceStore, verify_ledger


class EvidenceStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "evidence.sqlite3"
        self.store = EvidenceStore(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def append_one(self, **overrides):
        values = dict(
            source_id="test-source", media_type="image/png", payload=b"sample-image",
            producer="fixture-engine", producer_version="0.1.0",
            epistemic_status="observed", observation={"objects": ["gear"]},
            limitations=["synthetic fixture"],
            captured_at="2026-11-25T00:00:00Z",
        )
        values.update(overrides)
        return self.store.append(**values)

    def test_append_and_verify_single_record(self):
        record = self.append_one()
        self.assertEqual(self.store.count(), 1)
        self.assertEqual(len(record.payload_sha256), 64)
        self.assertTrue(verify_ledger(self.db).valid)

    def test_append_links_to_previous_record(self):
        first = self.append_one()
        second = self.append_one(source_id="second-source")
        self.assertEqual(second.previous_hash, first.record_hash)
        result = verify_ledger(self.db)
        self.assertTrue(result.valid)
        self.assertEqual(result.records_checked, 2)

    def test_payload_digest_is_stable_sha256(self):
        import hashlib
        record = self.append_one()
        self.assertEqual(record.payload_sha256, hashlib.sha256(b"sample-image").hexdigest())

    def test_verified_status_requires_verification_reference(self):
        with self.assertRaisesRegex(ValueError, "verification_ref"):
            self.append_one(epistemic_status="verified")

    def test_verified_status_accepts_reference(self):
        self.append_one(epistemic_status="verified", verification_ref="audit:independent:1")
        self.assertTrue(verify_ledger(self.db).valid)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            self.append_one(captured_at="2026-11-25T00:00:00")

    def test_update_and_delete_are_blocked(self):
        self.append_one()
        with sqlite3.connect(self.db) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE evidence_records SET source_id='tampered'")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM evidence_records")

    def test_tampered_record_is_detected(self):
        self.append_one()
        with sqlite3.connect(self.db) as connection:
            connection.execute("DROP TRIGGER evidence_no_update")
            connection.execute("UPDATE evidence_records SET observation_json='{}'")
        result = verify_ledger(self.db)
        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "record digest mismatch")

    def test_tampered_chain_link_is_detected(self):
        self.append_one()
        with sqlite3.connect(self.db) as connection:
            connection.execute("DROP TRIGGER evidence_no_update")
            connection.execute("UPDATE evidence_records SET previous_hash='f' || substr(previous_hash, 2)")
        self.assertFalse(verify_ledger(self.db).valid)

    def test_invalid_epistemic_state_is_rejected(self):
        with self.assertRaises(ValueError):
            self.append_one(epistemic_status="certain")

    def test_sequence_gap_is_detected(self):
        self.append_one()
        self.append_one(source_id="second-source")
        with sqlite3.connect(self.db) as connection:
            connection.execute("DROP TRIGGER evidence_no_delete")
            connection.execute("DELETE FROM evidence_records WHERE sequence=1")
        result = verify_ledger(self.db)
        self.assertFalse(result.valid)
        self.assertEqual(result.records_checked, 1)
        self.assertEqual(result.reason, "sequence discontinuity")

    def test_empty_ledger_verifies(self):
        result = verify_ledger(self.db)
        self.assertTrue(result.valid)
        self.assertEqual(result.records_checked, 0)


if __name__ == "__main__":
    unittest.main()
