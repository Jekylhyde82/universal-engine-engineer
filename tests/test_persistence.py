import sqlite3
import tempfile
import unittest
from pathlib import Path

from universal_engine.contracts import ContractViolation
from universal_engine.lifecycle import LifecycleState
from universal_engine.persistence import SQLiteCapabilityLifecycle


class SQLiteLifecycleTests(unittest.TestCase):
    def test_persists_state_and_hash_chain_across_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "lifecycle.db")
            ledger = SQLiteCapabilityLifecycle(path)
            ledger.discover("cap.alpha", actor="test", reason="found")
            for state in (LifecycleState.PROPOSED, LifecycleState.UNDER_EVALUATION, LifecycleState.APPROVED, LifecycleState.INTEGRATED):
                ledger.advance("cap.alpha", state, actor="test", reason=f"advance to {state.value}")
            self.assertTrue(ledger.verify_chain())
            ledger.close()
            reopened = SQLiteCapabilityLifecycle(path)
            self.assertEqual(reopened.state_of("cap.alpha"), LifecycleState.INTEGRATED)
            self.assertTrue(reopened.verify_chain())
            self.assertEqual(len(reopened.events()), 5)
            reopened.close()

    def test_rejects_skipped_lifecycle_transition(self):
        with SQLiteCapabilityLifecycle(":memory:") as ledger:
            ledger.discover("cap.beta")
            with self.assertRaises(ContractViolation):
                ledger.advance("cap.beta", LifecycleState.INTEGRATED)
            self.assertEqual(ledger.state_of("cap.beta"), LifecycleState.DISCOVERED)
            self.assertTrue(ledger.verify_chain())

    def test_detects_event_tampering(self):
        with SQLiteCapabilityLifecycle(":memory:") as ledger:
            ledger.discover("cap.gamma")
            ledger.advance("cap.gamma", LifecycleState.PROPOSED)
            ledger._connection.execute(
                "UPDATE lifecycle_events SET reason = ? WHERE sequence = 1",
                ("tampered",),
            )
            self.assertFalse(ledger.verify_chain())

    def test_rejects_duplicate_capability(self):
        with SQLiteCapabilityLifecycle(":memory:") as ledger:
            ledger.discover("cap.delta")
            with self.assertRaises(ContractViolation):
                ledger.discover("cap.delta")

    def test_rejects_unknown_capability_lookup(self):
        with SQLiteCapabilityLifecycle(":memory:") as ledger:
            with self.assertRaises(ContractViolation):
                ledger.state_of("missing")


if __name__ == "__main__":
    unittest.main()
