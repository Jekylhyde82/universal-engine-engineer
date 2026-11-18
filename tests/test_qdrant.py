import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4

from universal_engine.contracts import PolicyDecision, ProviderRequest, ResultStatus
from universal_engine.providers.qdrant import QdrantVectorStoreAdapter


class QdrantStubHandler(BaseHTTPRequestHandler):
    status_code = 200
    response_body = {"status": "ok", "result": {"status": "completed", "operation_id": 1}}
    request_count = 0
    last_method = None
    last_path = None
    last_body = None
    last_api_key = None

    def _handle(self):
        type(self).request_count += 1
        type(self).last_method = self.command
        type(self).last_path = self.path
        type(self).last_api_key = self.headers.get("api-key")
        length = int(self.headers.get("Content-Length", "0"))
        type(self).last_body = json.loads(self.rfile.read(length))
        raw = json.dumps(type(self).response_body).encode()
        self.send_response(type(self).status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_PUT = _handle
    do_POST = _handle

    def log_message(self, format, *args):
        pass


class QdrantAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), QdrantStubHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=2)
        cls.server.server_close()

    def setUp(self):
        QdrantStubHandler.status_code = 200
        QdrantStubHandler.response_body = {"status": "ok", "result": {"status": "completed", "operation_id": 1}}
        QdrantStubHandler.request_count = 0
        QdrantStubHandler.last_method = None
        QdrantStubHandler.last_path = None
        QdrantStubHandler.last_body = None
        QdrantStubHandler.last_api_key = None

    def make_request(self, operation, payload, policy=None):
        return ProviderRequest(
            correlation_id=str(uuid4()),
            capability_id="vector.qdrant",
            operation=operation,
            payload=payload,
            policy=policy or PolicyDecision(True, "approved", "test-policy"),
        )

    def test_upsert_uses_wait_true(self):
        adapter = QdrantVectorStoreAdapter(self.base_url)
        request = self.make_request("upsert", {"collection_name": "docs", "points": [{"id": 1, "vector": [0.1, 0.2], "payload": {"text": "hello"}}]})
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(QdrantStubHandler.last_method, "PUT")
        self.assertTrue(QdrantStubHandler.last_path.endswith("/points?wait=true"))

    def test_query_points_endpoint(self):
        QdrantStubHandler.response_body = {"status": "ok", "result": {"points": [{"id": 1, "score": 0.9, "payload": {"text": "hello"}}]}}
        adapter = QdrantVectorStoreAdapter(self.base_url)
        request = self.make_request("search", {"collection_name": "docs", "vector": [0.1, 0.2], "limit": 5})
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(result.output["points"][0]["score"], 0.9)
        self.assertTrue(QdrantStubHandler.last_path.endswith("/points/query"))

    def test_api_key_header(self):
        adapter = QdrantVectorStoreAdapter(self.base_url, api_key="test-key")
        request = self.make_request("search", {"collection_name": "docs", "vector": [0.1]})
        adapter.execute(request)
        self.assertEqual(QdrantStubHandler.last_api_key, "test-key")

    def test_denied_request_never_calls_server(self):
        adapter = QdrantVectorStoreAdapter(self.base_url)
        request = self.make_request("search", {"collection_name": "docs", "vector": [0.1]}, PolicyDecision(False, "denied", "deny"))
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.DENIED)
        self.assertEqual(QdrantStubHandler.request_count, 0)

    def test_invalid_vector_is_rejected_before_network(self):
        adapter = QdrantVectorStoreAdapter(self.base_url)
        request = self.make_request("search", {"collection_name": "docs", "vector": ["not-a-number"]})
        result = adapter.execute(request)
        self.assertEqual(result.error_code, "INVALID_VECTOR_REQUEST")
        self.assertEqual(QdrantStubHandler.request_count, 0)

    def test_remote_http_is_rejected(self):
        with self.assertRaises(ValueError):
            QdrantVectorStoreAdapter("http://example.com")

    def test_remote_https_requires_explicit_opt_in_and_key(self):
        with self.assertRaises(ValueError):
            QdrantVectorStoreAdapter("https://example.com")
        adapter = QdrantVectorStoreAdapter("https://example.com", api_key="secret", allow_remote=True)
        self.assertTrue(adapter.base_url.startswith("https://"))


if __name__ == "__main__":
    unittest.main()
