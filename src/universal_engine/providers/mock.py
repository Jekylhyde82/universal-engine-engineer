"""Deterministic mock provider for contract and orchestration tests."""
from ..contracts import ProviderRequest, ProviderResult, ResultStatus
class MockProvider:
    provider_id = "mock.echo"
    def execute(self, request: ProviderRequest) -> ProviderResult:
        if not request.policy.allowed:
            return ProviderResult(request.correlation_id, ResultStatus.DENIED, {"reason": request.policy.reason}, "POLICY_DENIED")
        return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, {
            "provider_id": self.provider_id,
            "capability_id": request.capability_id,
            "operation": request.operation,
            "echo": dict(request.payload),
        })
