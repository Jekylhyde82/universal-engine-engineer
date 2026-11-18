import tempfile
import unittest
from pathlib import Path

from universal_engine.uaie import UAIEError, UniversalAssimilationEngine


class UAIETests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "uaie.sqlite3")
        self.engine = UniversalAssimilationEngine(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ingests_and_assesses_text(self):
        record = self.engine.ingest_text(
            "A secure API integration capability with tests and verification.",
            "notes/design.md")
        self.assertEqual(record.state, "assimilated")
        self.assertGreater(record.value_score, 0)
        self.assertIn("integration", record.signals)
        self.assertEqual(self.engine.get(record.record_id).content_hash, record.content_hash)

    def test_binary_is_stored_without_execution_or_text_claim(self):
        record = self.engine.ingest_bytes(b"\x00\xff\x00", "payload.bin")
        self.assertEqual(record.state, "discovered")
        self.assertEqual(record.category, "binary_or_unparsed")
        self.assertEqual(record.byte_size, 3)

    def test_duplicate_content_is_deduplicated(self):
        first = self.engine.ingest_text("same content", "one.txt")
        second = self.engine.ingest_text("same content", "two.txt")
        self.assertEqual(first.record_id, second.record_id)
        self.assertTrue(second.duplicate)

    def test_directory_ingestion_and_search(self):
        root = Path(self.tmp.name) / "inbox"
        root.mkdir()
        (root / "a.md").write_text("Knowledge research and documentation", encoding="utf-8")
        (root / "b.py").write_text("def capability(): pass", encoding="utf-8")
        records = self.engine.ingest_path(root)
        self.assertEqual(len(records), 2)
        self.assertTrue(self.engine.search("knowledge"))

    def test_size_limit(self):
        engine = UniversalAssimilationEngine(self.db, max_bytes=3)
        with self.assertRaises(UAIEError):
            engine.ingest_bytes(b"four", "x.bin")

    def test_approval_then_integration_requires_two_steps(self):
        record = self.engine.ingest_text("A new capability", "idea.txt")
        with self.assertRaises(UAIEError):
            self.engine.set_state(record.record_id, "integrated")
        approved = self.engine.set_state(record.record_id, "approved")
        self.assertEqual(approved.state, "approved")
        integrated = self.engine.set_state(record.record_id, "integrated")
        self.assertEqual(integrated.state, "integrated")

    def test_rejected_record_cannot_be_integrated(self):
        record = self.engine.ingest_text("A candidate", "candidate.txt")
        self.engine.set_state(record.record_id, "rejected")
        with self.assertRaises(UAIEError):
            self.engine.set_state(record.record_id, "approved")

    def test_object_ingestion(self):
        record = self.engine.ingest_object({"tool": "example", "enabled": False})
        self.assertEqual(record.category, "structured_data")
        self.assertIn('"tool"', self.engine.export_record(record.record_id)["content"])


if __name__ == "__main__":
    unittest.main()
