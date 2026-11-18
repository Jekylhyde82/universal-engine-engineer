# Nine-Technology Integration Plan

**Project:** MULTIVERSAL OMNIVELOCITY PRIME — GENIUS ENGINEER PRIME  
**Foundation:** NINEFOLD INTRINSIC  
**Governing invariant:** INTRINSIC BY DESIGN  
**Status:** Source-verified candidates; integration design only  
**Review date:** 2026-11-18  
**Parent design:** PR #8, `integration/six-ai-capability-sources`

## Executive decision

The nine requested upstream projects are now registered as candidate capability providers. This is not a declaration that they are installed, integrated, tested or approved for production.

The existing six-source design in PR #8 remains the foundation. This plan extends it with OpenHands, SWE-agent and Goose while preserving the existing adapter contract and evaluation gates.

**Do not install all nine as one stack.** They occupy different layers and several overlap. The architecture must depend on stable internal contracts, not on all nine upstream frameworks simultaneously.

## Candidate registry

| Technology | Canonical repository | Verified repository licence | Intended responsibility | Proposed integration mode | Current disposition |
|---|---|---|---|---|---|
| LangGraph | https://github.com/langchain-ai/langgraph | MIT | Durable stateful workflow orchestration, checkpoints, interrupts and human approval | Optional workflow adapter | Candidate |
| llama.cpp | https://github.com/ggml-org/llama.cpp | MIT | Local model inference and local HTTP inference endpoint | Optional inference endpoint adapter | Candidate; target-device test required |
| LlamaIndex | https://github.com/run-llama/llama_index | MIT | Document connectors, parsing, ingestion, indexing and retrieval | Optional knowledge adapter | Candidate |
| Qdrant | https://github.com/qdrant/qdrant | Apache-2.0 | Vector persistence, similarity search and metadata filtering | Optional vector-store service adapter | Candidate |
| Promptfoo | https://github.com/promptfoo/promptfoo | MIT | Prompt/model regression, provider comparison and red-team tests | Development/CI evaluation tool | Candidate |
| DeepEval | https://github.com/confident-ai/deepeval | Apache-2.0 | Python-native LLM, agent and RAG metrics | Development/CI evaluation tool | Candidate |
| OpenHands | https://github.com/OpenHands/OpenHands | MIT | Autonomous software engineering agent and delegated coding workflows | Isolated coding-agent provider | Candidate; high privilege risk |
| SWE-agent | https://github.com/SWE-agent/SWE-agent | MIT | Research/benchmark comparison for issue-solving agents | Evaluation-only adapter | Defer as primary executor; upstream recommends mini-SWE-agent |
| Goose | https://github.com/aaif-goose/goose | Apache-2.0 | Extensible local/CLI/API agent for coding and general tool workflows | Optional coding/tool-agent provider | Candidate; high privilege risk |

Licence identifiers above were checked against GitHub repository metadata on 2026-11-18. Before redistributing binaries or source, verify the actual licence text, notices, bundled assets, dependency licences, model licences and any optional provider components at the exact selected commit.

### Important SWE-agent finding

The SWE-agent maintainers state in the upstream README that mini-SWE-agent has superseded SWE-agent for most new work and recommend mini-SWE-agent as the default. Therefore:

- Keep the requested SWE-agent repository in the candidate register and benchmark it as requested.
- Do not silently select it as the production coding agent.
- Run a separate comparison against https://github.com/SWE-agent/mini-swe-agent.
- Preserve the distinction between SWE-agent and its successor in provenance and evaluation records.

## Architecture placement

### A. Control plane

**LangGraph** owns workflow state transitions, resumability and explicit pause/resume points. It does not own global policy, identity, capability approval or permission escalation.

The Universal Engine remains the policy authority. A LangGraph interrupt is a mechanism to request a decision, not the authority to approve itself.

### B. Model and knowledge plane

- **llama.cpp:** optional local inference engine. Initially connect through a constrained HTTP/API adapter. Record runtime build, model hash, quantization, context length and inference parameters. Model weights and their licences are separately governed.
- **LlamaIndex:** ingestion, parsing, chunking, indexing and retrieval. Each item must preserve source URI, content hash, parser version, chunking configuration, access labels and provenance.
- **Qdrant:** optional vector persistence service behind a provider-neutral vector-store contract. Enforce tenant/namespace isolation server-side; include backup, restore, export and deletion tests.

LlamaIndex is not the database and Qdrant is not the knowledge-governance authority. Retrieved documents, embeddings and search results are untrusted data, never executable instructions.

### C. Evaluation and verification plane

- **Promptfoo:** black-box prompt/model comparison, regression suites and adversarial/red-team probes.
- **DeepEval:** metric-based tests for answer quality, faithfulness, task completion, agent trajectories and RAG behaviour.

These tools overlap. Use Promptfoo as the main declarative black-box/CI harness and DeepEval for selected Python-native metrics where those metrics add measurable value. Do not run duplicate suites merely to increase tool count. Neither tool independently proves safety or correctness.

### D. Software-engineering agent plane

