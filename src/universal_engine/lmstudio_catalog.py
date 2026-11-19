"""Governed intake for user-selected LM Studio Model Catalog entries.

This module does not scrape the public Hub or website. It accepts a candidate
record supplied by the user or an officially supported LM Studio workflow,
prepares (but never executes) an lms get command, and fuses metadata through AFI.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import yaml
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}/[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
QUANTIZATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ALLOWED_CAPABILITIES = {"vision", "reasoning", "tool_use", "audio", "video"}
SENSITIVE_METADATA_KEYS = {
    "token", "api_token", "access_token", "refresh_token", "api_key",
    "secret", "secret_key", "client_secret", "private_key", "password",
    "authorization", "credential", "access_key",
}


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
            or not re.fullmatch(r"/models/[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)?", parsed.path)):
        raise LMStudioCatalogError("catalog_url must be a clean HTTPS LM Studio model detail URL")
    return urllib.parse.urlunsplit(("https", "lmstudio.ai", parsed.path, "", ""))


def _reject_secret_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"(?<!^)(?=[A-Z])", "_", str(key)).casefold().replace("-", "_")
            if normalized in SENSITIVE_METADATA_KEYS or normalized.endswith(("_token", "_secret", "_password", "_credential", "_api_key")):
                raise LMStudioCatalogError(f"metadata field {key!r} is not permitted")
            _reject_secret_fields(child)
    elif isinstance(value, list):
        for child in value:
            _reject_secret_fields(child)


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
    _reject_secret_fields(metadata)
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
    if not isinstance(artifact_links, list) or len(artifact_links) > 50 or any(not isinstance(x, dict) for x in artifact_links):
        raise LMStudioCatalogError("artifact_links must be an array of at most 50 objects")
    checked_links = []
    for link in artifact_links:
        url = link.get("url")
        parsed = urllib.parse.urlsplit(url) if isinstance(url, str) else None
        try:
            port = parsed.port if parsed is not None else None
        except ValueError as exc:
            raise LMStudioCatalogError("artifact link has an invalid port") from exc
        if (parsed is None or parsed.scheme != "https"
                or parsed.hostname not in {"lmstudio.ai", "huggingface.co"}
                or parsed.username or parsed.password or port not in (None, 443)
                or parsed.query or parsed.fragment or len(url) > 2048):
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





def build_clone_command(candidate: LMStudioCatalogCandidate) -> tuple[str, ...]:
    """Return LM Studio's metadata-only clone command; it does not fetch model weights."""
    return ("lms", "clone", candidate.model_id)


