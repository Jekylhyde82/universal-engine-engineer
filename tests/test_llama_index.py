import unittest
from types import SimpleNamespace
from uuid import uuid4

from universal_engine.contracts import PolicyDecision, ProviderRequest, ResultStatus
from universal_engine.providers.llama_index import LlamaIndexKnowledgeAdapter


class FakeDocument:
    def __init__(self, *, text, metadata):
        self.text = text
        self.metadata = metadata


class FakeNode:
    def __init__(self, text, metadata=None):
        self.text = text
        self.metadata = metadata or {}
    def get_content(self):
        return self.text


class FakeRetriever:
    def __init__(self, nodes):
        self.nodes = nodes
    def retrieve(self, query):
        return self.nodes


class FakeIndex:
    def __init__(self):
        self.documents = []
        self.nodes = [SimpleNamespace(node=FakeNode("retrieved context", {"source": "test"}), score=0.91)]
        self.requested_top_k = None
        self.last_query = None
    def insert(self, document):
        self.documents.append(document)
    def as_retriever(self, *, similarity_top_k):
        self.requested_top_k = similarity_top_k
        return FakeRetriever(self.nodes)


class LlamaIndexAdapterTests(unittest.TestCase):
    def make_request(self, operation, payload, policy=None):
        return ProviderRequest(
            correlation_id=str(uuid4()),
            capability_id="knowledge.llamaindex",
            operation=operation,
            payload=payload,
            policy=policy or PolicyDecision(True, "approved", "test-policy"),
        )

    def test_ingests_documents_with_metadata(self):
        index = FakeIndex()
        adapter = LlamaIndexKnowledgeAdapter(index, document_factory=FakeDocument)
        request = self.make_request("ingest", {"documents": [{"text": "document text", "metadata": {"source": "test"}}]})
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(result.output["inserted"], 1)
        self.assertEqual(index.documents[0].metadata["source"], "test")

    def test_retrieves_nodes_without_calling_llm(self):
        index = FakeIndex()
        adapter = LlamaIndexKnowledgeAdapter(index, document_factory=FakeDocument)
        request = self.make_request("retrieve", {"query": "find context", "limit": 3})
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(result.output["nodes"][0]["text"], "retrieved context")
        self.assertEqual(index.requested_top_k, 3)

    def test_denied_request_never_touches_index(self):
        index = FakeIndex()
        adapter = LlamaIndexKnowledgeAdapter(index, document_factory=FakeDocument)
        request = self.make_request("ingest", {"documents": [{"text": "blocked"}]}, PolicyDecision(False, "denied", "deny"))
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.DENIED)
        self.assertEqual(index.documents, [])

    def test_rejects_empty_document_batch(self):
        adapter = LlamaIndexKnowledgeAdapter(FakeIndex(), document_factory=FakeDocument)
        result = adapter.execute(self.make_request("ingest", {"documents": []}))
        self.assertEqual(result.error_code, "INVALID_KNOWLEDGE_REQUEST")

    def test_rejects_invalid_retrieval_limit(self):
        adapter = LlamaIndexKnowledgeAdapter(FakeIndex(), document_factory=FakeDocument)
        result = adapter.execute(self.make_request("retrieve", {"query": "x", "limit": 0}))
        self.assertEqual(result.error_code, "INVALID_KNOWLEDGE_REQUEST")

    def test_requires_index_contract(self):
        with self.assertRaises(ValueError):
            LlamaIndexKnowledgeAdapter(object())


if __name__ == "__main__":
    unittest.main()
