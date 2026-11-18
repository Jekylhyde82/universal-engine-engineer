"""Small, dependency-free contracts shared by provider adapters."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import json
from typing import Any, Mapping
from uuid import UUID

MAX_PAYLOAD_BYTES = 256 * 1024

class ContractViolation(ValueError):
    """Raised when a request or result violates the runtime contract."""

class ResultStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"
    TIMED_OUT = "timed_out"

@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    policy_id: str
    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise ContractViolation("allowed must be a boolean")
        if not self.reason.strip() or not self.policy_id.strip():
            raise ContractViolation("policy reason and policy_id are required")

@dataclass(frozen=True, slots=True)
class ProviderRequest:
    correlation_id: str
    capability_id: str
    operation: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    deadline: datetime | None = None
    policy: PolicyDecision = field(default_factory=lambda: PolicyDecision(False, "No policy decision supplied", "default-deny"))
    def __post_init__(self) -> None:
        try:
            UUID(self.correlation_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ContractViolation("correlation_id must be a UUID") from exc
        if not self.capability_id.strip() or not self.operation.strip():
            raise ContractViolation("capability_id and operation are required")
        if not isinstance(self.payload, Mapping):
            raise ContractViolation("payload must be a mapping/object")
        try:
            encoded = json.dumps(dict(self.payload), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ContractViolation("payload must contain finite JSON-compatible values") from exc
        if len(encoded) > MAX_PAYLOAD_BYTES:
            raise ContractViolation(f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")
        if self.deadline is not None:
            if self.deadline.tzinfo is None or self.deadline.utcoffset() is None:
                raise ContractViolation("deadline must be timezone-aware")
            if self.deadline <= datetime.now(timezone.utc):
                raise ContractViolation("deadline must be in the future")

@dataclass(frozen=True, slots=True)
class ProviderResult:
    correlation_id: str
    status: ResultStatus
    output: Mapping[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    def __post_init__(self) -> None:
        try:
            UUID(self.correlation_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ContractViolation("result correlation_id must be a UUID") from exc
        if not isinstance(self.status, ResultStatus):
            raise ContractViolation("status must be a ResultStatus")
        if not isinstance(self.output, Mapping):
            raise ContractViolation("output must be a mapping/object")
        try:
            encoded = json.dumps(dict(self.output), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ContractViolation("output must contain finite JSON-compatible values") from exc
        if len(encoded) > MAX_PAYLOAD_BYTES:
            raise ContractViolation(f"output exceeds {MAX_PAYLOAD_BYTES} bytes")
        if self.status is ResultStatus.FAILED and not self.error_code:
            raise ContractViolation("failed results require error_code")
