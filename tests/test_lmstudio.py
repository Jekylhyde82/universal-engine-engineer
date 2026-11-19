import json
import tempfile
import unittest
from pathlib import Path

from universal_engine.afi import AFIPrimeFusionAdapter
from universal_engine.lmstudio import (
    LMStudioError, assimilate_catalog, list_models,
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
