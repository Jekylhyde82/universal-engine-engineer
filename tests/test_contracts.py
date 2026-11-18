import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from universal_engine.contracts import ContractViolation, PolicyDecision, ProviderRequest, ProviderResult, ResultStatus
from universal_engine.lifecycle import LifecycleState, transition
from universal_engine.providers.mock import MockProvider

def make_request(**overrides):
    values = dict(correlation_id=str(uuid4()), capability_id="test.echo", operation="echo",
        payload={"message": "hello"}, deadline=datetime.now(timezone.utc) + timedelta(minutes=1),
        policy=PolicyDecision(True, "test policy allows", "test-policy-v1"))
    values.update(overrides)
    return ProviderRequest(**values)

class ContractTests(unittest.TestCase):
    def test_valid_request(self):
        self.assertEqual(make_request().operation, "echo")
    def test_rejects_invalid_correlation_id(self):
        with self.assertRaises(ContractViolation): make_request(correlation_id="not-a-uuid")
    def test_rejects_empty_capability(self):
        with self.assertRaises(ContractViolation): make_request(capability_id=" ")
    def test_rejects_naive_deadline(self):
        with self.assertRaises(ContractViolation): make_request(deadline=datetime.now())
    def test_rejects_expired_deadline(self):
        with self.assertRaises(ContractViolation): make_request(deadline=datetime.now(timezone.utc)-timedelta(seconds=1))
    def test_rejects_non_json_payload(self):
        with self.assertRaises(ContractViolation): make_request(payload={"bad": object()})
    def test_rejects_non_object_payload(self):
        with self.assertRaises(ContractViolation): make_request(payload=["not", "an", "object"])
    def test_rejects_non_finite_json(self):
        with self.assertRaises(ContractViolation): make_request(payload={"bad": float("nan")})
    def test_mock_provider_success(self):
        result = MockProvider().execute(make_request())
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(result.output["echo"], {"message": "hello"})
    def test_mock_provider_denies_by_default(self):
        denied = make_request(policy=PolicyDecision(False, "not approved", "deny-v1"))
        result = MockProvider().execute(denied)
        self.assertEqual(result.status, ResultStatus.DENIED)
        self.assertEqual(result.error_code, "POLICY_DENIED")
    def test_failed_result_requires_error_code(self):
        with self.assertRaises(ContractViolation): ProviderResult(str(uuid4()), ResultStatus.FAILED)
    def test_lifecycle_happy_path(self):
        state = LifecycleState.DISCOVERED
        for target in (LifecycleState.PROPOSED, LifecycleState.UNDER_EVALUATION, LifecycleState.APPROVED, LifecycleState.INTEGRATED):
            state = transition(state, target)
        self.assertEqual(state, LifecycleState.INTEGRATED)
    def test_lifecycle_rejects_skipped_approval(self):
        with self.assertRaises(ContractViolation): transition(LifecycleState.DISCOVERED, LifecycleState.INTEGRATED)

if __name__ == "__main__":
    unittest.main()
