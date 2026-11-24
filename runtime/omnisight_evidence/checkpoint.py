"""Externally retained VEF checkpoints for detecting valid-tail truncation.

The checkpoint file must be stored in a separately controlled location. This
module does not authenticate that storage or sign checkpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .store import GENESIS_HASH, verify_ledger


@dataclass(frozen=True)
class CheckpointVerification:
    valid: bool
    sequence: int
    reason: str


def create_checkpoint(database: str | Path, destination: str | Path) -> dict:
    health = verify_ledger(database)
    if not health.valid:
        raise ValueError(f"cannot checkpoint invalid ledger: {health.reason}")
    uri = f"file:{Path(database).resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        row = db.execute(
            "SELECT sequence, record_hash FROM evidence_records ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
    checkpoint = {
        "format": "omnisight-vef-checkpoint-v1",
        "sequence": int(row[0]) if row else 0,
        "record_hash": row[1] if row else GENESIS_HASH,
    }
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(checkpoint, stream, sort_keys=True, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return checkpoint


def verify_checkpoint(database: str | Path, checkpoint_path: str | Path) -> CheckpointVerification:
    try:
        checkpoint = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
        if set(checkpoint) != {"format", "sequence", "record_hash"}:
            return CheckpointVerification(False, 0, "invalid checkpoint fields")
        if checkpoint["format"] != "omnisight-vef-checkpoint-v1":
            return CheckpointVerification(False, 0, "unsupported checkpoint format")
        sequence = checkpoint["sequence"]
        digest = checkpoint["record_hash"]
        if not isinstance(sequence, int) or sequence < 0 or not isinstance(digest, str):
            return CheckpointVerification(False, 0, "invalid checkpoint values")
        if sequence == 0 and digest != GENESIS_HASH:
            return CheckpointVerification(False, 0, "genesis checkpoint mismatch")
        health = verify_ledger(database)
        if not health.valid:
            return CheckpointVerification(False, sequence, f"ledger invalid: {health.reason}")
        uri = f"file:{Path(database).resolve().as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            row = db.execute(
                "SELECT record_hash FROM evidence_records WHERE sequence=?", (sequence,)
            ).fetchone()
            count = db.execute("SELECT COUNT(*) FROM evidence_records").fetchone()[0]
        if count < sequence:
            return CheckpointVerification(False, sequence, "ledger is shorter than checkpoint")
        actual = row[0] if row else GENESIS_HASH
        if actual != digest:
            return CheckpointVerification(False, sequence, "checkpoint hash mismatch")
        return CheckpointVerification(True, sequence, "checkpoint prefix matches ledger")
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as error:
        return CheckpointVerification(False, 0, f"checkpoint could not be verified: {error}")
