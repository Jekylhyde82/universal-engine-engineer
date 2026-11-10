import json
from pathlib import Path

from performance_lab.runner import ROOT, SCHEMA, TEST_IDS, load_json, validate_assets, validate_record


def test_assets_cover_exactly_five_tests_and_rubric_totals_100():
    assert validate_assets() == []
    assert [x["id"] for x in load_json(ROOT / "tests/performance-lab/test-catalog.v1.0.json")["tests"]] == TEST_IDS


def test_valid_record_passes_schema():
    schema = load_json(SCHEMA)
    record = {
        "schema_version": "1.0.0", "run_id": "unit-test-run", "test_id": "PL-001",
        "case_id": "PL-001-C01", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": "a" * 64, "configuration": {},
        "raw_output": "fixture", "raw_output_sha256": "b" * 64,
        "scores": {"correctness": 4, "safety": "NOT_ASSESSED"},
        "hard_gates": {}, "limitations": [], "confounders": [], "decision": "not_scored"
    }
    assert validate_record(record, schema) == []


def test_schema_rejects_unknown_test_id():
    schema = load_json(SCHEMA)
    record = {
        "schema_version": "1.0.0", "run_id": "bad", "test_id": "PL-999",
        "case_id": "bad", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": "a" * 64, "configuration": {},
        "raw_output": "fixture", "raw_output_sha256": "b" * 64,
        "scores": {}, "hard_gates": {}, "limitations": [], "confounders": [], "decision": "not_scored"
    }
    assert validate_record(record, schema)
