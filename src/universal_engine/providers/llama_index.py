"""Optional LlamaIndex adapter around an injected index instance."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from ..contracts import ProviderRequest, ProviderResult, ResultStatus


class LlamaIndexKnowledgeAdapter:
    """Ingests documents and retrieves nodes using an existing LlamaIndex index.

    The index, embedding model and vector-store configuration are constructed
    by the application and injected here. The adapter does not select a model,
    create a collection, or silently install integrations.
    """

    provider_id = "llamaindex"

    def __init__(self, index: Any, *, document_factory: Callable[..., Any] | None = None) -> None:
        if not callable(getattr(index, "insert", None)) or not callable(getattr(index, "as_retriever", None)):
            raise ValueError("index must provide insert() and as_retriever()")
        self.index = index
        self.document_factory = document_factory

    def ingest(self, request: ProviderRequest) -> ProviderResult:
        return self.execute(request)

    def retrieve(self, request: ProviderRequest) -> ProviderResult:
        return self.execute(request)

    def execute(self, request: ProviderRequest) -> ProviderResult:
        if not request.policy.allowed:
            return ProviderResult(request.correlation_id, ResultStatus.DENIED, {"reason": request.policy.reason}, "POLICY_DENIED")
        if request.deadline is not None and request.deadline <= datetime.now(timezone.utc):
            return ProviderResult(request.correlation_id, ResultStatus.TIMED_OUT, {}, "DEADLINE_EXPIRED")
        try:
            if request.operation == "ingest":
                return self._ingest(request)
            if request.operation == "retrieve":
                return self._retrieve(request)
            raise ValueError("operation must be 'ingest' or 'retrieve'")
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            return ProviderResult(request.correlation_id, ResultStatus.FAILED, {}, "INVALID_KNOWLEDGE_REQUEST", str(exc))
        except Exception:
            return ProviderResult(request.correlation_id, ResultStatus.FAILED, {}, "KNOWLEDGE_OPERATION_FAILED", "LlamaIndex operation failed")

    def _document_type(self):
        if self.document_factory is not None:
            return self.document_factory
        try:
            from llama_index.core import Document
        except ImportError as exc:
            raise RuntimeError("install the selected llama-index-core package to ingest documents") from exc
        return Document

    def _ingest(self, request: ProviderRequest) -> ProviderResult:
        payload = dict(request.payload)
        if set(payload) != {"documents"}:
            raise ValueError("ingest accepts only a documents field")
        documents = payload["documents"]
        if not isinstance(documents, list) or not documents or len(documents) > 100:
            raise ValueError("documents must be a non-empty list of at most 100 items")
        document_type = self._document_type()
        inserted = 0
        for item in documents:
            if not isinstance(item, dict) or not set(item) <= {"text", "metadata"} or "text" not in item:
                raise ValueError("each document requires text and optional metadata")
            if not isinstance(item["text"], str) or not item["text"].strip():
                raise ValueError("document text must be a non-empty string")
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError("document metadata must be an object")
            document = document_type(text=item["text"], metadata=metadata)
            self.index.insert(document)
            inserted += 1
        return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, {"inserted": inserted})

    def _retrieve(self, request: ProviderRequest) -> ProviderResult:
        payload = dict(request.payload)
        if not set(payload) <= {"query", "limit"} or "query" not in payload:
            raise ValueError("retrieve requires query and optional limit")
        query = payload["query"]
        limit = payload.get("limit", 5)
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 20:
            raise ValueError("limit must be an integer between 1 and 20")
        retriever = self.index.as_retriever(similarity_top_k=limit)
        nodes = retriever.retrieve(query)
        if not isinstance(nodes, list):
            raise ValueError("retriever must return a list")
        results = []
        for item in nodes:
            node = getattr(item, "node", item)
            text = node.get_content() if callable(getattr(node, "get_content", None)) else getattr(node, "text", None)
            if not isinstance(text, str):
                continue
            score = getattr(item, "score", None)
            metadata = getattr(node, "metadata", {})
            results.append({"text": text, "score": score, "metadata": metadata if isinstance(metadata, dict) else {}})
        return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, {"nodes": results})
