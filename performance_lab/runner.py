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
            prepared[test_id][condition] = (config, selected)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
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
                    "commit_sha": result.get("commit_sha", ""),
                    "notes": result.get("notes", "")
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
    print(f"Captured {created} immutable run records in {out}. Outputs were supplied by the operator; no model was invoked.")
    return 0


def command_report(args) -> int:
    records = []
    schema = load_json(SCHEMA)
    for path in sorted(Path(args.records).glob("PL-*.json")):
        record = load_json(path)
        problems = validate_record(record, schema)
        if problems:
            print(f"INVALID {path}: {'; '.join(problems)}", file=sys.stderr)
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
    run.set_defaults(func=command_run)
    report = sub.add_parser("report", help="create a descriptive comparison report from validated records")
    report.add_argument("--records", default="artifacts/performance-lab")
    report.add_argument("--out", default="artifacts/performance-lab/report.md")
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
