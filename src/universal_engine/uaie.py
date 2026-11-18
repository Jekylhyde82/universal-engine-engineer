"""UAIE: local-first universal acquisition, understanding and assimilation prototype.

This module stores source material and provenance without executing acquired content.
It is intentionally conservative: discovery/assimilation are automatic; integration
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
class AssimilationRecord:
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
    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml"}:
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


class UniversalAssimilationEngine:
    """Persistent intake and assessment store. Acquired material is never executed."""

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
            db.execute("CREATE INDEX IF NOT EXISTS idx_uaie_source ON assimilations(source)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_uaie_state ON assimilations(state)")

    def ingest_bytes(self, content: bytes, source: str, media_type: str | None = None) -> AssimilationRecord:
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
            existing = db.execute("SELECT * FROM assimilations WHERE content_hash=?", (digest,)).fetchone()
            if existing:
                return self._row_to_record(existing, duplicate=True)
            db.execute("""INSERT INTO assimilations
                (record_id,content_hash,source,media_type,category,byte_size,content,
                 extracted_text,value_score,signals_json,state,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (record_id,digest,source,guessed,category,len(content),content,text,
                 score,json.dumps(signals),state,now))
            row = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
        return self._row_to_record(row)

    def ingest_text(self, text: str, source: str = "inline://user-input") -> AssimilationRecord:
        if not isinstance(text, str):
            raise UAIEError("text must be a string")
        return self.ingest_bytes(text.encode("utf-8"), source, "text/plain; charset=utf-8")

    def ingest_object(self, value: Any, source: str = "inline://structured-object") -> AssimilationRecord:
        try:
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                                 allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise UAIEError("object must be finite JSON-serializable data") from exc
        return self.ingest_bytes(encoded, source, "application/json")

    def ingest_path(self, path: str | os.PathLike[str], recursive: bool = True) -> list[AssimilationRecord]:
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
        records: list[AssimilationRecord] = []
        for item in paths:
            size = item.stat().st_size
            if size > self.max_bytes:
                raise UAIEError(f"{item} exceeds configured {self.max_bytes}-byte limit")
            records.append(self.ingest_bytes(item.read_bytes(), str(item.resolve())))
        return records

    @staticmethod
    def _row_to_record(row: sqlite3.Row, duplicate: bool = False) -> AssimilationRecord:
        return AssimilationRecord(
            record_id=row["record_id"], content_hash=row["content_hash"],
            source=row["source"], media_type=row["media_type"], category=row["category"],
            byte_size=row["byte_size"], value_score=row["value_score"],
            signals=tuple(json.loads(row["signals_json"])), state=row["state"],
            created_at=row["created_at"], duplicate=duplicate)

    def get(self, record_id: str) -> AssimilationRecord:
        with self._connect() as db:
            row = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
        if row is None:
            raise UAIEError(f"unknown record: {record_id}")
        return self._row_to_record(row)

    def search(self, query: str, limit: int = 20) -> list[AssimilationRecord]:
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

    def set_state(self, record_id: str, state: str) -> AssimilationRecord:
        allowed = {"approved", "integrated", "rejected"}
        if state not in allowed:
            raise UAIEError(f"state must be one of: {', '.join(sorted(allowed))}")
        current = self.get(record_id)
        transitions = {
            "discovered": {"approved", "rejected"},
            "assimilated": {"approved", "rejected"},
            "approved": {"integrated", "rejected"},
            "integrated": set(),
            "rejected": set(),
        }
        if state not in transitions[current.state]:
            raise UAIEError(f"invalid transition: {current.state} -> {state}")
        with self._connect() as db:
            db.execute("UPDATE assimilations SET state=? WHERE record_id=?", (state, record_id))
            row = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
        return self._row_to_record(row)

    def export_record(self, record_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM assimilations WHERE record_id=?", (record_id,)).fetchone()
        if row is None:
            raise UAIEError(f"unknown record: {record_id}")
        result = asdict(self._row_to_record(row))
        result["content"] = bytes(row["content"]).decode("utf-8", errors="replace")
        result["extracted_text"] = row["extracted_text"]
        return result


def _print(record: AssimilationRecord) -> None:
    print(json.dumps(asdict(record), indent=2))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uaie", description="Universal Assimilation and Integration Engine prototype")
    parser.add_argument("--db", default="uaie.sqlite3", help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="assimilate a file or directory without executing it")
    ingest.add_argument("path")
    ingest.add_argument("--shallow", action="store_true", help="do not recurse into directories")
    search = sub.add_parser("search", help="search assimilated records")
    search.add_argument("query")
    show = sub.add_parser("show", help="show record metadata and extracted content")
    show.add_argument("record_id")
    state = sub.add_parser("state", help="approve, integrate, or reject a record")
    state.add_argument("record_id")
    state.add_argument("new_state", choices=("approved", "integrated", "rejected"))
    args = parser.parse_args(argv)
    engine = UniversalAssimilationEngine(args.db)
    try:
        if args.command == "ingest":
            records = engine.ingest_path(args.path, recursive=not args.shallow)
            for record in records:
                _print(record)
            print(f"Assimilated {len(records)} file(s).", file=sys.stderr)
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
