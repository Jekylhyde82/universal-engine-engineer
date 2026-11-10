import json
from pathlib import Path
from types import SimpleNamespace

from performance_lab.runner import ROOT, SCHEMA, TEST_IDS, canonical_json_hash, command_run, conditions_for_test, load_json, sha256, validate_assets, validate_record


def test_assets_cover_exactly_five_tests_and_rubric_totals_100():
    assert validate_assets() == []
    assert [x["id"] for x in load_json(ROOT / "tests/performance-lab/test-catalog.v1.0.json")["tests"]] == TEST_IDS


def test_valid_record_passes_schema():
    schema = load_json(SCHEMA)
    record = {
        "schema_version": "1.0.0", "run_id": "unit-test-run", "test_id": "PL-001",
        "case_id": "PL-001-C01", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]["input"]), "configuration": {}, "configuration_sha256": canonical_json_hash({}),
        "raw_output": "fixture", "raw_output_sha256": sha256("fixture"),
        "scores": {"correctness": 4, "safety": "NOT_ASSESSED"},
        "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": ""
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
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": ""
    }
    assert validate_record(record, schema)


def test_schema_rejects_tampered_raw_output_hash():
    schema = load_json(SCHEMA)
    case = load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]
    record = {
        "schema_version": "1.0.0", "run_id": "tampered", "test_id": "PL-001",
        "case_id": "PL-001-C01", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(case["input"]), "configuration": {}, "configuration_sha256": canonical_json_hash({}),
        "raw_output": "altered after capture", "raw_output_sha256": sha256("original"),
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": ""
    }
    assert any("raw_output_sha256" in error for error in validate_record(record, schema))



def test_schema_rejects_tampered_configuration_hash():
    schema = load_json(SCHEMA)
    case = load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]
    record = {
        "schema_version": "1.0.0", "run_id": "bad-config", "test_id": "PL-001",
        "case_id": "PL-001-C01", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(case["input"]), "configuration": {"model": "v1"},
        "configuration_sha256": canonical_json_hash({"model": "v0"}),
        "raw_output": "fixture", "raw_output_sha256": sha256("fixture"),
        "scores": {}, "hard_gates": {}, "limitations": [], "confounders": [], "decision": "not_scored"
    }
    assert any("configuration_sha256" in error for error in validate_record(record, schema))



def test_pl005_supports_fused_and_nine_specialist_arms():
    schema = load_json(SCHEMA)
    case = load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][4]
    record = {
        "schema_version": "1.0.0", "run_id": "specialist-arm", "test_id": "PL-005",
        "case_id": case["case_id"], "condition": "specialist_9", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(case["input"]), "configuration": {"specialist": "nine"},
        "configuration_sha256": canonical_json_hash({"specialist": "nine"}),
        "raw_output": "isolated specialist output", "raw_output_sha256": sha256("isolated specialist output"),
        "scores": {}, "hard_gates": {}, "limitations": [], "confounders": [], "decision": "not_scored"
    }
    assert "fused" in conditions_for_test("PL-005")
    assert len([x for x in conditions_for_test("PL-005") if x.startswith("specialist_")]) == 9
    assert validate_record(record, schema) == []


def test_invalid_multiarms_payload_writes_no_partial_records(tmp_path):
    payload = {}
    for test_id in TEST_IDS:
        conditions = conditions_for_test(test_id)
        payload[test_id] = {}
        for condition in conditions:
            payload[test_id][condition + "_configuration"] = {"model": "test"}
            payload[test_id][condition] = [{"output": "one"}, {"output": "two"}, {"output": "three"}]
    # Remove one required PL-005 arm; preflight must fail before creating records.
    del payload["PL-005"]["specialist_9"]
    response_path = tmp_path / "responses.json"
    response_path.write_text(json.dumps(payload), encoding="utf-8")
    output_dir = tmp_path / "records"
    args = SimpleNamespace(responses=str(response_path), repetitions=3, operator="unit-test", out=str(output_dir))
    assert command_run(args) == 2
    assert not output_dir.exists() or list(output_dir.iterdir()) == []



def test_pass_decision_requires_review_reference_and_all_gates_pass():
    schema = load_json(SCHEMA)
    case = load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]
    record = {
        "schema_version": "1.0.0", "run_id": "unsupported-pass", "test_id": "PL-001",
        "case_id": case["case_id"], "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(case["input"]), "configuration": {},
        "configuration_sha256": canonical_json_hash({}), "raw_output": "fixture",
        "raw_output_sha256": sha256("fixture"), "scores": {},
        "hard_gates": {"safety":"pass","no_fabricated_evidence":"pass","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"pass"},
        "limitations": [], "confounders": [], "decision": "pass", "reviewer": "reviewer-1",
        "independent_review_reference": "review-123"
    }
    assert any("every mandatory hard gate" in error for error in validate_record(record, schema))
