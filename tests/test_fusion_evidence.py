import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from universal_engine import AFIPrimeFusionCoordinator, ContractViolation, FusionEvidencePersistenceError, FusionResult, FusionStatus, ProviderRequest, ProviderResult, ResultStatus, SQLiteFusionEvidenceLedger, SpecialistInvocation, SpecialistOutcome
from universal_engine.fusion import FUSION_FUNCTION_ID
from universal_engine.lifecycle import LifecycleState
from universal_engine.policy import PolicyEngine, PolicyRule
from universal_engine.providers.registry import ProviderKind, ProviderRegistry


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



class IntegratedLifecycle:
    def state_of(self, capability_id):
        return LifecycleState.INTEGRATED


class TestProvider:
    def execute(self, request):
        return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, {"answer": "synthetic"})
    def generate(self, request):
        return self.execute(request)


class FailingSink:
    def record(self, result):
        raise OSError("synthetic storage failure")


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


    def test_coordinator_writes_fusion_result_to_configured_ledger(self):
        registry = ProviderRegistry()
        provider = TestProvider()
        registry.register("provider.one", "cap.one", ProviderKind.INFERENCE, provider, IntegratedLifecycle())
        policy = PolicyEngine([
            PolicyRule("allow-one", "operator", "cap.one", "generate", True, "test grant")
        ])
        with SQLiteFusionEvidenceLedger(":memory:") as ledger:
            coordinator = AFIPrimeFusionCoordinator(registry, policy, evidence_sink=ledger)
            request = ProviderRequest(
                correlation_id=str(uuid4()),
                capability_id="cap.one",
                operation="generate",
                payload={"input": "synthetic"},
            )
            result = coordinator.fuse(
                [SpecialistInvocation("provider.one", request)],
                principal_id="operator",
            )
            events = ledger.events(result.fusion_id)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].request_sha256, result.outcomes[0].request_sha256)
            self.assertEqual(events[0].result_sha256, result.outcomes[0].result_sha256)
            self.assertTrue(ledger.verify_chain())

    def test_evidence_sink_failure_returns_completed_result_on_exception(self):
        registry = ProviderRegistry()
        provider = TestProvider()
        registry.register("provider.one", "cap.one", ProviderKind.INFERENCE, provider, IntegratedLifecycle())
        policy = PolicyEngine([
            PolicyRule("allow-one", "operator", "cap.one", "generate", True, "test grant")
        ])
        coordinator = AFIPrimeFusionCoordinator(registry, policy, evidence_sink=FailingSink())
        request = ProviderRequest(
            correlation_id=str(uuid4()),
            capability_id="cap.one",
            operation="generate",
            payload={"input": "synthetic"},
        )
        with self.assertRaises(FusionEvidencePersistenceError) as raised:
            coordinator.fuse(
                [SpecialistInvocation("provider.one", request)],
                principal_id="operator",
            )
        self.assertEqual(raised.exception.result.status, FusionStatus.SUCCEEDED)
        self.assertEqual(raised.exception.result.outcomes[0].result.status, ResultStatus.SUCCEEDED)



if __name__ == "__main__":
    unittest.main()
