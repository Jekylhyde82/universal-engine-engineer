"""Small, dependency-free contracts shared by provider adapters."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import json
import math
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

def _validate_json_value(value: Any, path: str = "payload") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractViolation(f"{path} contains a non-finite number")
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ContractViolation(f"{path} object keys must be strings")
            _validate_json_value(nested, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _validate_json_value(nested, f"{path}[{index}]")
        return
    raise ContractViolation(f"{path} contains a non-JSON value: {type(value).__name__}")

def _validate_object_size(value: Mapping[str, Any], label: str) -> None:
    _validate_json_value(value, label)
    try:
        encoded = json.dumps(dict(value), allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractViolation(f"{label} must be finite JSON-compatible data") from exc
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ContractViolation(f"{label} exceeds {MAX_PAYLOAD_BYTES} bytes")

@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    policy_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise ContractViolation("allowed must be a boolean")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ContractViolation("policy reason is required")
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise ContractViolation("policy_id is required")

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
        if not isinstance(self.capability_id, str) or not self.capability_id.strip():
            raise ContractViolation("capability_id is required")
        if not isinstance(self.operation, str) or not self.operation.strip():
            raise ContractViolation("operation is required")
        if not isinstance(self.policy, PolicyDecision):
            raise ContractViolation("policy must be a PolicyDecision")
        if not isinstance(self.payload, Mapping):
            raise ContractViolation("payload must be a mapping/object")
        _validate_object_size(self.payload, "payload")
        if self.deadline is not None:
            if not isinstance(self.deadline, datetime) or self.deadline.tzinfo is None or self.deadline.utcoffset() is None:
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
        _validate_object_size(self.output, "output")
        if self.status in (ResultStatus.FAILED, ResultStatus.DENIED, ResultStatus.TIMED_OUT):
            if not isinstance(self.error_code, str) or not self.error_code.strip():
                raise ContractViolation("non-success results require error_code")
        elif self.error_code is not None:
            raise ContractViolation("successful results must not include error_code")
        if self.error_message is not None and not isinstance(self.error_message, str):
            raise ContractViolation("error_message must be a string when supplied")
