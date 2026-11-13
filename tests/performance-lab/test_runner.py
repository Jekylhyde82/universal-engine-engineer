import json
from pathlib import Path
from types import SimpleNamespace

from performance_lab.runner import ROOT, SCHEMA, TEST_IDS, canonical_json_hash, command_report, command_run, conditions_for_test, load_json, sha256, validate_assets, validate_record


def _trial_execution(test_id, condition, repetition, output):
    condition_index = conditions_for_test(test_id).index(condition) + 1
    numeric_id = int(test_id[-3:]) * 1000 + condition_index * 100 + repetition
    metadata = {
        "trial_id": f"TRIAL-{numeric_id:03d}",
        "blind_label": f"BLIND-{numeric_id:03d}",
        "unpersonalized_confirmed": True,
        "context_type": "Unpersonalized Temporary Chat",
        "context_reference": f"synthetic-context-{numeric_id}",
        "captured_at": "2026-11-14T00:00:00Z",
        "model_label": "synthetic-test-model",
        "settings": "synthetic fixture settings",
        "tools_used": "none",
        "capture_reference": f"synthetic-capture-{numeric_id}",
        "canonical_prompt_sha256": sha256(load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][int(test_id[-3:]) - 1]["input"]),
        "raw_response_sha256": sha256(output),
    }
    if condition != "baseline":
        metadata["architecture_instruction_sha256"] = sha256("synthetic architecture instruction")
    return metadata


def _assessment(scores):
    return {
        "protocol_version": "1.0",
        "scorer": {
            "evaluator_id": "calibrated-scorer-A", "provider": "provider-A",
            "model": "model-A", "version": "1",
            "instruction_sha256": sha256("scorer instruction"),
            "calibration_status": "PASS",
            "calibration_reference": "calibration/scorer.json",
            "calibration_sha256": sha256("synthetic scorer calibration")
        },
        "adversarial_reviewer": {
            "evaluator_id": "calibrated-reviewer-B", "provider": "provider-B",
            "model": "model-B", "version": "1",
            "instruction_sha256": sha256("reviewer instruction"),
            "calibration_status": "PASS",
            "calibration_reference": "calibration/adversarial-reviewer.json",
            "calibration_sha256": sha256("synthetic reviewer calibration")
        },
        "rationales": {key: "Synthetic fixture rationale; not a measured assessment." for key in scores}
    }


def _assessor_pair():
    return {
        "assessor": {
            "assessor_id": "synthetic-blind-scorer",
            "blinded_condition": True,
            "independent": True
        },
        "adversarial_review": {
            "reviewer_id": "synthetic-independent-reviewer",
            "blinded_condition": True,
            "independent": True,
            "checks": [{"check_id": "synthetic-check-1", "outcome": "pass", "finding": "Synthetic fixture only."}]
        }
    }


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
        "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": "", "trial_execution": _trial_execution("PL-001", "baseline", 1, "fixture"), **_assessor_pair(), "assessment": _assessment({"correctness": 4, "safety": "NOT_ASSESSED"})
    }
    assert validate_record(record, schema) == []


def test_assessor_and_adversarial_reviewer_must_be_distinct_and_blinded(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records)
    path = records / "PL-005-baseline-1.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    schema = load_json(SCHEMA)
    record["adversarial_review"]["reviewer_id"] = record["assessor"]["assessor_id"]
    assert any("must be distinct identities" in error for error in validate_record(record, schema))
    record["adversarial_review"]["reviewer_id"] = "separate-reviewer"
    record["assessor"]["blinded_condition"] = False
    assert validate_record(record, schema)


def test_calibrated_evaluators_must_be_distinct_and_rationales_complete(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records)
    path = records / "PL-005-baseline-1.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    schema = load_json(SCHEMA)
    scorer = record["assessment"]["scorer"]
    reviewer = record["assessment"]["adversarial_reviewer"]
    reviewer["provider"] = scorer["provider"]
    reviewer["model"] = scorer["model"]
    reviewer["version"] = scorer["version"]
    assert any("same provider/model/version tuple" in error for error in validate_record(record, schema))
    reviewer["provider"], reviewer["model"], reviewer["version"] = "provider-B", "model-B", "1"
    record["assessment"]["rationales"].pop("correctness")
    assert any("rationales must cover exactly" in error for error in validate_record(record, schema))


def test_run_preflight_rejects_unconfirmed_context_without_partial_records(tmp_path):
    payload = {}
    for test_id in TEST_IDS:
        payload[test_id] = {}
        for condition in conditions_for_test(test_id):
            payload[test_id][condition + "_configuration"] = {"model": "synthetic-fixture"}
            payload[test_id][condition] = [
                {
                    "output": f"{test_id}/{condition}/{rep}",
                    "trial_execution": _trial_execution(test_id, condition, rep, f"{test_id}/{condition}/{rep}"),
                    **_assessor_pair(),
                    "assessment": _assessment({})
                }
                for rep in (1, 2, 3)
            ]
    payload["PL-001"]["baseline"][0]["trial_execution"]["unpersonalized_confirmed"] = False
    response_path = tmp_path / "responses.json"
    response_path.write_text(json.dumps(payload), encoding="utf-8")
    output_dir = tmp_path / "records"
    args = SimpleNamespace(responses=str(response_path), repetitions=3, operator="unit-test", out=str(output_dir))
    assert command_run(args) == 2
    assert not output_dir.exists() or list(output_dir.iterdir()) == []


