"""Fail-closed capability lifecycle state machine and ledger."""
from enum import StrEnum
from .contracts import ContractViolation

class LifecycleState(StrEnum):
    DISCOVERED = "discovered"
    PROPOSED = "proposed"
    UNDER_EVALUATION = "under_evaluation"
    APPROVED = "approved"
    INTEGRATED = "integrated"
    REJECTED = "rejected"
    RETIRED = "retired"

_ALLOWED = {
    LifecycleState.DISCOVERED: {LifecycleState.PROPOSED, LifecycleState.REJECTED},
    LifecycleState.PROPOSED: {LifecycleState.UNDER_EVALUATION, LifecycleState.REJECTED},
    LifecycleState.UNDER_EVALUATION: {LifecycleState.APPROVED, LifecycleState.REJECTED},
    LifecycleState.APPROVED: {LifecycleState.INTEGRATED, LifecycleState.RETIRED},
    LifecycleState.INTEGRATED: {LifecycleState.RETIRED},
    LifecycleState.REJECTED: set(),
    LifecycleState.RETIRED: set(),
}

def transition(current: LifecycleState, target: LifecycleState) -> LifecycleState:
    """Return target only when explicitly permitted."""
    if target not in _ALLOWED[current]:
        raise ContractViolation(f"invalid lifecycle transition: {current} -> {target}")
    return target

class CapabilityLifecycle:
    """In-memory lifecycle ledger; callers advance state through validated transitions."""
    def __init__(self) -> None:
        self._states: dict[str, LifecycleState] = {}

    def discover(self, capability_id: str) -> None:
        if not capability_id or not capability_id.strip():
            raise ContractViolation("capability_id is required")
        if capability_id in self._states:
            raise ContractViolation(f"capability already exists: {capability_id}")
        self._states[capability_id] = LifecycleState.DISCOVERED

    def advance(self, capability_id: str, target: LifecycleState) -> LifecycleState:
        current = self.state_of(capability_id)
        updated = transition(current, target)
        self._states[capability_id] = updated
        return updated

    def state_of(self, capability_id: str) -> LifecycleState:
        try:
            return self._states[capability_id]
        except KeyError as exc:
            raise ContractViolation(f"unknown capability: {capability_id}") from exc
