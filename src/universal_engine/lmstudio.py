"""Read-only LM Studio v1 model inventory adapter for UAIE.

The adapter inventories models already available to a local LM Studio server.
It does not download, load, unload, execute, or modify models.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable

DEFAULT_BASE_URL = "http://127.0.0.1:1234"
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_MODELS = 5000
MODEL_TYPES = {"llm", "embedding", "decision"}


class LMStudioError(ValueError):
    """Raised when the local LM Studio inventory cannot be safely read."""


@dataclass(frozen=True, slots=True)
class LMStudioDownloadJob:
    job_id: str | None
    status: str
    total_size_bytes: int | None
    started_at: str | None
    completed_at: str | None


@dataclass(frozen=True, slots=True)
class LMStudioModel:
    key: str
    display_name: str
    model_type: str
    publisher: str | None
    architecture: str | None
    quantization: dict[str, Any] | None
    size_bytes: int | None
    params_string: str | None
    max_context_length: int | None
    format: str | None
    capabilities: dict[str, Any] | None
    reasoning: dict[str, Any] | None
    decision_type: str | None
    has_vision_adapter: bool | None
    description: str | None
    variants: tuple[str, ...]
    selected_variant: str | None
    loaded_instances: tuple[dict[str, Any], ...]


def _validated_endpoint(base_url: str) -> str:
    if not isinstance(base_url, str) or not base_url.strip():
        raise LMStudioError("LM Studio base URL is required")
    parsed = urllib.parse.urlsplit(base_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise LMStudioError("LM Studio endpoint must use HTTP or HTTPS")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise LMStudioError("endpoint credentials, query strings and fragments are forbidden")
    if parsed.path not in {"", "/"}:
        raise LMStudioError("base URL must not contain an API path")
    host = (parsed.hostname or "").casefold()
    if host not in {"localhost", "127.0.0.1", "::1"}:
        raise LMStudioError("only loopback LM Studio endpoints are allowed by this adapter")
    try:
        port = parsed.port
    except ValueError as exc:
        raise LMStudioError("invalid LM Studio endpoint port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise LMStudioError("invalid LM Studio endpoint port")
    netloc = f"[{host}]" if ":" in host else host
    if port is not None:
        netloc += f":{port}"
    return urllib.parse.urlunsplit((parsed.scheme, netloc, "", "", ""))


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise LMStudioError(f"model field {field!r} must be a string or null")
    return value


def _optional_positive_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LMStudioError(f"model field {field!r} must be a positive integer or null")
    return value


def _parse_model(item: Any) -> LMStudioModel:
    if not isinstance(item, dict):
        raise LMStudioError("each model entry must be an object")
    key = item.get("key")
    display_name = item.get("display_name")
    model_type = item.get("type")
    if not isinstance(key, str) or not key.strip() or len(key) > 512:
        raise LMStudioError("each model requires a valid key")
    if not isinstance(display_name, str) or not display_name.strip():
        raise LMStudioError(f"model {key!r} requires a display_name")
    if model_type not in MODEL_TYPES:
        raise LMStudioError(f"model {key!r} has unsupported type {model_type!r}")
    quantization = item.get("quantization")
    capabilities = item.get("capabilities")
    reasoning = item.get("reasoning")
    decision_type = item.get("decision_type")
    has_vision_adapter = item.get("has_vision_adapter")
    loaded = item.get("loaded_instances", [])
    variants = item.get("variants", [])
    if quantization is not None and not isinstance(quantization, dict):
        raise LMStudioError(f"model {key!r} quantization must be an object or null")
    if capabilities is not None and not isinstance(capabilities, dict):
        raise LMStudioError(f"model {key!r} capabilities must be an object or null")
    if reasoning is not None and not isinstance(reasoning, dict):
        raise LMStudioError(f"model {key!r} reasoning must be an object or null")
    if has_vision_adapter is not None and not isinstance(has_vision_adapter, bool):
        raise LMStudioError(f"model {key!r} has_vision_adapter must be a boolean or null")
    if not isinstance(loaded, list) or any(not isinstance(x, dict) for x in loaded):
        raise LMStudioError(f"model {key!r} loaded_instances must be an array of objects")
    if not isinstance(variants, list) or any(not isinstance(x, str) for x in variants):
        raise LMStudioError(f"model {key!r} variants must be an array of strings")
    return LMStudioModel(
        key=key,
        display_name=display_name,
        model_type=model_type,
        publisher=_optional_string(item.get("publisher"), "publisher"),
        architecture=_optional_string(item.get("architecture"), "architecture"),
        quantization=dict(quantization) if quantization is not None else None,
        size_bytes=_optional_positive_int(item.get("size_bytes"), "size_bytes"),
        params_string=_optional_string(item.get("params_string"), "params_string"),
        max_context_length=_optional_positive_int(item.get("max_context_length"), "max_context_length"),
        format=_optional_string(item.get("format"), "format"),
        capabilities=dict(capabilities) if capabilities is not None else None,
        reasoning=dict(reasoning) if reasoning is not None else None,
        decision_type=_optional_string(decision_type, "decision_type"),
        has_vision_adapter=has_vision_adapter,
        description=_optional_string(item.get("description"), "description"),
        variants=tuple(variants),
        selected_variant=_optional_string(item.get("selected_variant"), "selected_variant"),
        loaded_instances=tuple(dict(x) for x in loaded),
    )



def _ensure_loopback_response(response: Any, endpoint: str) -> None:
    """Prevent urllib redirects from forwarding credentials away from the local host."""
    final_url = response.geturl() if hasattr(response, "geturl") else endpoint
    final = urllib.parse.urlsplit(final_url)
    expected = urllib.parse.urlsplit(endpoint)
    try:
        final_port = final.port
        expected_port = expected.port
    except ValueError as exc:
        raise LMStudioError("LM Studio response redirected to an invalid endpoint") from exc
    if (final.scheme != expected.scheme or (final.hostname or "").casefold() != (expected.hostname or "").casefold()
            or final_port != expected_port or final.username or final.password):
        raise LMStudioError("LM Studio endpoint redirected outside its configured loopback origin")


def list_models(
    base_url: str = DEFAULT_BASE_URL,
    api_token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    opener: Callable[..., Any] | None = None,
) -> tuple[LMStudioModel, ...]:
    """Read and validate GET /api/v1/models from an explicitly local server."""
    endpoint = _validated_endpoint(base_url)
    if timeout <= 0 or timeout > 60:
        raise LMStudioError("timeout must be greater than 0 and no more than 60 seconds")
    if max_response_bytes < 1 or max_response_bytes > 16 * 1024 * 1024:
        raise LMStudioError("max_response_bytes must be between 1 byte and 16 MiB")
    if api_token is not None and (not isinstance(api_token, str) or not api_token.strip()):
        raise LMStudioError("API token, when supplied, must be a non-empty string")
    headers = {"Accept": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    request = urllib.request.Request(endpoint + "/api/v1/models", headers=headers, method="GET")
    open_request = opener or urllib.request.urlopen
    try:
        with open_request(request, timeout=timeout) as response:
            _ensure_loopback_response(response, endpoint)
            raw = response.read(max_response_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LMStudioError(f"could not read LM Studio model inventory: {type(exc).__name__}") from exc
    if len(raw) > max_response_bytes:
        raise LMStudioError("LM Studio response exceeds configured size limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LMStudioError("LM Studio returned invalid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise LMStudioError("LM Studio v1 response must contain a models array")
    if len(payload["models"]) > MAX_MODELS:
        raise LMStudioError(f"model inventory exceeds the {MAX_MODELS}-model safety limit")
    models = tuple(_parse_model(item) for item in payload["models"])
    keys = [model.key for model in models]
    if len(keys) != len(set(keys)):
        raise LMStudioError("LM Studio response contains duplicate model keys")
    return models


@dataclass(frozen=True, slots=True)
class CatalogAssimilationResult:
    model_records: tuple[Any, ...]
    afi_profile_records: tuple[Any, ...]


def assimilate_catalog(
    engine: Any,
    base_url: str = DEFAULT_BASE_URL,
    api_token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: Callable[..., Any] | None = None,
    afi_adapter: Any | None = None,
) -> CatalogAssimilationResult:
    """Persist LM Studio metadata and AFI PRIME capability profiles through UAIE."""
    from .afi import AFIPrimeFusionAdapter

    endpoint = _validated_endpoint(base_url)
    models = list_models(endpoint, api_token=api_token, timeout=timeout, opener=opener)
    afi = afi_adapter or AFIPrimeFusionAdapter()
    model_records = []
    afi_records = []
    for model in models:
        quoted_key = urllib.parse.quote(model.key, safe='/')
        source = f"{endpoint}/api/v1/models#{quoted_key}"
        model_records.append(engine.ingest_object(asdict(model), source=source))
        profile = afi.fuse_model(model)
        afi_source = f"afi-prime://lm-studio-model-catalog/{quoted_key}"
        afi_records.append(engine.ingest_object(afi.to_record(profile), source=afi_source))
    return CatalogAssimilationResult(tuple(model_records), tuple(afi_records))



def _parse_download_job(payload: Any) -> LMStudioDownloadJob:
    if not isinstance(payload, dict):
        raise LMStudioError("LM Studio download response must be an object")
    status = payload.get("status")
    if status not in {"downloading", "paused", "completed", "failed", "already_downloaded"}:
        raise LMStudioError("LM Studio returned an unknown download status")
    job_id = payload.get("job_id")
    if job_id is not None and (not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", job_id)):
        raise LMStudioError("LM Studio returned an invalid download job identifier")
    if status != "already_downloaded" and not job_id:
        raise LMStudioError("LM Studio download response is missing its job identifier")
    size = payload.get("total_size_bytes")
    if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 0):
        raise LMStudioError("LM Studio returned an invalid total_size_bytes value")
    started = payload.get("started_at")
    completed = payload.get("completed_at")
    if started is not None and not isinstance(started, str):
        raise LMStudioError("LM Studio returned an invalid started_at value")
    if completed is not None and not isinstance(completed, str):
        raise LMStudioError("LM Studio returned an invalid completed_at value")
    return LMStudioDownloadJob(job_id, status, size, started, completed)


def download_model(
    model_reference: str,
    *,
    approved: bool = False,
    base_url: str = DEFAULT_BASE_URL,
    api_token: str | None = None,
    quantization: str | None = None,
    timeout: float = 30.0,
    opener: Callable[..., Any] | None = None,
) -> LMStudioDownloadJob:
    """Start an official LM Studio download only after explicit caller approval."""
    if approved is not True:
        raise LMStudioError("explicit approval=True is required before any model download")
    if api_token is not None and (not isinstance(api_token, str) or not api_token.strip()):
        raise LMStudioError("API token, when supplied, must be a non-empty string")
    if not isinstance(model_reference, str) or not model_reference.strip():
        raise LMStudioError("model_reference is required")
    parsed_model_url = urllib.parse.urlsplit(model_reference)
    is_hf_url = parsed_model_url.scheme == "https" and parsed_model_url.hostname == "huggingface.co"
    if is_hf_url:
        try:
            model_port = parsed_model_url.port
        except ValueError as exc:
            raise LMStudioError("model_reference has an invalid port") from exc
        if (parsed_model_url.username or parsed_model_url.password or parsed_model_url.query
                or parsed_model_url.fragment or model_port not in (None, 443)
                or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", parsed_model_url.path)):
            raise LMStudioError("model_reference must be a clean Hugging Face model URL")
    elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}/[A-Za-z0-9][A-Za-z0-9._-]{0,127}", model_reference):
        raise LMStudioError("model_reference must be a publisher/model identifier or exact Hugging Face model URL")
    if quantization is not None:
        if not is_hf_url or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", quantization):
            raise LMStudioError("quantization is supported here only with an exact Hugging Face model URL")
    endpoint = _validated_endpoint(base_url)
    if timeout <= 0 or timeout > 300:
        raise LMStudioError("download timeout must be greater than 0 and no more than 300 seconds")
    body: dict[str, Any] = {"model": model_reference}
    if quantization is not None:
        body["quantization"] = quantization
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    request = urllib.request.Request(
        endpoint + "/api/v1/models/download",
        data=json.dumps(body, allow_nan=False).encode("utf-8"),
        headers=headers, method="POST")
    open_request = opener or urllib.request.urlopen
    try:
        with open_request(request, timeout=timeout) as response:
            _ensure_loopback_response(response, endpoint)
            raw = response.read(1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LMStudioError(f"LM Studio model download request failed: {type(exc).__name__}") from exc
    if len(raw) > 1024 * 1024:
        raise LMStudioError("LM Studio download response exceeds 1 MiB")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LMStudioError("LM Studio returned invalid download JSON") from exc
    return _parse_download_job(payload)


def get_download_status(
    job_id: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    api_token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: Callable[..., Any] | None = None,
) -> LMStudioDownloadJob:
    """Read status for a previously approved download job."""
    if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", job_id):
        raise LMStudioError("invalid download job identifier")
    if timeout <= 0 or timeout > 60:
        raise LMStudioError("status timeout must be greater than 0 and no more than 60 seconds")
    if api_token is not None and (not isinstance(api_token, str) or not api_token.strip()):
        raise LMStudioError("API token, when supplied, must be a non-empty string")
    endpoint = _validated_endpoint(base_url)
    headers = {"Accept": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    request = urllib.request.Request(
        endpoint + "/api/v1/models/download/status/" + urllib.parse.quote(job_id, safe=""),
        headers=headers, method="GET")
    open_request = opener or urllib.request.urlopen
    try:
        with open_request(request, timeout=timeout) as response:
            _ensure_loopback_response(response, endpoint)
            raw = response.read(1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LMStudioError(f"LM Studio download status request failed: {type(exc).__name__}") from exc
    if len(raw) > 1024 * 1024:
        raise LMStudioError("LM Studio download status response exceeds 1 MiB")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LMStudioError("LM Studio returned invalid download status JSON") from exc
    return _parse_download_job(payload)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only LM Studio model inventory for UAIE")
    parser.add_argument("--base-url", default=os.environ.get("LM_STUDIO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--token-env", default="LM_API_TOKEN", help="environment variable containing the optional API token")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    try:
        models = list_models(args.base_url, api_token=os.environ.get(args.token_env), timeout=args.timeout)
    except LMStudioError as exc:
        print(f"UAIE LM Studio error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"source": _validated_endpoint(args.base_url) + "/api/v1/models",
                      "read_only": True, "models": [asdict(model) for model in models]},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
