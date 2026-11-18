# Runtime Foundation Decision — v0.1

## Decision
Start with a dependency-free Python 3.11+ control-plane core: shared request/result contracts, explicit policy decisions, a fail-closed capability lifecycle, and a deterministic mock provider.

## Architectural status
The six-provider integration architecture and its nine-provider extension are both design-stage-approved. That approval does not mean adapters, dependencies, credentials, models, or services are installed or production-tested.

## Initial safety properties
- Policy defaults to deny.
- Requests carry UUID correlation IDs and optional timezone-aware deadlines.
- Payloads and outputs are JSON-compatible objects capped at 256 KiB.
- Lifecycle transitions are explicit; discovery does not imply approval.
- The mock provider performs no network, filesystem, model, or subprocess operations.
- External provider output is data, not trusted instructions.

## Excluded from v0.1
No real provider adapters, network calls, model downloads, database, secrets, autonomous coding agents, or production credentials.

## Next integration sequence
1. Validate contracts and lifecycle with CI.
2. Add provider-neutral interfaces and adapter conformance tests.
3. Add separate Promptfoo and DeepEval evaluation harnesses.
4. Integrate one workflow and knowledge provider behind the contracts.
5. Benchmark and sandbox OpenHands, Goose, SWE-agent, and mini-SWE-agent before selecting an executor.
6. Integrate inference and vector persistence as separately secured services.

## Release status
Development foundation only. Not a production release and does not establish production readiness.
