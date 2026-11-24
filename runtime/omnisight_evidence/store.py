"""Append-only, hash-linked SQLite evidence ledger.

This prototype stores observation metadata and content digests, not raw media.
It provides tamper-evidence for internal records, not proof of visual truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

GENESIS_HASH = "0" * 64
EPISTEMIC_STATES = {"observed", "interpreted", "inferred", "verified"}


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _utc_timestamp(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("captured_at must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class EvidenceRecord:
    record_id: str
    source_id: str
    captured_at: str
    media_type: str
    payload_sha256: str
    producer: str
    producer_version: str
    epistemic_status: str
    observation: dict[str, Any]
    limitations: tuple[str, ...]
    verification_ref: str | None
    previous_hash: str
    record_hash: str


@dataclass(frozen=True)
class LedgerVerification:
    valid: bool
    records_checked: int
    failing_record_id: str | None
    reason: str


class EvidenceStore:
    """SQLite ledger. Each append is atomic and hash-linked to its predecessor."""

    def __init__(self, database: str | Path):
        self.database = str(database)
        if self.database != ":memory:":
            Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS evidence_records (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    source_id TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    producer TEXT NOT NULL,
                    producer_version TEXT NOT NULL,
                    epistemic_status TEXT NOT NULL,
                    observation_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL,
                    verification_ref TEXT,
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE
                )
            """)
            connection.execute("""
                CREATE TRIGGER IF NOT EXISTS evidence_no_update
                BEFORE UPDATE ON evidence_records
                BEGIN SELECT RAISE(ABORT, 'evidence ledger is append-only'); END
            """)
            connection.execute("""
                CREATE TRIGGER IF NOT EXISTS evidence_no_delete
                BEFORE DELETE ON evidence_records
                BEGIN SELECT RAISE(ABORT, 'evidence ledger is append-only'); END
            """)

    def append(
        self, *, source_id: str, media_type: str, payload: bytes,
        producer: str, producer_version: str, epistemic_status: str,
        observation: dict[str, Any], limitations: tuple[str, ...] | list[str] = (),
        verification_ref: str | None = None, captured_at: str | None = None,
    ) -> EvidenceRecord:
        required = {
            "source_id": source_id, "media_type": media_type,
            "producer": producer, "producer_version": producer_version,
        }
        if any(not isinstance(v, str) or not v.strip() for v in required.values()):
            raise ValueError("source, media type, producer and version are required")
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        if epistemic_status not in EPISTEMIC_STATES:
            raise ValueError("unsupported epistemic_status")
        if not isinstance(observation, dict):
            raise TypeError("observation must be a JSON object")
        if epistemic_status == "verified" and not (verification_ref and verification_ref.strip()):
            raise ValueError("verified observations require verification_ref")

        timestamp = _utc_timestamp(captured_at)
        payload_digest = hashlib.sha256(payload).hexdigest()
        record_id = str(uuid4())
        observation_json = _canonical(observation).decode("utf-8")
        limitations_json = _canonical(list(limitations)).decode("utf-8")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT record_hash FROM evidence_records ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = row["record_hash"] if row else GENESIS_HASH
            body = {
                "record_id": record_id, "source_id": source_id,
                "captured_at": timestamp, "media_type": media_type,
                "payload_sha256": payload_digest, "producer": producer,
                "producer_version": producer_version,
                "epistemic_status": epistemic_status,
                "observation": json.loads(observation_json),
                "limitations": json.loads(limitations_json),
                "verification_ref": verification_ref,
                "previous_hash": previous_hash,
            }
            record_hash = hashlib.sha256(_canonical(body)).hexdigest()
            connection.execute("""
                INSERT INTO evidence_records (
                    record_id, source_id, captured_at, media_type, payload_sha256,
                    producer, producer_version, epistemic_status, observation_json,
                    limitations_json, verification_ref, previous_hash, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id, source_id, timestamp, media_type, payload_digest,
                producer, producer_version, epistemic_status, observation_json,
                limitations_json, verification_ref, previous_hash, record_hash,
            ))
            connection.commit()

        return EvidenceRecord(
            record_id, source_id, timestamp, media_type, payload_digest,
            producer, producer_version, epistemic_status, observation,
            tuple(limitations), verification_ref, previous_hash, record_hash,
        )

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM evidence_records").fetchone()[0])


def _record_body(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "record_id": row["record_id"],
        "source_id": row["source_id"],
        "captured_at": row["captured_at"],
        "media_type": row["media_type"],
        "payload_sha256": row["payload_sha256"],
        "producer": row["producer"],
        "producer_version": row["producer_version"],
        "epistemic_status": row["epistemic_status"],
        "observation": json.loads(row["observation_json"]),
        "limitations": json.loads(row["limitations_json"]),
        "verification_ref": row["verification_ref"],
        "previous_hash": row["previous_hash"],
    }


def verify_ledger(database: str | Path) -> LedgerVerification:
    """Read-only independent integrity pass over every stored record."""
    path = Path(database).resolve()
    if not path.exists():
        return LedgerVerification(False, 0, None, "ledger does not exist")
    uri = f"file:{path.as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM evidence_records ORDER BY sequence ASC"
        ).fetchall()
        previous = GENESIS_HASH
        for index, row in enumerate(rows, start=1):
            if row["previous_hash"] != previous:
                return LedgerVerification(False, index, row["record_id"], "previous-hash link mismatch")
            expected = hashlib.sha256(_canonical(_record_body(row))).hexdigest()
            if row["record_hash"] != expected:
                return LedgerVerification(False, index, row["record_id"], "record digest mismatch")
            previous = expected
        return LedgerVerification(True, len(rows), None, "all present records and hash links are valid")
    except (sqlite3.Error, ValueError, TypeError, json.JSONDecodeError) as error:
        return LedgerVerification(False, 0, None, f"ledger could not be verified: {error}")
    finally:
        try:
            connection.close()
        except (UnboundLocalError, sqlite3.Error):
            pass
