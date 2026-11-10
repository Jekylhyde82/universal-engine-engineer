import json
from pathlib import Path

from performance_lab.runner import ROOT, SCHEMA, TEST_IDS, load_json, sha256, validate_assets, validate_record


def test_assets_cover_exactly_five_tests_and_rubric_totals_100():
    assert validate_assets() == []
    assert [x["id"] for x in load_json(ROOT / "tests/performance-lab/test-catalog.v1.0.json")["tests"]] == TEST_IDS


def test_valid_record_passes_schema():
    schema = load_json(SCHEMA)
    record = {
        "schema_version": "1.0.0", "run_id": "unit-test-run", "test_id": "PL-001",
        "case_id": "PL-001-C01", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]["input"]), "configuration": {},
        "raw_output": "fixture", "raw_output_sha256": sha256("fixture"),
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
        "repetition": 1, "input_sha256": sha256(load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]["input"]), "configuration": {},
        "raw_output": "fixture", "raw_output_sha256": sha256("fixture"),
        "scores": {}, "hard_gates": {}, "limitations": [], "confounders": [], "decision": "not_scored"
    }
    assert validate_record(record, schema)


def test_schema_rejects_tampered_raw_output_hash():
    schema = load_json(SCHEMA)
    case = load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]
    record = {
        "schema_version": "1.0.0", "run_id": "tampered", "test_id": "PL-001",
        "case_id": "PL-001-C01", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(case["input"]), "configuration": {},
        "raw_output": "altered after capture", "raw_output_sha256": sha256("original"),
        "scores": {}, "hard_gates": {}, "limitations": [], "confounders": [], "decision": "not_scored"
    }
    assert any("raw_output_sha256" in error for error in validate_record(record, schema))
