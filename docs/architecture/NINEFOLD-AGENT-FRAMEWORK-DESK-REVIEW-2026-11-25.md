# NINEFOLD INTRINSIC — Agent Framework Desk Review
**Review date:** 2026-11-25  
**Parent:** UNIVERSAL ENGINE / ENGINEER  
**Architecture:** NINEFOLD INTRINSIC — MULTIVERSAL OMNIVELOCITY PRIME (9 FOLD OMNI)  
**Governance:** NINEFOLD INTRINSIC — MULTIVERSAL OMNI GOVERNANCE PRIME  
**Intelligence / continuity:** AFI OM × EB9 PRIME  
**Review status:** Source-backed desk review; empirical benchmark and production approval remain outstanding.

## 1. Executive decision

The repository already contains a provider-neutral Python control-plane prototype and four adapter implementations (LangGraph, llama.cpp, LlamaIndex and Qdrant). The adapter tests use fakes or local HTTP stubs; they do not prove compatibility with installed, pinned upstream frameworks or live services. The current branch's CI is green, but this is not production certification.

**Recommended evaluation sequence (not an integration approval):**
1. LangGraph — primary orchestration-runtime candidate.
2. LlamaIndex — knowledge ingestion/retrieval candidate.
3. DSPy — evaluation-driven optimisation candidate.
4. OpenHands Software Agent SDK — isolated software-engineering executor candidate, only after sandbox boundary review.

Keep Promptfoo and DeepEval as complementary evaluation harnesses, not orchestration runtimes. Keep llama.cpp as an optional inference backend and Qdrant as a replaceable vector-store backend. Do not deploy overlapping orchestration frameworks merely to collect logos.

## 2. Repository evidence checked

Branch: `architecture/omnisight-ninefold-intrinsic-v0.1`  
PR: https://github.com/Jekylhyde82/universal-engine-engineer/pull/35  
Reviewed head: `aeeb3a7a19111117ff1b43bdefd2730ebe732f15`

Repository files inspected:
- `docs/runtime/FOUNDATION-DECISION.md`
- `docs/runtime/PROVIDER-ADAPTER-MAP.md`
- `docs/runtime/THREAT-MODEL.md`
- `docs/runtime/EVALUATION-HARNESSES.md`
- `docs/runtime/LANGGRAPH-ADAPTER.md`
- `docs/runtime/LLAMAINDEX-ADAPTER.md`
- `docs/architecture/NINEFOLD-AGENT-FRAMEWORK-CAPABILITY-BENCHMARK-v1.0.md`
- `pyproject.toml`, `requirements-evaluation.txt`, and the LangGraph, LlamaIndex and Qdrant adapter tests.

The current head has six associated GitHub Actions workflows completed successfully: VISION-DD policy core, OMNISIGHT PRIME contract validation, Performance Lab validation, NINEFOLD AFI PRIME runtime proof, Python Core, and Repository Capability Scout checks. These results verify those workflows at this head only. They do not replace independent security review, end-to-end provider tests, or target-device benchmarks.

### Existing adapter maturity

| Component | Repository state | What the current tests establish | What remains unproven |
|---|---|---|---|
| LangGraph | Adapter implemented | Injected builder/checkpointer contract, thread ID, resume path, deny path using fakes | Real pinned LangGraph package, durable checkpointer, restart recovery, interruption semantics, async/streaming |
| LlamaIndex | Adapter implemented | Injected index ingestion/retrieval and deny path using fakes | Real pinned package, ingestion pipeline, embedding/vector-store integration, persistence, retrieval quality |
| Qdrant | REST adapter implemented | Request shape and policy behavior against local HTTP stub | Live Qdrant, tenant/collection authorization, production TLS/network controls, recovery and load |
| llama.cpp | HTTP adapter implemented | Local stub contract and remote opt-in checks | Actual model/server compatibility, resource profile, throughput, quality and device suitability |
| Promptfoo | Evaluation harness documented | Local-model smoke-test design | Live repeatable evaluation, locked transitive dependencies, red-team corpus and thresholds |
| DeepEval | Evaluation harness documented; direct pin `deepeval==4.3.4` | Local-model RAG smoke-test design | Judge calibration, reproducibility, statistical coverage, locked dependencies and independent assessment |

The base package currently declares only PyYAML as a runtime dependency. Optional evaluation dependencies are separate. This is a good starting point for a light control plane, but it also means adapter tests intentionally avoid installing the actual upstream frameworks.

