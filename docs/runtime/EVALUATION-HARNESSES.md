# Evaluation Harnesses — Promptfoo and DeepEval

The six-provider design assigns complementary evaluation responsibilities to Promptfoo and DeepEval. This milestone adds optional local-model harnesses but does not yet make them CI release gates.

## Direct version pins reviewed
- Promptfoo: 0.125.1 (npm).
- DeepEval: 4.3.4 (PyPI).
- Promptfoo's current docs require Node.js >=22.22; Node 24 is selected in .nvmrc.

These are direct package pins only. Transitive dependency lockfiles, hashes, SBOM and licence review remain required before production.

## Promptfoo
Location: evaluation/promptfoo/

The smoke test uses Promptfoo's OpenAI-compatible provider against a running llama.cpp server, configured through OPENAI_BASE_URL. It checks one deterministic READY response. It does not require a remote model provider or paid API.

Run with scripts/run-promptfoo-eval.sh. If authentication is enabled, provide OPENAI_API_KEY through a secret manager or shell environment.

## DeepEval
Location: evaluation/deepeval/

The optional Pytest test uses DeepEval LocalModel with an OpenAI-compatible local endpoint and evaluates Answer Relevancy and Faithfulness for a fixed RAG example.

Install the direct dependency with:
```bash
python -m pip install -r requirements-evaluation.txt
```

Set LOCAL_MODEL_NAME, LOCAL_MODEL_BASE_URL and LOCAL_MODEL_API_KEY, then run scripts/run-deepeval-eval.sh. For an unauthenticated local server, DeepEval documents that a placeholder API key is accepted; still use a non-secret local placeholder and never commit credentials.

## Division of responsibility
- Promptfoo: prompt/model regression, scenario datasets, adversarial and red-team probes, CI quality gates.
- DeepEval: metric-based answer relevance, faithfulness, RAG and agent trajectory quality.

Avoid duplicating identical assertions across both suites. Share reviewed test cases and trace/correlation identifiers where useful.

## Limitations and release blockers
- Neither harness is run by the core CI workflow; they require a live local model endpoint and optional dependencies.
- The Promptfoo direct version is pinned in the invocation, but npm transitive dependencies are not yet locked.
- DeepEval is directly pinned, but Python transitive dependencies are not yet hash-locked.
- The current test datasets are smoke fixtures, not a statistically meaningful benchmark.
- No judge-model calibration, inter-rater study, adversarial coverage review or independent evaluation audit has been completed.
- Do not use these harnesses as production release gates until dependency locks, service-backed runs, reviewed datasets, thresholds and reproducible result artifacts are in place.
