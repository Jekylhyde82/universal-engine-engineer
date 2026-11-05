# Provider-Neutral Adapter Contract

**Status:** Design contract; no runtime implementation is claimed.

## Purpose
The core architecture owns policy, identity, lifecycle, approvals and evidence. Third-party frameworks are providers behind narrow adapters. An adapter must be replaceable without rewriting the core capability registry.

## Required adapter metadata
Every adapter registration must expose:
- Stable internal adapter ID and human-readable name.
- Upstream repository URL, exact reviewed commit SHA and license identifier.
- Installed package/artifact name and exact version (when implemented).
- Supported capabilities and explicit unsupported capabilities.
- Runtime requirements, network/data flows and required permissions.
- Configuration schema with secrets referenced by name, never embedded.
- Health/availability state and timeout/retry policy.
- Owner, lifecycle state and disable/rollback procedure.

## Lifecycle states
Use explicit, evidence-backed states:

DISCOVERED → REVIEWED → APPROVED_FOR_TRIAL → IMPLEMENTED → INSTALLED → TESTED → VERIFIED → OPERATIONAL

A failed or revoked provider moves to QUARANTINED or DISABLED, with reason and evidence. A state must never be advanced merely because a branch, manifest, package declaration or pull request exists. APPROVED_FOR_TRIAL is not production approval.

## Common request/result envelope
Every adapter invocation should carry:
- request_id: unique correlation identifier.
- capability_id: stable internal capability identifier.
- input: schema-validated, size-bounded data.
- context: explicitly permitted non-secret context.
- deadline: absolute deadline or bounded timeout.
- policy: resolved policy decision and allowed operation scope.
- provenance: origin of inputs and source references.

Every result should carry:
- request_id and capability_id.
- status: success, rejected, unavailable, timeout, partial, or error.
- output: schema-validated result or null.
- provider: adapter ID, package/artifact version and upstream commit pin.
- metrics: latency, token/resource use where measurable.
- evidence: test/run ID, timestamps, hashes and relevant logs.
- warnings: truncation, partial data, uncertainty or fallback use.

## Mandatory behaviour
1. Validate inputs and outputs against versioned schemas.
2. Enforce timeouts, bounded retries, cancellation and concurrency limits.
3. Make retryable operations idempotent or require idempotency keys.
4. Never log credentials, raw secrets or sensitive payloads by default.
5. Apply redaction and retention policies to prompts, documents, traces and model outputs.
6. Treat external content and model output as untrusted.
7. Fail closed for policy/authorization failures; never silently fall back to a less-governed provider.
8. Surface partial results and uncertainty explicitly.
9. Emit tamper-evident evidence records with provenance.
10. Support health checks, disablement, rollback and provider replacement.

## Provider-specific contract boundaries
- **LangGraph:** workflow state must be serializable, versioned and checkpointed; interrupts must return control to the governing approval layer. Graph nodes cannot grant themselves authority.
- **llama.cpp:** inference is invoked through a constrained adapter; model identity/hash, quantization, context size, sampling parameters and runtime build must be recorded. No model download or execution without explicit policy.
- **LlamaIndex:** ingestion records source URI, content hash, parser/version, chunking configuration and access labels. Retrieval returns citations/provenance and never executes document instructions.
- **Qdrant:** namespace/collection isolation, tenant filters, schema/version management, backup/export and deletion semantics are mandatory. Filter enforcement must be server-side and tested.
- **Promptfoo:** test suites are version-controlled; provider credentials are scoped; red-team findings are treated as test results requiring triage, not proof of total security.
- **DeepEval:** metric definitions, thresholds, judge model/version, dataset version and evaluation configuration are pinned. Scores must be accompanied by examples and known limitations.

## Acceptance tests
At minimum: valid request, invalid schema, missing credential, forbidden operation, provider offline, timeout, cancellation, malformed provider response, retry/idempotency, oversized input/output, secret redaction, provenance preservation, disablement and rollback.

## Security boundary
No adapter may gain new permissions merely by being installed. The adapter's permission set must be declared, reviewed and minimized independently of its upstream framework's maximum capabilities.
