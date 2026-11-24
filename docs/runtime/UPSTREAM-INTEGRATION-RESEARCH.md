# Upstream Integration Research — 2026-11-18

This research validates integration boundaries for the design-stage-approved six-provider architecture and nine-provider extension. It is an upstream documentation review, not a substitute for pinned-version compatibility tests, licence review, threat modelling, or adapter integration tests.

## Findings that affect implementation

### Workflow orchestration — LangGraph
- LangGraph is a low-level runtime for long-running, stateful workflows, with checkpointing, durable execution, streaming and human-in-the-loop control.
- Its documentation states Python 3.11+ for the local CLI.
- The local `langgraph dev` server is in-memory and intended for development/testing. Production needs a persistent storage backend and the production Agent Server deployment path.
- Architecture decision: keep LangGraph behind WorkflowProvider; do not make it the global policy authority. Keep development and production deployment profiles separate.

Sources:
- https://docs.langchain.com/oss/python/langgraph/overview
- https://docs.langchain.com/oss/python/langgraph/local-server

### Knowledge and vector storage — LlamaIndex + Qdrant
- LlamaIndex uses namespaced packages. Its starter `llama-index` bundle includes OpenAI LLM and embedding integrations; selective package installation is available and is the correct direction for a provider-neutral/local-first build.
- Qdrant supports 64-bit x86_64/amd64 and AArch64/arm64; 32-bit is unsupported.
- Qdrant's own quickstart warns that the default local service has no encryption or authentication. Its production guidance expects security configuration, persistent performant storage, monitoring/logging and backup/recovery planning.
- Architecture decision: do not install the broad LlamaIndex starter bundle by default. Select exact packages after selecting inference and embedding providers. Never expose an unauthenticated Qdrant endpoint to an untrusted network.

Sources:
- https://developers.llamaindex.ai/python/framework/getting_started/installation/
- https://qdrant.tech/documentation/installation/
- https://qdrant.tech/documentation/quickstart/

### Evaluation — Promptfoo + DeepEval
- Promptfoo documents Node.js >=22.22.0 for current CI usage and recommends Node.js 24 LTS. It supports prompt/model evaluations, red-team runs, JSON/HTML/JUnit outputs and quality gates.
- DeepEval provides 50+ metrics, including end-to-end, trajectory, component-level, RAG, agent and safety evaluation. Its native Pytest integration supports CI.
- Architecture decision: Promptfoo owns prompt/model regression and adversarial/red-team suites; DeepEval owns metric-based quality, trajectory and RAG evaluation. Share datasets and trace IDs where useful, but avoid duplicating the same assertions in both tools. Pin exact versions rather than using floating `@latest` in release pipelines.

Sources:
- https://www.promptfoo.dev/docs/integrations/ci-cd/
- https://deepeval.com/docs/introduction
- https://deepeval.com/docs/metrics-introduction

### Inference — llama.cpp
- llama.cpp exposes OpenAI-compatible chat/completions endpoints, but upstream describes compatibility as practical rather than a guarantee of full OpenAI API specification conformance.
- Its server can enable built-in tools and MCP servers. Upstream warns not to expose tool-enabled servers to networks without authentication; tool/MCP child processes run with the server's privileges.
- Architecture decision: the adapter must use capability-specific endpoint tests and treat API compatibility as a tested subset, not an assumption. Disable server tools and MCP by default. If enabled for a controlled use case, bind to loopback or enforce API keys, network restrictions and OS-level isolation.

Sources:
- https://github.com/ggml-org/llama.cpp/tree/master/tools/server
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README-dev.md

### Coding-agent candidates — OpenHands, SWE-agent / mini-SWE-agent, Goose
- OpenHands supports local, Docker, VM, self-hosted and managed cloud backends. Its documentation makes the trust boundary explicit: an agent backend may execute shell commands and read/write files within its workspace. Workspace mounts and backend choice therefore define meaningful access boundaries.
- SWE-agent's current upstream README says most development effort has moved to mini-SWE-agent and recommends mini-SWE-agent for most new usage. mini-SWE-agent v2 emphasizes simpler execution and sandbox adapters.
- Goose's official permissions documentation states Autonomous Mode is the default; it can modify and delete files without approval. Its Chat Only, Manual Approval and Smart Approval modes provide different levels of tool access. Goose config also documents auto mode as the default.
- Architecture decision: do not connect any coding agent to the production repository or secrets in the initial release. Use a disposable isolated workspace, OS-enforced sandbox, no privileged host mounts, no production credentials, restricted network egress, CPU/memory/time limits, audit logs and human-reviewed patch proposals. For Goose, explicitly set Chat Only or Manual Approval for initial evaluation; never rely on the default mode. Compare mini-SWE-agent v2 against SWE-agent before choosing an executor.

Sources:
- https://docs.openhands.dev/openhands/usage/agent-canvas/overview
- https://github.com/SWE-agent/SWE-agent/blob/main/README.md
- https://mini-swe-agent.com/latest/
- https://github.com/block/goose/blob/58f3cc9e/documentation/docs/guides/goose-permissions.md
- https://github.com/block/goose/blob/main/documentation/docs/guides/config-files.md
- https://genai.owasp.org/download/49059/

## Release implications

1. Provider SDK/service versions must be pinned to exact versions or immutable commits with transitive dependency locks and licence records.
2. Provider adapters require contract conformance tests and endpoint-specific compatibility tests before registration.
3. Qdrant and llama.cpp network exposure must be disabled by default and explicitly secured.
4. Promptfoo requires a separate Node 24 CI job; DeepEval runs in the Python evaluation environment. Keep both optional until model credentials and deterministic test fixtures are available.
5. Coding-agent integration remains blocked on a documented threat model and OS-enforced sandbox proof.
6. No provider is production-approved solely because its architecture is design-stage-approved.

## Research limitations

- Upstream docs are mutable and may change after this snapshot.
- This pass did not pin package versions, execute provider adapters, run model benchmarks, perform a licence audit, or verify the user's target hardware.
- Search-result claims and benchmark scores are not treated as independent performance evidence.