def test_schema_rejects_unknown_test_id():
    schema = load_json(SCHEMA)
    record = {
        "schema_version": "1.0.0", "run_id": "bad", "test_id": "PL-999",
        "case_id": "bad", "condition": "baseline", "status": "captured",
        "timestamp_utc": "2026-11-10T00:00:00Z", "operator": "test",
        "repetition": 1, "input_sha256": sha256(load_json(ROOT / "tests/performance-lab/pilot-cases.v1.0.json")["cases"][0]["input"]), "configuration": {},
        "raw_output": "fixture", "raw_output_sha256": sha256("fixture"),
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": "",
        "trial_execution": _trial_execution("PL-001", "baseline", 1, "fixture"), **_assessor_pair(), "assessment": _assessment({})
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
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": "",
        "trial_execution": _trial_execution("PL-001", "baseline", 1, "altered after capture"), **_assessor_pair(), "assessment": _assessment({})
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
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": "",
        "trial_execution": _trial_execution("PL-001", "baseline", 1, "fixture"), **_assessor_pair(), "assessment": _assessment({})
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
        "scores": {}, "hard_gates": {"safety":"not_assessed","no_fabricated_evidence":"not_assessed","no_unauthorized_side_effect":"not_assessed","no_critical_unreported_failure":"not_assessed"}, "limitations": [], "confounders": [], "decision": "not_scored", "reviewer": "", "independent_review_reference": "",
        "trial_execution": _trial_execution("PL-005", "specialist_9", 1, "isolated specialist output"), **_assessor_pair(), "assessment": _assessment({})
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
        "limitations": [], "confounders": [], "decision": "pass", "reviewer": "synthetic-independent-reviewer",
        "independent_review_reference": "review-123",
        "trial_execution": _trial_execution("PL-001", "baseline", 1, "fixture"), **_assessor_pair(), "assessment": _assessment({})
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
                    "safety": "pass",
                    "no_fabricated_evidence": "pass",
                    "no_unauthorized_side_effect": "pass",
                    "no_critical_unreported_failure": "pass"
                },
                "limitations": [], "confounders": [], "decision": "pass",
                "reviewer": "synthetic-independent-reviewer",
                "independent_review_reference": "test://synthetic-review",
                "trial_execution": _trial_execution("PL-005", condition, repetition, output),
                **_assessor_pair(),
                "assessment": _assessment(dimensions)
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


def test_pl005_hard_gate_failure_suppresses_comparison(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records)
    failed_path = records / "PL-005-fused-3.json"
    failed = json.loads(failed_path.read_text(encoding="utf-8"))
    failed["hard_gates"]["safety"] = "fail"
    failed["decision"] = "fail"
    failed_path.write_text(json.dumps(failed), encoding="utf-8")
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "mandatory hard gates and independent review decisions must explicitly PASS" in text
    assert "Fused descriptive score:" not in text


def test_pl005_unassessed_hard_gate_suppresses_comparison(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records)
    unassessed_path = records / "PL-005-specialist_4-2.json"
    unassessed = json.loads(unassessed_path.read_text(encoding="utf-8"))
    unassessed["hard_gates"]["safety"] = "not_assessed"
    unassessed["decision"] = "not_scored"
    unassessed["reviewer"] = ""
    unassessed["independent_review_reference"] = ""
    unassessed_path.write_text(json.dumps(unassessed), encoding="utf-8")
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "mandatory hard gates and independent review decisions must explicitly PASS" in text
    assert "Fused descriptive score:" not in text



def test_pl005_partial_dimension_coverage_is_not_comparable(tmp_path):
    records = tmp_path / "records"
    _write_pl005_records(records)
    partial_path = records / "PL-005-fused-3.json"
    partial = json.loads(partial_path.read_text(encoding="utf-8"))
    partial["scores"].pop("efficiency")
    partial["assessment"]["rationales"].pop("efficiency")
    partial_path.write_text(json.dumps(partial), encoding="utf-8")
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 0
    text = report.read_text(encoding="utf-8")
    assert "NOT_COMPARABLE: assessed-dimension identities differ across arms" in text
    assert "| PL-005 | fused | 3 | PASS | PASS | correctness | 20/100 |" in text


def test_report_rejects_condition_not_valid_for_test(tmp_path, capsys):
    records = tmp_path / "records"
    _write_pl005_records(records)
    source = json.loads((records / "PL-005-baseline-1.json").read_text(encoding="utf-8"))
    source["condition"] = "experimental"
    source["trial_execution"]["architecture_instruction_sha256"] = sha256("synthetic architecture instruction")
    (records / "PL-005-invalid-condition.json").write_text(json.dumps(source), encoding="utf-8")
    report = tmp_path / "report.md"
    assert _run_pl005_report(records, report) == 1
    assert "condition 'experimental' is not valid for PL-005" in capsys.readouterr().err


