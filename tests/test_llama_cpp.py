import json
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4

from universal_engine.contracts import PolicyDecision, ProviderRequest, ResultStatus
from universal_engine.providers.llama_cpp import LlamaCppInferenceAdapter


class StubHandler(BaseHTTPRequestHandler):
    status_code = 200
    response_body = {"choices": [{"message": {"content": "hello from local model"}}], "model": "stub", "usage": {"total_tokens": 3}}
    request_count = 0
    last_body = None
    last_auth = None

    def do_POST(self):
        type(self).request_count += 1
        length = int(self.headers.get("Content-Length", "0"))
        type(self).last_body = json.loads(self.rfile.read(length))
        type(self).last_auth = self.headers.get("Authorization")
        raw = json.dumps(type(self).response_body).encode()
        self.send_response(type(self).status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format, *args):
        pass


class LlamaCppAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), StubHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=2)
        cls.server.server_close()

    def setUp(self):
        StubHandler.status_code = 200
        StubHandler.response_body = {"choices": [{"message": {"content": "hello from local model"}}], "model": "stub", "usage": {"total_tokens": 3}}
        StubHandler.request_count = 0
        StubHandler.last_body = None
        StubHandler.last_auth = None

    def make_request(self, **overrides):
        values = dict(
            correlation_id=str(uuid4()),
            capability_id="inference.llama",
            operation="generate",
            payload={"messages": [{"role": "user", "content": "hello"}]},
            policy=PolicyDecision(True, "approved", "test-policy"),
        )
        values.update(overrides)
        return ProviderRequest(**values)

    def test_local_chat_completion(self):
        adapter = LlamaCppInferenceAdapter(self.base_url)
        result = adapter.execute(self.make_request())
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(result.output["text"], "hello from local model")
        self.assertEqual(StubHandler.last_body["messages"][0]["content"], "hello")

    def test_optional_api_key_is_sent_as_bearer(self):
        adapter = LlamaCppInferenceAdapter(self.base_url, api_key="test-secret")
        adapter.execute(self.make_request())
        self.assertEqual(StubHandler.last_auth, "Bearer test-secret")

    def test_denied_request_never_calls_server(self):
        adapter = LlamaCppInferenceAdapter(self.base_url)
        request = self.make_request(policy=PolicyDecision(False, "denied", "deny"))
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.DENIED)
        self.assertEqual(StubHandler.request_count, 0)

    def test_invalid_payload_is_rejected_before_network(self):
        adapter = LlamaCppInferenceAdapter(self.base_url)
        result = adapter.execute(self.make_request(payload={"messages": []}))
        self.assertEqual(result.error_code, "INVALID_INFERENCE_REQUEST")
        self.assertEqual(StubHandler.request_count, 0)

    def test_remote_http_is_rejected(self):
        with self.assertRaises(ValueError):
            LlamaCppInferenceAdapter("http://example.com/v1")

    def test_remote_https_requires_explicit_opt_in_and_key(self):
        with self.assertRaises(ValueError):
            LlamaCppInferenceAdapter("https://example.com/v1")
        with self.assertRaises(ValueError):
            LlamaCppInferenceAdapter("https://example.com/v1", api_key="secret")
        adapter = LlamaCppInferenceAdapter("https://example.com/v1", api_key="secret", allow_remote=True)
        self.assertTrue(adapter.endpoint.endswith("/chat/completions"))

    def test_http_error_is_sanitized(self):
        StubHandler.status_code = 503
        result = LlamaCppInferenceAdapter(self.base_url).execute(self.make_request())
        self.assertEqual(result.status, ResultStatus.FAILED)
        self.assertEqual(result.error_code, "UPSTREAM_HTTP_ERROR")
        self.assertNotIn("secret", result.error_message)

    def test_expired_request_deadline_times_out(self):
        request = self.make_request(deadline=datetime.now(timezone.utc) + timedelta(milliseconds=2))
        import time
        time.sleep(0.01)
        result = LlamaCppInferenceAdapter(self.base_url).execute(request)
        self.assertEqual(result.status, ResultStatus.TIMED_OUT)


if __name__ == "__main__":
    unittest.main()
