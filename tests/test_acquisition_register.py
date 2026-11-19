import tempfile
import unittest
from pathlib import Path

from universal_engine.uaie import UAIEError, UniversalAcquisitionIntegrationEngine


class AcquisitionRegisterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = UniversalAcquisitionIntegrationEngine(Path(self.tmp.name) / "uaie.sqlite3")
        self.record = self.engine.ingest_object(
            {"candidate": "publisher/model", "capability": "vision"},
            source="https://lmstudio.ai/models/example",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_register_preserves_original_idea_and_required_portfolio_fields(self):
        entry = self.engine.register_acquisition(
            self.record.record_id,
            original_idea_value="Integrate this model through UAIE and AFI.",
            revenue_models=("internal productivity", "licensed deployment"),
        )
        self.assertEqual(entry.lifecycle_status, "discovered")
        self.assertEqual(entry.original_idea_value, "Integrate this model through UAIE and AFI.")
        self.assertEqual(entry.potential_market_value, "NOT_ASSESSED")
        self.assertEqual(entry.revenue_models, ("internal productivity", "licensed deployment"))
        self.assertEqual(entry.development_timeline, "NOT_ASSESSED")
        self.assertEqual(entry.development_cost, "NOT_ASSESSED")
        self.assertEqual(entry.integration_cost, "NOT_ASSESSED")
        self.assertEqual(entry.risk_assessment, "PENDING")
        self.assertEqual(entry.evidence_verification_status, "UNVERIFIED")
        self.assertEqual(self.engine.get_acquisition(self.record.record_id), entry)

    def test_rejects_revenue_models_as_a_plain_string(self):
        with self.assertRaises(UAIEError):
            self.engine.register_acquisition(
                self.record.record_id,
                original_idea_value="Test invalid revenue model input.",
                revenue_models="not-a-list",
            )

    def test_register_creation_is_idempotent(self):
        kwargs = {"original_idea_value": "Preserve the original acquisition idea."}
        first = self.engine.register_acquisition(self.record.record_id, **kwargs)
        second = self.engine.register_acquisition(self.record.record_id, **kwargs)
        self.assertEqual(first.acquisition_id, second.acquisition_id)
        self.assertEqual(first.created_at, second.created_at)

    def test_lifecycle_requires_uaie_approval_before_register_approval_and_integration(self):
        entry = self.engine.register_acquisition(
            self.record.record_id, original_idea_value="Test governed lifecycle."
        )
        entry = self.engine.set_acquisition_lifecycle(self.record.record_id, "proposed")
        self.assertEqual(entry.lifecycle_status, "proposed")
        entry = self.engine.set_acquisition_lifecycle(self.record.record_id, "under_evaluation")
        self.assertEqual(entry.lifecycle_status, "under_evaluation")
        with self.assertRaises(UAIEError):
            self.engine.set_acquisition_lifecycle(self.record.record_id, "approved")
        self.engine.set_state(self.record.record_id, "approved")
        entry = self.engine.set_acquisition_lifecycle(self.record.record_id, "approved")
        self.assertEqual(entry.lifecycle_status, "approved")
        with self.assertRaises(UAIEError):
            self.engine.set_acquisition_lifecycle(self.record.record_id, "integrated")
        self.engine.set_state(self.record.record_id, "integrated")
        entry = self.engine.set_acquisition_lifecycle(self.record.record_id, "integrated")
        self.assertEqual(entry.lifecycle_status, "integrated")

    def test_rejects_missing_original_idea_and_unknown_assimilation(self):
        with self.assertRaises(UAIEError):
            self.engine.register_acquisition(self.record.record_id, original_idea_value="")
        with self.assertRaises(UAIEError):
            self.engine.register_acquisition("missing", original_idea_value="Idea")


if __name__ == "__main__":
    unittest.main()
