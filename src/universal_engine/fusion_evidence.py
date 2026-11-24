"""SQLite-backed hash-chained evidence for AFI PRIME specialist outcomes.

Only identifiers, statuses, timing and SHA-256 digests are persisted. Raw prompts,
payloads and provider outputs are deliberately excluded from this ledger.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import sqlite3
import threading

from .contracts import ContractViolation
from .fusion import FUSION_FUNCTION_ID, FusionResult


_HEX_256 = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class FusionEvidenceEvent:
    sequence: int
    fusion_id: str
    fusion_function_id: str
    principal_id: str
    provider_id: str
    capability_id: str
    correlation_id: str
    status: str
    elapsed_ms: float
    occurred_at: str
    request_sha256: str
    result_sha256: str
    previous_hash: str
    event_hash: str


class SQLiteFusionEvidenceLedger:
    """Local append-only fusion evidence ledger with a tamper-evident hash chain.

    A privileged database owner can rewrite the entire database and recompute the
    chain. Production use requires external anchoring, access controls and backups.
    """

    def __init__(self, database_path: str) -> None:
        if not isinstance(database_path, str) or not database_path.strip():
            raise ValueError("database_path is required")
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(database_path, timeout=5.0, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA busy_timeout = 5000")
        if database_path != ":memory:":
            self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS fusion_evidence_events (
                sequence INTEGER PRIMARY KEY,
                fusion_id TEXT NOT NULL,
                fusion_function_id TEXT NOT NULL,
                principal_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                capability_id TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                status TEXT NOT NULL,
                elapsed_ms REAL NOT NULL,
                occurred_at TEXT NOT NULL,
                request_sha256 TEXT NOT NULL,
                result_sha256 TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                UNIQUE(fusion_id, correlation_id)
            )
            """
        )
        self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> "SQLiteFusionEvidenceLedger":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def record(self, result: FusionResult) -> tuple[FusionEvidenceEvent, ...]:
        """Atomically append one digest-only event for every specialist outcome."""
        if not isinstance(result, FusionResult):
            raise ContractViolation("result must be a FusionResult")
        if result.fusion_function_id != FUSION_FUNCTION_ID:
            raise ContractViolation("fusion function identity mismatch")
        if not result.fusion_id or not result.principal_id or not result.outcomes:
            raise ContractViolation("fusion result identity and specialist outcomes are required")
        if result.created_at.tzinfo is None or result.created_at.utcoffset() is None:
            raise ContractViolation("fusion result created_at must be timezone-aware")
        correlations = [outcome.correlation_id for outcome in result.outcomes]
        if len(correlations) != len(set(correlations)):
            raise ContractViolation("fusion outcome correlation IDs must be unique")

        for outcome in result.outcomes:
            if not isinstance(outcome.elapsed_ms, (int, float)) or isinstance(outcome.elapsed_ms, bool):
                raise ContractViolation("elapsed_ms must be a finite non-negative number")
            if not math.isfinite(outcome.elapsed_ms) or outcome.elapsed_ms < 0:
                raise ContractViolation("elapsed_ms must be a finite non-negative number")
            if not _HEX_256.fullmatch(outcome.request_sha256):
                raise ContractViolation("request_sha256 must be a lowercase SHA-256 digest")
            if not _HEX_256.fullmatch(outcome.result_sha256):
                raise ContractViolation("result_sha256 must be a lowercase SHA-256 digest")
            if outcome.result.correlation_id != outcome.correlation_id:
                raise ContractViolation("outcome correlation ID does not match provider result")

        occurred_at = result.created_at.astimezone(timezone.utc).isoformat()
        appended: list[FusionEvidenceEvent] = []
        with self._lock:
            connection = self._connection
            connection.execute("BEGIN IMMEDIATE")
            try:
                latest = connection.execute(
                    "SELECT sequence, event_hash FROM fusion_evidence_events ORDER BY sequence DESC LIMIT 1"
                ).fetchone()
                sequence = (latest["sequence"] + 1) if latest else 1
                previous_hash = latest["event_hash"] if latest else ""
                for outcome in result.outcomes:
                    payload = {
                        "sequence": sequence,
                        "fusion_id": result.fusion_id,
                        "fusion_function_id": result.fusion_function_id,
                        "principal_id": result.principal_id,
                        "provider_id": outcome.provider_id,
                        "capability_id": outcome.capability_id,
                        "correlation_id": outcome.correlation_id,
                        "status": outcome.result.status.value,
                        "elapsed_ms": outcome.elapsed_ms,
                        "occurred_at": occurred_at,
                        "request_sha256": outcome.request_sha256,
                        "result_sha256": outcome.result_sha256,
                        "previous_hash": previous_hash,
                    }
                    event_hash = hashlib.sha256(
                        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
                    ).hexdigest()
                    connection.execute(
                        """
                        INSERT INTO fusion_evidence_events(
                            sequence, fusion_id, fusion_function_id, principal_id,
                            provider_id, capability_id, correlation_id, status,
                            elapsed_ms, occurred_at, request_sha256, result_sha256,
                            previous_hash, event_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sequence, result.fusion_id, result.fusion_function_id, result.principal_id,
                            outcome.provider_id, outcome.capability_id, outcome.correlation_id,
                            outcome.result.status.value, outcome.elapsed_ms, occurred_at,
                            outcome.request_sha256, outcome.result_sha256, previous_hash, event_hash,
                        ),
                    )
                    appended.append(FusionEvidenceEvent(**payload, event_hash=event_hash))
                    previous_hash = event_hash
                    sequence += 1
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise ContractViolation("duplicate or conflicting fusion evidence event") from exc
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()
        return tuple(appended)

    def events(self, fusion_id: str | None = None) -> tuple[FusionEvidenceEvent, ...]:
        with self._lock:
            if fusion_id is None:
                rows = self._connection.execute(
                    "SELECT * FROM fusion_evidence_events ORDER BY sequence"
                ).fetchall()
            else:
                rows = self._connection.execute(
                    "SELECT * FROM fusion_evidence_events WHERE fusion_id = ? ORDER BY sequence",
                    (fusion_id,),
                ).fetchall()
        return tuple(FusionEvidenceEvent(**dict(row)) for row in rows)

    def verify_chain(self) -> bool:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM fusion_evidence_events ORDER BY sequence"
            ).fetchall()
        previous_hash = ""
        expected_sequence = 1
        for row in rows:
            event = dict(row)
            if event["sequence"] != expected_sequence or event["previous_hash"] != previous_hash:
                return False
            payload = {key: event[key] for key in (
                "sequence", "fusion_id", "fusion_function_id", "principal_id",
                "provider_id", "capability_id", "correlation_id", "status",
                "elapsed_ms", "occurred_at", "request_sha256", "result_sha256",
                "previous_hash",
            )}
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
            ).hexdigest()
            if digest != event["event_hash"]:
                return False
            previous_hash = digest
            expected_sequence += 1
        return True
