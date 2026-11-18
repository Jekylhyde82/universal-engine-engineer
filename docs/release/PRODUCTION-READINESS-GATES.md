# Production Readiness Gates

**Status:** Acceptance criteria — not yet passed

A release is not production-ready until every applicable gate has evidence attached to the exact release candidate.

| Gate | Minimum acceptance evidence | Status |
|---|---|---|
| Architecture | Approved component map, interfaces, trust boundaries and dependency inventory | NOT STARTED |
| Build | Reproducible clean build; pinned dependencies | NOT STARTED |
| Tests | Unit, integration, regression and failure-path results | NOT STARTED |
| Security | Threat model, access controls, secret handling, vulnerability review | NOT STARTED |
| Data | Classification, retention, export/deletion and backup/restore tests | NOT STARTED |
| Reliability | Health checks, timeouts, retries, resource limits and graceful failure | NOT STARTED |
| Observability | Structured logs, metrics, traces where appropriate, alerting and audit trail | NOT STARTED |
| Deployment | Repeatable deployment, environment configuration and rollback plan | NOT STARTED |
| Operations | Runbooks, ownership, incident response and recovery objectives | NOT STARTED |
| Verification | Independent review of test evidence and acceptance criteria | NOT STARTED |
| Approval | Explicit release decision by authorised owner | NOT STARTED |

## Non-negotiable rules
1. A green unit-test suite alone does not establish production readiness.
2. A model reviewing its own output is not independent verification.
3. Security-sensitive and destructive actions require explicit authority and auditability.
4. Secrets must never be committed to the repository.
5. Every release candidate identifies its exact source revision and dependency set.
6. Failed gates block release; they are not averaged away.
7. Exceptions require an owner, rationale, expiry and compensating controls.

## Release states
DRAFT → BUILT → TESTED → SECURITY_REVIEWED → INDEPENDENTLY_VERIFIED → APPROVED → RELEASED

A failed check returns the candidate to remediation. Rollback preserves the prior known-good release and records the reason.
