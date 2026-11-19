# UAIE PRIME — Production Readiness Plan

**Canonical name:** Universal Acquisition and Integration Engine  
**Parent architecture:** NINEFOLD INTRINSIC  
**Current implementation:** Local-first prototype with LM Studio local inventory adapter  
**Release status:** NOT PRODUCTION READY

This document is the release-control checklist. A phase is complete only when its acceptance evidence is attached to the repository and independently reviewed.

## Current verified foundation

- [x] Local file and JSON-object acquisition.
- [x] SHA-256 content identity and duplicate detection.
- [x] Preserve every observed source for deduplicated content.
- [x] SQLite persistence for acquired content and provenance.
- [x] Basic classification and transparent heuristic triage.
- [x] Approval-before-integration lifecycle.
- [x] Capability assessment record with mandatory Original Idea Value, market-value field, revenue-model field, development timeline, risk assessment, evidence and verification status.
- [x] Local SHA-256 hash-chained audit events for acquisition, duplicate-source observation, assessment updates and lifecycle transitions.
- [x] Audit-chain verification and tamper-detection tests.
- [x] Read-only LM Studio local model inventory adapter using the documented native REST v1 endpoint.
- [x] Backward-compatible Python API aliases for the former prototype class names.
- [x] Package install, source compilation and unit-test workflow passing on recorded commits; verify the current branch head before release.

## Release gates

### Gate 1 — Core data integrity and lifecycle
- [ ] Replace legacy table/state naming through a versioned, tested migration strategy; preserve existing databases.
- [ ] Add authenticated actor identity to every acquisition, assessment and lifecycle event.
- [ ] Enforce lifecycle transitions through a single policy boundary; reject direct or unauthorised state changes.
- [ ] Add transactional backup/restore tests and documented recovery objectives.
- [ ] Add external audit anchoring; the local hash chain alone is not tamper-proof against a database administrator.
- [ ] Add retention, deletion, export and data-minimisation policies.

### Gate 2 — Acquisition source framework
- [ ] Define versioned connector contracts with source identity, scopes, pagination, rate limits, retries, cancellation and provenance.
- [ ] Add permission-scoped repository and web acquisition connectors.
- [ ] Add a documented public model-catalog discovery mechanism. The LM Studio local inventory API is not a public catalog search API. Do not scrape undocumented endpoints.
- [ ] Add safe handling for HTTP errors, redirects, hostile content, compressed responses and rate limiting.
- [ ] Add reproducible fixtures and contract tests for each supported connector.

### Gate 3 — Content understanding
- [ ] Add sandboxed PDF, DOCX, XLSX, archive and source-tree extraction with decompression, size, depth and time limits.
- [ ] Add OCR and audio/video extraction as optional, separately permissioned processors.
- [ ] Add semantic indexing/retrieval with evidence citations and deletion propagation.
- [ ] Add source-code dependency, licence and vulnerability analysis.
- [ ] Preserve raw source artifacts and parser/version provenance for every extracted representation.

### Gate 4 — Model and capability acquisition
- [ ] Separate model discovery, candidate evaluation, approval, download, verification, installation and integration.
- [ ] Require explicit approval for each model acquisition; no automatic download based only on discovery.
- [ ] Enforce pre-download storage/network budgets, hardware compatibility and cancellation.
- [ ] Capture publisher, model identifier, quantization, source URL, licence, revision, checksums/signatures where available and acquisition timestamp.
- [ ] Verify downloaded artifact integrity before marking acquisition complete.
- [ ] Keep model loading and inference execution outside the acquisition adapter and behind separate policy controls.

### Gate 5 — Security and operational readiness
- [ ] Implement authentication, role-based authorization and least-privilege connector credentials.
- [ ] Isolate parsers, evaluators and acquired code in disposable, resource-limited sandboxes.
- [ ] Add secret management, dependency pinning, software supply-chain checks and vulnerability scanning.
- [ ] Add structured logs, metrics, tracing, health checks and incident procedures.
- [ ] Test concurrency, crash recovery, database corruption, resource exhaustion and hostile inputs.
- [ ] Complete independent security review and threat-model sign-off.

### Gate 6 — Deployment and release
- [ ] Define supported deployment targets and resource profiles.
- [ ] Define upgrade/migration compatibility and rollback procedures.
- [ ] Build signed, reproducible release artifacts and publish an SBOM.
- [ ] Run end-to-end tests against real supported external services.
- [ ] Publish operator documentation, configuration reference and disaster-recovery runbook.
- [ ] Obtain explicit release approval after all mandatory gates pass.

## Non-negotiable invariants

1. Discovery is not approval.
2. Acquisition is not integration.
3. Integration is not execution.
4. Original Idea Value and source provenance are preserved, not overwritten.
5. Missing evidence remains explicitly unknown.
6. Commercial estimates are evidence-labelled assessments, not heuristic scores.
7. No component certifies its own consequential output as the sole verifier.
8. Security, licensing, privacy and policy constraints outrank velocity or convenience.

**Release rule:** UAIE must not be labelled production-ready until all mandatory gates pass with recorded evidence. A green unit-test workflow is necessary, but insufficient.
