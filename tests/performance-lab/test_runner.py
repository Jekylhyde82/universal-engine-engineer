import json
from pathlib import Path
from types import SimpleNamespace

from performance_lab.runner import ROOT, SCHEMA, TEST_IDS, canonical_json_hash, command_report, command_run, command_validate, conditions_for_test, load_json, sha256, validate_assets, validate_record


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
    record["scores"]["invented_dimension"] = 5
    assert any("unknown rubric dimension IDs" in error for error in validate_record(record, schema))


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
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": ""
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
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": ""
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



def test_run_preflights_late_schema_invalid_record_before_writing(tmp_path):
    payload = {}
    for test_id in TEST_IDS:
        conditions = conditions_for_test(test_id)
        payload[test_id] = {}
        for condition in conditions:
            payload[test_id][condition + "_configuration"] = {"model": "test"}
            payload[test_id][condition] = [
                {"output": "one"}, {"output": "two"}, {"output": "three"}
            ]
    # Fail at the final PL-005 arm/repetition, after every earlier arm is valid.
    payload["PL-005"]["fused"][2]["scores"] = {"invented_dimension": 4}
    response_path = tmp_path / "responses.json"
    response_path.write_text(json.dumps(payload), encoding="utf-8")
    output_dir = tmp_path / "records"
    args = SimpleNamespace(
        responses=str(response_path), repetitions=3, operator="unit-test", out=str(output_dir)
    )
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



def _write_pl005_records(directory, repetitions_by_condition=None, dimensions_by_condition=None):
    """Create valid synthetic records for report-gate tests; not benchmark evidence."""
    directory.mkdir(parents=True, exist_ok=True)
    case = load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][4]
    conditions = conditions_for_test("PL-005")
    repetitions_by_condition = repetitions_by_condition or {}
    dimensions_by_condition = dimensions_by_condition or {}
    for condition in conditions:
        repetitions = repetitions_by_condition.get(condition, [1, 2, 3])
        dimensions = dimensions_by_condition.get(condition, {"correctness": 4, "efficiency": 4})
        for record_index, repetition in enumerate(repetitions, start=1):
            output = f"{condition}-{record_index}-{repetition}"
            configuration = {"condition": condition}
            record = {
                "schema_version": "1.0.0", "run_id": f"{condition}-{repetition}",
                "test_id": "PL-005", "case_id": case["case_id"],
                "condition": condition, "status": "captured",
                "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
                "repetition": repetition, "input_sha256": sha256(case["input"]),
                "configuration": configuration,
                "configuration_sha256": canonical_json_hash(configuration),
                "raw_output": output, "raw_output_sha256": sha256(output),
                "scores": dimensions,
                "hard_gates": {
                    "safety": "not_assessed",
                    "no_fabricated_evidence": "not_assessed",
                    "no_unauthorized_side_effect": "not_assessed",
                    "no_critical_unreported_failure": "not_assessed"
                },
                "limitations": [], "confounders": [], "decision": "not_scored",
                "reviewer": "", "independent_review_reference": ""
            }
            (directory / f"PL-005-{condition}-{record_index}.json").write_text(
                json.dumps(record), encoding="utf-8"
            )


def _run_pl005_report(records_dir, output_path):
    return command_report(SimpleNamespace(records=str(records_dir), out=str(output_path)))


def test_report_marks_under_three_repetitions_not_verified(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records, {"baseline": [1, 2]})
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "baseline | 2 | NOT_VERIFIED (2/3)" in text
    assert "NOT_VERIFIED: minimum distinct repetition requirement not met" in text


def test_report_duplicate_repetition_numbers_do_not_satisfy_minimum(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records, {"specialist_1": [1, 1, 2]})
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "specialist_1 | 3 | DUPLICATE_REPETITION" in text
    assert "NOT_VERIFIED: minimum distinct repetition requirement not met" in text


def test_pl005_equal_weight_but_different_dimension_sets_are_not_comparable(tmp_path):
    records = tmp_path / "records"
    dimensions = {
        "baseline": {"correctness": 4, "efficiency": 4},
        "fused": {"reliability": 4, "calibration": 4}
    }
    _write_pl005_records(records, dimensions_by_condition=dimensions)
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "NOT_COMPARABLE: assessed-dimension identities differ across arms" in text
    assert "correctness, efficiency" in text
    assert "calibration, reliability" in text


def test_pl005_matching_dimension_identity_sets_allow_comparison(tmp_path):
    records = tmp_path / "records"
    dimensions = {
        condition: {"correctness": 4, "efficiency": 4}
        for condition in conditions_for_test("PL-005")
    }
    _write_pl005_records(records, dimensions_by_condition=dimensions)
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "Fused descriptive score:" in text
    assert "NOT_COMPARABLE" not in text


def test_pl005_missing_arm_fails_closed(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records)
    (records / "PL-005-specialist_9-3.json").unlink()
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "specialist_9=NOT_VERIFIED (2/3)" in text
    assert "Fused descriptive score:" not in text



def test_pl005_partial_dimension_coverage_is_not_comparable(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records)
    partial_path = records / "PL-005-fused-3.json"
    partial = json.loads(partial_path.read_text(encoding="utf-8"))
    partial["scores"].pop("efficiency")
    partial_path.write_text(json.dumps(partial), encoding="utf-8")
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "NOT_COMPARABLE: assessed-dimension identities differ across arms" in text
    assert "| PL-005 | fused | 3 | PASS | correctness | 20/100 |" in text


def test_report_rejects_condition_not_valid_for_test(tmp_path, capsys):
    records = tmp_path / "records"
    _write_pl005_records(records)
    source = json.loads((records / "PL-005-baseline-1.json").read_text(encoding="utf-8"))
    source["condition"] = "experimental"
    (records / "PL-005-invalid-condition.json").write_text(json.dumps(source), encoding="utf-8")
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 1
    assert "condition 'experimental' is not valid for PL-005" in capsys.readouterr().err


def test_validate_rejects_condition_not_valid_for_test(tmp_path, capsys):
    records = tmp_path / "records"
    _write_pl005_records(records)
    source = json.loads((records / "PL-005-baseline-1.json").read_text(encoding="utf-8"))
    source["condition"] = "experimental"
    (records / "PL-005-invalid-condition.json").write_text(json.dumps(source), encoding="utf-8")
    args = SimpleNamespace(records=str(records))
    assert command_validate(args) == 1
    assert "condition 'experimental' is not valid for PL-005" in capsys.readouterr().out
