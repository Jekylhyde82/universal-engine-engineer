import unittest

from universal_engine.contracts import ContractViolation
from universal_engine.lifecycle import CapabilityLifecycle, LifecycleState
from universal_engine.providers.registry import ProviderKind, ProviderRegistry


class MinimalNetworkProvider:
    def execute(self, request):
        return None

    def connect(self, request):
        return None

    def disconnect(self, request):
        return None

    def status(self, request):
        return None


def integrated_lifecycle(capability_id):
    lifecycle = CapabilityLifecycle()
    lifecycle.discover(capability_id)
    for state in (
        LifecycleState.PROPOSED,
        LifecycleState.UNDER_EVALUATION,
        LifecycleState.APPROVED,
        LifecycleState.INTEGRATED,
    ):
        lifecycle.advance(capability_id, state)
    return lifecycle


class UPNProviderRegistrationTests(unittest.TestCase):
    def test_network_provider_kind_is_available(self):
        self.assertEqual(ProviderKind.NETWORK.value, "network")

    def test_network_provider_registration_requires_integrated_capability(self):
        registry = ProviderRegistry()
        lifecycle = CapabilityLifecycle()
        lifecycle.discover("cap.upn.network")
        with self.assertRaises(ContractViolation):
            registry.register(
                "upn.wireguard", "cap.upn.network", ProviderKind.NETWORK,
                MinimalNetworkProvider(), lifecycle,
            )

        result = registry.register(
            "upn.wireguard", "cap.upn.network", ProviderKind.NETWORK,
            MinimalNetworkProvider(), integrated_lifecycle("cap.upn.network"),
        )
        self.assertEqual(result.provider_id, "upn.wireguard")

    def test_network_adapter_must_implement_full_contract(self):
        class IncompleteNetworkProvider:
            def execute(self, request):
                return None

        with self.assertRaises(ContractViolation):
            ProviderRegistry().register(
                "upn.incomplete", "cap.upn.network", ProviderKind.NETWORK,
                IncompleteNetworkProvider(), integrated_lifecycle("cap.upn.network"),
            )


if __name__ == "__main__":
    unittest.main()