## 3. Candidate review — all nine selected groups

Scores are deliberately **Not Assessed** at this desk-review stage. Official documentation establishes advertised capability and intended usage, not measured reliability, security or superiority.

| Candidate | Best-fit role in this architecture | Desk-review finding | Main gate / concern |
|---|---|---|---|
| LangChain / LangGraph | LangGraph: orchestration runtime. LangChain: higher-level agent framework and model/tool abstractions. | These are distinct layers, not one interchangeable package. LangGraph best matches deterministic + agentic workflow control, checkpoints and human approval. | Test real durable checkpointer, interruption/resume, restart recovery, concurrency and policy enforcement. |
| OpenAI Agents SDK | Agent loop, tools, handoffs, guardrails, sessions and tracing. | Strong comparator for specialist delegation and compact SDK-owned agent loops. | Verify provider coupling, trace/data handling, external policy boundary and session persistence fit. |
| Google ADK | Agent construction, workflow agents and multi-agent composition. | Worth retaining as a portability and orchestration comparator. | Pin language/runtime track and verify maturity differences by language and deployment target. |
| Microsoft Agent Framework | Agent and graph workflows, harness, middleware, sessions and integrations. | Broad framework spanning agents, workflows and enterprise integrations. | Avoid duplicating LangGraph; evaluate only against a defined Microsoft/.NET or provider-interoperability need. |
| CrewAI | Role-based crews and stateful flows. | Useful comparator for task/role coordination and human-in-loop flows. | Compare orchestration determinism, traceability, memory semantics and control-plane fit against LangGraph. |
| Claude Agent SDK | Tool-enabled coding and multi-step engineering agent. | Strong coding-agent capability candidate with permissions, hooks and sessions. | Verify applicable Anthropic terms, provider coupling, permission modes and sandbox isolation. |
| OpenHands | Software-engineering agent and controlled repository executor. | Best candidate in this list for a dedicated code-execution work package. SDK separates agent behavior from workspace/runtime deployment. | Never run without an OS-enforced disposable sandbox, restricted mounts/network, resource limits and patch-only output. |
| LlamaIndex | Knowledge ingestion, indexing, retrieval, workflows and data-connected agents. | Strong fit for the knowledge plane; its ingestion pipeline and vector-store abstractions complement the current adapter boundary. | Retrieved content is untrusted; validate provenance, access control, deletion, metadata filtering and retrieval quality. |
| DSPy | Metric-driven evaluation and optimisation of LM programs. | Best treated as an optimisation/evaluation layer, not an agent orchestration runtime. | Require held-out data, leakage controls, reproducible metrics, cost ceilings and regression gates. |

### Important taxonomy correction

The original benchmark list grouped LangChain and LangGraph as one candidate. Current first-party documentation describes a layered stack: LangGraph is the lower-level orchestration runtime; LangChain provides higher-level agent framework abstractions; Deep Agents is a higher-level harness. Assess these as separate components when testing a concrete layer. This is a taxonomy refinement, not an extra pillar, UMIC or fusion authority.

## 4. First-party source register

Sources were checked on 2026-11-25. These links are evidence pointers, not endorsements.

- LangChain OSS stack and layer distinction: https://www.langchain.com/oss-overview
- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph persistence and checkpointers: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph interrupts and approval/resume: https://docs.langchain.com/oss/python/langgraph/interrupts
- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents/sdk
- OpenAI agent orchestration and handoffs: https://developers.openai.com/api/docs/guides/agents/orchestration
- Google ADK documentation: https://google.github.io/adk-docs/
- Microsoft Agent Framework overview: https://learn.microsoft.com/agent-framework/overview
- CrewAI documentation: https://docs.crewai.com/
- Claude Agent SDK overview: https://code.claude.com/docs/en/agent-sdk/overview
- OpenHands SDK architecture: https://docs.openhands.dev/sdk/arch/overview
- OpenHands runtime architecture: https://docs.openhands.dev/openhands/usage/architecture/runtime
- LlamaIndex framework documentation: https://developers.llamaindex.ai/python/framework/
- LlamaIndex ingestion pipeline: https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/
- DSPy optimisation: https://dspy.ai/learn/optimization/optimizers/
- DSPy evaluation: https://dspy.ai/current/api/evaluation/

## 5. Architecture and safety findings

