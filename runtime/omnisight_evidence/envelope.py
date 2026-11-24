"""Adapter from persisted VEF records to the published observation envelope."""
from __future__ import annotations

from typing import Any
from .store import EvidenceRecord


def to_observation_envelope(
    record: EvidenceRecord, *, correlation_id: str,
    coordinate_frame: str = "source-image-pixels",
    region: dict[str, Any] | None = None,
    content_type: str = "other",
    confidence: dict[str, Any] | None = None,
    transformations: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Map a persisted record into schema v0.1.0 without inventing verification.

    A verified envelope is emitted only when the source record itself contains
    a verification reference. The caller must run JSON Schema validation.
    """
    if not isinstance(record, EvidenceRecord):
        raise TypeError("record must be an EvidenceRecord")
    if not isinstance(correlation_id, str) or not correlation_id.strip():
        raise ValueError("correlation_id is required")
    region_value = region or {"shape": "full_frame", "coordinates": []}
    if not isinstance(region_value, dict):
        raise TypeError("region must be an object")
    shape = region_value.get("shape", "full_frame")
    coordinates = region_value.get("coordinates", [])
    envelope = {
        "schema_version": "0.1.0",
        "observation_id": record.record_id,
        "correlation_id": correlation_id,
        "source": {
            "source_id": record.source_id,
            "captured_at": record.captured_at,
            "media_digest": f"sha256:{record.payload_sha256}",
            "provenance_ref": record.record_id,
        },
        "region": {
            "coordinate_frame": coordinate_frame,
            "shape": shape,
            "coordinates": coordinates,
        },
        "content_type": content_type,
        "result": record.observation,
        "producer": {
            "capability_id": record.producer,
            "semantic_version": record.producer_version,
        },
        "epistemic_status": record.epistemic_status,
        "evidence_refs": [record.record_id],
        "limitations": list(record.limitations),
    }
    if confidence is not None:
        envelope["confidence"] = confidence
    if transformations:
        envelope["transformations"] = transformations
    if warnings:
        envelope["warnings"] = warnings
    if record.epistemic_status == "verified":
        if not record.verification_ref:
            raise ValueError("verified record lacks verification_ref")
        envelope["verification_ref"] = record.verification_ref
    return envelope
