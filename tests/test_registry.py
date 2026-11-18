import unittest
from universal_engine.contracts import ContractViolation
from universal_engine.lifecycle import CapabilityLifecycle, LifecycleState
from universal_engine.providers.registry import ProviderKind, ProviderRegistry

class MinimalInference:
    def execute(self, request):
        return None
    def generate(self, request):
        return None

class MinimalWorkflow:
    def execute(self, request):
        return None
    def run(self, request):
        return None
    def resume(self, checkpoint_id, request):
        return None

def integrated_lifecycle(capability_id):
    lifecycle = CapabilityLifecycle()
    lifecycle.discover(capability_id)
    for state in (LifecycleState.PROPOSED, LifecycleState.UNDER_EVALUATION, LifecycleState.APPROVED, LifecycleState.INTEGRATED):
        lifecycle.advance(capability_id, state)
    return lifecycle

class RegistryTests(unittest.TestCase):
    def test_registers_only_integrated_capabilities(self):
        registry = ProviderRegistry()
        lifecycle = CapabilityLifecycle()
        lifecycle.discover("cap.llama")
        lifecycle.advance("cap.llama", LifecycleState.PROPOSED)
        with self.assertRaises(ContractViolation):
            registry.register("local.llama", "cap.llama", ProviderKind.INFERENCE, MinimalInference(), lifecycle)
        result = registry.register("local.llama", "cap.llama", ProviderKind.INFERENCE, MinimalInference(), integrated_lifecycle("cap.llama"))
        self.assertEqual(result.provider_id, "local.llama")

    def test_rejects_duplicate_provider_ids(self):
        registry = ProviderRegistry()
        lifecycle = integrated_lifecycle("cap.workflow")
        registry.register("workflow.langgraph", "cap.workflow", ProviderKind.WORKFLOW, MinimalWorkflow(), lifecycle)
        with self.assertRaises(ContractViolation):
            registry.register("workflow.langgraph", "cap.workflow", ProviderKind.WORKFLOW, MinimalWorkflow(), lifecycle)

    def test_rejects_adapter_missing_contract_methods(self):
        with self.assertRaises(ContractViolation):
            ProviderRegistry().register("bad.workflow", "cap.workflow", ProviderKind.WORKFLOW, MinimalInference(), integrated_lifecycle("cap.workflow"))

    def test_rejects_unknown_provider_lookup(self):
        with self.assertRaises(ContractViolation):
            ProviderRegistry().get("unknown")

    def test_rejects_invalid_provider_kind(self):
        with self.assertRaises(ContractViolation):
            ProviderRegistry().register("bad.kind", "cap.bad", "unknown", MinimalInference(), integrated_lifecycle("cap.bad"))

    def test_list_is_immutable_snapshot(self):
        registry = ProviderRegistry()
        lifecycle = integrated_lifecycle("cap.llama")
        registry.register("local.llama", "cap.llama", ProviderKind.INFERENCE, MinimalInference(), lifecycle)
        self.assertIsInstance(registry.list(), tuple)
        self.assertEqual(len(registry.list()), 1)

if __name__ == "__main__":
    unittest.main()
