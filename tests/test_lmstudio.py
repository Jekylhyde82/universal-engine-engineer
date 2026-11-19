import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from universal_engine.lmstudio import LMStudioClient, LMStudioError
from universal_engine.uaie import UniversalAssimilationEngine


SAMPLE = {"models": [{
    "type": "llm", "publisher": "example", "key": "example/model",
    "display_name": "Example Model", "architecture": "example-arch",
    "quantization": {"name": "Q4_K_M", "bits_per_weight": 4},
    "size_bytes": 1024, "params_string": "1B",
    "loaded_instances": [{"id": "example/model", "config": {"context_length": 4096}}],
    "max_context_length": 8192
}]}


class FakeResponse:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit=-1):
        return self.body[:limit]


class FakeOpener:
    def __init__(self, response):
        self.response = response
    def open(self, request, timeout=0):
        self.request = request
        self.timeout = timeout
        return self.response


class LMStudioTests(unittest.TestCase):
    def test_loopback_only_by_default(self):
        for url in ("https://127.0.0.1:1234", "http://192.168.1.5:1234",
                    "http://user:pass@127.0.0.1:1234", "http://127.0.0.1:1234/path",
                    "http://127.0.0.1:bad"):
            with self.subTest(url=url), self.assertRaises(LMStudioError):
                LMStudioClient(url)

    def test_validates_timeout(self):
        with self.assertRaises(LMStudioError):
            LMStudioClient(timeout=0)

    @patch("universal_engine.lmstudio.build_opener")
    def test_lists_and_parses_models(self, mocked):
        mocked.return_value = FakeOpener(FakeResponse(json.dumps(SAMPLE).encode()))
        models = LMStudioClient().list_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].key, "example/model")
        self.assertEqual(models[0].loaded_instance_count, 1)
        request = mocked.return_value.request
        self.assertEqual(request.full_url, "http://127.0.0.1:1234/api/v1/models")
        self.assertEqual(mocked.return_value.timeout, 5.0)

    @patch("universal_engine.lmstudio.build_opener")
    def test_sends_optional_bearer_token(self, mocked):
        mocked.return_value = FakeOpener(FakeResponse(json.dumps({"models": []}).encode()))
        LMStudioClient(api_token="secret-token").list_models()
        self.assertEqual(mocked.return_value.request.get_header("Authorization"),
                         "Bearer secret-token")

    @patch("universal_engine.lmstudio.build_opener")
    def test_rejects_malformed_payload(self, mocked):
        mocked.return_value = FakeOpener(FakeResponse(b'{"wrong": []}'))
        with self.assertRaises(LMStudioError):
            LMStudioClient().list_models()

    @patch("universal_engine.lmstudio.build_opener")
    def test_rejects_invalid_model_metadata(self, mocked):
        mocked.return_value = FakeOpener(FakeResponse(json.dumps({"models": [{"key": "bad"}]}).encode()))
        with self.assertRaises(LMStudioError):
            LMStudioClient().list_models()

    @patch("universal_engine.lmstudio.build_opener")
    def test_assimilates_metadata_into_uaie_without_weights(self, mocked):
        mocked.return_value = FakeOpener(FakeResponse(json.dumps(SAMPLE).encode()))
        with tempfile.TemporaryDirectory() as tmp:
            engine = UniversalAssimilationEngine(Path(tmp) / "uaie.sqlite3")
            records = LMStudioClient().assimilate_inventory(engine)
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0].source.startswith("lmstudio://local/"))
            exported = engine.export_record(records[0].record_id)
            self.assertIn("metadata_only_no_weights_no_execution", exported["content"])


if __name__ == "__main__":
    unittest.main()
