# Runtime Foundation Decision — v0.1

## Decision
Start with a dependency-free Python 3.11+ control-plane core: shared request/result contracts, explicit policy decisions, a fail-closed capability lifecycle, a provider registry and deterministic local tests.

## Architectural status
The six-provider integration architecture and its nine-provider extension are both design-stage-approved. The runtime now has provider-neutral interfaces and four executable adapter implementations: LangGraph, llama.cpp, LlamaIndex and Qdrant. Promptfoo and DeepEval evaluation harnesses, plus the three coding-agent candidates, remain unintegrated.

## Current v0.1 components
- Validated request/result contracts with finite JSON validation and bounded payloads.
- Exact-match deny-by-default in-process policy engine.
- Capability lifecycle state machine and SQLite-backed local ledger with hash-chain verification.
- Explicit provider registry requiring integrated lifecycle state.
- Policy-enforcing dispatch with correlation and deadline checks.
- Four adapter implementations with local/fake tests and documented limitations.

## Deliberately excluded from this milestone
No model downloads, production credentials, production data, autonomous coding-agent execution, production deployment, distributed identity/authorization service, external audit anchoring, or independent production certification. CI does not contact external provider services; HTTP adapters are tested against local ephemeral servers and the framework adapters against fakes.

## Integration sequence
1. Complete provider adapter contract and security review.
2. Pin and test exact upstream versions for all four implemented adapters.
3. Add Promptfoo prompt/model regression and red-team harness.
4. Add DeepEval metric/trajectory/RAG harness with a pinned local or hosted judge model.
5. Benchmark and sandbox OpenHands, Goose, SWE-agent and mini-SWE-agent before selecting an executor.
6. Add distributed identity/authz, durable checkpoint/vector configuration, audit anchoring and operations.
7. Run end-to-end integration, resilience, security, performance and recovery tests.

## Release status
Development foundation only. Not a production release and does not establish production readiness.
