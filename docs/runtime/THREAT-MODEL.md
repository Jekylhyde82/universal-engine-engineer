# Runtime Threat Model — v0.1

**Status:** Initial engineering threat model. Not independently reviewed or production-approved.

## System boundary

The v0.1 runtime is a Python control-plane library with validated provider-neutral contracts, an exact-match deny-by-default in-process policy engine, a process-local registry, an in-memory lifecycle state machine, a SQLite-backed lifecycle ledger with a hash-chained event history, a dispatch boundary, and four adapter implementations:
- llama.cpp OpenAI-compatible chat-completions over HTTP(S).
- Qdrant REST point upsert and vector query.
- LlamaIndex document ingestion and retrieval around an injected index.
- LangGraph graph compilation, checkpointed run and resume around an injected builder/checkpointer.

It does not currently include a server API, authenticated user identity, distributed policy administration, remote production credentials, autonomous coding-agent execution or production deployment. CI uses local ephemeral HTTP servers and fake framework objects; it does not connect to external provider services.

## Assets to protect

1. Repository source, build pipeline and release artifacts.
2. Provider API keys and model-service credentials.
3. User prompts, documents, retrieved context and evaluation datasets.
4. Vector data, indexes and workflow checkpoints.
5. Provider outputs, traces, error messages and audit records.
6. Integrity of capability approval, integration and retirement state.

## Trust boundaries

- Application caller → provider-neutral runtime contracts.
- Authenticated identity source (not yet implemented) → in-process policy evaluator.
- Policy evaluator → dispatch enforcement.
- Runtime → provider adapter.
- Adapter → upstream inference, workflow, knowledge or vector service.
- Future coding-agent executor → isolated workspace, host filesystem and network.
- CI workflow → repository source and third-party GitHub Actions.

## Threats and current controls

| Threat | Current control | Residual risk |
|---|---|---|
| Unapproved capability execution | Exact-match deny-by-default policy; dispatch replaces caller-supplied decisions | Principal identity is not authenticated; rules are process-local and not persistently administered |
| Lifecycle skipping | Explicit transition graph; registry consults lifecycle state | In-memory ledger is mutable; SQLite ledger can be rewritten by database administrator |
| Provider response confusion/replay | UUID correlation ID must match request | No signed provider response, nonce store or replay ledger |
| Oversized payloads/responses | 256 KiB request/result limit; HTTP adapter response caps | No per-user quotas or global rate limiting |
| Malformed JSON/non-finite values | Recursive JSON validation and finite-number checks | Deeply nested hostile payloads can consume CPU before size checks in future server contexts |
| Plaintext credential/network exposure | Remote HTTP adapters require HTTPS, API key and explicit opt-in; URL credentials rejected | No certificate pinning, DNS/IP allowlist or egress firewall in this library |
| Accidental tool execution | llama.cpp adapter does not enable server tools/MCP | Operator may independently start a tool-enabled server; infrastructure policy must prevent it |
| Prompt injection in retrieved content | Retrieved LlamaIndex content is treated as untrusted data | No complete taint tracking or prompt-injection defence implemented |
| Workflow state loss | LangGraph adapter requires an explicit checkpointer and thread ID | Durable checkpointer implementation and recovery tests are not supplied |
| Vector data exposure | Qdrant remote adapter requires HTTPS/API key/explicit opt-in | Collection authorization, tenant isolation and service-side network controls are external |
| Autonomous coding-agent compromise | No coding agent is wired into runtime | Future executor requires OS-enforced sandbox, least privilege, no production secrets and human-reviewed patches |
| CI supply-chain compromise | GitHub Actions pinned to immutable commit SHAs; read-only contents permission; checkout credentials disabled | Python build backend and transitive dependencies still need lockfiles, hashes and provenance review |

## Required production controls — not yet implemented

### Identity and authorization
- Authenticate users and service identities.
- Authorize capability, operation, resource, tenant and data scope independently.
- Bind policy decisions to caller identity, request, policy version and expiry.
- Do not accept caller-asserted lifecycle states as authorization proof.

### Secrets and network
- Use a managed secret store; never store secrets in repository files, logs or endpoint URLs.
- Enforce outbound network allowlists and DNS/IP validation at infrastructure boundaries.
- Require TLS for remote services; define certificate validation, rotation and revocation.
- Disable tool/MCP endpoints unless a separate threat model and sandbox approval exist.

### Runtime and data
- Add tenant isolation, quotas, rate limits, concurrency limits and resource budgets.
- Define data classification, retention, deletion, backup and restore policies.
- Redact prompts, outputs and credentials from logs; establish observability and alerting.
- Define retry, timeout, circuit-breaker and idempotency behaviour for each provider.
- Add external anchoring for SQLite audit hashes and test database restore.

### Coding agents
- Use disposable OS-enforced containers or microVMs with non-root identities.
- Mount only a dedicated scratch workspace; no host home directory, SSH agent, Docker socket or production repository write token.
- Restrict network egress and command allowlists; enforce CPU, memory, disk and wall-clock limits.
- Require human review of patches; prohibit autonomous merge, release and deployment.

### Build and release
- Lock direct and transitive dependencies with hashes.
- Record exact provider/model versions, licences and provenance.
- Run static analysis, dependency and secret scanning, SBOM generation and artifact signing.
- Test backup/restore, deployment, rollback, disaster recovery and operational runbooks.
- Obtain independent security review and evidence-based production sign-off.

## Production gate

Passing unit tests and CI is necessary but not sufficient for production. No production release may be approved until every required control above has an owner, implementation evidence, test evidence and independent review.
