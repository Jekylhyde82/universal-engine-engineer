import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from universal_engine.lmstudio_catalog import (
    LMStudioCatalogError, assimilate_catalog_candidate,
    build_download_command, candidate_from_mapping, download_catalog_candidate,
    main, status_main,
)
from universal_engine.lmstudio import LMStudioDownloadJob
from universal_engine.uaie import UniversalAcquisitionIntegrationEngine


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body[:size]


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
        for metadata in ({"nested": {"api_token": "do-not-store"}}, {"clientSecret": "do-not-store"}):
            with self.subTest(metadata=metadata), self.assertRaises(LMStudioCatalogError):
                candidate_from_mapping({**CANDIDATE, "metadata": metadata})

    def test_rejects_oversized_or_non_json_metadata(self):
        for metadata in ({"payload": "x" * (256 * 1024)}, {"value": float("nan")}):
            with self.subTest(metadata_type=type(metadata["payload"] if "payload" in metadata else metadata["value"])), self.assertRaises(LMStudioCatalogError):
                candidate_from_mapping({**CANDIDATE, "metadata": metadata})

    def test_catalog_candidate_download_requires_dual_approval_and_reviewed_artifact(self):
        candidate = candidate_from_mapping({**CANDIDATE, "quantization": "Q4_K_M"})
        with tempfile.TemporaryDirectory() as tmp:
            engine = UniversalAcquisitionIntegrationEngine(Path(tmp) / "uaie.sqlite3")
            catalog_record, _, register_entry = assimilate_catalog_candidate(engine, candidate)
            with self.assertRaises(LMStudioCatalogError):
                download_catalog_candidate(
                    engine, candidate, catalog_record.record_id, approved=True)
            engine.set_state(catalog_record.record_id, "approved")
            engine.set_acquisition_lifecycle(catalog_record.record_id, "proposed")
            engine.set_acquisition_lifecycle(catalog_record.record_id, "under_evaluation")
            engine.set_acquisition_lifecycle(catalog_record.record_id, "approved")
            with self.assertRaises(LMStudioCatalogError):
                download_catalog_candidate(
                    engine, candidate, catalog_record.record_id, approved=True)
            with self.assertRaises(LMStudioCatalogError):
                download_catalog_candidate(
                    engine, candidate, catalog_record.record_id, approved=True,
                    huggingface_model_url="https://huggingface.co/other/model")
            seen = {}
            def opener(request, timeout):
                seen["body"] = json.loads(request.data.decode())
                return FakeResponse(b'{"status":"already_downloaded"}')
            job = download_catalog_candidate(
                engine, candidate, catalog_record.record_id, approved=True,
                huggingface_model_url="https://huggingface.co/liquid-ai/lfm3-vl-2b",
                opener=opener)
            self.assertEqual(job.status, "already_downloaded")
            self.assertEqual(seen["body"]["quantization"], "Q4_K_M")

    def test_cli_imports_reviewed_json_and_only_prints_download_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate_path = Path(tmp) / "candidate.json"
            candidate_path.write_text(json.dumps(CANDIDATE), encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                result = main([str(candidate_path), "--db", str(Path(tmp) / "uaie.sqlite3")])
            self.assertEqual(result, 0)
            payload = json.loads(output.getvalue())
            self.assertFalse(payload["command_executed"])
            self.assertFalse(payload["model_downloaded"])
            self.assertEqual(payload["lifecycle_status"], "discovered")

    def test_cli_download_requires_explicit_flag_and_approved_register(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate_path = Path(tmp) / "candidate.json"
            candidate_path.write_text(json.dumps(CANDIDATE), encoding="utf-8")
            db_path = Path(tmp) / "uaie.sqlite3"
            engine = UniversalAcquisitionIntegrationEngine(db_path)
            candidate = candidate_from_mapping(CANDIDATE)
            catalog_record, _, _ = assimilate_catalog_candidate(engine, candidate)
            engine.set_state(catalog_record.record_id, "approved")
            engine.set_acquisition_lifecycle(catalog_record.record_id, "proposed")
            engine.set_acquisition_lifecycle(catalog_record.record_id, "under_evaluation")
            engine.set_acquisition_lifecycle(catalog_record.record_id, "approved")
            with patch("universal_engine.lmstudio_catalog.download_catalog_candidate",
                       return_value=LMStudioDownloadJob("job_1", "downloading", 123, None, None)):
                output = StringIO()
                with redirect_stdout(output):
                    result = main([str(candidate_path), "--db", str(db_path), "--download",
                                   "--approved", "--record-id", catalog_record.record_id])
            self.assertEqual(result, 0)
            payload = json.loads(output.getvalue())
            self.assertTrue(payload["download_started"])
            self.assertEqual(payload["download_job"]["job_id"], "job_1")

    def test_status_cli_reports_job_without_executing_download(self):
        with patch("universal_engine.lmstudio.get_download_status",
                   return_value=LMStudioDownloadJob("job_2", "completed", 456, None, "2026-11-20T00:00:00Z")):
            output = StringIO()
            with redirect_stdout(output):
                result = status_main(["job_2"])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "completed")

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
