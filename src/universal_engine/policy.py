"""Deny-by-default in-process policy evaluation."""
from dataclasses import dataclass
from typing import Iterable

from .contracts import ContractViolation, PolicyDecision


@dataclass(frozen=True, slots=True)
class PolicyRule:
    rule_id: str
    principal_id: str
    capability_id: str
    operation: str
    allowed: bool
    reason: str

    def __post_init__(self) -> None:
        for label, value in (
            ("rule_id", self.rule_id),
            ("principal_id", self.principal_id),
            ("capability_id", self.capability_id),
            ("operation", self.operation),
            ("reason", self.reason),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractViolation(f"{label} is required")
        if not isinstance(self.allowed, bool):
            raise ContractViolation("allowed must be a boolean")


class PolicyEngine:
    """Exact-match policy evaluator. No matching allow rule means deny.

    principal_id must come from a separately authenticated identity layer.
    This class is an in-process authorization primitive, not authentication.
    """

    def __init__(self, rules: Iterable[PolicyRule] = ()) -> None:
        self._rules = tuple(rules)
        ids = [rule.rule_id for rule in self._rules]
        if len(ids) != len(set(ids)):
            raise ContractViolation("policy rule IDs must be unique")

    def evaluate(self, principal_id: str, capability_id: str, operation: str) -> PolicyDecision:
        for label, value in (
            ("principal_id", principal_id),
            ("capability_id", capability_id),
            ("operation", operation),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractViolation(f"{label} is required")
        matches = [
            rule for rule in self._rules
            if rule.principal_id == principal_id
            and rule.capability_id == capability_id
            and rule.operation == operation
        ]
        denies = [rule for rule in matches if not rule.allowed]
        if denies:
            rule = denies[0]
            return PolicyDecision(False, rule.reason, rule.rule_id)
        allows = [rule for rule in matches if rule.allowed]
        if allows:
            rule = allows[0]
            return PolicyDecision(True, rule.reason, rule.rule_id)
        return PolicyDecision(False, "No matching allow rule", "default-deny")
