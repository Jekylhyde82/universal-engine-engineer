"""Explicit allowlist registry for integrated provider adapters."""
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol
from ..contracts import ContractViolation
from ..lifecycle import LifecycleState

class LifecycleStateReader(Protocol):
    def state_of(self, capability_id: str) -> LifecycleState: ...

class ProviderKind(StrEnum):
    WORKFLOW = "workflow"
    INFERENCE = "inference"
    KNOWLEDGE = "knowledge"
    VECTOR_STORE = "vector_store"
    EVALUATION = "evaluation"
    CODING_AGENT = "coding_agent"
    NETWORK = "network"

_REQUIRED_METHODS = {
    ProviderKind.WORKFLOW: ("execute", "run", "resume"),
    ProviderKind.INFERENCE: ("execute", "generate"),
    ProviderKind.KNOWLEDGE: ("execute", "ingest", "retrieve"),
    ProviderKind.VECTOR_STORE: ("execute", "upsert", "search"),
    ProviderKind.EVALUATION: ("execute", "evaluate"),
    ProviderKind.CODING_AGENT: ("execute", "propose_patch"),
    ProviderKind.NETWORK: ("execute", "connect", "disconnect", "status"),
}

@dataclass(frozen=True, slots=True)
class ProviderRegistration:
    provider_id: str
    capability_id: str
    kind: ProviderKind
    adapter: Any

class ProviderRegistry:
    """In-memory allowlist; adapters are registered explicitly, never auto-loaded."""
    def __init__(self) -> None:
        self._providers: dict[str, ProviderRegistration] = {}

    def register(self, provider_id: str, capability_id: str, kind: ProviderKind, adapter: Any, lifecycle: LifecycleStateReader) -> ProviderRegistration:
        if not isinstance(kind, ProviderKind):
            raise ContractViolation("kind must be a ProviderKind")
        if not provider_id or not provider_id.strip():
            raise ContractViolation("provider_id is required")
        if provider_id in self._providers:
            raise ContractViolation(f"provider already registered: {provider_id}")
        if lifecycle.state_of(capability_id) is not LifecycleState.INTEGRATED:
            raise ContractViolation("only lifecycle-integrated capabilities may be registered")
        missing = [name for name in _REQUIRED_METHODS[kind] if not callable(getattr(adapter, name, None))]
        if missing:
            raise ContractViolation(f"provider {provider_id} is missing required methods: {', '.join(missing)}")
        registration = ProviderRegistration(provider_id, capability_id, kind, adapter)
        self._providers[provider_id] = registration
        return registration

    def get(self, provider_id: str) -> ProviderRegistration:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise ContractViolation(f"provider is not registered: {provider_id}") from exc

    def list(self) -> tuple[ProviderRegistration, ...]:
        return tuple(self._providers.values())