1. **Keep the control plane authoritative.** Framework middleware, agent guardrails and provider-side approvals are useful defence-in-depth, but must not replace the Universal Engine policy decision, scoped identity, capability lifecycle or independent assurance.
2. **Separate orchestration from execution.** LangGraph may coordinate a workflow; OpenHands may execute code inside an isolated workspace. The orchestrator must not grant the executor ambient host credentials or unrestricted network access.
3. **Separate operational state from canonical memory.** Checkpoints and framework stores are runtime state. They are not automatically approved EB9 PRIME memory. Promotion requires provenance, scope, retention, conflict handling and explicit policy.
4. **Treat retrieved material and tool output as untrusted data.** Preserve source attribution and distinguish evidence from instructions, hypotheses, simulation and prediction.
5. **Keep evaluation independent.** DSPy optimisers must not tune against the final holdout set. LLM-as-judge metrics need calibration and human review. Candidate frameworks cannot certify themselves.
6. **Do not target the 4 GB Android handset with server workloads by default.** Keep the phone as a control terminal; place orchestration, vector databases and code sandboxes on a measured local host or cloud runtime. Offline phone-side capability is a separate constrained workload requiring device benchmarks.
7. **Avoid false security from process separation.** The repository's nine-process runtime proof is useful for state/fault-boundary tests, but its own threat model correctly says it is not a hardened OS isolation boundary.
8. **Keep governance above capability pillars.** The governing architecture is the authority that governs the nine capability domains; it must not be counted as one of those nine domains. The current benchmark document already expresses governance separately from the pillars.

## 6. Next reproducible benchmark work

Run these in an isolated development environment, not on the phone and not against production data:

### Workload A — LangGraph
- Install and pin a reviewed LangGraph version plus one durable checkpointer backend.
- Execute a deterministic workflow with an approval interrupt.
- Deny one action; prove no side effect occurred.
- Pause, restart the process, resume using the same thread/checkpoint, and verify state.
- Inject timeout, duplicate request and provider failure; record recovery and idempotency.
- Compare durable write modes and measure latency/storage overhead.

### Workload B — LlamaIndex
- Use a fixed, licensed, synthetic document corpus with known answers and conflicting sources.
- Run ingestion, metadata preservation, retrieval and deletion/update tests.
- Compare chunking, embedding and vector-store choices with a fixed query set.
- Measure recall@k, precision@k, groundedness, latency and cost.
- Attempt prompt injection embedded in retrieved documents; verify it remains data, not authority.

### Workload C — DSPy
- Define explicit task metrics and a baseline program.
- Split development, validation and held-out test sets before optimisation.
- Run one optimiser with fixed inference budget and seed where supported.
- Compare baseline vs optimised outputs on untouched holdout cases.
- Report quality, variance, cost, latency and regressions; reject optimisation that improves a proxy while harming task success or safety.

### Workload D — OpenHands
- Use a disposable container or microVM, non-root identity, scratch-only workspace and no host secrets.
- Disable or tightly restrict egress; enforce CPU, memory, disk and wall-clock budgets.
- Provide a synthetic repository issue and require a patch proposal plus tests.
- Test malicious repository instructions, prompt injection, secret discovery attempts and destructive commands.
- Require independent patch review; prohibit autonomous merge, release or deployment.

### Common evidence record
For every run preserve: framework/version and dependency lock, source commit, environment/hardware, dataset fixture digest, configuration, task ID, start/end time, tool calls, approvals/denials, side effects, latency, token/API cost, CPU/RAM/storage, result, failure/recovery outcome, evaluator identity, rubric, confidence and raw evidence location. Hashes alone are not a substitute for inspectable evidence.

## 7. Decision status

| Decision | Status |
|---|---|
| Continue source-backed evaluation of all nine selected groups | APPROVED FOR RESEARCH |
| Deep-test LangGraph, LlamaIndex, DSPy and OpenHands first | PROVISIONAL PRIORITY |
| Keep Promptfoo and DeepEval complementary | RETAIN |
| Install every candidate | NOT APPROVED |
| Production integration or deployment | NOT APPROVED |
| Claim empirical benchmark scores | NOT ASSESSED |
| Claim production security or independent verification | NOT VERIFIED |

**Completion boundary:** This desk review is complete. The empirical benchmark is not complete until the four workload families are run with reproducible evidence, and no integration is complete until its hard gates and independent review pass.

**Governing principle:** PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.
