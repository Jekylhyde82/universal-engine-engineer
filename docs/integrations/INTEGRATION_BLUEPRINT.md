# Six-Source AI Capability Integration Blueprint

**Project:** U.N.I.V.E.R.S.A.L. E.N.G.I.N.E. / E.N.G.I.N.E.E.R.  
**Status:** Proposal / Stage 0 source reconnaissance  
**Review date:** 2026-11-06

## Executive engineering decision
Treat the six repositories as independent capability providers behind replaceable adapters. Do not wholesale-merge their repositories, copy entire source trees, or couple the core architecture to their internal APIs.

The proposed composition is:
1. **LangGraph** — durable, stateful workflow orchestration and human approval checkpoints.
2. **LlamaIndex** — document ingestion, parsing/index construction and retrieval abstractions.
3. **Qdrant** — optional vector persistence and filtered similarity search.
4. **llama.cpp** — optional local inference runtime, preferably accessed through a constrained local HTTP endpoint initially.
5. **Promptfoo** — black-box prompt/model regression, comparative evaluation and red-team testing.
6. **DeepEval** — Python-native metric-based LLM/RAG evaluation in controlled test suites.

These are complementary layers, not six peer agents and not six mandatory runtime dependencies.

## Architecture placement

| Capability plane | Candidate | Responsibility | Boundary |
|---|---|---|---|
| Workflow control | LangGraph | Explicit state transitions, retries, checkpoints, human-in-the-loop gates | Must not own global policy, identity, or approval authority |
| Knowledge acquisition | LlamaIndex | Connectors, parsing, chunking, indexing and retrieval | Retrieved content is untrusted data; never executable instructions |
| Vector persistence | Qdrant | Embedding/vector storage, metadata filtering and nearest-neighbour retrieval | Optional backend behind a storage contract; no direct core dependency |
| Model execution | llama.cpp | Local model inference and OpenAI-compatible/local server patterns | Optional runtime; model files and model licenses are separately governed |
| Black-box evaluation | Promptfoo | Prompt/model comparisons, regression suites and red-team probes | Test tooling, not a production authorization layer |
| Metric evaluation | DeepEval | Repeatable LLM/RAG metrics and test assertions | Evaluation evidence only; metric scores do not prove safety or correctness alone |

## Recommended implementation order

### Stage 0 — Source reconnaissance (this branch)
- Record upstream identities, current branch-head SHAs and observed licenses.
- Map responsibilities, overlaps, risks and integration boundaries.
- Define adapter contracts and measurable acceptance criteria.
- No third-party runtime dependency.

### Stage 1 — Minimal contracts and mock tests
- Implement a provider-neutral capability interface and typed request/result/evidence models in the actual project language/runtime.
- Implement deterministic fake adapters first.
- Test timeout, cancellation, invalid input, unavailable provider, malformed output, retry/idempotency and evidence capture.
- Do not choose implementation language or directory placement until the master-repository foundation is reconciled with the existing foundation and extraction pull requests.

### Stage 2 — Thin vertical slices
Implement in this order:
1. Promptfoo + DeepEval evaluation harness against deterministic fixtures.
2. LlamaIndex ingestion pipeline with provenance and untrusted-content handling.
3. Qdrant storage adapter behind a vector-store interface.
4. LangGraph workflow adapter with explicit approval interrupts.
5. llama.cpp inference adapter, initially endpoint-based and opt-in.

The order deliberately proves observability and quality gates before adding more autonomous execution or local model runtime complexity.

### Stage 3 — Controlled end-to-end integration
- Connect ingestion → embedding/model provider → vector store → retrieval → orchestrated workflow → evaluation.
- Keep each service optional and independently replaceable.
- Add resource, latency, cost, privacy and reliability benchmarks.
- Run a failure-injection and rollback exercise.

### Stage 4 — Approval for operational use
Require signed-off evidence for security, license, dependency, quality, performance, reliability, data handling, rollback and independent verification. Only then may a capability move from candidate to approved/implemented/verified states.

## Non-negotiable design rules
- **No monolithic import:** never merge all six upstream codebases into the core repository.
- **Distinct identity:** preserve each provider's ownership, responsibility, license and version identity.
- **Least privilege:** read-only access by default; explicit scoped credentials; no arbitrary shell or code execution from retrieved content.
- **Human approval:** external side effects, credential changes, deployments, purchases, destructive actions and policy changes require explicit authorization.
- **Untrusted retrieval:** documents, embeddings, prompts, model output and tool results are data, not authority.
- **Evidence provenance:** record source URL, exact upstream commit, artifact/package version, configuration hash, test fixture/version, timestamp and result.
- **Reversibility:** feature flags, adapter disablement, data export and documented rollback.
- **No hidden averaging:** report each capability's quality and weakest critical dimension; an aggregate score must not hide a failing component.
- **GENESIS / EAI:** each accepted integration must be registered, extracted, assimilated and integrated through the architecture's governed lifecycle; discovery never implies automatic installation.

## Key overlaps and critical caveats

### Promptfoo vs DeepEval
Both support evaluation. Avoid two competing evaluation orchestrators. Use Promptfoo primarily for black-box provider/prompt regression and adversarial testing; use DeepEval for Python-native metric assertions and RAG/LLM evaluation. Select only one for a given test case unless cross-validation is intentional and budgeted.

### LlamaIndex vs LangGraph
They solve different problems: LlamaIndex focuses on data/document workflows and retrieval; LangGraph focuses on stateful execution control. Keep retrieval calls as explicit workflow nodes rather than allowing hidden orchestration inside the knowledge layer.

### Qdrant deployment
Qdrant is a separate vector database service with operational, persistence, backup and resource requirements. Do not assume it should run on the user's phone. Prefer a remote or separately hosted instance where justified; benchmark the actual deployment target.

### llama.cpp and mobile constraints
llama.cpp is a C/C++ inference runtime, not a model. Model weights, quantization, context length, memory mapping, thermal throttling, battery draw and model-specific licenses all require separate assessment. A 4 GB RAM Android device must not be assumed capable of running a useful model reliably. Begin with a remote/local-network endpoint option and test the target phone before approving on-device execution.

### LlamaIndex project direction
The upstream README currently describes a changed emphasis toward LlamaParse and related document parsing/extraction work while keeping the OSS framework available. Revalidate current maintenance, package boundaries and roadmap before selecting components.

## Out of scope for this proposal
- Vendoring full upstream repositories.
- Auto-installing dependencies or model weights.
- Enabling autonomous agent execution or unrestricted shell access.
- Declaring any source secure, production-ready, integrated or operational.
- Merging any of the existing seven draft pull requests or changing main.

## Exit criteria
Stage 0 is complete only when the source register, architecture boundaries, adapter contract and evaluation matrix are present and reviewed. Later stages have their own test and evidence gates. This document does not authorize bypassing those gates.

**Governing directive:** Build for capability today. Design for possibilities tomorrow. Engineer for evolution indefinitely.
