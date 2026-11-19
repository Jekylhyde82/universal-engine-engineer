import tempfile
import unittest
from pathlib import Path

from universal_engine.lmstudio_catalog import (
    LMStudioCatalogError, assimilate_catalog_candidate,
    build_download_command, candidate_from_mapping,
)
from universal_engine.uaie import UniversalAcquisitionIntegrationEngine


CANDIDATE = {
    "model_id": "liquid/lfm3-vl-2b",
    "original_idea_value": "Use UAIE PRIME and AFI PRIME to assimilate LM Studio model-catalog capabilities.",
    "display_name": "LFM3",
    "catalog_url": "https://lmstudio.ai/models/lfm3",
    "publisher": "Liquid AI",
    "parameter_sizes": ["1.92B", "2B"],
    "max_context": "128K",
    "minimum_memory": "1 GB",
    "availability": ["local"],
    "capabilities": {"tool_use": True, "reasoning": True, "vision": True},
    "license_text": "LFM Open License v1.0",
    "description": "Vision-language model for on-device understanding.",
    "artifact_links": [
        {"text": "LFM3-VL-2B", "url": "https://huggingface.co/liquid-ai/lfm3-vl-2b"}
    ],
    "metadata": {"catalog_source": "LM Studio", "notes": "User-reviewed catalog details"},
}


class CatalogCandidateTests(unittest.TestCase):
    def test_validates_user_supplied_catalog_candidate(self):
        candidate = candidate_from_mapping(CANDIDATE)
        self.assertEqual(candidate.model_id, "liquid/lfm3-vl-2b")
        self.assertEqual(candidate.capabilities["vision"], True)
        self.assertEqual(candidate.license_text, "LFM Open License v1.0")

    def test_builds_official_cli_command_without_executing_it(self):
        candidate = candidate_from_mapping({**CANDIDATE, "quantization": "Q4_K_M"})
        self.assertEqual(build_download_command(candidate), ("lms", "get", "liquid/lfm3-vl-2b@Q4_K_M"))

    def test_download_command_without_quantization(self):
        candidate = candidate_from_mapping(CANDIDATE)
        self.assertEqual(build_download_command(candidate), ("lms", "get", "liquid/lfm3-vl-2b"))

    def test_rejects_non_lmstudio_catalog_origin(self):
        with self.assertRaises(LMStudioCatalogError):
            candidate_from_mapping({**CANDIDATE, "catalog_url": "https://example.com/models/lfm3"})

    def test_rejects_query_credentials_and_wrong_path(self):
        bad_urls = (
            "https://user:pass@lmstudio.ai/models/lfm3",
            "https://lmstudio.ai/models/lfm3?x=1",
            "https://lmstudio.ai/other/lfm3",
        )
        for url in bad_urls:
            with self.subTest(url=url), self.assertRaises(LMStudioCatalogError):
                candidate_from_mapping({**CANDIDATE, "catalog_url": url})

    def test_original_idea_value_is_mandatory(self):
        candidate = dict(CANDIDATE)
        candidate.pop("original_idea_value")
        with self.assertRaises(LMStudioCatalogError):
            candidate_from_mapping(candidate)

    def test_rejects_invalid_model_id_and_quantization(self):
        for candidate in (
            {**CANDIDATE, "model_id": "not-a-qualified-id"},
            {**CANDIDATE, "quantization": "Q4_K_M;rm -rf"},
        ):
            with self.subTest(candidate=candidate), self.assertRaises(LMStudioCatalogError):
                candidate_from_mapping(candidate)

    def test_rejects_unapproved_capabilities_and_artifact_origins(self):
        for candidate in (
            {**CANDIDATE, "capabilities": {"tool_use": "yes"}},
            {**CANDIDATE, "artifact_links": [{"url": "https://example.com/file"}]},
        ):
            with self.subTest(candidate=candidate), self.assertRaises(LMStudioCatalogError):
                candidate_from_mapping(candidate)

    def test_rejects_secret_material_in_metadata(self):
        with self.assertRaises(LMStudioCatalogError):
            candidate_from_mapping({**CANDIDATE, "metadata": {"nested": {"api_token": "do-not-store"}}})

    def test_rejects_oversized_or_non_json_metadata(self):
        for metadata in ({"payload": "x" * (256 * 1024)}, {"value": float("nan")}):
            with self.subTest(metadata_type=type(metadata["payload"] if "payload" in metadata else metadata["value"])), self.assertRaises(LMStudioCatalogError):
                candidate_from_mapping({**CANDIDATE, "metadata": metadata})

    def test_assimilates_candidate_and_fuses_afi_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = UniversalAcquisitionIntegrationEngine(Path(tmp) / "uaie.sqlite3")
            candidate = candidate_from_mapping(CANDIDATE)
            catalog_record, afi_record, register_entry = assimilate_catalog_candidate(engine, candidate)
            self.assertEqual(catalog_record.state, "assimilated")
            profile = engine.export_record(afi_record.record_id)
            self.assertEqual(profile["source"], "afi-prime://lm-studio-model-catalog/liquid/lfm3-vl-2b")
            self.assertIn("tool_use_listed_in_catalog", profile["extracted_text"])
            self.assertIn("USER_SUPPLIED_CATALOG_METADATA", profile["extracted_text"])
            self.assertIn("METADATA_ONLY_NOT_BENCHMARKED", profile["extracted_text"])
            self.assertIn("LFM Open License v1.0", profile["extracted_text"])
            self.assertIn("1 GB", profile["extracted_text"])
            candidate_data = engine.export_record(catalog_record.record_id)
            self.assertIn("original_idea_value", candidate_data["extracted_text"])
            self.assertIn("NOT_ASSESSED", candidate_data["extracted_text"])
            self.assertEqual(register_entry.lifecycle_status, "discovered")
            self.assertEqual(register_entry.original_idea_value, CANDIDATE["original_idea_value"])
            self.assertEqual(register_entry.evidence_verification_status, "USER_SUPPLIED_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
