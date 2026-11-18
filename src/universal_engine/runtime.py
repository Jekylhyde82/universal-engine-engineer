"""Policy-enforcing dispatch boundary for provider adapters."""
from dataclasses import replace
from datetime import datetime, timezone
from typing import Protocol

from .contracts import ContractViolation, PolicyDecision, ProviderRequest, ProviderResult, ResultStatus


class ExecutableProvider(Protocol):
    def execute(self, request: ProviderRequest) -> ProviderResult: ...


class PolicyEvaluator(Protocol):
    def evaluate(self, principal_id: str, capability_id: str, operation: str) -> PolicyDecision: ...


def dispatch(
    provider: ExecutableProvider,
    request: ProviderRequest,
    *,
    policy_engine: PolicyEvaluator,
    principal_id: str,
) -> ProviderResult:
    """Evaluate trusted in-process policy before executing one provider.

    The principal ID must originate from an authenticated identity layer.
    Provider execute methods are internal adapter entry points and must not be
    exposed directly to untrusted callers.
    """
    decision = policy_engine.evaluate(principal_id, request.capability_id, request.operation)
    if not isinstance(decision, PolicyDecision):
        raise ContractViolation("policy engine must return a PolicyDecision")
    if not decision.allowed:
        return ProviderResult(
            correlation_id=request.correlation_id,
            status=ResultStatus.DENIED,
            output={"reason": decision.reason},
            error_code="POLICY_DENIED",
        )
    if request.deadline is not None and request.deadline <= datetime.now(timezone.utc):
        return ProviderResult(
            correlation_id=request.correlation_id,
            status=ResultStatus.TIMED_OUT,
            output={},
            error_code="DEADLINE_EXPIRED",
        )
    authorized_request = replace(request, policy=decision)
    result = provider.execute(authorized_request)
    if not isinstance(result, ProviderResult):
        raise ContractViolation("provider must return a ProviderResult")
    if result.correlation_id != request.correlation_id:
        raise ContractViolation("provider result correlation_id does not match request")
    return result
