"""UAIE: local-first Universal Acquisition and Integration Engine prototype.

This module stores source material and provenance without executing acquired content.
It is intentionally conservative: discovery/acquisition intake is automatic; integration
and execution remain explicit, separately governed operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_MAX_BYTES = 10 * 1024 * 1024
TEXT_MIME_PREFIXES = ("text/",)
TEXT_SUFFIXES = {".md", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".xml", ".html", ".css", ".sql", ".sh", ".ps1", ".txt", ".log"}
VALUE_SIGNALS = {
    "capability": ("capability", "feature", "function", "ability", "tool", "engine"),
    "knowledge": ("knowledge", "research", "paper", "documentation", "guide", "tutorial"),
    "security": ("security", "privacy", "authentication", "authorization", "encryption", "threat"),
    "integration": ("api", "integration", "connector", "plugin", "adapter", "protocol"),
    "automation": ("automation", "workflow", "agent", "orchestration", "pipeline"),
    "quality": ("test", "verification", "validation", "benchmark", "reliability"),
}


class UAIEError(ValueError):
    """Raised when an acquisition request violates UAIE safety or size limits."""


@dataclass(frozen=True, slots=True)
class CapabilityAssessment:
    record_id: str
    original_idea_value: str
    market_value: str
    revenue_models: tuple[str, ...]
    development_timeline: str
    risk_assessment: str
    evidence: tuple[str, ...]
    verification_status: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class AcquisitionRecord:
    record_id: str
    content_hash: str
    source: str
    media_type: str
    category: str
    byte_size: int
    value_score: int
    signals: tuple[str, ...]
    state: str
    created_at: str
    duplicate: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _classify(source: str, media_type: str, text: str | None) -> str:
    suffix = Path(source).suffix.lower()
    if text is None:
        return "binary_or_unparsed"
    if suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".ps1", ".sql"}:
        return "source_code"
    if "json" in media_type or suffix in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml"}:
        return "structured_data"
    if suffix in {".md", ".rst"}:
        return "documentation"
    if suffix == ".csv":
        return "tabular_data"
    return "text"


def _assess(text: str | None) -> tuple[int, tuple[str, ...]]:
    if not text:
        return 0, ()
    lowered = text.casefold()
    found = tuple(sorted(name for name, words in VALUE_SIGNALS.items()
                         if any(word in lowered for word in words)))
    # This is a transparent triage heuristic, not an intelligence/value verdict.
    score = min(100, len(found) * 15 + (10 if len(text) >= 500 else 0))
    return score, found


class UniversalAcquisitionEngine:
    """Persistent acquisition and assessment store. Acquired material is never executed."""

    def __init__(self, database: str | os.PathLike[str] = "uaie.sqlite3",
                 max_bytes: int = DEFAULT_MAX_BYTES):
        if max_bytes < 1:
            raise UAIEError("max_bytes must be positive")
        self.database = str(database)
        self.max_bytes = max_bytes
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS assimilations (
                record_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL UNIQUE,
                source TEXT NOT NULL,
                media_type TEXT NOT NULL,
                category TEXT NOT NULL,
                byte_size INTEGER NOT NULL,
                content BLOB NOT NULL,
                extracted_text TEXT,
                value_score INTEGER NOT NULL,
                signals_json TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN
                  ('discovered','assimilated','approved','integrated','rejected')),
                created_at TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS audit_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS acquisition_sources (
                record_id TEXT NOT NULL,
                source TEXT NOT NULL,
                media_type TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                PRIMARY KEY(record_id, source, media_type)
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS capability_assessments (
                record_id TEXT PRIMARY KEY,
                original_idea_value TEXT NOT NULL,
                market_value TEXT NOT NULL,
                revenue_models_json TEXT NOT NULL,
                development_timeline TEXT NOT NULL,
                risk_assessment TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                verification_status TEXT NOT NULL CHECK(verification_status IN
                  ('not_assessed','under_review','verified','failed')),
                updated_at TEXT NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_uaie_source ON assimilations(source)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_uaie_state ON assimilations(state)")

    def ingest_bytes(self, content: bytes, source: str, media_type: str | None = None) -> AcquisitionRecord:
        if not isinstance(content, bytes):
            raise UAIEError("content must be bytes")
        if len(content) > self.max_bytes:
            raise UAIEError(f"source exceeds configured {self.max_bytes}-byte limit")
        if not isinstance(source, str) or not source.strip():
            raise UAIEError("source/provenance is required")
        digest = hashlib.sha256(content).hexdigest()
        guessed = media_type or mimetypes.guess_type(source)[0] or "application/octet-stream"
        text: str | None
        try:
            text = content.decode("utf-8-sig")
            if "\x00" in text:
                text = None
        except UnicodeDecodeError:
            text = None
        category = _classify(source, guessed, text)
        score, signals = _assess(text)
        record_id = "uaie_" + digest[:20]
        now = _now()
        state = "assimilated" if text is not None else "discovered"
        with self._connect() as db:
            cursor = db.execute("""INSERT OR IGNORE INTO assimilations
                (record_id,content_hash,source,media_type,category,byte_size,content,
                 extracted_text,value_score,signals_json,state,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (record_id,digest,source,guessed,category,len(content),content,text,
                 score,json.dumps(signals),state,now))
            row = db.execute("SELECT * FROM assimilations WHERE content_hash=?", (digest,)).fetchone()
            db.execute("""INSERT OR IGNORE INTO acquisition_sources
                (record_id,source,media_type,observed_at) VALUES (?,?,?,?)""",
                (row["record_id"], source, guessed, now))
            self._append_audit_event(db,
                "acquired" if cursor.rowcount else "duplicate_source_observed",
                row["record_id"], {"content_hash": digest, "source": source,
                                   "media_type": guessed, "state": row["state"]})
        # INSERT OR IGNORE makes concurrent duplicate intake idempotent under SQLite's
        # unique constraint instead of leaking an IntegrityError to the caller.
        return self._row_to_record(row, duplicate=cursor.rowcount == 0)

    def ingest_text(self, text: str, source: str = "inline://user-input") -> AcquisitionRecord:
        if not isinstance(text, str):
            raise UAIEError("text must be a string")
        return self.ingest_bytes(text.encode("utf-8"), source, "text/plain; charset=utf-8")

    def ingest_object(self, value: Any, source: str = "inline://structured-object") -> AcquisitionRecord:
        try:
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                                 allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise UAIEError("object must be finite JSON-serializable data") from exc
        return self.ingest_bytes(encoded, source, "application/json")

    def ingest_path(self, path: str | os.PathLike[str], recursive: bool = True) -> list[AcquisitionRecord]:
        root = Path(path).expanduser()
        if root.is_symlink():
            raise UAIEError("symbolic links are not followed")
        if not root.exists():
            raise UAIEError(f"path does not exist: {root}")
        paths = [root] if root.is_file() else sorted(
            p for p in root.rglob("*") if p.is_file() and not p.is_symlink()
        ) if recursive and root.is_dir() else []
        if root.is_dir() and not recursive:
            paths = sorted(p for p in root.iterdir() if p.is_file() and not p.is_symlink())
        records: list[AcquisitionRecord] = []
        for item in paths:
            size = item.stat().st_size
            if size > self.max_bytes:
                raise UAIEError(f"{item} exceeds configured {self.max_bytes}-byte limit")
            records.append(self.ingest_bytes(item.read_bytes(), str(item.resolve())))
        return records

    @staticmethod
    def _row_to_record(row: sqlite3.Row, duplicate: bool = False) -> AcquisitionRecord:
        return AcquisitionRecord(
            record_id=row["record_id"], content_hash=row["content_hash"],
            source=row["source"], media_type=row["media_type"], category=row["category"],
            byte_size=row["byte_size"], value_score=row["value_score"],
            signals=tuple(json.loads(row["signals_json"])), state=row["state"],
            created_at=row["created_at"], duplicate=duplicate)

    @staticmethod
    def _append_audit_event(db: sqlite3.Connection, event_type: str,
                            record_id: str, payload: dict[str, Any],
                            actor: str = "local-unverified") -> None:
        previous = db.execute(
            "SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous["event_hash"] if previous else "0" * 64
        sequence = db.execute(
            "SELECT COALESCE((SELECT seq FROM sqlite_sequence WHERE name='audit_events'), 0) + 1"
        ).fetchone()[0]
        created_at = _now()
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":"), allow_nan=False)
        material = json.dumps({
            "sequence": sequence, "event_type": event_type, "record_id": record_id,
            "actor": actor, "payload": payload_json, "previous_hash": previous_hash,
            "created_at": created_at,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        event_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
        db.execute("""INSERT INTO audit_events
            (sequence,event_type,record_id,actor,payload_json,previous_hash,event_hash,created_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (sequence,event_type,record_id,actor,payload_json,previous_hash,event_hash,created_at))

    def verify_audit_chain(self) -> dict[str, Any]:
        """Verify the local append-only hash chain; this is not external tamper-proofing."""
        with self._connect() as db:
            rows = db.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        previous_hash = "0" * 64
        for expected_sequence, row in enumerate(rows, start=1):
            if row["sequence"] != expected_sequence or row["previous_hash"] != previous_hash:
                return {"valid": False, "event_count": len(rows),
                        "failure_sequence": row["sequence"], "final_hash": previous_hash}
            material = json.dumps({
                "sequence": row["sequence"], "event_type": row["event_type"],
                "record_id": row["record_id"], "actor": row["actor"],
                "payload": row["payload_json"], "previous_hash": row["previous_hash"],
                "created_at": row["created_at"],
            }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            expected_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
            if row["event_hash"] != expected_hash:
                return {"valid": False, "event_count": len(rows),
                        "failure_sequence": row["sequence"], "final_hash": previous_hash}
            previous_hash = row["event_hash"]
        return {"valid": True, "event_count": len(rows), "failure_sequence": None,
                "final_hash": previous_hash}

    def get_sources(self, record_id: str) -> list[dict[str, str]]:
        """Return every observed source for a content record, not only its first source."""
        with self._connect() as db:
            if db.execute("SELECT 1 FROM assimilations WHERE record_id=?", (record_id,)).fetchone() is None:
                raise UAIEError(f"unknown record: {record_id}")
            rows = db.execute("""SELECT source,media_type,observed_at
                FROM acquisition_sources WHERE record_id=? ORDER BY observed_at,source""",
                (record_id,)).fetchall()
        return [dict(row) for row in rows]

    def get(self, record_id: str) -> AcquisitionRecord:
        with self._connect() as db:
            row = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
        if row is None:
            raise UAIEError(f"unknown record: {record_id}")
        return self._row_to_record(row)

    def search(self, query: str, limit: int = 20) -> list[AcquisitionRecord]:
        if not query.strip():
            raise UAIEError("search query is required")
        if not 1 <= limit <= 100:
            raise UAIEError("limit must be between 1 and 100")
        needle = "%" + query.casefold() + "%"
        with self._connect() as db:
            rows = db.execute("""SELECT * FROM assimilations
                WHERE lower(source) LIKE ? OR lower(coalesce(extracted_text,'')) LIKE ?
                   OR lower(category) LIKE ? OR lower(signals_json) LIKE ?
                ORDER BY value_score DESC, created_at DESC LIMIT ?""",
                (needle, needle, needle, needle, limit)).fetchall()
        return [self._row_to_record(row) for row in rows]

    def set_state(self, record_id: str, state: str) -> AcquisitionRecord:
        allowed = {"approved", "integrated", "rejected"}
        if state not in allowed:
            raise UAIEError(f"state must be one of: {', '.join(sorted(allowed))}")
        transitions = {
            "discovered": {"approved", "rejected"},
            "assimilated": {"approved", "rejected"},
            "approved": {"integrated", "rejected"},
            "integrated": set(),
            "rejected": set(),
        }
        with self._connect() as db:
            # Serialize read/validate/write so concurrent callers cannot race a
            # lifecycle transition or bypass the approval-before-integration rule.
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
            if row is None:
                raise UAIEError(f"unknown record: {record_id}")
            current_state = row["state"]
            if state not in transitions[current_state]:
                raise UAIEError(f"invalid transition: {current_state} -> {state}")
            db.execute("UPDATE assimilations SET state=? WHERE record_id=?", (state, record_id))
            self._append_audit_event(db, "lifecycle_transition", record_id,
                                     {"from": current_state, "to": state})
            updated = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
        return self._row_to_record(updated)

    def record_capability_assessment(
        self, record_id: str, *, original_idea_value: str, market_value: str,
        revenue_models: list[str] | tuple[str, ...], development_timeline: str,
        risk_assessment: str, evidence: list[str] | tuple[str, ...],
        verification_status: str = "not_assessed",
    ) -> CapabilityAssessment:
        """Persist mandatory portfolio fields without inventing missing evidence."""
        required = {
            "original_idea_value": original_idea_value,
            "market_value": market_value,
            "development_timeline": development_timeline,
            "risk_assessment": risk_assessment,
        }
        for name, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise UAIEError(f"{name} is mandatory and must be non-empty")
        if verification_status not in {"not_assessed", "under_review", "verified", "failed"}:
            raise UAIEError("invalid verification_status")
        if not isinstance(revenue_models, (list, tuple)) or not all(
            isinstance(item, str) and item.strip() for item in revenue_models
        ):
            raise UAIEError("revenue_models must contain non-empty strings")
        if not isinstance(evidence, (list, tuple)) or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            raise UAIEError("evidence must contain non-empty source references")
        now = _now()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM assimilations WHERE record_id=?", (record_id,)).fetchone() is None:
                raise UAIEError(f"unknown record: {record_id}")
            existing = db.execute(
                "SELECT original_idea_value FROM capability_assessments WHERE record_id=?",
                (record_id,)).fetchone()
            if existing is not None and existing["original_idea_value"] != original_idea_value:
                raise UAIEError("Original Idea Value is immutable; create a new candidate/version to preserve the change.")
            db.execute("""INSERT INTO capability_assessments
                (record_id,original_idea_value,market_value,revenue_models_json,
                 development_timeline,risk_assessment,evidence_json,verification_status,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(record_id) DO UPDATE SET
                 market_value=excluded.market_value,
                 revenue_models_json=excluded.revenue_models_json,
                 development_timeline=excluded.development_timeline,
                 risk_assessment=excluded.risk_assessment,
                 evidence_json=excluded.evidence_json,
                 verification_status=excluded.verification_status,
                 updated_at=excluded.updated_at""",
                (record_id, original_idea_value, market_value,
                 json.dumps(list(revenue_models), ensure_ascii=False),
                 development_timeline, risk_assessment,
                 json.dumps(list(evidence), ensure_ascii=False), verification_status, now))
            self._append_audit_event(db, "capability_assessment_updated", record_id,
                {"verification_status": verification_status, "evidence_count": len(evidence)})
        return self.get_capability_assessment(record_id)

    def get_capability_assessment(self, record_id: str) -> CapabilityAssessment:
        with self._connect() as db:
            row = db.execute("SELECT * FROM capability_assessments WHERE record_id=?",
                             (record_id,)).fetchone()
        if row is None:
            raise UAIEError(f"no capability assessment for record: {record_id}")
        return CapabilityAssessment(
            record_id=row["record_id"],
            original_idea_value=row["original_idea_value"],
            market_value=row["market_value"],
            revenue_models=tuple(json.loads(row["revenue_models_json"])),
            development_timeline=row["development_timeline"],
            risk_assessment=row["risk_assessment"],
            evidence=tuple(json.loads(row["evidence_json"])),
            verification_status=row["verification_status"],
            updated_at=row["updated_at"],
        )

    def export_record(self, record_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
        if row is None:
            raise UAIEError(f"unknown record: {record_id}")
        result = asdict(self._row_to_record(row))
        result["content"] = bytes(row["content"]).decode("utf-8", errors="replace")
        result["extracted_text"] = row["extracted_text"]
        return result


# Backwards-compatible aliases for existing prototype callers and stored records.
UniversalAssimilationEngine = UniversalAcquisitionEngine
AssimilationRecord = AcquisitionRecord


def _print(record: AcquisitionRecord) -> None:
    print(json.dumps(asdict(record), indent=2))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uaie", description="Universal Acquisition and Integration Engine prototype")
    parser.add_argument("--db", default="uaie.sqlite3", help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="acquire a file or directory without executing it")
    ingest.add_argument("path")
    ingest.add_argument("--shallow", action="store_true", help="do not recurse into directories")
    search = sub.add_parser("search", help="search acquired records")
    search.add_argument("query")
    show = sub.add_parser("show", help="show record metadata and extracted content")
    show.add_argument("record_id")
    state = sub.add_parser("state", help="approve, integrate, or reject a record")
    state.add_argument("record_id")
    state.add_argument("new_state", choices=("approved", "integrated", "rejected"))
    args = parser.parse_args(argv)
    engine = UniversalAcquisitionEngine(args.db)
    try:
        if args.command == "ingest":
            records = engine.ingest_path(args.path, recursive=not args.shallow)
            for record in records:
                _print(record)
            print(f"Acquired {len(records)} file(s).", file=sys.stderr)
        elif args.command == "search":
            for record in engine.search(args.query):
                _print(record)
        elif args.command == "show":
            print(json.dumps(engine.export_record(args.record_id), indent=2, ensure_ascii=False))
        elif args.command == "state":
            _print(engine.set_state(args.record_id, args.new_state))
        return 0
    except (UAIEError, OSError) as exc:
        print(f"UAIE error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
