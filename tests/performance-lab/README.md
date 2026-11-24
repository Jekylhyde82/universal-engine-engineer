# Running the Performance Lab

The runner records supplied outputs; it does **not** invoke ChatGPT, another model, or an external agent. This separation prevents a harness run from being misrepresented as an actual model benchmark.

## Install

```bash
python -m pip install -e ".[test]"
```

## Validate the catalogue and schema

```bash
performance-lab validate --records tests/performance-lab
pytest -q
```

## Capture five-test comparison runs

Prepare a JSON file with all five test IDs. Each condition must contain at least three independently captured repetitions. Example shape:

```json
{
  "PL-001": {
    "baseline_configuration": {"model": "record exact model/version/settings"},
    "experimental_configuration": {"model": "record exact model/version/settings"},
    "baseline": [
      {"output": "raw baseline output"},
      {"output": "raw baseline output"},
      {"output": "raw baseline output"}
    ],
    "experimental": [
      {"output": "raw experimental output"},
      {"output": "raw experimental output"},
      {"output": "raw experimental output"}
    ]
  }
}
```

Repeat the baseline/experimental structure for PL-002 through PL-004. PL-005 uses a different, explicitly multi-arm structure: provide `baseline`, `specialist_1` through `specialist_9`, and `fused`, each with its matching `<condition>_configuration` object and at least three outputs. The nine specialist labels are stable arm identifiers; record the exact specialist identity, version and settings in each configuration. The report compares fused against the strongest scored baseline/specialist comparator only when all ten comparator arms and fused have matching assessed-weight coverage. That descriptive delta is not itself proof of synergy. Each repetition may also include reviewer-supplied `scores`, `hard_gates`, `limitations`, `confounders`, `decision`, and reviewer references. The runner never invents scores.

```bash
performance-lab run --responses responses.json --operator "operator-id" --out artifacts/performance-lab
performance-lab validate --records artifacts/performance-lab
performance-lab report --records artifacts/performance-lab --out artifacts/performance-lab/report.md
```

The runner requires at least three repetitions. It hashes the fixed pilot input, canonicalized configuration and every raw output, then verifies those hashes again when validating or reporting. The entire five-test input batch (PL-001–004 two-condition; PL-005 eleven-arm) is preflighted before any record is written, preventing incomplete input from leaving a partial batch. It writes unique run records and refuses to overwrite existing records. Hashes detect content changes; they do not authenticate the operator or reviewer. Protect artifacts and retain their hashes. Add independent review references only after a reviewer has actually completed that work.

## Interpretation

- Empty/missing scores are not zero; they are unassessed.
- Weighted scores use the versioned rubric weights and disclose assessed-weight coverage; missing dimensions remain NOT_ASSESSED.
- Per-dimension median and range are reported across repetitions. A failed hard gate cannot be offset by a weighted score.
- CI tests the harness and fixtures, not model quality.
- A successful CI run does not mean the five model trials have been executed.


## Known protocol limitations

See [the adversarial audit](../../docs/performance-lab-v1.0/ADVERSARIAL_AUDIT.md). In particular, PL-005 now supports baseline, nine isolated specialist arms and fused capture, but no synergy claim is possible until all arms are executed and independently scored. PL-001 now includes a self-contained fictional reference packet with five supported facts and two explicitly unsupported claims. These remain explicit blockers, not assumed passes.