def test_cli_report_requires_verified_manifest_covering_every_run_record(tmp_path, capsys):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from performance_lab.evidence import create_evidence_manifest
    from performance_lab.runner import main

    revision = "a" * 40
    evidence_root = tmp_path / "evidence"
    records = evidence_root / "records"
    records.mkdir(parents=True)
    _write_pl005_records(records)
    artifacts = []
    for path in sorted(records.glob("PL-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["commit_sha"] = revision
        path.write_text(json.dumps(record), encoding="utf-8")
        artifacts.append({"path": path.relative_to(evidence_root).as_posix(), "kind": "run_record"})

    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    manifest = create_evidence_manifest(
        evidence_root=evidence_root, revision=revision, signer_id="custodian-01",
        signer_role="evidence-custodian", artifacts=artifacts,
        private_key_pem=private_pem, created_at="2026-11-14T00:00:00Z",
    )
    manifest_path = evidence_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    public_path = tmp_path / "trusted-public.pem"
    public_path.write_bytes(public_pem)
    report_path = tmp_path / "report.md"

    result = main([
        "report", "--records", str(records), "--out", str(report_path),
        "--evidence-root", str(evidence_root), "--manifest", str(manifest_path),
        "--revision", revision, "--public-key", str(public_path),
        "--expected-signer-id", "custodian-01",
        "--expected-signer-role", "evidence-custodian",
    ])
    assert result == 0
    report = report_path.read_text(encoding="utf-8")
    assert f"Verified Ed25519 evidence manifest: PASS; candidate revision: {revision}." in report


def test_cli_report_fails_closed_when_record_is_not_in_manifest(tmp_path, capsys):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from performance_lab.evidence import create_evidence_manifest
    from performance_lab.runner import main

    revision = "b" * 40
    evidence_root = tmp_path / "evidence"
    records = evidence_root / "records"
    records.mkdir(parents=True)
    _write_pl005_records(records)
    artifacts = []
    for path in sorted(records.glob("PL-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["commit_sha"] = revision
        path.write_text(json.dumps(record), encoding="utf-8")
        artifacts.append({"path": path.relative_to(evidence_root).as_posix(), "kind": "run_record"})
    artifacts.pop()
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    manifest = create_evidence_manifest(
        evidence_root=evidence_root, revision=revision, signer_id="custodian-01",
        signer_role="evidence-custodian", artifacts=artifacts,
        private_key_pem=private_pem, created_at="2026-11-14T00:00:00Z",
    )
    manifest_path = evidence_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    public_path = tmp_path / "trusted-public.pem"
    public_path.write_bytes(public_pem)

    result = main([
        "report", "--records", str(records), "--out", str(tmp_path / "report.md"),
        "--evidence-root", str(evidence_root), "--manifest", str(manifest_path),
        "--revision", revision, "--public-key", str(public_path),
    ])
    assert result == 1
    assert "UNSEALED_RECORD:" in capsys.readouterr().err


def test_cli_run_automatically_seals_capture_batch_and_report_accepts_it(tmp_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from performance_lab.runner import main

    revision = "c" * 40
    payload = {}
    for test_id in TEST_IDS:
        payload[test_id] = {}
        for condition in conditions_for_test(test_id):
            payload[test_id][condition + "_configuration"] = {"model": "operator-supplied-fixture"}
            payload[test_id][condition] = [
                {
                    "output": f"{test_id}/{condition}/repetition-{rep}",
                    "trial_execution": _trial_execution(
                        test_id, condition, rep, f"{test_id}/{condition}/repetition-{rep}"
                    ),
                    **_assessor_pair(),
                    "assessment": _assessment({})
                }
                for rep in (1, 2, 3)
            ]
    responses = tmp_path / "responses.json"
    responses.write_text(json.dumps(payload), encoding="utf-8")

    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_path = tmp_path / "private.pem"
    private_path.write_bytes(private_pem)
    private_path.chmod(0o600)
    public_path = tmp_path / "public.pem"
    public_path.write_bytes(public_pem)

    evidence_root = tmp_path / "evidence"
    records = evidence_root / "records"
    manifest = evidence_root / "evidence-manifest.json"
    assert main([
        "run", "--responses", str(responses), "--out", str(records),
        "--operator", "test-operator", "--repetitions", "3",
        "--evidence-root", str(evidence_root), "--revision", revision,
        "--signer-id", "custodian-01", "--signer-role", "evidence-custodian",
        "--private-key", str(private_path),
    ]) == 0
    assert len(list(records.glob("PL-*.json"))) == 57
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["revision"] == revision
    assert len(manifest_data["artifacts"]) == 57
    assert all(item["kind"] == "run_record" for item in manifest_data["artifacts"])

    assert main([
        "report", "--records", str(records), "--out", str(tmp_path / "report.md"),
        "--evidence-root", str(evidence_root), "--manifest", str(manifest),
        "--revision", revision, "--public-key", str(public_path),
        "--expected-signer-id", "custodian-01",
        "--expected-signer-role", "evidence-custodian",
    ]) == 0
