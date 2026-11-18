import unittest
from universal_engine.contracts import ContractViolation
from universal_engine.lifecycle import LifecycleState
from universal_engine.providers.registry import ProviderKind, ProviderRegistry

class MinimalInference:
    def generate(self, request):
        return None

class MinimalWorkflow:
    def run(self, request):
        return None
    def resume(self, checkpoint_id, request):
        return None

class RegistryTests(unittest.TestCase):
    def test_registers_only_integrated_providers(self):
        registry = ProviderRegistry()
        with self.assertRaises(ContractViolation):
            registry.register("local.llama", ProviderKind.INFERENCE, MinimalInference(), LifecycleState.APPROVED)
        result = registry.register("local.llama", ProviderKind.INFERENCE, MinimalInference(), LifecycleState.INTEGRATED)
        self.assertEqual(result.provider_id, "local.llama")

    def test_rejects_duplicate_provider_ids(self):
        registry = ProviderRegistry()
        registry.register("workflow.langgraph", ProviderKind.WORKFLOW, MinimalWorkflow(), LifecycleState.INTEGRATED)
        with self.assertRaises(ContractViolation):
            registry.register("workflow.langgraph", ProviderKind.WORKFLOW, MinimalWorkflow(), LifecycleState.INTEGRATED)

    def test_rejects_adapter_missing_contract_methods(self):
        registry = ProviderRegistry()
        with self.assertRaises(ContractViolation):
            registry.register("bad.workflow", ProviderKind.WORKFLOW, MinimalInference(), LifecycleState.INTEGRATED)

    def test_lookup_rejects_unknown_provider(self):
        with self.assertRaises(ContractViolation):
            ProviderRegistry().get("unknown")

    def test_list_is_immutable_snapshot(self):
        registry = ProviderRegistry()
        registry.register("local.llama", ProviderKind.INFERENCE, MinimalInference(), LifecycleState.INTEGRATED)
        self.assertIsInstance(registry.list(), tuple)
        self.assertEqual(len(registry.list()), 1)

if __name__ == "__main__":
    unittest.main()
