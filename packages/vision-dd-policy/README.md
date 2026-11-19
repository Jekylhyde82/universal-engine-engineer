# V.I.S.I.O.N. / D.D. Policy Core

A dependency-free Node.js reference package for deterministic policy evaluation and guarded action-state transitions.

## Status

**Prototype / testable policy logic only. Not a production enforcement service.**

This package does not:
- capture screens or images;
- control a browser, desktop or Android device;
- authenticate users or devices;
- issue signed execution grants;
- provide durable nonce storage;
- persist an action ledger;
- independently verify application outcomes;
- implement V.I.S.I.O.N., D.D., AFI PRIME or EB9PRIME runtimes.

## Run tests

Requires Node.js 22 or later.

```sh
npm test
```

## Decision semantics

- `DENY`: request is malformed, out of scope, prohibited or cannot be safely evaluated.
- `REQUIRE_APPROVAL`: action risk class requires human approval.
- `ELIGIBLE_FOR_GRANT`: deterministic checks passed. This is **not** an execution token and must never be passed directly to an executor.

For R2/R3, callers must provide a trusted cryptographic `verifyApproval` function and an atomic, durable `consumeApprovalNonce` function. Tests use fakes only. Production must use authenticated approver keys and persistent replay protection. Approval is bound to the current policy version and exact action/session.

The action-state transition guard checks allowed role/state transitions and requires evidence references for grant, verification and recovery states. Its caller must authenticate actor identity and validate the referenced grant/evidence independently.

A separate policy service must issue a short-lived, one-use, action/session-bound grant. D.D. must independently validate that grant before every action.
