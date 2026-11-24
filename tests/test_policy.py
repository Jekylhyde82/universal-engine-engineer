import unittest
from universal_engine.contracts import PolicyDecision
from universal_engine.policy import PolicyEngine, PolicyRule


class PolicyEngineTests(unittest.TestCase):
    def test_default_deny(self):
        decision = PolicyEngine().evaluate("user-1", "inference.llama", "generate")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_id, "default-deny")

    def test_exact_allow_rule(self):
        engine = PolicyEngine([PolicyRule("allow-1", "user-1", "inference.llama", "generate", True, "approved")])
        self.assertTrue(engine.evaluate("user-1", "inference.llama", "generate").allowed)

    def test_non_matching_principal_is_denied(self):
        engine = PolicyEngine([PolicyRule("allow-1", "user-1", "inference.llama", "generate", True, "approved")])
        self.assertFalse(engine.evaluate("user-2", "inference.llama", "generate").allowed)

    def test_explicit_deny_overrides_allow(self):
        engine = PolicyEngine([
            PolicyRule("allow-1", "user-1", "inference.llama", "generate", True, "approved"),
            PolicyRule("deny-1", "user-1", "inference.llama", "generate", False, "revoked"),
        ])
        decision = engine.evaluate("user-1", "inference.llama", "generate")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.policy_id, "deny-1")

    def test_rejects_duplicate_rule_ids(self):
        rule = PolicyRule("same", "user-1", "cap", "op", True, "allowed")
        with self.assertRaises(ValueError):
            PolicyEngine([rule, rule])


if __name__ == "__main__":
    unittest.main()
