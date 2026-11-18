"""SQLite-backed lifecycle ledger with a tamper-evident event hash chain."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import threading
from typing import Iterator

from .contracts import ContractViolation
from .lifecycle import LifecycleState, transition


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    sequence: int
    capability_id: str
    from_state: str | None
    to_state: str
    occurred_at: str
    actor: str
    reason: str
    previous_hash: str
    event_hash: str


class SQLiteCapabilityLifecycle:
    """Durable local lifecycle ledger.

    The hash chain detects accidental or unsophisticated event edits, but a
    database administrator can rewrite the entire database. Production use
    still requires external anchoring, access controls and backup procedures.
    """

    def __init__(self, database_path: str) -> None:
        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path is required")
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(database_path, timeout=5.0, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        if database_path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                capability_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lifecycle_events (
                sequence INTEGER PRIMARY KEY,
                capability_id TEXT NOT NULL REFERENCES capabilities(capability_id),
                from_state TEXT,
                to_state TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                actor TEXT NOT NULL,
                reason TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                yield self._connection
            except Exception:
                self._connection.rollback()
                raise
            else:
                self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> "SQLiteCapabilityLifecycle":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def discover(self, capability_id: str, *, actor: str = "system", reason: str = "discovered") -> None:
        if not isinstance(capability_id, str) or not capability_id.strip():
            raise ContractViolation("capability_id is required")
        self._validate_actor_reason(actor, reason)
        with self._transaction() as connection:
            if connection.execute(
                "SELECT 1 FROM capabilities WHERE capability_id = ?", (capability_id,)
            ).fetchone():
                raise ContractViolation(f"capability already exists: {capability_id}")
            occurred_at = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "INSERT INTO capabilities(capability_id, state, created_at) VALUES (?, ?, ?)",
                (capability_id, LifecycleState.DISCOVERED.value, occurred_at),
            )
            self._append_event(
                connection, capability_id, None, LifecycleState.DISCOVERED,
                occurred_at, actor, reason,
            )

    def advance(
        self,
        capability_id: str,
        target: LifecycleState,
        *,
        actor: str = "system",
        reason: str = "state transition",
    ) -> LifecycleState:
        self._validate_actor_reason(actor, reason)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state FROM capabilities WHERE capability_id = ?", (capability_id,)
            ).fetchone()
            if row is None:
                raise ContractViolation(f"unknown capability: {capability_id}")
            current = LifecycleState(row["state"])
            updated = transition(current, target)
            occurred_at = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "UPDATE capabilities SET state = ? WHERE capability_id = ?",
                (updated.value, capability_id),
            )
            self._append_event(
                connection, capability_id, current, updated,
                occurred_at, actor, reason,
            )
            return updated

    def state_of(self, capability_id: str) -> LifecycleState:
        with self._lock:
            row = self._connection.execute(
                "SELECT state FROM capabilities WHERE capability_id = ?", (capability_id,)
            ).fetchone()
        if row is None:
            raise ContractViolation(f"unknown capability: {capability_id}")
        return LifecycleState(row["state"])

    def events(self) -> tuple[LifecycleEvent, ...]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM lifecycle_events ORDER BY sequence"
            ).fetchall()
        return tuple(LifecycleEvent(**dict(row)) for row in rows)

    def verify_chain(self) -> bool:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM lifecycle_events ORDER BY sequence"
            ).fetchall()
            capabilities = self._connection.execute(
                "SELECT capability_id, state FROM capabilities"
            ).fetchall()
        previous_hash = ""
        expected_states: dict[str, str] = {}
        for row in rows:
            event = dict(row)
            if event["previous_hash"] != previous_hash:
                return False
            if event["from_state"] != expected_states.get(event["capability_id"]):
                return False
            if event["from_state"] is None and event["to_state"] != LifecycleState.DISCOVERED.value:
                return False
            payload = {key: event[key] for key in (
                "sequence", "capability_id", "from_state", "to_state",
                "occurred_at", "actor", "reason", "previous_hash",
            )}
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            if digest != event["event_hash"]:
                return False
            previous_hash = digest
            expected_states[event["capability_id"]] = event["to_state"]
        return expected_states == {row["capability_id"]: row["state"] for row in capabilities}

    @staticmethod
    def _validate_actor_reason(actor: str, reason: str) -> None:
        if not isinstance(actor, str) or not actor.strip():
            raise ContractViolation("actor is required")
        if not isinstance(reason, str) or not reason.strip():
            raise ContractViolation("reason is required")

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        capability_id: str,
        from_state: LifecycleState | None,
        to_state: LifecycleState,
        occurred_at: str,
        actor: str,
        reason: str,
    ) -> None:
        previous = connection.execute(
            "SELECT event_hash FROM lifecycle_events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous["event_hash"] if previous else ""
        sequence = connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence FROM lifecycle_events"
        ).fetchone()["next_sequence"]
        payload = {
            "sequence": sequence,
            "capability_id": capability_id,
            "from_state": from_state.value if from_state else None,
            "to_state": to_state.value,
            "occurred_at": occurred_at,
            "actor": actor,
            "reason": reason,
            "previous_hash": previous_hash,
        }
        event_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        connection.execute(
            """
            INSERT INTO lifecycle_events(
                sequence, capability_id, from_state, to_state, occurred_at,
                actor, reason, previous_hash, event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sequence, capability_id, payload["from_state"], to_state.value,
                occurred_at, actor, reason, previous_hash, event_hash,
            ),
        )
