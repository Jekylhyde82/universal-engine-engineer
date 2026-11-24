"""Executable contract tests for OMNISIGHT PRIME JSON Schemas.

Run: python -m unittest discover -s schemas/omnisight/tests -v
"""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FORMAT_CHECKER = FormatChecker()


def load_schema(filename):
    with (ROOT / filename).open(encoding="utf-8") as stream:
        schema = json.load(stream)
    Draft202012Validator.check_schema(schema)
    return schema


CAPABILITY_SCHEMA = load_schema("capability-manifest.schema.json")
OBSERVATION_SCHEMA = load_schema("observation-envelope.schema.json")


def validator(schema):
    return Draft202012Validator(schema, format_checker=FORMAT_CHECKER)


def valid_capability():
    return {
        "capability_id": "omnisight.ocr.basic",
        "semantic_version": "1.2.3",
        "domain": "recognition",
        "operations": ["recognise_text"],
        "input_schema": "schemas/omnisight/observation-envelope.schema.json",
        "output_schema": "schemas/omnisight/observation-envelope.schema.json",
        "runtime_requirements": {
            "platforms": ["android"],
            "minimum_ram_mb": 256,
            "network_required": False,
            "accelerators": []
        },
        "permission_scopes": ["visual.capture.read"],
        "lifecycle_state": "proposed",
        "provenance": {
            "source_uri": "https://example.org/ocr",
            "source_revision": "fixture-1",
            "licence": "example-test-only",
            "review_record": "TEST-FIXTURE"
        }
    }


def valid_observation():
    return {
        "schema_version": "0.1.0",
        "observation_id": "obs-0001",
        "correlation_id": "corr-0001",
        "source": {
            "source_id": "test-screen",
            "captured_at": "2026-11-25T00:00:00Z",
            "media_digest": "sha256:" + ("a" * 64)
        },
        "region": {
            "coordinate_frame": "screen-pixels",
            "shape": "rectangle",
            "coordinates": [0, 0, 100, 40],
            "units": "px"
        },
        "content_type": "text",
        "result": {"text": "fixture text"},
        "producer": {
            "capability_id": "omnisight.ocr.basic",
            "semantic_version": "1.2.3"
        },
        "epistemic_status": "observed",
        "confidence": {
            "value": 0.97,
            "meaning": "fixture confidence; not calibrated"
        },
        "evidence_refs": ["source:sha256:" + ("a" * 64)],
        "transformations": [],
        "limitations": ["Synthetic test fixture; not real capture."]
    }


class CapabilityManifestContractTests(unittest.TestCase):
    def setUp(self):
        self.checker = validator(CAPABILITY_SCHEMA)

    def test_schema_is_valid_draft_2020_12(self):
        self.assertEqual(CAPABILITY_SCHEMA["$schema"],
                         "https://json-schema.org/draft/2020-12/schema")

    def test_valid_manifest_is_accepted(self):
        self.checker.validate(valid_capability())

    def test_semantic_version_rejects_malformed_version(self):
        instance = valid_capability()
        instance["semantic_version"] = "1.2"
        self.assertFalse(self.checker.is_valid(instance))

    def test_semantic_version_accepts_prerelease_and_build(self):
        instance = valid_capability()
        instance["semantic_version"] = "2.0.0-rc.1+build.7"
        self.checker.validate(instance)

    def test_unknown_lifecycle_state_is_rejected(self):
        instance = valid_capability()
        instance["lifecycle_state"] = "deployed_without_approval"
        self.assertFalse(self.checker.is_valid(instance))

    def test_unknown_top_level_property_is_rejected(self):
        instance = valid_capability()
        instance["unreviewed_authority"] = True
        self.assertFalse(self.checker.is_valid(instance))

    def test_duplicate_operations_are_rejected(self):
        instance = valid_capability()
        instance["operations"] = ["ocr", "ocr"]
        self.assertFalse(self.checker.is_valid(instance))


class ObservationEnvelopeContractTests(unittest.TestCase):
    def setUp(self):
        self.checker = validator(OBSERVATION_SCHEMA)

    def test_schema_is_valid_draft_2020_12(self):
        self.assertEqual(OBSERVATION_SCHEMA["$schema"],
                         "https://json-schema.org/draft/2020-12/schema")

    def test_valid_observation_is_accepted(self):
        self.checker.validate(valid_observation())

    def test_invalid_timestamp_is_rejected(self):
        instance = valid_observation()
        instance["source"]["captured_at"] = "not-a-date"
        self.assertFalse(self.checker.is_valid(instance))

    def test_confidence_above_one_is_rejected(self):
        instance = valid_observation()
        instance["confidence"]["value"] = 1.01
        self.assertFalse(self.checker.is_valid(instance))

    def test_empty_evidence_references_are_rejected(self):
        instance = valid_observation()
        instance["evidence_refs"] = []
        self.assertFalse(self.checker.is_valid(instance))

    def test_verified_status_is_a_valid_enum_value(self):
        instance = valid_observation()
        instance["epistemic_status"] = "verified"
        self.checker.validate(instance)

    def test_unknown_top_level_property_is_rejected(self):
        instance = valid_observation()
        instance["instruction"] = "untrusted fixture data"
        self.assertFalse(self.checker.is_valid(instance))

    def test_invalid_digest_is_rejected(self):
        instance = valid_observation()
        instance["source"]["media_digest"] = "sha256:not-a-digest"
        self.assertFalse(self.checker.is_valid(instance))


if __name__ == "__main__":
    unittest.main()
