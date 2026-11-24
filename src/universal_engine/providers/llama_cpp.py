"""Optional stdlib HTTP adapter for a local/secured llama.cpp server."""
from __future__ import annotations

from datetime import datetime, timezone
import ipaddress
import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request as HttpRequest, urlopen

from ..contracts import ProviderRequest, ProviderResult, ResultStatus

_MAX_RESPONSE_BYTES = 1024 * 1024
_ALLOWED_PAYLOAD_KEYS = {"model", "messages", "temperature", "top_p", "max_tokens", "stop"}
_ALLOWED_ROLES = {"system", "user", "assistant"}


class LlamaCppInferenceAdapter:
    """Calls llama.cpp's OpenAI-compatible chat-completions endpoint.

    Plain HTTP is permitted only for loopback. Remote endpoints require HTTPS,
    an API key, and explicit allow_remote=True. Server-side tools are not
    enabled by this adapter.
    """

    provider_id = "llama.cpp"

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        allow_remote: bool = False,
        timeout_seconds: float = 30.0,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("base_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("base_url must not contain credentials, query, or fragment")
        try:
            is_loopback = parsed.hostname.lower() == "localhost" or ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            is_loopback = parsed.hostname.lower() == "localhost"
        if parsed.scheme == "http" and not is_loopback:
            raise ValueError("plain HTTP is allowed only for loopback endpoints")
        if not is_loopback and (not allow_remote or parsed.scheme != "https" or not api_key):
            raise ValueError("remote endpoints require HTTPS, an API key, and allow_remote=True")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive finite number")
        self.endpoint = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.timeout_seconds = min(timeout_seconds, 120.0)

    def generate(self, request: ProviderRequest) -> ProviderResult:
        return self.execute(request)

    def execute(self, request: ProviderRequest) -> ProviderResult:
        if not request.policy.allowed:
            return ProviderResult(
                request.correlation_id, ResultStatus.DENIED,
                {"reason": request.policy.reason}, "POLICY_DENIED",
            )
        if request.deadline is not None:
            remaining = (request.deadline - datetime.now(timezone.utc)).total_seconds()
            if remaining <= 0:
                return ProviderResult(
                    request.correlation_id, ResultStatus.TIMED_OUT, {},
                    "DEADLINE_EXPIRED",
                )
            timeout = min(self.timeout_seconds, remaining)
        else:
            timeout = self.timeout_seconds

        try:
            body = self._build_body(request)
        except (TypeError, ValueError) as exc:
            return ProviderResult(
                request.correlation_id, ResultStatus.FAILED, {},
                "INVALID_INFERENCE_REQUEST", str(exc),
            )

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        outbound = HttpRequest(
            self.endpoint,
            data=json.dumps(body, allow_nan=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(outbound, timeout=timeout) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(raw) > _MAX_RESPONSE_BYTES:
                return self._failure(request, "UPSTREAM_RESPONSE_TOO_LARGE", "Inference response exceeded the size limit")
            decoded = json.loads(raw.decode("utf-8"))
            return self._parse_response(request, decoded)
        except HTTPError as exc:
            return self._failure(request, "UPSTREAM_HTTP_ERROR", f"Inference server returned HTTP {exc.code}")
        except (URLError, TimeoutError, OSError):
            return self._failure(request, "UPSTREAM_UNAVAILABLE", "Inference server could not be reached")
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError, IndexError, AttributeError):
            return self._failure(request, "INVALID_UPSTREAM_RESPONSE", "Inference server returned an invalid response")

    @staticmethod
    def _build_body(request: ProviderRequest) -> dict:
        if request.operation != "generate":
            raise ValueError("operation must be 'generate'")
        payload = dict(request.payload)
        unknown = set(payload) - _ALLOWED_PAYLOAD_KEYS
        if unknown:
            raise ValueError(f"unsupported inference payload fields: {', '.join(sorted(unknown))}")
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("payload.messages must be a non-empty list")
        normalized = []
        for message in messages:
            if not isinstance(message, dict) or set(message) != {"role", "content"}:
                raise ValueError("each message must contain only role and content")
            if message["role"] not in _ALLOWED_ROLES or not isinstance(message["content"], str):
                raise ValueError("message role/content is invalid")
            normalized.append({"role": message["role"], "content": message["content"]})
        body = {"model": payload.get("model", "local-model"), "messages": normalized}
        if not isinstance(body["model"], str) or not body["model"].strip():
            raise ValueError("model must be a non-empty string")
        for key in ("temperature", "top_p"):
            if key in payload:
                value = payload[key]
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                    raise ValueError(f"{key} must be a finite number")
                body[key] = value
        if "max_tokens" in payload:
            value = payload["max_tokens"]
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError("max_tokens must be a positive integer")
            body["max_tokens"] = value
        if "stop" in payload:
            stop = payload["stop"]
            if not (isinstance(stop, str) or isinstance(stop, list) and all(isinstance(x, str) for x in stop)):
                raise ValueError("stop must be a string or list of strings")
            body["stop"] = stop
        return body

    @staticmethod
    def _parse_response(request: ProviderRequest, decoded: object) -> ProviderResult:
        if not isinstance(decoded, dict):
            raise ValueError("response root must be an object")
        choices = decoded["choices"]
        if not isinstance(choices, list) or not choices:
            raise ValueError("response choices must be a non-empty list")
        message = choices[0]["message"]
        text = message["content"]
        if not isinstance(text, str):
            raise ValueError("response content must be text")
        output = {"text": text, "model": decoded.get("model", "unknown")}
        usage = decoded.get("usage")
        if isinstance(usage, dict):
            output["usage"] = usage
        return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, output)

    @staticmethod
    def _failure(request: ProviderRequest, code: str, message: str) -> ProviderResult:
        return ProviderResult(request.correlation_id, ResultStatus.FAILED, {}, code, message)
