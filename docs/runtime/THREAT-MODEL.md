# Runtime Threat Model — v0.1

**Status:** Initial engineering threat model. Not independently reviewed or production-approved.

## System boundary

The v0.1 runtime is a Python control-plane library with provider-neutral contracts, a process-local capability lifecycle ledger, an explicit provider registry, a dispatch boundary and a local/secured HTTP adapter for llama.cpp. It does not currently include a server API, user authentication, persistent storage, remote provider credentials, autonomous coding-agent execution or production deployment.

## Assets to protect

1. Repository source, build pipeline and release artifacts.
2. Provider API keys and model-service credentials.
3. User prompts, documents, retrieved context and evaluation datasets.
4. Vector data, indexes and workflow checkpoints when persistence is introduced.
5. Provider outputs, traces, error messages and audit records.
6. Integrity of capability approval, integration and retirement state.

## Trust boundaries

- Application caller → provider-neutral runtime contracts.
- Policy decision source → dispatch enforcement.
- Runtime → third-party provider adapter.
- Adapter → upstream inference, workflow, knowledge, evaluation or vector service.
- Future coding-agent executor → isolated workspace, host filesystem and network.
- CI workflow → repository source and third-party GitHub Actions.

## Threats and current controls

| Threat | Current control | Residual risk |
|---|---|---|
| Unapproved capability execution | Policy defaults to deny; dispatch blocks denied requests | No identity-bound policy engine or authorization service exists |
| Lifecycle skipping | Explicit state transition graph; registry consults lifecycle ledger | Ledger is process-local, mutable in memory and not tamper-proof |
| Provider response confusion/replay | UUID correlation ID must match request | No signed provider response, nonce store or replay ledger |
| Oversized payloads/responses | 256 KiB request/result limit; 1 MiB llama.cpp response cap | No global per-user quota or rate limiting |
| Malformed JSON/non-finite values | Recursive JSON validation and finite-number checks | Deeply nested hostile payloads can still consume CPU before size checks in future server contexts |
| Plaintext credential/network exposure | Remote inference requires HTTPS, API key and explicit opt-in; URL credentials rejected | No certificate pinning, DNS/IP allowlist or egress firewall in this library |
| Accidental tool execution | llama.cpp adapter uses chat-completions only and never enables server tools/MCP | Operator may independently start a tool-enabled server; infrastructure policy must prevent it |
| Prompt injection in retrieved content | Architecture treats retrieved/provider content as untrusted data | No complete taint tracking or prompt-injection defence implemented |
| Autonomous coding-agent compromise | No coding agent is wired into runtime | Future executor requires OS-enforced sandbox, least privilege, no production secrets and human-reviewed patches |
| CI supply-chain compromise | GitHub Actions pinned to immutable commit SHAs; read-only contents permission; checkout credentials disabled | Python build backend and transitive dependencies still need lockfiles, hashes and provenance review |

## Required production controls — not yet implemented

### Identity and authorization
- Authenticate users and service identities.
- Authorize capability, operation, resource, tenant and data scope independently.
- Bind policy decisions to the caller identity, request, policy version and expiry.
- Do not accept caller-asserted lifecycle states as authorization proof.

### Secrets and network
- Use a managed secret store; never store secrets in repository files, logs or endpoint URLs.
- Enforce outbound network allowlists and DNS/IP validation at infrastructure boundaries.
- Require TLS for remote services; define certificate validation, rotation and revocation.
- Disable tool/MCP endpoints unless a separate threat model and sandbox approval exist.

### Runtime and data
- Add durable lifecycle and audit records with integrity protection.
- Add tenant isolation, quotas, rate limits, concurrency limits and resource budgets.
- Define data classification, retention, deletion, backup and restore policies.
- Redact prompts, outputs and credentials from logs; establish observability and alerting.
- Define retry, timeout, circuit-breaker and idempotency behaviour for each provider.

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

The current implementation is a development foundation only. Passing unit tests and CI is necessary but not sufficient for production. No production release may be approved until every required control above has an owner, implementation evidence, test evidence and independent review.
