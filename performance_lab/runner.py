"""Five-test runner. It records supplied outputs; it does not generate model outputs or scores."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "tests" / "performance-lab"
CATALOG = ASSETS / "test-catalog.v1.0.json"
CASES = ASSETS / "pilot-cases.v1.0.json"
RUBRIC = ASSETS / "scoring-rubric.v1.0.json"
SCHEMA = ROOT / "performance_lab" / "run-record.schema.json"
TEST_IDS = [f"PL-{i:03d}" for i in range(1, 6)]


def load_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_assets() -> list[str]:
    errors: list[str] = []
    try:
        catalog, cases, rubric = load_json(CATALOG), load_json(CASES), load_json(RUBRIC)
        schema = load_json(SCHEMA)
        Draft202012Validator.check_schema(schema)
        ids = [item["id"] for item in catalog["tests"]]
        case_ids = [item["test_id"] for item in cases["cases"]]
        if ids != TEST_IDS:
            errors.append(f"catalog test IDs must be exactly {TEST_IDS}; got {ids}")
        if case_ids != TEST_IDS:
            errors.append(f"pilot cases must cover exactly {TEST_IDS}; got {case_ids}")
        if sum(item["weight"] for item in rubric["dimensions"]) != 100:
            errors.append("rubric dimension weights must total 100")
        if len(cases["cases"]) != 5:
            errors.append("exactly five pilot cases are required")
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        errors.append(f"asset load/structure error: {exc}")
    return errors


def validate_record(record: dict, schema: dict) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
            for error in validator.iter_errors(record)]


def command_validate(args) -> int:
    errors = validate_assets()
    schema = load_json(SCHEMA)
    for path in sorted(Path(args.records).glob("*.json")):
        try:
            errors.extend(f"{path}: {message}" for message in validate_record(load_json(path), schema))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
    if errors:
        print("\n".join(errors))
        return 1
    print("PASS: five catalog entries, five pilot cases, 100-point rubric, schema valid, records valid.")
    return 0


def command_run(args) -> int:
    errors = validate_assets()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    payload = load_json(Path(args.responses))
    cases = {item["test_id"]: item for item in load_json(CASES)["cases"]}
    schema = load_json(SCHEMA)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    created = 0
    for test_id in TEST_IDS:
        case = cases[test_id]
        trial = payload.get(test_id, {})
        for condition in ("baseline", "experimental"):
            repetitions = trial.get(condition, [])
            if len(repetitions) < args.repetitions:
                print(f"{test_id}/{condition}: need {args.repetitions} supplied repetitions; found {len(repetitions)}", file=sys.stderr)
                return 2
            config = trial.get(condition + "_configuration", {})
            for index, result in enumerate(repetitions[:args.repetitions], start=1):
                output = result.get("output", "")
                if not isinstance(output, str) or not output.strip():
                    print(f"{test_id}/{condition}/{index}: non-empty output required", file=sys.stderr)
                    return 2
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
                    "raw_output": output,
                    "raw_output_sha256": sha256(output),
                    "scores": result.get("scores", {}),
                    "hard_gates": result.get("hard_gates", {}),
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
    for path in sorted(Path(args.records).glob("*.json")):
        record = load_json(path)
        problems = validate_record(record, schema)
        if problems:
            print(f"INVALID {path}: {'; '.join(problems)}", file=sys.stderr)
            return 1
        records.append(record)
    lines = ["# Performance Lab comparison report", "", f"Records: {len(records)}", "",
             "| Test | Condition | Runs | Scored dimensions | Mean normalized score | Decision states |",
             "|---|---:|---:|---:|---:|---|"]
    for test_id in TEST_IDS:
        for condition in ("baseline", "experimental"):
            group = [r for r in records if r["test_id"] == test_id and r["condition"] == condition]
            values = [score for r in group for score in r["scores"].values() if isinstance(score, int)]
            mean = f"{statistics.mean(values) * 20:.1f}" if values else "NOT_ASSESSED"
            decisions = ", ".join(sorted({r["decision"] for r in group})) or "NO_RUNS"
            lines.append(f"| {test_id} | {condition} | {len(group)} | {len(values)} | {mean} | {decisions} |")
    lines += ["", "## Evidence limitations", "",
              "- Scores are operator/reviewer supplied; this tool does not independently judge outputs.",
              "- Missing scores remain NOT_ASSESSED; a mean is descriptive and never overrides a failed hard gate.",
              "- A report is not evidence of model improvement unless configurations, raw outputs, scoring and confounders are independently checked."]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="performance-lab")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate benchmark assets and run-record JSON")
    validate.add_argument("--records", default="artifacts/performance-lab")
    validate.set_defaults(func=command_validate)
    run = sub.add_parser("run", help="record supplied baseline/experimental outputs for all five tests")
    run.add_argument("--responses", required=True, help="JSON mapping each PL test to baseline and experimental repetition arrays")
    run.add_argument("--out", default="artifacts/performance-lab")
    run.add_argument("--operator", required=True)
    run.add_argument("--repetitions", type=int, default=3)
    run.set_defaults(func=command_run)
    report = sub.add_parser("report", help="create a descriptive comparison report from validated records")
    report.add_argument("--records", default="artifacts/performance-lab")
    report.add_argument("--out", default="artifacts/performance-lab/report.md")
    report.set_defaults(func=command_report)
    args = parser.parse_args(argv)
    if getattr(args, "repetitions", 3) < 3:
        parser.error("the controlled protocol requires at least three repetitions")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
