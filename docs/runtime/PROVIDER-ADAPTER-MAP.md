# Provider Adapter Map

The six-provider integration architecture and its nine-provider extension are both design-stage-approved. This map translates those approved design inputs into runtime adapter boundaries.

| Approved technology | Runtime adapter kind | Current implementation status | Responsibility | Integration constraint |
|---|---|---|---|---|
| LangGraph | WorkflowProvider | Adapter implemented; fake tests only | Stateful workflow orchestration, checkpoints, approval interrupts | Production requires durable checkpointer; workflow orchestration is not global policy authority |
| llama.cpp | InferenceProvider | HTTP adapter implemented; local stub tests only | Optional local or hosted inference endpoint | Remote requires HTTPS/API key/explicit opt-in; server tools and MCP disabled |
| LlamaIndex | KnowledgeProvider | Injected-index adapter implemented; fake tests only | Document ingestion, indexing and retrieval | Application injects index/embedding/vector store; retrieved content is untrusted |
| Qdrant | VectorStoreProvider | REST adapter implemented; local stub tests only | Vector point persistence and similarity query | Require auth, restricted network, TLS and audit logging in production |
| Promptfoo | EvaluationProvider | Not implemented | Prompt/model regression and red-team evaluation | Pin Node runtime/package; keep separate from metric-oriented evaluation |
| DeepEval | EvaluationProvider | Not implemented | Metric-based LLM, agent and RAG evaluation | Pin Python package and judge model; complement Promptfoo |
| OpenHands | CodingAgentProvider | Not implemented | Candidate software-engineering executor | Isolated workspace and patch-proposal boundary; no unrestricted credentials |
| SWE-agent | CodingAgentProvider | Not implemented | Candidate software-engineering executor / benchmark | Compare with mini-SWE-agent before selection |
| Goose | CodingAgentProvider | Not implemented | Candidate extensible local/CLI/API agent | Autonomous mode is default upstream; explicitly force Chat Only or Manual Approval for evaluation |

## Selection and implementation rules

- The registry is an explicit allowlist. It performs no dynamic imports or auto-discovery.
- Registration consults the in-memory capability lifecycle ledger and accepts only capabilities that reached INTEGRATED through permitted transitions.
- Provider IDs are unique within one registry instance; required methods are checked at registration time.
- The SQLite lifecycle ledger is durable local persistence, not a distributed authorization service or tamper-proof audit log.
- Promptfoo and DeepEval remain complementary evaluation tools.
- OpenHands, SWE-agent and Goose overlap. Benchmark all candidates and mini-SWE-agent before selecting one initial executor.
- Do not run the Qdrant service or coding-agent executors on the user's 4 GB Android handset by default; treat the handset as a control terminal unless measured benchmarks prove otherwise.

## Runtime status

Four adapter implementations exist. CI validates them using fake framework objects and local ephemeral HTTP servers. No external provider service, model, Qdrant instance, production LangGraph checkpointer, or autonomous coding agent has been integrated or tested end-to-end.
