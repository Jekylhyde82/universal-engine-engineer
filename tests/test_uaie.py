import tempfile
import unittest
from pathlib import Path

from universal_engine.uaie import (UAIEError, UniversalAcquisitionEngine,
                                    UniversalAssimilationEngine)


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

    def test_concurrent_duplicate_ingestion_is_idempotent(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as pool:
            records = list(pool.map(
                lambda _: self.engine.ingest_text("same concurrent payload", "parallel.txt"),
                range(8)))
        self.assertEqual(len({record.record_id for record in records}), 1)
        self.assertEqual(sum(1 for record in records if not record.duplicate), 1)

    def test_integrated_record_cannot_be_rejected_or_reapproved(self):
        record = self.engine.ingest_text("Lifecycle test", "lifecycle.txt")
        self.engine.set_state(record.record_id, "approved")
        self.engine.set_state(record.record_id, "integrated")
        with self.assertRaises(UAIEError):
            self.engine.set_state(record.record_id, "rejected")

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


    def test_audit_chain_records_acquisition_and_detects_tampering(self):
        record = self.engine.ingest_text("audited payload", "audit/source.md")
        self.engine.ingest_text("audited payload", "audit/duplicate.md")
        self.assertTrue(self.engine.verify_audit_chain()["valid"])
        self.assertEqual(self.engine.verify_audit_chain()["event_count"], 2)
        import sqlite3
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE audit_events SET payload_json=? WHERE sequence=1",
                       ('{"tampered":true}',))
        result = self.engine.verify_audit_chain()
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_sequence"], 1)

    def test_audit_chain_records_lifecycle_and_assessment_events(self):
        record = self.engine.ingest_text("audited lifecycle", "audit/lifecycle.md")
        self.engine.record_capability_assessment(
            record.record_id, original_idea_value="Original idea",
            market_value="Unknown", revenue_models=[],
            development_timeline="Unknown", risk_assessment="Unassessed", evidence=[])
        self.engine.set_state(record.record_id, "approved")
        self.assertTrue(self.engine.verify_audit_chain()["valid"])
        self.assertEqual(self.engine.verify_audit_chain()["event_count"], 3)


    def test_duplicate_content_retains_all_source_provenance(self):
        first = self.engine.ingest_text("shared artifact", "source/first.md")
        second = self.engine.ingest_text("shared artifact", "source/second.md")
        self.assertEqual(first.record_id, second.record_id)
        self.assertTrue(second.duplicate)
        sources = self.engine.get_sources(first.record_id)
        self.assertEqual({item["source"] for item in sources},
                         {"source/first.md", "source/second.md"})


    def test_canonical_engine_name_and_legacy_alias(self):
        self.assertIs(UniversalAssimilationEngine, UniversalAcquisitionEngine)
        canonical = UniversalAcquisitionEngine(self.db)
        self.assertEqual(canonical.ingest_text("canonical", "canonical.txt").state,
                         "assimilated")


    def test_capability_register_preserves_original_idea_and_required_fields(self):
        record = self.engine.ingest_text("candidate", "ideas/original.md")
        assessment = self.engine.record_capability_assessment(
            record.record_id,
            original_idea_value="Original concept: adaptive capability discovery.",
            market_value="Unknown; requires market research.",
            revenue_models=["subscription", "licensing"],
            development_timeline="Unknown; requires technical scoping.",
            risk_assessment="Unassessed; threat and feasibility reviews required.",
            evidence=["https://example.invalid/source-note"],
            verification_status="under_review",
        )
        self.assertEqual(assessment.original_idea_value,
                         "Original concept: adaptive capability discovery.")
        self.assertEqual(assessment.verification_status, "under_review")
        self.assertEqual(assessment.revenue_models, ("subscription", "licensing"))
        self.assertEqual(self.engine.get_capability_assessment(record.record_id), assessment)

    def test_original_idea_value_cannot_be_overwritten(self):
        record = self.engine.ingest_text("original concept", "ideas/immutable.md")
        self.engine.record_capability_assessment(
            record.record_id, original_idea_value="Exact original wording",
            market_value="Unknown", revenue_models=[],
            development_timeline="Unknown", risk_assessment="Unassessed", evidence=[])
        with self.assertRaises(UAIEError):
            self.engine.record_capability_assessment(
                record.record_id, original_idea_value="Rewritten by a later process",
                market_value="Updated estimate", revenue_models=[],
                development_timeline="Updated timeline",
                risk_assessment="Updated risk review", evidence=[])
        stored = self.engine.get_capability_assessment(record.record_id)
        self.assertEqual(stored.original_idea_value, "Exact original wording")


    def test_capability_register_rejects_missing_original_idea_value(self):
        record = self.engine.ingest_text("candidate", "ideas/empty.md")
        with self.assertRaises(UAIEError):
            self.engine.record_capability_assessment(
                record.record_id, original_idea_value=" ", market_value="unknown",
                revenue_models=[], development_timeline="unknown",
                risk_assessment="unknown", evidence=[])

    def test_capability_register_requires_existing_acquisition_record(self):
        with self.assertRaises(UAIEError):
            self.engine.record_capability_assessment(
                "missing", original_idea_value="Original idea",
                market_value="unknown", revenue_models=[],
                development_timeline="unknown", risk_assessment="unknown", evidence=[])


if __name__ == "__main__":
    unittest.main()
