"""Five-test runner. It records supplied outputs; it does not generate model outputs or scores."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import stat
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .evidence import create_evidence_manifest, verify_evidence_manifest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "tests" / "performance-lab"
CATALOG = ASSETS / "test-catalog.v1.0.json"
CASES = ASSETS / "pilot-cases.v1.0.json"
RUBRIC = ASSETS / "scoring-rubric.v1.0.json"
SCHEMA = ROOT / "performance_lab" / "run-record.schema.json"
CATALOG_SCHEMA = ASSETS / "schemas" / "test-catalog.schema.json"
CASES_SCHEMA = ASSETS / "schemas" / "pilot-cases.schema.json"
RUBRIC_SCHEMA = ASSETS / "schemas" / "scoring-rubric.schema.json"
TEST_IDS = [f"PL-{i:03d}" for i in range(1, 6)]
SPECIALIST_ARMS = [f"specialist_{i}" for i in range(1, 10)]


def conditions_for_test(test_id: str) -> list[str]:
    if test_id == "PL-005":
        return ["baseline", *SPECIALIST_ARMS, "fused"]
    return ["baseline", "experimental"]


def load_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json_hash(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded)


def validate_assets() -> list[str]:
    errors: list[str] = []
    try:
        catalog, cases, rubric = load_json(CATALOG), load_json(CASES), load_json(RUBRIC)
        schema_files = [
            (catalog, CATALOG_SCHEMA, "catalogue"),
            (cases, CASES_SCHEMA, "pilot cases"),
            (rubric, RUBRIC_SCHEMA, "scoring rubric"),
        ]
        for document, schema_path, label in schema_files:
            schema = load_json(schema_path)
            Draft202012Validator.check_schema(schema)
            for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document):
                errors.append(f"{label} schema: {'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}")
        Draft202012Validator.check_schema(load_json(SCHEMA))

        ids = [item["id"] for item in catalog["tests"]]
        case_ids = [item["test_id"] for item in cases["cases"]]
        dimension_ids = [item["id"] for item in rubric["dimensions"]]
        if ids != TEST_IDS or len(set(ids)) != len(ids):
            errors.append(f"catalog test IDs must be unique and exactly {TEST_IDS}; got {ids}")
        if case_ids != TEST_IDS or len(set(case_ids)) != len(case_ids):
            errors.append(f"pilot cases must cover each test exactly once: {TEST_IDS}; got {case_ids}")
        if catalog["version"] != cases["version"]:
            errors.append("catalogue and pilot-case versions must match")
        if len(set(dimension_ids)) != len(dimension_ids):
            errors.append("rubric dimension IDs must be unique")
        if sum(item["weight"] for item in rubric["dimensions"]) != 100:
            errors.append("rubric dimension weights must total 100")
        if catalog["protocol"]["minimum_repetitions"] < 3:
            errors.append("protocol minimum repetitions cannot be below 3")
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        errors.append(f"asset load/structure error: {exc}")
    return errors

def validate_record(record: dict, schema: dict) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
              for error in validator.iter_errors(record)]
    if not errors:
        if record["raw_output_sha256"] != sha256(record["raw_output"]):
            errors.append("raw_output_sha256 does not match raw_output")
        case_map = {item["test_id"]: item for item in load_json(CASES)["cases"]}
        case = case_map[record["test_id"]]
        if record["case_id"] != case["case_id"]:
            errors.append("case_id does not match the versioned pilot case")
        if record["input_sha256"] != sha256(case["input"]):
            errors.append("input_sha256 does not match the versioned pilot input")
        if record["configuration_sha256"] != canonical_json_hash(record["configuration"]):
            errors.append("configuration_sha256 does not match configuration")
    if not errors:
        execution = record["trial_execution"]
        if execution["canonical_prompt_sha256"] != record["input_sha256"]:
            errors.append("trial_execution canonical_prompt_sha256 does not match the canonical pilot input")
        if execution["raw_response_sha256"] != record["raw_output_sha256"]:
            errors.append("trial_execution raw_response_sha256 does not match the captured raw output")
        if record["condition"] == "baseline":
            if execution.get("architecture_instruction_sha256") not in (None, ""):
                errors.append("baseline trial must not declare an architecture instruction hash")
        elif not execution.get("architecture_instruction_sha256"):
            errors.append("non-baseline trial requires architecture_instruction_sha256")
    if not errors:
        assessment = record["assessment"]
        scorer = assessment["scorer"]
        adversarial_evaluator = assessment["adversarial_reviewer"]
        if scorer["evaluator_id"] == adversarial_evaluator["evaluator_id"]:
            errors.append("scorer and adversarial evaluator must be distinct identities")
        if (scorer["provider"], scorer["model"], scorer["version"]) == (
            adversarial_evaluator["provider"], adversarial_evaluator["model"], adversarial_evaluator["version"]
        ):
            errors.append("scorer and adversarial evaluator cannot use the same provider/model/version tuple")
        if set(assessment["rationales"]) != set(record["scores"]):
            errors.append("assessment rationales must cover exactly the dimensions present in scores")
    if not errors:
        assessor = record["assessor"]
        adversarial = record["adversarial_review"]
        if assessor["assessor_id"] == adversarial["reviewer_id"]:
            errors.append("scorer/assessor and adversarial reviewer must be distinct identities")
        if record["reviewer"] and record["reviewer"] != adversarial["reviewer_id"]:
            errors.append("reviewer identity must match adversarial_review.reviewer_id")
        if record["decision"] == "pass" and any(item["outcome"] != "pass" for item in adversarial["checks"]):
            errors.append("pass decision requires every adversarial check to explicitly pass")
    if not errors:
        gates = record["hard_gates"]
        if record["decision"] == "pass":
            if not record["reviewer"].strip() or not record["independent_review_reference"].strip():
                errors.append("pass decision requires reviewer identity and independent review reference")
            if any(value != "pass" for value in gates.values()):
                errors.append("pass decision requires every mandatory hard gate to be explicitly pass")
        elif record["decision"] == "fail":
            if not record["reviewer"].strip() or not record["independent_review_reference"].strip():
                errors.append("fail decision requires reviewer identity and independent review reference")
            if "fail" not in gates.values():
                errors.append("fail decision requires at least one explicitly failed hard gate")
        elif record["decision"] == "inconclusive" and not record["reviewer"].strip():
            errors.append("inconclusive decision requires reviewer identity")
    return errors


def command_validate(args) -> int:
    errors = validate_assets()
    schema = load_json(SCHEMA)
    for path in sorted(Path(args.records).glob("PL-*.json")):
        try:
            errors.extend(f"{path}: {message}" for message in validate_record(load_json(path), schema))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
    if errors:
        print("\n".join(errors))
        return 1
    print("PASS: catalogue, pilot cases, rubric and run-record schemas valid; cross-file IDs and 100-point weights valid; records valid.")
    return 0


def command_run(args) -> int:
    errors = validate_assets()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    payload = load_json(Path(args.responses))
    cases = {item["test_id"]: item for item in load_json(CASES)["cases"]}
    schema = load_json(SCHEMA)

    # Preflight the entire batch before creating any records. Invalid input must
    # never leave a misleading partial benchmark dataset.
    if not isinstance(payload, dict) or set(payload) != set(TEST_IDS):
        print(f"responses must contain exactly these test IDs: {TEST_IDS}", file=sys.stderr)
        return 2
    prepared = {}
    seen_trial_ids, seen_blind_labels = set(), set()
    for test_id in TEST_IDS:
        trial = payload[test_id]
        if not isinstance(trial, dict):
            print(f"{test_id}: trial entry must be an object", file=sys.stderr)
            return 2
        prepared[test_id] = {}
        required_conditions = conditions_for_test(test_id)
        expected_keys = set(required_conditions) | {condition + "_configuration" for condition in required_conditions}
        if set(trial) != expected_keys:
            print(f"{test_id}: expected exactly condition and configuration keys {sorted(expected_keys)}", file=sys.stderr)
            return 2
        for condition in required_conditions:
            repetitions = trial.get(condition)
            config = trial.get(condition + "_configuration")
            if not isinstance(config, dict):
                print(f"{test_id}/{condition}: configuration object required", file=sys.stderr)
                return 2
            if not isinstance(repetitions, list) or len(repetitions) < args.repetitions:
                found = len(repetitions) if isinstance(repetitions, list) else 0
                print(f"{test_id}/{condition}: need {args.repetitions} supplied repetitions; found {found}", file=sys.stderr)
                return 2
            selected = repetitions[:args.repetitions]
            for index, result in enumerate(selected, start=1):
                if not isinstance(result, dict):
                    print(f"{test_id}/{condition}/{index}: repetition must be an object", file=sys.stderr)
                    return 2
                output = result.get("output", "")
                if not isinstance(output, str) or not output.strip():
                    print(f"{test_id}/{condition}/{index}: non-empty output required", file=sys.stderr)
                    return 2
                execution = result.get("trial_execution")
                if not isinstance(execution, dict):
                    print(f"{test_id}/{condition}/{index}: trial_execution metadata required", file=sys.stderr)
                    return 2
                trial_id, blind_label = execution.get("trial_id"), execution.get("blind_label")
                if not trial_id or trial_id in seen_trial_ids or not blind_label or blind_label in seen_blind_labels:
                    print(f"{test_id}/{condition}/{index}: trial_id and blind_label must be present and globally unique", file=sys.stderr)
                    return 2
                seen_trial_ids.add(trial_id)
                seen_blind_labels.add(blind_label)
                if execution.get("unpersonalized_confirmed") is not True:
                    print(f"{test_id}/{condition}/{index}: verified Unpersonalized Temporary Chat confirmation required", file=sys.stderr)
                    return 2
                assessor = result.get("assessor")
                adversarial = result.get("adversarial_review")
                assessment = result.get("assessment")
                if not isinstance(assessor, dict) or not isinstance(adversarial, dict):
                    print(f"{test_id}/{condition}/{index}: separate assessor and adversarial_review attestations required", file=sys.stderr)
                    return 2
                if not isinstance(assessment, dict):
                    print(f"{test_id}/{condition}/{index}: calibrated assessment metadata and rationales required", file=sys.stderr)
                    return 2
                if assessor.get("blinded_condition") is not True or assessor.get("independent") is not True:
                    print(f"{test_id}/{condition}/{index}: assessor must attest blinding and independence", file=sys.stderr)
                    return 2
                if adversarial.get("blinded_condition") is not True or adversarial.get("independent") is not True:
                    print(f"{test_id}/{condition}/{index}: adversarial reviewer must attest blinding and independence", file=sys.stderr)
                    return 2
                if assessor.get("assessor_id") == adversarial.get("reviewer_id"):
                    print(f"{test_id}/{condition}/{index}: scorer and adversarial reviewer must be distinct", file=sys.stderr)
                    return 2
                evaluator = assessment.get("scorer", {})
                adversarial_evaluator = assessment.get("adversarial_reviewer", {})
                if evaluator.get("evaluator_id") == adversarial_evaluator.get("evaluator_id"):
                    print(f"{test_id}/{condition}/{index}: scorer and adversarial evaluator IDs must differ", file=sys.stderr)
                    return 2
                if (evaluator.get("provider"), evaluator.get("model"), evaluator.get("version")) == (
                    adversarial_evaluator.get("provider"), adversarial_evaluator.get("model"), adversarial_evaluator.get("version")
                ):
                    print(f"{test_id}/{condition}/{index}: scorer and adversarial evaluator configurations must differ", file=sys.stderr)
                    return 2
                if set(assessment.get("rationales", {})) != set(result.get("scores", {})):
                    print(f"{test_id}/{condition}/{index}: rationale coverage must exactly match scored dimensions", file=sys.stderr)
                    return 2
                nested = [
                    ("trial_execution", execution),
                    ("assessor", assessor),
                    ("adversarial_review", adversarial),
                    ("assessment", assessment),
                ]
                for field, value in nested:
                    nested_errors = list(Draft202012Validator(
                        schema["properties"][field], format_checker=FormatChecker()
                    ).iter_errors(value))
                    if nested_errors:
                        print(
                            f"{test_id}/{condition}/{index}: invalid {field} metadata: "
                            + "; ".join(error.message for error in nested_errors),
                            file=sys.stderr,
                        )
                        return 2
                if execution.get("canonical_prompt_sha256") != sha256(cases[test_id]["input"]):
                    print(f"{test_id}/{condition}/{index}: canonical prompt hash mismatch", file=sys.stderr)
                    return 2
                if execution.get("raw_response_sha256") != sha256(output):
                    print(f"{test_id}/{condition}/{index}: raw response hash mismatch", file=sys.stderr)
                    return 2
                if condition == "baseline" and execution.get("architecture_instruction_sha256") not in (None, ""):
                    print(f"{test_id}/{condition}/{index}: baseline must not include architecture instruction hash", file=sys.stderr)
                    return 2
                if condition != "baseline" and not execution.get("architecture_instruction_sha256"):
                    print(f"{test_id}/{condition}/{index}: non-baseline requires architecture instruction hash", file=sys.stderr)
                    return 2
            prepared[test_id][condition] = (config, selected)

    revision = args.revision
    if not getattr(args, "manifest_out", None):
        args.manifest_out = str(Path(args.evidence_root) / "evidence-manifest.json")
    if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        print("revision must be a 40-character lowercase Git commit SHA", file=sys.stderr)
        return 2
    evidence_root = Path(args.evidence_root)
    evidence_root.mkdir(parents=True, exist_ok=True)
    resolved_root = evidence_root.resolve(strict=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        out.resolve(strict=True).relative_to(resolved_root)
    except ValueError:
        print("record output directory must be inside the evidence root", file=sys.stderr)
        return 2
    key_path = Path(args.private_key)
    try:
        if os.name == "posix" and stat.S_IMODE(key_path.stat().st_mode) & 0o077:
            print("private key file permissions must exclude group and other access", file=sys.stderr)
            return 2
        private_key_pem = key_path.read_bytes()
    except OSError as exc:
        print(f"cannot read protected signing key: {exc}", file=sys.stderr)
        return 2
    calibration_artifacts = {}
    for test_id in TEST_IDS:
        for condition in conditions_for_test(test_id):
            for result in prepared[test_id][condition][1]:
                assessment = result["assessment"]
                for evaluator_role in ("scorer", "adversarial_reviewer"):
                    evaluator = assessment[evaluator_role]
                    reference = evaluator["calibration_reference"]
                    relative_path = Path(reference)
                    if relative_path.is_absolute() or ".." in relative_path.parts:
                        print(f"invalid calibration artifact path: {reference}", file=sys.stderr)
                        return 2
                    try:
                        resolved = (resolved_root / relative_path).resolve(strict=True)
                        relative = resolved.relative_to(resolved_root).as_posix()
                        if not resolved.is_file():
                            raise ValueError("calibration reference is not a regular file")
                        actual_hash = hashlib.sha256(resolved.read_bytes()).hexdigest()
                    except (OSError, ValueError) as exc:
                        print(f"calibration artifact unavailable or outside evidence root: {reference}: {exc}", file=sys.stderr)
                        return 2
                    if actual_hash != evaluator["calibration_sha256"]:
                        print(f"calibration artifact hash mismatch: {reference}", file=sys.stderr)
                        return 2
                    calibration_artifacts[relative] = "calibration_reference"
    created = 0
    for test_id in TEST_IDS:
        case = cases[test_id]
        trial = prepared[test_id]
        for condition in conditions_for_test(test_id):
            config, repetitions = trial[condition]
            for index, result in enumerate(repetitions, start=1):
                output = result["output"]
                record = {
                    "schema_version": "1.0.0",
                    "run_id": str(uuid.uuid4()),
                    "test_id": test_id,
                    "case_id": case["case_id"],
                    "condition": condition,
                    "status": "captured",
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "operator": args.operator,
                    "repetition": index,
                    "input_sha256": sha256(case["input"]),
                    "configuration": config,
                    "configuration_sha256": canonical_json_hash(config),
                    "raw_output": output,
                    "raw_output_sha256": sha256(output),
                    "scores": result.get("scores", {}),
                    "hard_gates": result.get("hard_gates", {"safety": "not_assessed", "no_fabricated_evidence": "not_assessed", "no_unauthorized_side_effect": "not_assessed", "no_critical_unreported_failure": "not_assessed"}),
                    "limitations": result.get("limitations", []),
                    "confounders": result.get("confounders", []),
                    "decision": result.get("decision", "not_scored"),
                    "reviewer": result.get("reviewer", ""),
                    "independent_review_reference": result.get("independent_review_reference", ""),
                    "commit_sha": revision,
                    "notes": result.get("notes", ""),
                    "trial_execution": {
                        **result["trial_execution"],
                        "canonical_prompt_sha256": sha256(case["input"]),
                        "raw_response_sha256": sha256(output)
                    },
                    "assessor": result["assessor"],
                    "adversarial_review": result["adversarial_review"],
                    "assessment": result["assessment"]
                }
                problems = validate_record(record, schema)
                if problems:
                    print(f"{test_id}/{condition}/{index}: " + "; ".join(problems), file=sys.stderr)
                    return 2
                filename = f"{test_id}-{condition}-r{index}-{record['run_id']}.json"
                target = out / filename
                if target.exists():
                    raise FileExistsError(target)
                target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
                created += 1
    # Seal the complete capture batch before declaring the run successful.
    try:
        artifacts = [
            {"path": path.resolve(strict=True).relative_to(resolved_root).as_posix(), "kind": "run_record"}
            for path in sorted(out.glob("PL-*.json"))
        ]
        artifacts.extend(
            {"path": path, "kind": kind}
            for path, kind in sorted(calibration_artifacts.items())
        )
        if sum(item["kind"] == "run_record" for item in artifacts) != created:
            raise ValueError("capture batch record count changed before evidence sealing")
        manifest = create_evidence_manifest(
            evidence_root=resolved_root,
            revision=revision,
            signer_id=args.signer_id,
            signer_role=args.signer_role,
            artifacts=artifacts,
            private_key_pem=private_key_pem,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        manifest_path = Path(args.manifest_out)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = manifest_path.with_name(manifest_path.name + ".tmp")
        temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temporary.replace(manifest_path)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"CAPTURE_UNSEALED: records were written but evidence sealing failed: {exc}", file=sys.stderr)
        return 2
    print(f"Captured and sealed {created} run records in {out}; manifest: {manifest_path}. Outputs were supplied by the operator; no model was invoked.")
    return 0


def command_report(args) -> int:
    records = []
    schema = load_json(SCHEMA)
    record_paths = sorted(Path(args.records).glob("PL-*.json"))
    verified_artifacts = {}

    # The public CLI requires a trusted, revision-bound manifest before it
    # will produce a comparison report. Direct function calls remain available
    # to isolated unit tests of report arithmetic; they are not a release path.
    manifest_revision = None
    if getattr(args, "manifest", None):
        try:
            evidence_root = Path(args.evidence_root).resolve(strict=True)
            manifest = load_json(Path(args.manifest))
            manifest_errors = verify_evidence_manifest(
                manifest,
                evidence_root=evidence_root,
                trusted_public_key_pem=Path(args.public_key).read_bytes(),
                expected_revision=args.revision,
                expected_signer_id=args.expected_signer_id,
                expected_signer_role=args.expected_signer_role,
            )
            if manifest_errors:
                print("MANIFEST_INVALID: " + "; ".join(manifest_errors), file=sys.stderr)
                return 1
            verified_artifacts = {item["path"]: item for item in manifest["artifacts"]}
            sealed_records = {
                item["path"] for item in manifest["artifacts"]
                if item["kind"] == "run_record"
            }
            for record_path in record_paths:
                try:
                    relative = record_path.resolve(strict=True).relative_to(evidence_root).as_posix()
                except (OSError, ValueError) as exc:
                    print(f"UNSEALED_RECORD: {record_path} is outside the evidence root: {exc}", file=sys.stderr)
                    return 1
                if relative not in sealed_records:
                    print(f"UNSEALED_RECORD: {relative} is not covered as a run_record by the verified manifest", file=sys.stderr)
                    return 1
            manifest_revision = args.revision
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            print(f"MANIFEST_INVALID: {exc}", file=sys.stderr)
            return 1

    for path in record_paths:
        record = load_json(path)
        if manifest_revision and record.get("commit_sha") != manifest_revision:
            print(
                f"REVISION_MISMATCH: {path} must declare commit_sha {manifest_revision}",
                file=sys.stderr,
            )
            return 1
        problems = validate_record(record, schema)
        if problems:
            print(f"INVALID {path}: {'; '.join(problems)}", file=sys.stderr)
            return 1
        if manifest_revision:
            for evaluator_role in ("scorer", "adversarial_reviewer"):
                evaluator = record["assessment"][evaluator_role]
                reference = evaluator["calibration_reference"]
                artifact = verified_artifacts.get(reference)
                if (
                    artifact is None
                    or artifact["kind"] != "calibration_reference"
                    or artifact["sha256"] != evaluator["calibration_sha256"]
                ):
                    print(
                        f"CALIBRATION_UNSEALED: {path} {evaluator_role} reference "
                        f"{reference!r} is not covered by the verified manifest with its declared hash",
                        file=sys.stderr,
                    )
                    return 1
        if record["condition"] not in conditions_for_test(record["test_id"]):
            expected = ", ".join(conditions_for_test(record["test_id"]))
            print(
                f"INVALID {path}: condition {record['condition']!r} is not valid for "
                f"{record['test_id']}; expected one of: {expected}",
                file=sys.stderr,
            )
            return 1
        records.append(record)

    rubric = load_json(RUBRIC)
    weights = {item["id"]: item["weight"] for item in rubric["dimensions"]}
    minimum_repetitions = max(3, load_json(CATALOG)["protocol"]["minimum_repetitions"])

    def group_for(test_id: str, condition: str) -> list[dict]:
        return [r for r in records if r["test_id"] == test_id and r["condition"] == condition]

    def repetition_status(group: list[dict]) -> tuple[bool, str]:
        repetitions = [r["repetition"] for r in group]
        if len(set(repetitions)) != len(repetitions):
            return False, "DUPLICATE_REPETITION"
        if len(repetitions) < minimum_repetitions:
            return False, f"NOT_VERIFIED ({len(repetitions)}/{minimum_repetitions})"
        return True, "PASS"

    def assessed_dimensions(group: list[dict]) -> set[str]:
        # A dimension counts as assessed only when every repetition has a
        # valid numeric score. Partial scoring must not masquerade as full
        # dimension coverage in a comparison.
        return {
            dimension for dimension in weights
            if group and all(
                isinstance(r["scores"].get(dimension), int)
                and not isinstance(r["scores"].get(dimension), bool)
                for r in group
            )
        }

    def score_for(group: list[dict], dimensions: set[str]) -> tuple[float | None, int]:
        covered = sum(weights[d] for d in dimensions)
        if not covered:
            return None, 0
        weighted_total = 0.0
        for dimension in dimensions:
            values = [r["scores"].get(dimension) for r in group]
            values = [v for v in values if isinstance(v, int) and not isinstance(v, bool)]
            weighted_total += weights[dimension] * (statistics.mean(values) / 5.0) * 100.0
        return weighted_total / covered, covered

    def evidence_gate_status(group: list[dict]) -> bool:
        # A weighted score is not eligible for comparison unless every record
        # has an explicit PASS decision and every mandatory hard gate passes.
        # NOT_ASSESSED and FAIL are both fail-closed.
        return bool(group) and all(
            record["decision"] == "pass"
            and all(status == "pass" for status in record["hard_gates"].values())
            for record in group
        )

    lines = [
        "# Performance Lab comparison report", "",
        (f"Verified Ed25519 evidence manifest: PASS; candidate revision: {manifest_revision}." if manifest_revision else "UNSEALED UNIT-TEST REPORT — not a release artifact."), "",
        f"Each condition requires at least {minimum_repetitions} distinct repetitions. Comparisons require identical assessed-dimension identities; equal aggregate weight coverage alone is insufficient.", "",
        "| Test | Condition | Runs | Repetition gate | Evidence gate | Assessed dimensions | Assessed weight | Weighted score /100 | Worst dimension | Hard-gate failures | Gates not assessed | Decisions |",
        "|---|---:|---:|---|---|---|---:|---:|---|---:|---:|---|"
    ]
    for test_id in TEST_IDS:
        for condition in conditions_for_test(test_id):
            group = group_for(test_id, condition)
            repetition_ok, rep_status = repetition_status(group)
            evidence_ok = evidence_gate_status(group)
            eligible = repetition_ok and evidence_ok
            evidence_status = "PASS" if evidence_ok else "NOT_VERIFIED"
            dimensions = assessed_dimensions(group)
            score_value, covered = score_for(group, dimensions) if eligible else (None, sum(weights[d] for d in dimensions))
            means = {}
            if eligible:
                for dimension in dimensions:
                    values = [r["scores"].get(dimension) for r in group]
                    values = [v for v in values if isinstance(v, int) and not isinstance(v, bool)]
                    if values:
                        means[dimension] = statistics.mean(values)
            score = f"{score_value:.1f}" if score_value is not None else ("NOT_VERIFIED" if not eligible else "NOT_ASSESSED")
            worst = min(means, key=means.get) if means else ("NOT_VERIFIED" if not eligible else "NOT_ASSESSED")
            gate_failures = sum(1 for r in group for status in r["hard_gates"].values() if status == "fail")
            gate_unassessed = sum(1 for r in group for status in r["hard_gates"].values() if status == "not_assessed")
            decisions = ", ".join(sorted({r["decision"] for r in group})) or "NO_RUNS"
            coverage = f"{covered}/100" if dimensions else "0/100"
            dimension_label = ", ".join(sorted(dimensions)) or "NOT_ASSESSED"
            lines.append(f"| {test_id} | {condition} | {len(group)} | {rep_status} | {evidence_status} | {dimension_label} | {coverage} | {score} | {worst} | {gate_failures} | {gate_unassessed} | {decisions} |")

    lines += ["", "## PL-005 fusion comparison", ""]
    comparator_names = ["baseline", *SPECIALIST_ARMS]
    comparator_groups = {name: group_for("PL-005", name) for name in comparator_names}
    fused_group = group_for("PL-005", "fused")
    all_groups = {**comparator_groups, "fused": fused_group}
    repetition_failures = [
        f"{name}={repetition_status(group)[1]}"
        for name, group in all_groups.items()
        if not repetition_status(group)[0]
    ]
    evidence_gate_failures = [name for name, group in all_groups.items() if not evidence_gate_status(group)]
    if repetition_failures:
        lines.append("NOT_VERIFIED: minimum distinct repetition requirement not met: " + "; ".join(repetition_failures) + ".")
    elif evidence_gate_failures:
        lines.append("NOT_VERIFIED: mandatory hard gates and independent review decisions must explicitly PASS for every repetition in every arm; blocked arms: " + ", ".join(evidence_gate_failures) + ".")
    else:
        dimension_sets = {name: assessed_dimensions(group) for name, group in all_groups.items()}
        reference_dimensions = dimension_sets["fused"]
        mismatches = [
            f"{name}=[{', '.join(sorted(dimensions)) or 'NONE'}]"
            for name, dimensions in dimension_sets.items()
            if dimensions != reference_dimensions
        ]
        missing_scores = [name for name, dimensions in dimension_sets.items() if not dimensions]
        if missing_scores:
            lines.append("NOT_ASSESSED: no scored rubric dimensions for: " + ", ".join(missing_scores) + ".")
        elif mismatches:
            lines.append("NOT_COMPARABLE: assessed-dimension identities differ across arms; " + "; ".join(mismatches) + ". Equal total weight coverage does not establish equivalent coverage.")
        else:
            scored = {name: score_for(group, dimension_sets[name])[0] for name, group in all_groups.items()}
            best_name = max(comparator_names, key=lambda name: scored[name])
            delta = scored["fused"] - scored[best_name]
            lines.append(f"Fused descriptive score: {scored['fused']:.1f}/100; strongest baseline/isolated-specialist comparator: {best_name} at {scored[best_name]:.1f}/100; descriptive delta: {delta:+.1f} points.")
            lines.append("This delta is not proof of synergy. Review matched tasks, per-dimension regressions, hard gates, latency/resource cost, ablation evidence and independent scoring before any conclusion.")

    lines += ["", "## Per-dimension repeatability", "",
              "| Test | Condition | Dimension | Runs | Median (1–5) | Range (1–5) |",
              "|---|---|---|---:|---:|---:|"]
    for test_id in TEST_IDS:
        for condition in conditions_for_test(test_id):
            group = group_for(test_id, condition)
            for dimension in weights:
                values = [r["scores"].get(dimension) for r in group]
                values = [v for v in values if isinstance(v, int) and not isinstance(v, bool)]
                med = f"{statistics.median(values):.1f}" if values else "NOT_ASSESSED"
                spread = f"{min(values)}-{max(values)}" if values else "NOT_ASSESSED"
                lines.append(f"| {test_id} | {condition} | {dimension} | {len(values)} | {med} | {spread} |")

    lines += ["", "## Evidence limitations", "",
              "- Scores and hard-gate results are reviewer supplied; this tool does not independently judge outputs. Missing gates remain NOT_ASSESSED and cannot be treated as passes.",
              "- A condition with fewer than the protocol minimum of distinct repetitions is NOT_VERIFIED; duplicate repetition numbers do not increase the count.",
              "- PL-005 comparability requires the exact same assessed rubric dimensions in every arm, not merely equal summed weights.",
              "- Hash validation detects altered raw outputs or pilot inputs, but does not authenticate the operator or reviewer.",
              "- A failed hard gate cannot be offset by a weighted score.",
              "- This report does not establish improvement unless configurations, raw outputs, scoring and confounders are independently checked."]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0

def command_seal(args) -> int:
    """Create a signed manifest over explicitly listed evidence artifacts."""
    root = Path(args.evidence_root)
    key_path = Path(args.private_key)
    try:
        if os.name == "posix" and stat.S_IMODE(key_path.stat().st_mode) & 0o077:
            print("private key file permissions must exclude group and other access", file=sys.stderr)
            return 2
        artifacts = json.loads(Path(args.artifacts_json).read_text(encoding="utf-8"))
        if not isinstance(artifacts, list):
            raise ValueError("artifacts JSON must contain an array")
        manifest = create_evidence_manifest(
            evidence_root=root,
            revision=args.revision,
            signer_id=args.signer_id,
            signer_role=args.signer_role,
            artifacts=artifacts,
            private_key_pem=key_path.read_bytes(),
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temporary.replace(target)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"SEAL_FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"SEALED: {len(manifest['artifacts'])} artifacts bound to revision {args.revision}; manifest written to {target}")
    return 0


def command_verify_manifest(args) -> int:
    """Verify a signed manifest against an externally supplied trust key and revision."""
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        errors = verify_evidence_manifest(
            manifest,
            evidence_root=args.evidence_root,
            trusted_public_key_pem=Path(args.public_key).read_bytes(),
            expected_revision=args.revision,
            expected_signer_id=args.expected_signer_id,
            expected_signer_role=args.expected_signer_role,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"MANIFEST_INVALID: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"VERIFIED: signed evidence manifest is valid for revision {args.revision}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="performance-lab")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate benchmark assets and run-record JSON")
    validate.add_argument("--records", default="artifacts/performance-lab")
    validate.set_defaults(func=command_validate)
    run = sub.add_parser("run", help="record supplied comparison outputs for all five tests, including isolated PL-005 specialists")
    run.add_argument("--responses", required=True, help="JSON mapping each PL test to required condition arms and repetition arrays")
    run.add_argument("--out", default="artifacts/performance-lab")
    run.add_argument("--operator", required=True)
    run.add_argument("--repetitions", type=int, default=3)
    run.add_argument("--evidence-root", required=True, help="root directory for the sealed evidence batch")
    run.add_argument("--revision", required=True, help="exact frozen 40-character candidate commit SHA")
    run.add_argument("--signer-id", required=True)
    run.add_argument("--signer-role", required=True, choices=["evidence-custodian", "independent-reviewer", "release-approver"])
    run.add_argument("--private-key", required=True, help="protected Ed25519 private-key PEM; never commit this key")
    run.add_argument("--manifest-out", help="manifest destination (defaults to evidence-root/evidence-manifest.json)")
    run.set_defaults(func=command_run)
    report = sub.add_parser("report", help="create a descriptive comparison report from validated records")
    report.add_argument("--records", default="artifacts/performance-lab")
    report.add_argument("--out", default="artifacts/performance-lab/report.md")
    report.add_argument("--evidence-root", required=True, help="root containing the sealed run records and raw evidence")
    report.add_argument("--manifest", required=True, help="revision-bound signed evidence manifest")
    report.add_argument("--revision", required=True, help="exact candidate commit SHA expected in the manifest and every run record")
    report.add_argument("--public-key", required=True, help="independently trusted Ed25519 public-key PEM")
    report.add_argument("--expected-signer-id", help="externally trusted signer identity")
    report.add_argument("--expected-signer-role", choices=["evidence-custodian", "independent-reviewer", "release-approver"])
    report.set_defaults(func=command_report)
    seal = sub.add_parser("seal", help="sign listed evidence artifacts with an Ed25519 key")
    seal.add_argument("--evidence-root", required=True)
    seal.add_argument("--artifacts-json", required=True, help="JSON array of relative artifact path/kind objects")
    seal.add_argument("--revision", required=True, help="exact 40-character candidate Git commit SHA")
    seal.add_argument("--signer-id", required=True)
    seal.add_argument("--signer-role", required=True, choices=["evidence-custodian", "independent-reviewer", "release-approver"])
    seal.add_argument("--private-key", required=True, help="path to protected Ed25519 private-key PEM; never commit this key")
    seal.add_argument("--out", default="artifacts/performance-lab/evidence-manifest.json")
    seal.set_defaults(func=command_seal)
    verify = sub.add_parser("verify-manifest", help="verify a signed manifest against an external trust key and exact revision")
    verify.add_argument("--evidence-root", required=True)
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--revision", required=True)
    verify.add_argument("--public-key", required=True, help="path to externally trusted Ed25519 public-key PEM")
    verify.add_argument("--expected-signer-id")
    verify.add_argument("--expected-signer-role", choices=["evidence-custodian", "independent-reviewer", "release-approver"])
    verify.set_defaults(func=command_verify_manifest)
    args = parser.parse_args(argv)
    if getattr(args, "repetitions", 3) < 3:
        parser.error("the controlled protocol requires at least three repetitions")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
