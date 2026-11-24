"""Canonical AFI PRIME specialist coordination over approved provider adapters.

This module coordinates independent specialists. It deliberately preserves their
separate outputs and failures; it does not fabricate consensus or certify truth.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from time import perf_counter
from typing import Iterable
from uuid import uuid4

from .contracts import ContractViolation, ProviderRequest, ProviderResult, ResultStatus
from .providers.registry import ProviderRegistry
from .runtime import PolicyEvaluator, dispatch

FUSION_FUNCTION_ID = "UNIFIED FUSION SYNERGY — AFI PRIME"


class FusionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    DENIED = "denied"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SpecialistInvocation:
    """One explicit request to one already-registered specialist provider."""

    provider_id: str
    request: ProviderRequest

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ContractViolation("provider_id is required")
        if not isinstance(self.request, ProviderRequest):
            raise ContractViolation("request must be a ProviderRequest")


@dataclass(frozen=True, slots=True)
class SpecialistOutcome:
    """One specialist's uncollapsed result and execution metadata."""

    provider_id: str
    capability_id: str
    correlation_id: str
    result: ProviderResult
    elapsed_ms: float


@dataclass(frozen=True, slots=True)
class FusionResult:
    """Aggregate execution envelope; specialist findings remain individually addressable."""

    fusion_id: str
    fusion_function_id: str
    principal_id: str
    created_at: datetime
    status: FusionStatus
    outcomes: tuple[SpecialistOutcome, ...]


class AFIPrimeFusionCoordinator:
    """The canonical AFI PRIME coordinator for approved provider specialists.

    The coordinator is not an authentication service, policy authority, verifier,
    or unrestricted agent. The principal must come from a trusted identity layer.
    All providers are preflighted before any specialist is dispatched. Policy is
    evaluated independently for every invocation by the existing dispatch boundary.
    """

    def __init__(
        self,
        providers: ProviderRegistry,
        policy_engine: PolicyEvaluator,
        *,
        max_workers: int = 9,
    ) -> None:
        if not isinstance(max_workers, int) or isinstance(max_workers, bool) or max_workers < 1:
            raise ContractViolation("max_workers must be a positive integer")
        self._providers = providers
        self._policy_engine = policy_engine
        self._max_workers = max_workers

    def fuse(
        self,
        invocations: Iterable[SpecialistInvocation],
        *,
        principal_id: str,
    ) -> FusionResult:
        """Dispatch an explicit batch and preserve every specialist outcome.

        Preflight errors reject the whole batch before side effects. Runtime failures
        are isolated to their invocation so healthy specialists can still return.
        No automatic retries, provider discovery, activation, or approval occur here.
        """
        if not isinstance(principal_id, str) or not principal_id.strip():
            raise ContractViolation("principal_id is required")
        batch = tuple(invocations)
        if not batch:
            raise ContractViolation("at least one specialist invocation is required")
        if any(not isinstance(item, SpecialistInvocation) for item in batch):
            raise ContractViolation("every invocation must be a SpecialistInvocation")

        correlation_ids = [item.request.correlation_id for item in batch]
        if len(correlation_ids) != len(set(correlation_ids)):
            raise ContractViolation("correlation_id values must be unique within a fusion batch")

        # Resolve every provider and validate capability binding before dispatching
        # anything. A bad final entry must not leave earlier providers half-executed.
        registrations = []
        for item in batch:
            registration = self._providers.get(item.provider_id)
            if registration.capability_id != item.request.capability_id:
                raise ContractViolation(
                    f"provider {item.provider_id} is registered for capability "
                    f"{registration.capability_id}, not {item.request.capability_id}"
                )
            registrations.append(registration)

        outcomes: list[SpecialistOutcome | None] = [None] * len(batch)

        def execute_one(index: int, item: SpecialistInvocation) -> tuple[int, SpecialistOutcome]:
            started = perf_counter()
            try:
                registration = registrations[index]
                result = dispatch(
                    registration.adapter,
                    item.request,
                    policy_engine=self._policy_engine,
                    principal_id=principal_id,
                )
            except ContractViolation as exc:
                result = ProviderResult(
                    correlation_id=item.request.correlation_id,
                    status=ResultStatus.FAILED,
                    output={"failure_class": "contract_violation"},
                    error_code="PROVIDER_CONTRACT_VIOLATION",
                    error_message=type(exc).__name__,
                )
            except Exception as exc:  # isolate one provider fault from its peers
                result = ProviderResult(
                    correlation_id=item.request.correlation_id,
                    status=ResultStatus.FAILED,
                    output={"failure_class": "provider_exception"},
                    error_code="PROVIDER_EXECUTION_FAILED",
                    error_message=type(exc).__name__,
                )
            elapsed_ms = (perf_counter() - started) * 1000
            return index, SpecialistOutcome(
                provider_id=item.provider_id,
                capability_id=item.request.capability_id,
                correlation_id=item.request.correlation_id,
                result=result,
                elapsed_ms=round(elapsed_ms, 3),
            )

        worker_count = min(self._max_workers, len(batch))
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="afi-prime") as pool:
            futures = [pool.submit(execute_one, index, item) for index, item in enumerate(batch)]
            for future in as_completed(futures):
                index, outcome = future.result()
                outcomes[index] = outcome

        completed = tuple(item for item in outcomes if item is not None)
        statuses = [item.result.status for item in completed]
        if all(status is ResultStatus.SUCCEEDED for status in statuses):
            fusion_status = FusionStatus.SUCCEEDED
        elif all(status is ResultStatus.DENIED for status in statuses):
            fusion_status = FusionStatus.DENIED
        elif any(status is ResultStatus.SUCCEEDED for status in statuses):
            fusion_status = FusionStatus.PARTIAL
        else:
            fusion_status = FusionStatus.FAILED

        return FusionResult(
            fusion_id=str(uuid4()),
            fusion_function_id=FUSION_FUNCTION_ID,
            principal_id=principal_id,
            created_at=datetime.now(timezone.utc),
            status=fusion_status,
            outcomes=completed,
        )
