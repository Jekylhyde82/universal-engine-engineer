"""Policy-enforcing dispatch boundary for provider adapters."""
from datetime import datetime, timezone
from typing import Protocol
from .contracts import ContractViolation, ProviderRequest, ProviderResult, ResultStatus

class ExecutableProvider(Protocol):
    def execute(self, request: ProviderRequest) -> ProviderResult: ...

def dispatch(provider: ExecutableProvider, request: ProviderRequest) -> ProviderResult:
    """Enforce policy and correlation invariants around one provider call.

    The policy decision must be made upstream. This function enforces the
    decision; it does not grant permissions or turn workflow providers into
    policy authorities.
    """
    if not request.policy.allowed:
        return ProviderResult(
            correlation_id=request.correlation_id,
            status=ResultStatus.DENIED,
            output={"reason": request.policy.reason},
            error_code="POLICY_DENIED",
        )
    if request.deadline is not None and request.deadline <= datetime.now(timezone.utc):
        return ProviderResult(
            correlation_id=request.correlation_id,
            status=ResultStatus.TIMED_OUT,
            output={},
            error_code="DEADLINE_EXPIRED",
        )
    result = provider.execute(request)
    if result.correlation_id != request.correlation_id:
        raise ContractViolation("provider result correlation_id does not match request")
    return result
