# Provider Adapter Map

The six-provider integration architecture and its nine-provider extension are both design-stage-approved. This map translates those approved design inputs into runtime adapter boundaries; it does not claim that any external technology is installed or integrated.

| Approved technology | Runtime adapter kind | Responsibility | Integration constraint |
|---|---|---|---|
| LangGraph | WorkflowProvider | Stateful workflow orchestration, checkpoints, approval interrupts | Workflow orchestration is not the global policy authority |
| llama.cpp | InferenceProvider | Optional local or hosted inference endpoint | Benchmark target hardware/model/context before selecting deployment |
| LlamaIndex | KnowledgeProvider | Document parsing, ingestion, indexing and retrieval | Retrieved content is untrusted data |
| Qdrant | VectorStoreProvider | Vector persistence and similarity search | Require authentication, restricted network, TLS and audit logging |
| Promptfoo | EvaluationProvider | Prompt/model regression and red-team evaluation | Keep its suite distinct from metric-oriented evaluation |
| DeepEval | EvaluationProvider | Metric-based LLM, agent and RAG evaluation | Complement Promptfoo; avoid duplicated suites |
| OpenHands | CodingAgentProvider | Candidate software-engineering executor | Isolated workspace and patch-proposal boundary; no unrestricted credentials |
| SWE-agent | CodingAgentProvider | Candidate software-engineering executor / benchmark | Compare with mini-SWE-agent before selection |
| Goose | CodingAgentProvider | Candidate extensible local/CLI/API agent | Command execution and file writes require explicit sandbox and permission controls |

## Selection and implementation rules

- The registry is an explicit allowlist. It performs no dynamic imports or auto-discovery.
- An adapter can be registered only after its capability lifecycle reaches INTEGRATED.
- Provider IDs are unique within one registry instance.
- Required methods are checked at registration time.
- Promptfoo and DeepEval remain complementary evaluation tools.
- OpenHands, SWE-agent and Goose overlap. Benchmark all candidates and mini-SWE-agent before selecting one initial executor.
- Do not run the Qdrant service or coding-agent executors on the user's 4 GB Android handset by default; treat the handset as a control terminal unless measured benchmarks prove otherwise.

## Runtime status

The provider-neutral interfaces and registry are implemented as local Python code. No third-party adapter, network integration, model, vector database or coding-agent executor is implemented by this map.