def candidate_from_model_yaml(
    value: Mapping[str, Any],
    *,
    original_idea_value: str,
    catalog_url: str | None = None,
) -> LMStudioCatalogCandidate:
    """Map the official model.yaml specification into a governed UAIE candidate."""
    if not isinstance(value, Mapping):
        raise LMStudioCatalogError("model.yaml root must be a mapping")
    model_id = value.get("model")
    if not isinstance(model_id, str) or not MODEL_ID_RE.fullmatch(model_id):
        raise LMStudioCatalogError("model.yaml requires model: publisher/model")
    base = value.get("base", [])
    if not isinstance(base, list) or len(base) > 100 or any(not isinstance(x, dict) for x in base):
        raise LMStudioCatalogError("model.yaml base must be an array of at most 100 model variants")
    overrides = value.get("metadataOverrides", {})
    if not isinstance(overrides, dict):
        raise LMStudioCatalogError("model.yaml metadataOverrides must be a mapping")
    architectures = overrides.get("architectures", [])
    params = overrides.get("paramsStrings", [])
    contexts = overrides.get("contextLengths", [])
    compatibility = overrides.get("compatibilityTypes", [])
    if not isinstance(architectures, list) or any(not isinstance(x, str) for x in architectures):
        raise LMStudioCatalogError("metadataOverrides.architectures must be an array of strings")
    if not isinstance(params, list) or any(not isinstance(x, str) for x in params):
        raise LMStudioCatalogError("metadataOverrides.paramsStrings must be an array of strings")
    if not isinstance(contexts, list) or any(isinstance(x, bool) or not isinstance(x, int) or x < 1 for x in contexts):
        raise LMStudioCatalogError("metadataOverrides.contextLengths must contain positive integers")
    if not isinstance(compatibility, list) or any(not isinstance(x, str) for x in compatibility):
        raise LMStudioCatalogError("metadataOverrides.compatibilityTypes must be an array of strings")
    memory_bytes = overrides.get("minMemoryUsageBytes")
    if memory_bytes is not None and (isinstance(memory_bytes, bool) or not isinstance(memory_bytes, int) or memory_bytes < 1):
        raise LMStudioCatalogError("metadataOverrides.minMemoryUsageBytes must be a positive integer")
    capabilities = {}
    for source_key, target_key in (("vision", "vision"), ("reasoning", "reasoning"),
                                   ("trainedForToolUse", "tool_use")):
        flag = overrides.get(source_key)
        if flag is not None:
            if not isinstance(flag, bool):
                raise LMStudioCatalogError(f"metadataOverrides.{source_key} must be a boolean")
            capabilities[target_key] = flag
    artifact_links = []
    for variant in base:
        variant_key = variant.get("key")
        if variant_key is not None and not isinstance(variant_key, str):
            raise LMStudioCatalogError("model.yaml variant keys must be strings")
        sources = variant.get("sources", [])
        if not isinstance(sources, list):
            raise LMStudioCatalogError("model.yaml variant sources must be an array")
        for source in sources:
            if not isinstance(source, dict):
                raise LMStudioCatalogError("model.yaml source entries must be mappings")
            if source.get("type") == "huggingface":
                user, repo = source.get("user"), source.get("repo")
                if not isinstance(user, str) or not isinstance(repo, str):
                    raise LMStudioCatalogError("Hugging Face sources require user and repo")
                artifact_links.append({
                    "text": str(variant_key or f"{user}/{repo}"),
                    "url": f"https://huggingface.co/{urllib.parse.quote(user, safe='')}/{urllib.parse.quote(repo, safe='')}",
                })
    display_name = str(overrides.get("name") or model_id.split("/", 1)[1])
    if catalog_url is None:
        catalog_url = f"https://lmstudio.ai/models/{model_id}"
    memory_text = None
    if memory_bytes is not None:
        memory_text = f"{memory_bytes / 1_000_000_000:.2f} GB"
    license_text = value.get("license") or overrides.get("license")
    description = overrides.get("description") or value.get("description")
    candidate_mapping = {
        "model_id": model_id,
        "display_name": display_name,
        "catalog_url": catalog_url,
        "publisher": model_id.split("/", 1)[0],
        "architecture": architectures[0] if architectures else None,
        "parameter_sizes": params,
        "max_context": str(max(contexts)) if contexts else None,
        "minimum_memory": memory_text,
        "availability": [],
        "capabilities": capabilities,
        "license_text": license_text,
        "description": description,
        "artifact_links": artifact_links,
        "metadata": {"model_yaml": dict(value), "compatibility_types": compatibility},
        "original_idea_value": original_idea_value,
    }
    return candidate_from_mapping(candidate_mapping)


def assimilate_model_yaml_file(
    engine: Any,
    file_path: str | Path,
    *,
    original_idea_value: str,
    catalog_url: str | None = None,
) -> tuple[Any, Any, Any]:
    """Safely read an official model.yaml file and assimilate it through UAIE/AFI."""
    path = Path(file_path).expanduser()
    if path.is_symlink() or not path.is_file():
        raise LMStudioCatalogError("model.yaml path must be a regular non-symlink file")
    raw = path.read_bytes()
    if len(raw) > 256 * 1024:
        raise LMStudioCatalogError("model.yaml exceeds the 256 KiB limit")
    try:
        parsed = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise LMStudioCatalogError("model.yaml is invalid UTF-8 or invalid safe YAML") from exc
    candidate = candidate_from_model_yaml(
        parsed, original_idea_value=original_idea_value, catalog_url=catalog_url)
    return assimilate_catalog_candidate(engine, candidate)