- **OpenHands:** candidate for complex delegated engineering tasks and interactive software development.
- **Goose:** candidate for local CLI/API workflows and extensible tool integration.
- **SWE-agent:** research comparison; compare against mini-SWE-agent before deciding whether any SWE-agent lineage is suitable.

These are alternative agent providers, not three mandatory agents running with unrestricted authority. Select one initial executor only after sandbox and benchmark testing. All agents must use the same constrained task, repository, evidence and approval contracts.

## Integration order and gates

### Stage 0 — Source and architecture registration

- Preserve PR #8's six-source work.
- Register all nine candidates with canonical repository URL, exact reviewed upstream SHA, licence, package/artifact identity and review timestamp.
- Record unresolved provenance and third-party licensing separately.
- No package installation, model download or source vendoring.

### Stage 1 — Internal contracts and deterministic mocks

Define and test provider-neutral interfaces before adopting any upstream runtime:

1. `WorkflowProvider` — state transition, checkpoint, interrupt, resume and cancellation.
2. `InferenceProvider` — model identity, inference request/result, resource metrics and cancellation.
3. `KnowledgeProvider` — ingestion, source provenance, access labels and retrieval citations.
4. `VectorStoreProvider` — collection lifecycle, filtered query, upsert, delete, export and restore.
5. `EvaluationProvider` — test suite, dataset, metric, thresholds, raw results and reproducibility metadata.
6. `CodingAgentProvider` — scoped task, isolated workspace, tool permissions, patch output, test evidence and explicit approval request.

All interfaces use versioned schemas and a common request/result/evidence envelope. Mock implementations must pass failure, timeout, cancellation, malformed output, idempotency, redaction and rollback tests before real providers are introduced.

### Stage 2 — Low-risk evaluation integration

1. Promptfoo and selected DeepEval metrics against deterministic fixtures.
2. LlamaIndex ingestion against a fixed document corpus with provenance checks.
3. Qdrant adapter against a disposable isolated collection, including tenant-isolation and backup/restore tests.
4. LangGraph orchestration with human approval interrupts and restart/recovery tests.

### Stage 3 — Model and coding-agent integration

5. llama.cpp endpoint adapter; only then evaluate on-device execution.
6. One coding-agent provider selected from OpenHands, Goose, SWE-agent/mini-SWE-agent after benchmark and sandbox comparison.

No coding agent receives unrestricted shell, network, repository write or credential access. Begin with read-only repository inspection and patch proposals. Any write is restricted to a disposable worktree or isolated branch. Main, existing PRs and user-authored work remain protected.

### Stage 4 — End-to-end proof

Demonstrate:

Discover capability → register provenance → assess compatibility → propose → critic challenge → approval → isolated execution → tests → independent verification → evidence record → rollback.

The complete flow must work with provider mocks first, then with one selected provider per interface. The system must remain functional when optional providers are absent.

## Device and deployment constraints

The user's OPPO A6 4G (4 GB RAM) is a control terminal, not the assumed execution host.

- Do not assume llama.cpp can run a useful model locally on that phone. Measure peak RSS, free RAM, model size, context length, cold start, tokens/second, thermal throttling, battery draw and crash rate first.
- Qdrant is a database service; do not put it on the phone by default.
- OpenHands, Goose and SWE-agent require controlled execution environments. Do not run them directly on the phone or on the user's main repository workspace.
- Cloud/remote execution requires explicit environment, privacy, cost and credential review. No cloud resources are provisioned by this plan.

## Security, governance and licence requirements

- Least privilege; explicit allowlists; deny by default.
- External content and model output are untrusted.
- No secrets in prompts, source control, logs or evaluation datasets.
- Model weights, datasets, containers, plugins/extensions and transitive dependencies have independent provenance and licence obligations.
- Pin exact source commit and package/artifact version for every trial.
- Generate SBOM and vulnerability review before any distributable build.
- Require sandbox escape tests, permission-boundary tests, prompt-injection tests, credential-isolation tests and audit integrity tests.
- Disablement and rollback must be demonstrated.
- No provider may approve its own access, safety or release.

## Overlap and selection decisions

| Overlap | Decision |
|---|---|
| Promptfoo / DeepEval | Complementary evaluators; avoid duplicated suites. |
| LangGraph / coding agents | LangGraph coordinates approved workflows; coding agents are task executors behind a constrained interface. |
| LlamaIndex / Qdrant | Retrieval/index framework vs vector persistence; separate contracts. |
| OpenHands / Goose / SWE-agent | Competing/overlapping coding-agent executors; evaluate, do not deploy all by default. |
| llama.cpp / hosted inference | Local inference is an optional provider, not a required system dependency. |

## Acceptance criteria

A provider may advance from candidate to trial only when:
- Upstream repository and exact source commit are recorded.
- Licence and third-party notices are reviewed.
- Package/artifact and transitive dependency inventory is available.
- Adapter schema and permissions are reviewed.
- Reproducible tests pass against a pinned version.
- Security, privacy, performance and resource costs are measured.
- Failure, disablement and rollback are tested.

A provider may be marked integrated only after an implementation exists in the repository and tests prove its contract. It may be marked operational only after independent verification and explicit release approval.

**Current truthful state:** all nine are registered as candidates in this plan. No upstream software, package, model or service has been installed or integrated by this document.
