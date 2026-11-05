# Six-Source Evaluation and Acceptance Matrix

**Status:** Proposed gates; no tests have been run by this document.

| Candidate | Primary value | Required proof | Main risks / rejection triggers |
|---|---|---|---|
| LangGraph | Stateful, durable, human-interruptible workflows | Deterministic state-transition tests; checkpoint recovery; interruption/approval tests; retry/idempotency; failure recovery | Hidden side effects, non-deterministic state, unbounded loops, unsafe tool permissions |
| llama.cpp | Optional local inference and model portability | Target-device RAM/latency/thermal/battery benchmark; model hash and license record; API conformance; crash/recovery test | Phone memory pressure, unsupported hardware, thermal throttling, model license mismatch |
| LlamaIndex | Document parsing, ingestion and retrieval | Source-to-chunk provenance; parser accuracy corpus; access-control filtering; injection-content tests; reproducible indexing | Untrusted document instructions, parser vulnerabilities, changing package/roadmap boundaries |
| Qdrant | Filtered vector persistence and search | Recall@k/precision@k on fixed dataset; tenant isolation tests; backup/restore; deletion verification; latency/load test | Cross-tenant leakage, stale embeddings, operational overhead, backup gaps |
| Promptfoo | Prompt/model regression and red-team harness | Versioned test suite; repeatable baselines; regression detection; adversarial coverage; credential isolation | False negatives, unsafe test payloads, secret exposure, overclaiming from finite tests |
| DeepEval | Metric-driven LLM/RAG quality tests | Dataset/metric/judge pinning; reproducibility; threshold calibration; human-reviewed sample; failure examples | Judge bias, metric gaming, false precision, duplicated evaluation effort |

## Cross-cutting scorecard
Score each dimension independently on a documented 0–5 scale; do not hide a critical failure in an average.
- Capability fit and measurable value.
- Correctness and quality.
- Reliability and recoverability.
- Security and privacy.
- License and provenance.
- Integration complexity and dependency burden.
- Performance, resource use and cost.
- Maintainability and upstream activity.
- Portability and replaceability.
- Observability and evidence quality.

A zero in security, license/provenance, or data isolation blocks adoption regardless of total score.

## Minimum experiment design
For each candidate:
1. Pin exact source commit and package/artifact version.
2. Define one narrow use case and baseline without the candidate.
3. Use a versioned, representative dataset and deterministic fixtures where possible.
4. Measure before/after quality, latency, resource use, failure rate and operating cost.
5. Include adversarial, malformed, unavailable and degraded-provider cases.
6. Re-run independently and retain raw outputs, config hashes and test commands.
7. Record decision: reject, defer, trial, or approve for implementation.

## Target device gate
For llama.cpp and any phone-resident component, measure on the actual OPPO A6 4G configuration before recommending deployment. Capture free RAM, peak RSS, model size, context length, cold-start time, tokens/second, temperature/thermal throttling, battery drain and stability. A successful desktop test does not satisfy the mobile gate.

## Release gate
No integration may be marked verified or operational until all mandatory tests pass, risks are triaged, the exact artifact and configuration are pinned, rollback is demonstrated, and an independent reviewer confirms the evidence.
