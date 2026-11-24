import unittest
from uuid import uuid4

from universal_engine.contracts import ProviderRequest, ProviderResult, ResultStatus, ContractViolation
from universal_engine.fusion import AFIPrimeFusionCoordinator, FusionStatus, FUSION_FUNCTION_ID, SpecialistInvocation
from universal_engine.lifecycle import LifecycleState
from universal_engine.policy import PolicyEngine, PolicyRule
from universal_engine.providers.registry import ProviderKind, ProviderRegistry


class IntegratedLifecycle:
    def state_of(self, capability_id):
        return LifecycleState.INTEGRATED


class EchoProvider:
    def __init__(self, value):
        self.value = value
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        return ProviderResult(
            correlation_id=request.correlation_id,
            status=ResultStatus.SUCCEEDED,
            output={"finding": self.value, "input": dict(request.payload)},
        )

    def generate(self, request):
        return self.execute(request)


class RaisingProvider(EchoProvider):
    def execute(self, request):
        self.calls += 1
        raise RuntimeError("synthetic provider failure")


def make_request(capability_id, operation="generate", correlation_id=None):
    return ProviderRequest(
        correlation_id=correlation_id or str(uuid4()),
        capability_id=capability_id,
        operation=operation,
        payload={"question": "test"},
    )


def make_coordinator(*, deny_critic=False):
    registry = ProviderRegistry()
    brainstorm = EchoProvider("three alternatives")
    critic = EchoProvider("one risk")
    registry.register("brainstorm", "cap.brainstorm", ProviderKind.INFERENCE, brainstorm, IntegratedLifecycle())
    registry.register("critic", "cap.critic", ProviderKind.INFERENCE, critic, IntegratedLifecycle())
    rules = [
        PolicyRule("allow-brainstorm", "operator-1", "cap.brainstorm", "generate", True, "test grant"),
        PolicyRule(
            "critic-policy", "operator-1", "cap.critic", "generate",
            not deny_critic, "test critic decision",
        ),
    ]
    return AFIPrimeFusionCoordinator(registry, PolicyEngine(rules)), registry, brainstorm, critic


class AFIPrimeFusionTests(unittest.TestCase):
    def test_dispatches_multiple_specialists_and_preserves_distinct_findings(self):
        coordinator, _, brainstorm, critic = make_coordinator()
        result = coordinator.fuse(
            [
                SpecialistInvocation("brainstorm", make_request("cap.brainstorm")),
                SpecialistInvocation("critic", make_request("cap.critic")),
            ],
            principal_id="operator-1",
        )
        self.assertEqual(result.fusion_function_id, FUSION_FUNCTION_ID)
        self.assertEqual(result.status, FusionStatus.SUCCEEDED)
        self.assertEqual([item.provider_id for item in result.outcomes], ["brainstorm", "critic"])
        self.assertEqual(result.outcomes[0].result.output["finding"], "three alternatives")
        self.assertEqual(result.outcomes[1].result.output["finding"], "one risk")
        self.assertEqual((brainstorm.calls, critic.calls), (1, 1))

    def test_denied_specialist_is_not_called_and_successful_peer_is_preserved(self):
        coordinator, _, brainstorm, critic = make_coordinator(deny_critic=True)
        result = coordinator.fuse(
            [
                SpecialistInvocation("brainstorm", make_request("cap.brainstorm")),
                SpecialistInvocation("critic", make_request("cap.critic")),
            ],
            principal_id="operator-1",
        )
        self.assertEqual(result.status, FusionStatus.PARTIAL)
        self.assertEqual(result.outcomes[0].result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(result.outcomes[1].result.status, ResultStatus.DENIED)
        self.assertEqual((brainstorm.calls, critic.calls), (1, 0))

    def test_provider_capability_mismatch_rejects_entire_batch_before_side_effects(self):
        coordinator, _, brainstorm, critic = make_coordinator()
        invocations = [
            SpecialistInvocation("brainstorm", make_request("cap.brainstorm")),
            SpecialistInvocation("critic", make_request("cap.wrong")),
        ]
        with self.assertRaises(ContractViolation):
            coordinator.fuse(invocations, principal_id="operator-1")
        self.assertEqual((brainstorm.calls, critic.calls), (0, 0))

    def test_one_provider_exception_does_not_erase_peer_result(self):
        registry = ProviderRegistry()
        broken = RaisingProvider("unused")
        healthy = EchoProvider("independent finding")
        registry.register("broken", "cap.broken", ProviderKind.INFERENCE, broken, IntegratedLifecycle())
        registry.register("healthy", "cap.healthy", ProviderKind.INFERENCE, healthy, IntegratedLifecycle())
        policy = PolicyEngine([
            PolicyRule("allow-broken", "operator-1", "cap.broken", "generate", True, "test grant"),
            PolicyRule("allow-healthy", "operator-1", "cap.healthy", "generate", True, "test grant"),
        ])
        coordinator = AFIPrimeFusionCoordinator(registry, policy)
        result = coordinator.fuse(
            [
                SpecialistInvocation("broken", make_request("cap.broken")),
                SpecialistInvocation("healthy", make_request("cap.healthy")),
            ],
            principal_id="operator-1",
        )
        self.assertEqual(result.status, FusionStatus.PARTIAL)
        self.assertEqual(result.outcomes[0].result.status, ResultStatus.FAILED)
        self.assertEqual(result.outcomes[0].result.error_code, "PROVIDER_EXECUTION_FAILED")
        self.assertEqual(result.outcomes[1].result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(healthy.calls, 1)

    def test_unknown_provider_rejects_batch_before_any_provider_runs(self):
        coordinator, _, brainstorm, critic = make_coordinator()
        with self.assertRaises(ContractViolation):
            coordinator.fuse(
                [SpecialistInvocation("not-registered", make_request("cap.unknown"))],
                principal_id="operator-1",
            )
        self.assertEqual((brainstorm.calls, critic.calls), (0, 0))

    def test_duplicate_correlation_ids_are_rejected_before_dispatch(self):
        coordinator, _, brainstorm, critic = make_coordinator()
        correlation_id = str(uuid4())
        invocations = [
            SpecialistInvocation("brainstorm", make_request("cap.brainstorm", correlation_id=correlation_id)),
            SpecialistInvocation("critic", make_request("cap.critic", correlation_id=correlation_id)),
        ]
        with self.assertRaises(ContractViolation):
            coordinator.fuse(invocations, principal_id="operator-1")
        self.assertEqual((brainstorm.calls, critic.calls), (0, 0))

    def test_no_matching_allow_rules_produce_denied_fusion(self):
        registry = ProviderRegistry()
        provider = EchoProvider("must not run")
        registry.register("brainstorm", "cap.brainstorm", ProviderKind.INFERENCE, provider, IntegratedLifecycle())
        coordinator = AFIPrimeFusionCoordinator(registry, PolicyEngine())
        result = coordinator.fuse(
            [SpecialistInvocation("brainstorm", make_request("cap.brainstorm"))],
            principal_id="operator-1",
        )
        self.assertEqual(result.status, FusionStatus.DENIED)
        self.assertEqual(result.outcomes[0].result.status, ResultStatus.DENIED)
        self.assertEqual(provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
