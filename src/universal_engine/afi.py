"""AFI PRIME's metadata-only model capability extraction boundary.

This adapter preserves provider facts and does not claim benchmarked intelligence,
model safety, compatibility, or approval to integrate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
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
        required = ("key", "display_name", "model_type")
        if any(not hasattr(model, field) for field in required):
            raise ValueError("AFI PRIME requires a validated LM Studio model record")
        facts: set[str] = set()
        if model.model_type == "llm":
            facts.add("language_model")
        elif model.model_type == "embedding":
            facts.add("text_embedding")
        elif model.model_type == "decision":
            facts.add("decision_model")
        capabilities = getattr(model, "capabilities", None) or {}
        if capabilities.get("vision") is True:
            facts.add("vision_input")
        if capabilities.get("trained_for_tool_use") is True:
            facts.add("tool_use_training")
        reasoning = getattr(model, "reasoning", None)
        if isinstance(reasoning, dict) and reasoning:
            facts.add("reasoning_configuration_exposed")
        if getattr(model, "has_vision_adapter", False) is True:
            facts.add("vision_adapter_available")
        if getattr(model, "loaded_instances", ()):
            facts.add("currently_loaded_instance")
        key = str(model.key)
        return AFIModelCapabilityProfile(
            profile_id="afi_model_" + key.replace("/", "_"),
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
            capability_facts=tuple(sorted(facts)),
            evidence_source="LM Studio native REST API v1 model inventory",
            evidence_class="PUBLISHER_REPORTED_METADATA",
            evaluation_state="METADATA_ONLY_NOT_BENCHMARKED",
            performance_verified=False,
            integration_approved=False,
        )

    @staticmethod
    def to_record(profile: AFIModelCapabilityProfile) -> dict[str, Any]:
        return asdict(profile)
