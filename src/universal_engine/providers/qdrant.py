"""Optional stdlib REST adapter for Qdrant vector persistence and search."""
from __future__ import annotations

from datetime import datetime, timezone
import ipaddress
import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request as HttpRequest, urlopen

from ..contracts import ProviderRequest, ProviderResult, ResultStatus

_MAX_RESPONSE_BYTES = 1024 * 1024


class QdrantVectorStoreAdapter:
    """Minimal Qdrant REST adapter for point upsert and vector query.

    Plain HTTP is loopback-only. Remote endpoints require HTTPS, an API key,
    and explicit allow_remote=True. Collection creation is intentionally
    outside this adapter's scope.
    """

    provider_id = "qdrant"

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        allow_remote: bool = False,
        timeout_seconds: float = 15.0,
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
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive finite number")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = min(float(timeout_seconds), 120.0)

    def upsert(self, request: ProviderRequest) -> ProviderResult:
        return self.execute(request)

    def search(self, request: ProviderRequest) -> ProviderResult:
        return self.execute(request)

    def execute(self, request: ProviderRequest) -> ProviderResult:
        if not request.policy.allowed:
            return ProviderResult(request.correlation_id, ResultStatus.DENIED, {"reason": request.policy.reason}, "POLICY_DENIED")
        if request.deadline is not None:
            remaining = (request.deadline - datetime.now(timezone.utc)).total_seconds()
            if remaining <= 0:
                return ProviderResult(request.correlation_id, ResultStatus.TIMED_OUT, {}, "DEADLINE_EXPIRED")
            timeout = min(self.timeout_seconds, remaining)
        else:
            timeout = self.timeout_seconds
        try:
            method, url, body = self._build_operation(request)
        except (TypeError, ValueError) as exc:
            return ProviderResult(request.correlation_id, ResultStatus.FAILED, {}, "INVALID_VECTOR_REQUEST", str(exc))
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        outbound = HttpRequest(url, data=json.dumps(body, allow_nan=False).encode("utf-8"), headers=headers, method=method)
        try:
            with urlopen(outbound, timeout=timeout) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(raw) > _MAX_RESPONSE_BYTES:
                return self._failure(request, "UPSTREAM_RESPONSE_TOO_LARGE", "Vector service response exceeded the size limit")
            decoded = json.loads(raw.decode("utf-8"))
            return self._parse_response(request, decoded)
        except HTTPError as exc:
            return self._failure(request, "UPSTREAM_HTTP_ERROR", f"Vector service returned HTTP {exc.code}")
        except (URLError, TimeoutError, OSError):
            return self._failure(request, "UPSTREAM_UNAVAILABLE", "Vector service could not be reached")
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError, IndexError, AttributeError):
            return self._failure(request, "INVALID_UPSTREAM_RESPONSE", "Vector service returned an invalid response")

    def _build_operation(self, request: ProviderRequest) -> tuple[str, str, dict]:
        payload = dict(request.payload)
        collection = payload.get("collection_name")
        if not isinstance(collection, str) or not collection.strip():
            raise ValueError("collection_name is required")
        path = f"{self.base_url}/collections/{quote(collection, safe='')}/points"
        if request.operation == "upsert":
            if set(payload) != {"collection_name", "points"}:
                raise ValueError("upsert accepts only collection_name and points")
            points = payload["points"]
            if not isinstance(points, list) or not points or len(points) > 1000:
                raise ValueError("points must be a non-empty list of at most 1000 items")
            normalized = []
            for point in points:
                if not isinstance(point, dict) or not {"id", "vector"} <= set(point) or not set(point) <= {"id", "vector", "payload"}:
                    raise ValueError("each point requires id and vector, with optional payload")
                point_id = point["id"]
                if isinstance(point_id, bool) or not isinstance(point_id, (int, str)):
                    raise ValueError("point id must be an integer or UUID string")
                vector = point["vector"]
                if not isinstance(vector, list) or not vector:
                    raise ValueError("point vector must be a non-empty list")
                if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) for value in vector):
                    raise ValueError("point vector values must be finite numbers")
                item = {"id": point_id, "vector": vector}
                if "payload" in point:
                    if not isinstance(point["payload"], dict):
                        raise ValueError("point payload must be an object")
                    item["payload"] = point["payload"]
                normalized.append(item)
            return "PUT", path + "?wait=true", {"points": normalized}
        if request.operation == "search":
            allowed = {"collection_name", "vector", "limit", "with_payload"}
            if not set(payload) <= allowed or not {"collection_name", "vector"} <= set(payload):
                raise ValueError("search requires collection_name and vector; unsupported fields supplied")
            vector = payload["vector"]
            if not isinstance(vector, list) or not vector or any(
                not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)
                for value in vector
            ):
                raise ValueError("vector must be a non-empty list of finite numbers")
            limit = payload.get("limit", 10)
            if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
                raise ValueError("limit must be an integer between 1 and 100")
            with_payload = payload.get("with_payload", True)
            if not isinstance(with_payload, bool):
                raise ValueError("with_payload must be a boolean")
            return "POST", path + "/query", {"query": vector, "limit": limit, "with_payload": with_payload}
        raise ValueError("operation must be 'upsert' or 'search'")

    @staticmethod
    def _parse_response(request: ProviderRequest, decoded: object) -> ProviderResult:
        if not isinstance(decoded, dict) or decoded.get("status") != "ok":
            raise ValueError("Qdrant response status is not ok")
        result = decoded.get("result")
        if not isinstance(result, dict):
            raise ValueError("Qdrant response result must be an object")
        if request.operation == "search":
            points = result.get("points")
            if not isinstance(points, list):
                raise ValueError("Qdrant query response has no points list")
            return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, {"points": points})
        return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, {"operation": result})

    @staticmethod
    def _failure(request: ProviderRequest, code: str, message: str) -> ProviderResult:
        return ProviderResult(request.correlation_id, ResultStatus.FAILED, {}, code, message)