def download_catalog_candidate(
    engine: Any,
    candidate: LMStudioCatalogCandidate,
    acquisition_record_id: str,
    *,
    approved: bool = False,
    base_url: str = "http://127.0.0.1:1234",
    api_token: str | None = None,
    huggingface_model_url: str | None = None,
    opener: Any | None = None,
) -> Any:
    """Start a candidate download through LM Studio's official API after approval."""
    from .lmstudio import download_model

    if not isinstance(candidate, LMStudioCatalogCandidate):
        raise LMStudioCatalogError("candidate must be validated before download")
    if approved is not True:
        raise LMStudioCatalogError("explicit approved=True is required")
    try:
        register_entry = engine.get_acquisition(acquisition_record_id)
        assimilation = engine.get(acquisition_record_id)
        stored = json.loads(engine.export_record(acquisition_record_id)["extracted_text"])
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise LMStudioCatalogError("a valid UAIE acquisition register record is required") from exc
    if (register_entry.lifecycle_status != "approved" or assimilation.state != "approved"
            or stored.get("model_id") != candidate.model_id
            or stored.get("catalog_url") != candidate.catalog_url):
        raise LMStudioCatalogError("candidate must match a UAIE record approved in both governed lifecycles")
    if huggingface_model_url is not None:
        approved_urls = {item["url"] for item in candidate.artifact_links}
        if huggingface_model_url not in approved_urls:
            raise LMStudioCatalogError("Hugging Face download URL must be present in the reviewed candidate")
    if candidate.quantization:
        if huggingface_model_url is None:
            raise LMStudioCatalogError(
                "LM Studio REST API quantization is supported only for an explicitly selected Hugging Face artifact; "
                "use the reviewed lms get proposal for catalog-ID quantization"
            )
        model_reference = huggingface_model_url
        quantization = candidate.quantization
    else:
        model_reference = huggingface_model_url or candidate.model_id
        quantization = None
    return download_model(
        model_reference, approved=approved, base_url=base_url,
        api_token=api_token, quantization=quantization, opener=opener,
    )


def assimilate_catalog_candidate(
    engine: Any,
    candidate: LMStudioCatalogCandidate,
    afi_adapter: Any | None = None,
) -> tuple[Any, Any, Any]:
    """Persist the supplied candidate, AFI profile and acquisition-register entry."""
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


