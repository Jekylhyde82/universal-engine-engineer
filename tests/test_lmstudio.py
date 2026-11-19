import json
import tempfile
import unittest
from pathlib import Path

from universal_engine.afi import AFIPrimeFusionAdapter
from universal_engine.lmstudio import (
    LMStudioError, assimilate_catalog, download_model, get_download_status, list_models,
)
from universal_engine.uaie import UniversalAssimilationEngine


MODEL = {
    "type": "llm",
    "publisher": "lmstudio-community",
    "key": "publisher/example-7b",
    "display_name": "Example 7B",
    "architecture": "llama",
    "quantization": {"name": "Q4_K_M", "bits_per_weight": 4},
    "size_bytes": 4_200_000_000,
    "params_string": "7B",
    "max_context_length": 32768,
    "format": "gguf",
    "capabilities": {"vision": False, "trained_for_tool_use": True},
    "description": "Fixture model",
    "variants": ["Q4_K_M", "Q5_K_M"],
    "selected_variant": "Q4_K_M",
    "loaded_instances": [],
}


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body[:size]


class RedirectResponse(FakeResponse):
    def geturl(self):
        return "https://attacker.example/collect"


class LMStudioAdapterTests(unittest.TestCase):
    def opener_for(self, payload):
        body = json.dumps(payload).encode()
        return lambda request, timeout: FakeResponse(body)

    def test_reads_native_v1_inventory_and_maps_capabilities(self):
        models = list_models(opener=self.opener_for({"models": [MODEL]}))
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].key, MODEL["key"])
        self.assertEqual(models[0].quantization["name"], "Q4_K_M")
        self.assertTrue(models[0].capabilities["trained_for_tool_use"])

    def test_sends_bearer_token_without_exposing_it_in_result(self):
        seen = {}
        def opener(request, timeout):
            seen["authorization"] = request.get_header("Authorization")
            return FakeResponse(json.dumps({"models": []}).encode())
        self.assertEqual(list_models(api_token="secret-test-token", opener=opener), ())
        self.assertEqual(seen["authorization"], "Bearer secret-test-token")

    def test_rejects_redirects_away_from_loopback_for_all_api_calls(self):
        opener = lambda request, timeout: RedirectResponse(b'{"models":[]}')
        with self.assertRaises(LMStudioError):
            list_models(opener=opener)
        with self.assertRaises(LMStudioError):
            download_model("publisher/model", approved=True, opener=opener)
        with self.assertRaises(LMStudioError):
            get_download_status("job_123", opener=opener)

    def test_rejects_non_loopback_endpoint(self):
        with self.assertRaises(LMStudioError):
            list_models("http://example.com:1234", opener=self.opener_for({"models": []}))

    def test_rejects_url_credentials_and_query(self):
        for url in ("http://user:pass@127.0.0.1:1234", "http://127.0.0.1:1234?x=1"):
            with self.subTest(url=url), self.assertRaises(LMStudioError):
                list_models(url, opener=self.opener_for({"models": []}))

    def test_rejects_malformed_catalog_shape_and_model(self):
        for payload in ([], {"data": []}, {"models": [dict(MODEL, type="unknown")]}):
            with self.subTest(payload=payload), self.assertRaises(LMStudioError):
                list_models(opener=self.opener_for(payload))

    def test_rejects_duplicate_keys(self):
        with self.assertRaises(LMStudioError):
            list_models(opener=self.opener_for({"models": [MODEL, MODEL]}))

    def test_enforces_response_size_limit(self):
        with self.assertRaises(LMStudioError):
            list_models(max_response_bytes=2, opener=self.opener_for({"models": []}))

    def test_download_requires_explicit_approval_before_network_call(self):
        called = {"value": False}
        def opener(request, timeout):
            called["value"] = True
            return FakeResponse(b'{"job_id":"job_123","status":"downloading"}')
        with self.assertRaises(LMStudioError):
            download_model("publisher/model", approved=False, opener=opener)
        self.assertFalse(called["value"])

    def test_download_uses_official_api_and_returns_job(self):
        seen = {}
        def opener(request, timeout):
            seen["method"] = request.get_method()
            seen["url"] = request.full_url
            seen["body"] = json.loads(request.data.decode())
            seen["authorization"] = request.get_header("Authorization")
            return FakeResponse(json.dumps({
                "job_id": "job_493c7c9ded", "status": "downloading",
                "total_size_bytes": 123456, "started_at": "2026-11-20T00:00:00Z"
            }).encode())
        job = download_model("publisher/model", approved=True, api_token="test-token", opener=opener)
        self.assertEqual(job.status, "downloading")
        self.assertEqual(job.total_size_bytes, 123456)
        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["url"], "http://127.0.0.1:1234/api/v1/models/download")
        self.assertEqual(seen["body"], {"model": "publisher/model"})
        self.assertEqual(seen["authorization"], "Bearer test-token")

    def test_quantization_requires_exact_huggingface_url(self):
        with self.assertRaises(LMStudioError):
            download_model("publisher/model", approved=True, quantization="Q4_K_M",
                           opener=self.opener_for({"job_id": "job_1", "status": "downloading"}))
        seen = {}
        def opener(request, timeout):
            seen["body"] = json.loads(request.data.decode())
            return FakeResponse(b'{"status":"already_downloaded"}')
        job = download_model(
            "https://huggingface.co/publisher/model-GGUF", approved=True,
            quantization="Q4_K_M", opener=opener)
        self.assertEqual(job.status, "already_downloaded")
        self.assertIsNone(job.job_id)
        self.assertEqual(seen["body"]["quantization"], "Q4_K_M")

    def test_download_status_reads_existing_job(self):
        seen = {}
        def opener(request, timeout):
            seen["method"] = request.get_method()
            seen["url"] = request.full_url
            return FakeResponse(b'{"job_id":"job_123","status":"completed","completed_at":"2026-11-20T00:01:00Z"}')
        job = get_download_status("job_123", opener=opener)
        self.assertEqual(job.status, "completed")
        self.assertEqual(seen["method"], "GET")
        self.assertTrue(seen["url"].endswith("/api/v1/models/download/status/job_123"))

    def test_rejects_invalid_download_job_id(self):
        with self.assertRaises(LMStudioError):
            get_download_status("../admin", opener=self.opener_for({"status": "completed"}))

    def test_assimilates_metadata_into_uaie_without_model_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = UniversalAssimilationEngine(Path(tmp) / "uaie.sqlite3")
            def opener(request, timeout):
                return FakeResponse(json.dumps({"models": [MODEL]}).encode())
            result = assimilate_catalog(engine, api_token=None, timeout=3, opener=opener)
            self.assertEqual(len(result.model_records), 1)
            self.assertEqual(len(result.afi_profile_records), 1)
            self.assertEqual(result.model_records[0].state, "assimilated")
            profile = engine.export_record(result.afi_profile_records[0].record_id)
            self.assertEqual(profile["source"], "afi-prime://lm-studio-model-catalog/publisher/example-7b")
            self.assertIn("tool_use_training", profile["extracted_text"])
            self.assertIn("METADATA_ONLY_NOT_BENCHMARKED", profile["extracted_text"])

    def test_afi_extracts_only_explicit_publisher_capability_facts(self):
        from universal_engine.lmstudio import _parse_model
        model = _parse_model(MODEL)
        profile = AFIPrimeFusionAdapter.fuse_model(model)
        self.assertIn("tool_use_training", profile.capability_facts)
        self.assertNotIn("vision_input", profile.capability_facts)
        self.assertFalse(profile.performance_verified)
        self.assertFalse(profile.integration_approved)
        self.assertEqual(profile.evidence_class, "PUBLISHER_REPORTED_METADATA")

    def test_catalog_metadata_can_be_stored_as_provenance_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = UniversalAssimilationEngine(Path(tmp) / "uaie.sqlite3")
            record = engine.ingest_object(MODEL, source="http://127.0.0.1:1234/api/v1/models#publisher/example-7b")
            self.assertEqual(record.state, "assimilated")
            self.assertIn("capability", record.signals)
            self.assertEqual(engine.export_record(record.record_id)["source"],
                             "http://127.0.0.1:1234/api/v1/models#publisher/example-7b")


if __name__ == "__main__":
    unittest.main()
