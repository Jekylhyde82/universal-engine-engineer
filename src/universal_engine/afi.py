"""AFI PRIME's metadata-only model capability extraction boundary.

This adapter preserves provider facts and does not claim benchmarked intelligence,
model safety, compatibility, or approval to integrate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any


@dataclass(frozen=True, slots=True)
class AFIModelCapabilityProfile:
    profile_id: str
    model_key: str
    display_name: str
    publisher: str | None
    model_type: str
    architecture: str | None
    quantization: dict[str, Any] | None
    size_bytes: int | None
    params_string: str | None
    max_context_length: int | None
    format: str | None
    catalog_availability: tuple[str, ...]
    catalog_parameter_sizes: tuple[str, ...]
    catalog_compatibility_types: tuple[str, ...]
    catalog_minimum_memory: str | None
    catalog_license_text: str | None
    catalog_download_count: str | None
    catalog_star_count: str | None
    catalog_updated: str | None
    catalog_artifact_links: tuple[dict[str, str], ...]
    source_url: str | None
    capability_facts: tuple[str, ...]
    evidence_source: str
    evidence_class: str
    evaluation_state: str
    performance_verified: bool
    integration_approved: bool


class AFIPrimeFusionAdapter:
    """Extract explicit model capability facts into AFI's governed profile shape."""

    @staticmethod
    def fuse_model(model: Any) -> AFIModelCapabilityProfile:
        required = ("display_name", "model_type")
        if any(not hasattr(model, field) for field in required):
            raise ValueError("AFI PRIME requires a validated LM Studio model record")
        key_value = getattr(model, "key", getattr(model, "model_id", None))
        if not isinstance(key_value, str) or not key_value:
            raise ValueError("AFI PRIME requires a stable model key")
        facts: set[str] = set()
        if model.model_type == "llm":
            facts.add("language_model")
        elif model.model_type == "embedding":
            facts.add("text_embedding")
        elif model.model_type == "decision":
            facts.add("decision_model")
        elif model.model_type in {"catalog_model", "catalog_candidate"}:
            facts.add("catalog_model")
        capabilities = getattr(model, "capabilities", None) or {}
        if capabilities.get("vision") is True:
            facts.add("vision_input")
        if capabilities.get("trained_for_tool_use") is True:
            facts.add("tool_use_training")
        if capabilities.get("tool_use") is True:
            facts.add("tool_use_listed_in_catalog")
        if capabilities.get("reasoning") is True:
            facts.add("reasoning_listed_in_catalog")
        reasoning = getattr(model, "reasoning", None)
        if isinstance(reasoning, dict) and reasoning:
            facts.add("reasoning_configuration_exposed")
        if getattr(model, "has_vision_adapter", False) is True:
            facts.add("vision_adapter_available")
        if getattr(model, "loaded_instances", ()):
            facts.add("currently_loaded_instance")
        availability = getattr(model, "availability", ()) or ()
        if "local" in availability:
            facts.add("local_catalog_availability")
        if "cloud" in availability:
            facts.add("cloud_catalog_availability")
        key = key_value
        is_public_catalog = model.model_type in {"catalog_model", "catalog_candidate"}
        return AFIModelCapabilityProfile(
            profile_id="afi_model_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20],
            model_key=key,
            display_name=str(model.display_name),
            publisher=getattr(model, "publisher", None),
            model_type=str(model.model_type),
            architecture=getattr(model, "architecture", None),
            quantization=getattr(model, "quantization", None),
            size_bytes=getattr(model, "size_bytes", None),
            params_string=getattr(model, "params_string", None),
            max_context_length=getattr(model, "max_context_length", None),
            format=getattr(model, "format", None),
            catalog_availability=tuple(availability),
            catalog_parameter_sizes=tuple(getattr(model, "parameter_sizes", ()) or ()),
            catalog_compatibility_types=tuple(getattr(model, "compatibility_types", ()) or ()),
            catalog_minimum_memory=getattr(model, "minimum_memory", None),
            catalog_license_text=getattr(model, "license_text", None),
            catalog_download_count=getattr(model, "download_count", None),
            catalog_star_count=getattr(model, "star_count", None),
            catalog_updated=getattr(model, "updated", None),
            catalog_artifact_links=tuple(getattr(model, "artifact_links", ()) or ()),
            source_url=getattr(model, "details_url", getattr(model, "catalog_url", None)),
            capability_facts=tuple(sorted(facts)),
            evidence_source=(
                "User-supplied LM Studio Model Catalog record" if is_public_catalog
                else "LM Studio native REST API v1 model inventory"
            ),
            evidence_class=(
                "USER_SUPPLIED_CATALOG_METADATA" if model.model_type == "catalog_candidate" else "PUBLISHER_REPORTED_CATALOG_METADATA" if is_public_catalog
                else "PUBLISHER_REPORTED_METADATA"
            ),
            evaluation_state="METADATA_ONLY_NOT_BENCHMARKED",
            performance_verified=False,
            integration_approved=False,
        )

    @staticmethod
    def to_record(profile: AFIModelCapabilityProfile) -> dict[str, Any]:
        return asdict(profile)