def main(argv: Any = None) -> int:
    """Import a reviewed catalog candidate, or download it after dual approval."""
    parser = argparse.ArgumentParser(
        description="Import and govern an LM Studio catalog candidate in UAIE")
    parser.add_argument("candidate_json", help="path to a user-reviewed candidate JSON file")
    parser.add_argument("--db", default="uaie.sqlite3", help="UAIE SQLite database path")
    parser.add_argument("--download", action="store_true", help="start an approved model download")
    parser.add_argument("--approved", action="store_true", help="explicitly confirm the download action")
    parser.add_argument("--record-id", help="UAIE acquisition record ID; required for download")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234")
    parser.add_argument("--token-env", default="LM_API_TOKEN")
    parser.add_argument("--huggingface-url", help="exact reviewed Hugging Face artifact URL")
    args = parser.parse_args(argv)
    try:
        if args.download and not args.approved:
            raise LMStudioCatalogError("--download requires explicit --approved")
        if args.approved and not args.download:
            raise LMStudioCatalogError("--approved is valid only with --download")
        if args.download and not args.record_id:
            raise LMStudioCatalogError("--download requires --record-id for the approved acquisition entry")
        source_path = Path(args.candidate_json).expanduser()
        if source_path.is_symlink() or not source_path.is_file():
            raise LMStudioCatalogError("candidate path must be a regular non-symlink file")
        raw = source_path.read_bytes()
        if len(raw) > 256 * 1024:
            raise LMStudioCatalogError("candidate JSON exceeds the 256 KiB limit")
        value = json.loads(raw.decode("utf-8"))
        candidate = candidate_from_mapping(value)
        from .uaie import UniversalAcquisitionIntegrationEngine
        engine = UniversalAcquisitionIntegrationEngine(args.db)
        catalog_record, afi_record, register_entry = assimilate_catalog_candidate(engine, candidate)
        if args.download:
            from .lmstudio import download_model
            job = download_catalog_candidate(
                engine, candidate, args.record_id, approved=True,
                base_url=args.base_url, api_token=os.environ.get(args.token_env),
                huggingface_model_url=args.huggingface_url,
            )
            result = {
                "catalog_record_id": catalog_record.record_id,
                "afi_profile_record_id": afi_record.record_id,
                "acquisition_id": register_entry.acquisition_id,
                "download_job": asdict(job),
                "download_started": job.status in {"downloading", "paused"},
            }
        else:
            result = {
                "catalog_record_id": catalog_record.record_id,
                "afi_profile_record_id": afi_record.record_id,
                "acquisition_id": register_entry.acquisition_id,
                "lifecycle_status": register_entry.lifecycle_status,
                "download_command_proposal": build_download_command(candidate),
                "command_executed": False,
                "model_downloaded": False,
            }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, LMStudioCatalogError, ValueError) as exc:
        print(f"UAIE catalog intake error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0



def model_yaml_main(argv: Any = None) -> int:
    """Import a metadata-only model.yaml produced by the official lms clone command."""
    parser = argparse.ArgumentParser(description="Assimilate official LM Studio model.yaml metadata")
    parser.add_argument("model_yaml_file")
    parser.add_argument("--db", default="uaie.sqlite3")
    parser.add_argument("--original-idea-value", required=True)
    parser.add_argument("--catalog-url")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("--record-id")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234")
    parser.add_argument("--token-env", default="LM_API_TOKEN")
    parser.add_argument("--huggingface-url")
    args = parser.parse_args(argv)
    try:
        if args.download and not args.approved:
            raise LMStudioCatalogError("--download requires explicit --approved")
        if args.approved and not args.download:
            raise LMStudioCatalogError("--approved is valid only with --download")
        if args.download and not args.record_id:
            raise LMStudioCatalogError("--download requires --record-id")
        from .uaie import UniversalAcquisitionIntegrationEngine
        engine = UniversalAcquisitionIntegrationEngine(args.db)
        path = Path(args.model_yaml_file).expanduser()
        if path.is_symlink() or not path.is_file():
            raise LMStudioCatalogError("model.yaml path must be a regular non-symlink file")
        if path.stat().st_size > 256 * 1024:
            raise LMStudioCatalogError("model.yaml exceeds the 256 KiB limit")
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        candidate = candidate_from_model_yaml(
            parsed, original_idea_value=args.original_idea_value, catalog_url=args.catalog_url)
        catalog_record, afi_record, register_entry = assimilate_catalog_candidate(engine, candidate)
        if args.download:
            job = download_catalog_candidate(
                engine, candidate, args.record_id, approved=True,
                base_url=args.base_url, api_token=os.environ.get(args.token_env),
                huggingface_model_url=args.huggingface_url)
            output = {
                "catalog_record_id": catalog_record.record_id,
                "afi_profile_record_id": afi_record.record_id,
                "acquisition_id": register_entry.acquisition_id,
                "download_job": asdict(job),
                "download_started": job.status in {"downloading", "paused"},
            }
        else:
            output = {
                "catalog_record_id": catalog_record.record_id,
                "afi_profile_record_id": afi_record.record_id,
                "acquisition_id": register_entry.acquisition_id,
                "lifecycle_status": register_entry.lifecycle_status,
                "model_id": candidate.model_id,
                "download_command_proposal": build_download_command(candidate),
                "weights_downloaded": False,
            }
    except (OSError, UnicodeDecodeError, yaml.YAMLError, LMStudioCatalogError, ValueError) as exc:
        print(f"UAIE model.yaml intake error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def status_main(argv: Any = None) -> int:
    """Poll a download job through the official local LM Studio REST API."""
    parser = argparse.ArgumentParser(description="Check an LM Studio model download job")
    parser.add_argument("job_id")
    parser.add_argument("--base-url", default="http://127.0.0.1:1234")
    parser.add_argument("--token-env", default="LM_API_TOKEN")
    args = parser.parse_args(argv)
    try:
        from .lmstudio import get_download_status
        job = get_download_status(
            args.job_id, base_url=args.base_url, api_token=os.environ.get(args.token_env))
    except ValueError as exc:
        print(f"UAIE download status error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(asdict(job), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
