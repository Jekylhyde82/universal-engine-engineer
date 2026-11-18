"""Fail-closed capability lifecycle state machine."""
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
