"""Governed intake for user-selected LM Studio Model Catalog entries.

This module does not scrape the public Hub or website. It accepts a candidate
record supplied by the user or an officially supported LM Studio workflow,
prepares (but never executes) an lms get command, and fuses metadata through AFI.
"""
from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import asdict, dataclass
from typing import Any, Mapping


MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}/[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
QUANTIZATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ALLOWED_CAPABILITIES = {"vision", "reasoning", "tool_use", "audio", "video"}


class LMStudioCatalogError(ValueError):
    """Raised when a supplied LM Studio catalog candidate is invalid."""


@dataclass(frozen=True, slots=True)
class LMStudioCatalogCandidate:
    model_id: str
    display_name: str
    catalog_url: str
    quantization: str | None
    publisher: str | None
    architecture: str | None
    parameter_sizes: tuple[str, ...]
    max_context: str | None
    minimum_memory: str | None
    availability: tuple[str, ...]
    capabilities: dict[str, bool]
    license_text: str | None
    description: str | None
    artifact_links: tuple[dict[str, str], ...]
    metadata: dict[str, Any]
    original_idea_value: str
    potential_market_value: str
    revenue_models: tuple[str, ...]
    development_timeline: str
    development_cost: str
    integration_cost: str
    risk_assessment: str
    evidence_verification_status: str
    model_type: str = "catalog_candidate"


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 4000:
        raise LMStudioCatalogError(f"{field} must be a string of at most 4000 characters")
    return value


def _validate_catalog_url(value: Any) -> str:
    if not isinstance(value, str):
        raise LMStudioCatalogError("catalog_url is required")
    parsed = urllib.parse.urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise LMStudioCatalogError("catalog URL has an invalid port") from exc
    if (parsed.scheme != "https" or parsed.hostname != "lmstudio.ai"
            or parsed.username or parsed.password or port not in (None, 443)
            or parsed.query or parsed.fragment
            or not re.fullmatch(r"/models/[A-Za-z0-9][A-Za-z0-9._-]*", parsed.path)):
        raise LMStudioCatalogError("catalog_url must be a clean HTTPS LM Studio model detail URL")
    return urllib.parse.urlunsplit(("https", "lmstudio.ai", parsed.path, "", ""))


def candidate_from_mapping(value: Mapping[str, Any]) -> LMStudioCatalogCandidate:
    """Validate a user-supplied/exported catalog record without network access."""
    if not isinstance(value, Mapping):
        raise LMStudioCatalogError("candidate must be a mapping")
    model_id = value.get("model_id")
    display_name = value.get("display_name")
    if not isinstance(model_id, str) or not MODEL_ID_RE.fullmatch(model_id):
        raise LMStudioCatalogError("model_id must be a publisher/model identifier")
    if not isinstance(display_name, str) or not display_name.strip() or len(display_name) > 256:
        raise LMStudioCatalogError("display_name is required and must be at most 256 characters")
    catalog_url = _validate_catalog_url(value.get("catalog_url"))
    quantization = value.get("quantization")
    if quantization is not None and (not isinstance(quantization, str) or not QUANTIZATION_RE.fullmatch(quantization)):
        raise LMStudioCatalogError("quantization must be a simple identifier")
    original_idea_value = value.get("original_idea_value")
    if not isinstance(original_idea_value, str) or not original_idea_value.strip() or len(original_idea_value) > 4000:
        raise LMStudioCatalogError("original_idea_value is mandatory and must be a non-empty string of at most 4000 characters")
    revenue_models = value.get("revenue_models", [])
    if not isinstance(revenue_models, list) or len(revenue_models) > 20 or any(not isinstance(x, str) or len(x) > 256 for x in revenue_models):
        raise LMStudioCatalogError("revenue_models must be an array of at most 20 short strings")
    metadata = value.get("metadata", {})
    if not isinstance(metadata, dict):
        raise LMStudioCatalogError("metadata must be a JSON object")
    try:
        encoded = json.dumps(metadata, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise LMStudioCatalogError("metadata must contain finite JSON-compatible values") from exc
    if len(encoded) > 256 * 1024:
        raise LMStudioCatalogError("metadata exceeds the 256 KiB limit")
    capabilities = value.get("capabilities", {})
    if not isinstance(capabilities, dict) or any(
        key not in ALLOWED_CAPABILITIES or not isinstance(flag, bool)
        for key, flag in capabilities.items()
    ):
        raise LMStudioCatalogError("capabilities must contain only supported boolean capability declarations")
    parameter_sizes = value.get("parameter_sizes", [])
    availability = value.get("availability", [])
    artifact_links = value.get("artifact_links", [])
    if not isinstance(parameter_sizes, list) or any(not isinstance(x, str) or len(x) > 64 for x in parameter_sizes):
        raise LMStudioCatalogError("parameter_sizes must be an array of short strings")
    if not isinstance(availability, list) or any(x not in {"local", "cloud"} for x in availability):
        raise LMStudioCatalogError("availability may contain only local and cloud")
    if not isinstance(artifact_links, list) or any(not isinstance(x, dict) for x in artifact_links):
        raise LMStudioCatalogError("artifact_links must be an array of objects")
    checked_links = []
    for link in artifact_links:
        url = link.get("url")
        parsed = urllib.parse.urlsplit(url) if isinstance(url, str) else None
        if (parsed is None or parsed.scheme != "https"
                or parsed.hostname not in {"lmstudio.ai", "huggingface.co"}
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise LMStudioCatalogError("artifact links must use approved HTTPS model origins")
        checked_links.append({"text": str(link.get("text", ""))[:256], "url": url})
    return LMStudioCatalogCandidate(
        model_id=model_id,
        display_name=display_name.strip(),
        catalog_url=catalog_url,
        quantization=quantization,
        publisher=_optional_text(value.get("publisher"), "publisher"),
        architecture=_optional_text(value.get("architecture"), "architecture"),
        parameter_sizes=tuple(parameter_sizes),
        max_context=_optional_text(value.get("max_context"), "max_context"),
        minimum_memory=_optional_text(value.get("minimum_memory"), "minimum_memory"),
        availability=tuple(sorted(set(availability))),
        capabilities=dict(capabilities),
        license_text=_optional_text(value.get("license_text"), "license_text"),
        description=_optional_text(value.get("description"), "description"),
        artifact_links=tuple(checked_links),
        metadata=dict(metadata),
        original_idea_value=original_idea_value.strip(),
        potential_market_value=_optional_text(value.get("potential_market_value", "NOT_ASSESSED"), "potential_market_value") or "NOT_ASSESSED",
        revenue_models=tuple(revenue_models),
        development_timeline=_optional_text(value.get("development_timeline", "NOT_ASSESSED"), "development_timeline") or "NOT_ASSESSED",
        development_cost=_optional_text(value.get("development_cost", "NOT_ASSESSED"), "development_cost") or "NOT_ASSESSED",
        integration_cost=_optional_text(value.get("integration_cost", "NOT_ASSESSED"), "integration_cost") or "NOT_ASSESSED",
        risk_assessment=_optional_text(value.get("risk_assessment", "PENDING"), "risk_assessment") or "PENDING",
        evidence_verification_status=_optional_text(value.get("evidence_verification_status", "USER_SUPPLIED_UNVERIFIED"), "evidence_verification_status") or "USER_SUPPLIED_UNVERIFIED",
    )


def build_download_command(candidate: LMStudioCatalogCandidate) -> tuple[str, ...]:
    """Return the official CLI command for review; never run or download anything."""
    model_ref = candidate.model_id
    if candidate.quantization:
        model_ref += "@" + candidate.quantization
    return ("lms", "get", model_ref)


def assimilate_catalog_candidate(
    engine: Any,
    candidate: LMStudioCatalogCandidate,
    afi_adapter: Any | None = None,
) -> tuple[Any, Any]:
    """Persist the supplied candidate and AFI profile; no website or model access."""
    from .afi import AFIPrimeFusionAdapter

    if not isinstance(candidate, LMStudioCatalogCandidate):
        raise LMStudioCatalogError("candidate must be validated with candidate_from_mapping")
    afi = afi_adapter or AFIPrimeFusionAdapter()
    catalog_record = engine.ingest_object(asdict(candidate), source=candidate.catalog_url)
    profile = afi.fuse_model(candidate)
    profile_record = engine.ingest_object(
        afi.to_record(profile),
        source=f"afi-prime://lm-studio-model-catalog/{candidate.model_id}",
    )
    register_entry = engine.register_acquisition(
        catalog_record.record_id,
        original_idea_value=candidate.original_idea_value,
        potential_market_value=candidate.potential_market_value,
        revenue_models=candidate.revenue_models,
        development_timeline=candidate.development_timeline,
        development_cost=candidate.development_cost,
        integration_cost=candidate.integration_cost,
        risk_assessment=candidate.risk_assessment,
        evidence_verification_status=candidate.evidence_verification_status,
    )
    return catalog_record, profile_record, register_entry
