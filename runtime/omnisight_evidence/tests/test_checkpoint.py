import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from omnisight_evidence import EvidenceStore
from omnisight_evidence.checkpoint import create_checkpoint, verify_checkpoint


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "evidence.sqlite3"
        self.checkpoint = self.root / "separate" / "checkpoint.json"
        self.store = EvidenceStore(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def append(self, source="source"):
        return self.store.append(
            source_id=source, media_type="image/png", payload=b"fixture",
            producer="test-engine", producer_version="0.1.0",
            epistemic_status="observed", observation={"ok": True},
        )

    def test_checkpoint_matches_current_ledger(self):
        self.append()
        create_checkpoint(self.db, self.checkpoint)
        self.assertTrue(verify_checkpoint(self.db, self.checkpoint).valid)

    def test_checkpoint_remains_valid_after_append(self):
        self.append()
        create_checkpoint(self.db, self.checkpoint)
        self.append("second")
        self.assertTrue(verify_checkpoint(self.db, self.checkpoint).valid)

    def test_checkpoint_detects_valid_tail_truncation(self):
        self.append()
        self.append("second")
        create_checkpoint(self.db, self.checkpoint)
        with sqlite3.connect(self.db) as db:
            db.execute("DROP TRIGGER evidence_no_delete")
            db.execute("DELETE FROM evidence_records WHERE sequence=2")
        result = verify_checkpoint(self.db, self.checkpoint)
        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "ledger is shorter than checkpoint")

    def test_checkpoint_detects_replaced_prefix(self):
        self.append()
        create_checkpoint(self.db, self.checkpoint)
        with sqlite3.connect(self.db) as db:
            db.execute("DROP TRIGGER evidence_no_update")
            db.execute("UPDATE evidence_records SET record_hash=?", ("f" * 64,))
        result = verify_checkpoint(self.db, self.checkpoint)
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
