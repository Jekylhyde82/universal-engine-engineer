# U.N.I.V.E.R.S.A.L. E.N.G.I.N.E. / E.N.G.I.N.E.E.R.

**Canonical identity:** MULTIVERSAL OMNIVELOCITY PRIME — GENIUS ENGINEER PRIME  
**Foundational architecture:** NINEFOLD INTRINSIC  
**Universal governing invariant:** INTRINSIC BY DESIGN

> Build for capability today. Design for possibilities tomorrow. Engineer for evolution indefinitely.

## Project status

This repository contains the first executable runtime foundation. The six-provider integration architecture and its nine-provider extension are both design-stage-approved.

Current development branch: `runtime/core-contracts-v0.1`  
Current review: [Draft PR #16](https://github.com/Jekylhyde82/universal-engine-engineer/pull/16)

Implemented adapter boundaries:
- LangGraph — checkpointed workflow execution.
- llama.cpp — OpenAI-compatible text chat inference.
- LlamaIndex — document ingestion and retrieval around an injected index.
- Qdrant — vector point upsert and query.

Not yet implemented:
- Promptfoo and DeepEval evaluation harnesses.
- OpenHands, SWE-agent and Goose coding-agent adapters.
- Full upstream service integration tests, production identity/authentication, distributed authorization, external audit anchoring and production deployment.

**This is not production-ready software.** CI success proves the current package builds and its local tests pass; it does not certify external services, deployment security or production operations.

## Requirements

- Python 3.11 or newer.
- Core runtime has no mandatory third-party dependencies.
- LangGraph and LlamaIndex must be installed separately when using their real framework objects.
- llama.cpp and Qdrant adapters use Python's standard-library HTTP client.

## Install and test

```bash
python -m pip install .
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

## First dispatch example

The policy engine uses exact-match rules and defaults to deny. The principal ID must come from an authenticated identity layer; this repository does not implement authentication.

```python
from uuid import uuid4

from universal_engine.contracts import ProviderRequest
from universal_engine.policy import PolicyEngine, PolicyRule
from universal_engine.providers.mock import MockProvider
from universal_engine.runtime import dispatch

request = ProviderRequest(
    correlation_id=str(uuid4()),
    capability_id="demo.echo",
    operation="echo",
    payload={"message": "hello"},
)

policy = PolicyEngine([
    PolicyRule(
        rule_id="demo-allow",
        principal_id="local-operator",
        capability_id="demo.echo",
        operation="echo",
        allowed=True,
        reason="approved for local demonstration",
    )
])

result = dispatch(
    MockProvider(),
    request,
    policy_engine=policy,
    principal_id="local-operator",
)
print(result.status, result.output)
```

## Adapter configuration boundaries

- **llama.cpp:** local example base URL is `http://127.0.0.1:8080/v1`. Plain HTTP is loopback-only. Remote use requires HTTPS, an API key and explicit `allow_remote=True`.
- **Qdrant:** local example base URL is `http://127.0.0.1:6333`. Remote use requires HTTPS, an API key and explicit opt-in. Collections must already exist. Never expose a default unauthenticated Qdrant service to an untrusted network.
- **LlamaIndex:** inject an application-created index, embedding model and vector-store configuration. The adapter does not silently choose an LLM or vector database.
- **LangGraph:** inject a StateGraph builder and an explicit checkpointer. In-memory checkpointers are for development/testing; production requires durable checkpoint storage and recovery tests.

See [runtime adapter map](docs/runtime/PROVIDER-ADAPTER-MAP.md), [upstream integration research](docs/runtime/UPSTREAM-INTEGRATION-RESEARCH.md), and [runtime threat model](docs/runtime/THREAT-MODEL.md).

## Capability lifecycle and audit

The lifecycle is:

`Discovered → Proposed → Under Evaluation → Approved → Integrated`

Capabilities may also be rejected or retired. Discovery never implies approval.

The runtime includes:
- An in-memory lifecycle state machine.
- A SQLite-backed local lifecycle ledger with transactional transitions.
- A SHA-256 event hash chain that detects event edits and broken sequence/state continuity.
- An explicit provider registry that accepts only lifecycle-integrated capabilities.

The SQLite ledger is local persistence, not distributed consensus or tamper-proof storage against a database administrator. Production requires external audit anchoring, access controls and tested backup/restore.

## Engineering invariants

- PROOF BEFORE CLAIM.
- EVIDENCE BEFORE CONFIDENCE.
- VERIFICATION BEFORE COMPLETION.
- Policy defaults to deny.
- Provider outputs and retrieved documents are untrusted data.
- Provider registration is explicit; no dynamic imports or automatic adapter loading.
- Coding agents must operate in isolated workspaces and produce human-reviewed patch proposals. No autonomous merge or deployment authority.

## Repository map

- `src/universal_engine/contracts.py` — validated request/result contracts.
- `src/universal_engine/policy.py` — deny-by-default policy evaluator.
- `src/universal_engine/runtime.py` — policy-enforcing dispatch.
- `src/universal_engine/lifecycle.py` — lifecycle state machine and in-memory ledger.
- `src/universal_engine/persistence.py` — SQLite lifecycle ledger and hash-chain verification.
- `src/universal_engine/providers/` — adapter interfaces, registry, mock and implemented adapters.
- `tests/` — unit and local HTTP adapter tests.
- `docs/runtime/` — decisions, adapter boundaries, research, threat model and limitations.

May our RAM never run out, our dependencies never conflict, and our builds always pass!
