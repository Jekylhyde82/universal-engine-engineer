"""Evidence-linked typed world-model assertion prototype.

This is a deliberately small graph projection: assertions refer to persisted
observations and retain epistemic state rather than silently becoming facts.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from .store import verify_ledger


@dataclass(frozen=True)
class WorldAssertion:
    assertion_id: str
    subject_id: str
    predicate: str
    object_value: Any
    epistemic_status: str
    evidence_record_id: str
    verification_ref: str | None


class WorldModel:
    def __init__(self, database: str | Path, evidence_database: str | Path):
        self.database = str(database)
        self.evidence_database = str(evidence_database)
        if not Path(self.evidence_database).is_file():
            raise FileNotFoundError("evidence_database must point to an existing VEF ledger")
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("""
                CREATE TABLE IF NOT EXISTS world_assertions (
                    assertion_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object_json TEXT NOT NULL,
                    epistemic_status TEXT NOT NULL CHECK (
                        epistemic_status IN ('observed','interpreted','inferred','verified')
                    ),
                    evidence_record_id TEXT NOT NULL,
                    verification_ref TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(subject_id, predicate, object_json, evidence_record_id)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS world_assertions_subject ON world_assertions(subject_id)")
            db.execute("CREATE INDEX IF NOT EXISTS world_assertions_evidence ON world_assertions(evidence_record_id)")

    def add_assertion(
        self, *, subject_id: str, predicate: str, object_value: Any,
        epistemic_status: str, evidence_record_id: str,
        verification_ref: str | None = None,
    ) -> WorldAssertion:
        if not subject_id.strip() or not predicate.strip() or not evidence_record_id.strip():
            raise ValueError("subject_id, predicate and evidence_record_id are required")
        if epistemic_status not in {"observed", "interpreted", "inferred", "verified"}:
            raise ValueError("invalid epistemic status")
        if epistemic_status == "verified" and not (verification_ref and verification_ref.strip()):
            raise ValueError("verified assertions require verification_ref")
        health = verify_ledger(self.evidence_database)
        if not health.valid:
            raise ValueError(f"evidence ledger failed integrity verification: {health.reason}")
        with sqlite3.connect(f"file:{Path(self.evidence_database).resolve().as_posix()}?mode=ro", uri=True) as evidence_db:
            exists = evidence_db.execute(
                "SELECT 1 FROM evidence_records WHERE record_id=?", (evidence_record_id,)
            ).fetchone()
        if not exists:
            raise ValueError("evidence_record_id does not exist in the verified VEF ledger")
        object_json = json.dumps(object_value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        assertion_id = str(uuid4())
        with sqlite3.connect(self.database) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("""
                INSERT INTO world_assertions (
                    assertion_id, subject_id, predicate, object_json,
                    epistemic_status, evidence_record_id, verification_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (assertion_id, subject_id, predicate, object_json,
                  epistemic_status, evidence_record_id, verification_ref))
        return WorldAssertion(assertion_id, subject_id, predicate, object_value,
                              epistemic_status, evidence_record_id, verification_ref)

    def list_assertions(self, subject_id: str | None = None) -> list[WorldAssertion]:
        with sqlite3.connect(self.database) as db:
            db.row_factory = sqlite3.Row
            if subject_id is None:
                rows = db.execute("SELECT * FROM world_assertions ORDER BY created_at, assertion_id").fetchall()
            else:
                rows = db.execute("SELECT * FROM world_assertions WHERE subject_id=? ORDER BY created_at, assertion_id", (subject_id,)).fetchall()
        return [WorldAssertion(
            row["assertion_id"], row["subject_id"], row["predicate"],
            json.loads(row["object_json"]), row["epistemic_status"],
            row["evidence_record_id"], row["verification_ref"],
        ) for row in rows]

    def evidence_health(self, evidence_database: str | Path) -> dict[str, Any]:
        result = verify_ledger(evidence_database)
        return {"valid": result.valid, "records_checked": result.records_checked,
                "failing_record_id": result.failing_record_id, "reason": result.reason}
