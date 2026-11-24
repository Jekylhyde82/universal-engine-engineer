import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from universal_engine import ContractViolation, FusionResult, FusionStatus, ProviderResult, ResultStatus, SQLiteFusionEvidenceLedger, SpecialistOutcome
from universal_engine.fusion import FUSION_FUNCTION_ID


def make_result(fusion_id=None, correlation_id=None):
    correlation_id = correlation_id or str(uuid4())
    outcome = SpecialistOutcome(
        provider_id="specialist.critic",
        capability_id="capability.critic",
        correlation_id=correlation_id,
        request_sha256="a" * 64,
        result_sha256="b" * 64,
        result=ProviderResult(
            correlation_id=correlation_id,
            status=ResultStatus.SUCCEEDED,
            output={"finding": "synthetic fixture"},
        ),
        elapsed_ms=1.25,
    )
    return FusionResult(
        fusion_id=fusion_id or str(uuid4()),
        fusion_function_id=FUSION_FUNCTION_ID,
        principal_id="test-principal",
        created_at=datetime.now(timezone.utc),
        status=FusionStatus.SUCCEEDED,
        outcomes=(outcome,),
    )


class SQLiteFusionEvidenceTests(unittest.TestCase):
    def test_records_digest_only_events_and_verifies_hash_chain(self):
        with SQLiteFusionEvidenceLedger(":memory:") as ledger:
            result = make_result()
            events = ledger.record(result)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].fusion_id, result.fusion_id)
            self.assertEqual(events[0].request_sha256, "a" * 64)
            self.assertEqual(events[0].result_sha256, "b" * 64)
            self.assertTrue(ledger.verify_chain())
            self.assertEqual(len(ledger.events(result.fusion_id)), 1)
            self.assertFalse(hasattr(events[0], "raw_output"))

    def test_hash_chain_detects_event_tampering(self):
        with SQLiteFusionEvidenceLedger(":memory:") as ledger:
            ledger.record(make_result())
            ledger._connection.execute(
                "UPDATE fusion_evidence_events SET status = ? WHERE sequence = 1",
                ("failed",),
            )
            self.assertFalse(ledger.verify_chain())

    def test_persists_and_verifies_chain_after_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "fusion-evidence.db")
            first = SQLiteFusionEvidenceLedger(path)
            result = make_result()
            first.record(result)
            self.assertTrue(first.verify_chain())
            first.close()

            reopened = SQLiteFusionEvidenceLedger(path)
            self.assertTrue(reopened.verify_chain())
            self.assertEqual(len(reopened.events()), 1)
            reopened.close()

    def test_duplicate_fusion_event_is_rejected_atomically(self):
        with SQLiteFusionEvidenceLedger(":memory:") as ledger:
            result = make_result()
            ledger.record(result)
            with self.assertRaises(ContractViolation):
                ledger.record(result)
            self.assertEqual(len(ledger.events()), 1)
            self.assertTrue(ledger.verify_chain())


if __name__ == "__main__":
    unittest.main()
