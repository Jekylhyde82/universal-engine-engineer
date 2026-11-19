"""Read-only LM Studio inventory adapter for UAIE.

Uses LM Studio's native v1 REST API. It inventories models already available
on the configured LM Studio instance; it never downloads, loads, executes, or
changes a model. The public online catalog is a separate discovery source.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .uaie import UAIEError, UniversalAssimilationEngine

DEFAULT_BASE_URL = "http://127.0.0.1:1234"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class LMStudioError(ValueError):
    """LM Studio connection or response validation failed."""


@dataclass(frozen=True, slots=True)
class LMStudioModel:
    key: str
    display_name: str
    publisher: str
    model_type: str
    architecture: str | None
    quantization: dict[str, Any] | None
    size_bytes: int
    params_string: str | None
    max_context_length: int | None
    loaded_instance_count: int
    raw_metadata: dict[str, Any]


def _validate_base_url(base_url: str) -> str:
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError as exc:
        raise LMStudioError("Endpoint URL is malformed.") from exc
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise LMStudioError(
            "Only a loopback HTTP LM Studio endpoint is accepted by default; "
            "do not expose the local model server to an untrusted network."
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise LMStudioError("Endpoint URL must not contain credentials, query, or fragment.")
    if parsed.path not in {"", "/"}:
        raise LMStudioError("Endpoint URL must be an origin without a path.")
    # Custom loopback ports are valid; the default port is merely conventional.
    if port is not None and not 1 <= port <= 65535:
        raise LMStudioError("Endpoint port is invalid.")
    return f"http://{parsed.netloc}"


class _NoRedirectHandler(HTTPRedirectHandler):
    """Reject redirects so bearer credentials cannot be forwarded elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LMStudioClient:
    """Read-only client for GET /api/v1/models."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, api_token: str | None = None,
                 timeout: float = 5.0):
        if not 0 < timeout <= 30:
            raise LMStudioError("timeout must be greater than 0 and at most 30 seconds")
        self.base_url = _validate_base_url(base_url)
        self.api_token = api_token
        self.timeout = timeout

    def list_models(self) -> list[LMStudioModel]:
        headers = {"Accept": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        request = Request(f"{self.base_url}/api/v1/models", headers=headers, method="GET")
        try:
            opener = build_opener(_NoRedirectHandler)
            with opener.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            if exc.code == 401:
                raise LMStudioError("LM Studio rejected the API token (HTTP 401).") from exc
            raise LMStudioError(f"LM Studio returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise LMStudioError(f"Cannot reach LM Studio at {self.base_url}: {exc}") from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise LMStudioError("LM Studio response exceeds the 2 MiB safety limit.")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LMStudioError("LM Studio returned invalid UTF-8 JSON.") from exc
        entries = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(entries, list):
            raise LMStudioError("LM Studio response must contain a models array.")
        models: list[LMStudioModel] = []
        for item in entries:
            if not isinstance(item, dict):
                raise LMStudioError("Model entries must be JSON objects.")
            key, display_name = item.get("key"), item.get("display_name")
            model_type, publisher = item.get("type"), item.get("publisher", "")
            size = item.get("size_bytes")
            if not all(isinstance(v, str) and v for v in (key, display_name, model_type)):
                raise LMStudioError("A model is missing key, display_name, or type.")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                raise LMStudioError(f"Model {key!r} has invalid size_bytes.")
            quant = item.get("quantization")
            if quant is not None and not isinstance(quant, dict):
                raise LMStudioError(f"Model {key!r} has invalid quantization metadata.")
            loaded = item.get("loaded_instances", [])
            if not isinstance(loaded, list):
                raise LMStudioError(f"Model {key!r} has invalid loaded_instances.")
            max_context = item.get("max_context_length")
            if max_context is not None and (not isinstance(max_context, int) or max_context < 0):
                raise LMStudioError(f"Model {key!r} has invalid max_context_length.")
            models.append(LMStudioModel(
                key=key, display_name=display_name,
                publisher=publisher if isinstance(publisher, str) else "",
                model_type=model_type, architecture=item.get("architecture"),
                quantization=quant, size_bytes=size,
                params_string=item.get("params_string"),
                max_context_length=max_context, loaded_instance_count=len(loaded),
                raw_metadata=item,
            ))
        return models

    def assimilate_inventory(self, engine: UniversalAssimilationEngine) -> list[Any]:
        """Store model metadata as UAIE records; does not acquire model weights."""
        records = []
        for model in self.list_models():
            payload = {
                "source_system": "LM Studio",
                "source_api": "GET /api/v1/models",
                "model": model.raw_metadata,
                "acquisition_boundary": "metadata_only_no_weights_no_execution",
            }
            records.append(engine.ingest_object(
                payload, source=f"lmstudio://local/api/v1/models/{model.key}"
            ))
        return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uaie-lmstudio",
        description="Read-only LM Studio model inventory adapter for UAIE")
    parser.add_argument("--db", default="uaie.sqlite3")
    parser.add_argument("--url", default=os.environ.get("LM_STUDIO_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--token-env", default="LM_API_TOKEN",
        help="environment variable containing the optional LM Studio API token")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("command", choices=("list", "assimilate"))
    args = parser.parse_args(argv)
    try:
        client = LMStudioClient(args.url, os.environ.get(args.token_env), args.timeout)
        if args.command == "list":
            print(json.dumps([m.raw_metadata for m in client.list_models()], indent=2))
        else:
            engine = UniversalAssimilationEngine(args.db)
            records = client.assimilate_inventory(engine)
            print(json.dumps([r.__dict__ if hasattr(r, "__dict__") else {
                "record_id": r.record_id, "source": r.source, "state": r.state,
                "content_hash": r.content_hash
            } for r in records], indent=2))
        return 0
    except (LMStudioError, UAIEError, OSError) as exc:
        print(f"UAIE LM Studio error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
