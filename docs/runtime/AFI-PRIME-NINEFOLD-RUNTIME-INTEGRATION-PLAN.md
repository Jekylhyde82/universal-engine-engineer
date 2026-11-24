# AFI PRIME — Nine-Instance Runtime Integration Plan

**Status:** implementation contract / next engineering work package  
**Authority:** NINEFOLD INTRINSIC  
**Canonical function:** UNIFIED FUSION SYNERGY — AFI PRIME  
**Instance topology:** nine scoped UMIC execution contexts; one shared function identity  
**Release status:** NO-GO for production

## 1. Current verified boundary

Two executable prototypes exist, but they are not yet one integrated runtime:

1. `src/universal_engine/fusion.py` provides a provider-neutral Python AFI PRIME coordinator. It preflights registered providers, applies the existing policy dispatch boundary per invocation, bounds parallel execution, preserves each specialist result, and optionally persists digest-only evidence through `SQLiteFusionEvidenceLedger`.
2. `packages/ninefold-fusion-runtime/` starts nine Node.js child processes with distinct process IDs, state namespaces and hash-chained evidence streams. Its current command surface is deliberately limited to health, state read/write, evidence inspection and audit markers.

The Node.js process proof is not a reasoning engine. The Python coordinator is not currently hosted inside, or connected to, those nine process contexts. No integrated runtime should be claimed until the bridge and end-to-end tests below exist.

## 2. Target responsibility split

- **Parent supervisor:** lifecycle of the nine processes, authenticated actor binding, instance-scope admission, request correlation, bounded IPC, timeout handling and fault containment.
- **Shared AFI PRIME function:** one versioned implementation identity, loaded into each scoped UMIC context. Nine instances do not create nine independent authorities or nine divergent codebases.
- **Python provider coordinator:** specialist registration, capability binding, preflight, per-specialist policy dispatch and preservation of distinct outcomes. It remains a coordinator, not an independent policy authority or verifier.
- **Independent policy service:** supplies trusted actor identity and scoped authorisation. The AFI PRIME process cannot mint grants or widen its own permissions.
- **Evidence:** per-instance append-only local evidence plus the Python fusion digest ledger, connected by common fusion ID, correlation IDs, function version and policy version. External anchoring remains a separate production requirement.
- **Independent verifier:** separately operated and able to disagree; never implemented as a self-certification method on the coordinator.

## 3. Required bridge contract

A bridge request must be a versioned, schema-validated envelope containing:

- protocol version;
- fusion ID and unique correlation ID;
- canonical fusion-function ID and version;
- target UMIC instance ID;
- provider ID and capability ID;
- operation name;
- authenticated principal reference (opaque, non-PII);
- policy version and a reference to the independently issued decision/grant;
- bounded deadline and payload-size limit;
- payload digest and idempotency classification.

A response must preserve the same correlation, fusion, function and instance identities and contain:

- provider result status;
- output or typed error;
- elapsed time;
- request and result digests;
- instance evidence sequence and head hash;
- execution outcome classification: completed, denied, failed-before-start, or UNKNOWN-after-start.

The bridge must reject unknown protocol versions, identity mismatches, stale grants, duplicate correlation IDs, expired deadlines, unregistered providers, capability mismatches and oversized payloads before execution.

## 4. Dispatch sequence

1. Trusted caller submits an explicit batch; discovery does not auto-register or activate providers.
2. Parent authenticates the actor and resolves the approved instance scope.
3. Coordinator validates the complete batch and provider/capability bindings before side effects.
4. Independent policy evaluates each invocation; deny-by-default.
5. Parent routes each approved invocation to the designated UMIC process over bounded IPC.
6. Instance records a start/decision marker before provider execution and a terminal marker after outcome.
7. Coordinator collects all outcomes without erasing specialist identity or converting them into unsupported consensus.
8. Fusion evidence sink records request/result digests and metadata atomically.
9. Independent verifier evaluates the outcome against separate evidence and returns VERIFIED, REJECTED or INCONCLUSIVE.
10. If any stage fails after execution may have begun, record UNKNOWN and reconcile; never blindly retry a non-idempotent action.

## 5. Failure semantics

- Preflight rejection: no provider is invoked.
- Policy denial: denied invocation is recorded; other invocations may proceed only if batch policy permits.
- Provider failure: isolate the failure and preserve successful peer outcomes.
- Instance process exit before dispatch: fail that invocation without dispatch.
- Timeout after dispatch: mark UNKNOWN; terminate/quarantine the affected instance as appropriate and reconcile evidence before any retry.
- Evidence write failure: surface the completed result and persistence failure separately; do not claim durable evidence.
- Parent restart: reopen the same runtime namespace and verify each evidence chain before admitting requests.
- Hash-chain verification is tamper evidence, not protection from a privileged host able to rewrite the whole store.

## 6. Mandatory integration tests

1. One shared function version is reported by all nine instances.
2. Nine instance IDs, process IDs, state namespaces and evidence streams remain unique.
3. Each UMIC can dispatch only providers assigned to its approved capability scope.
4. Cross-instance dispatch is denied absent an explicit independent grant.
5. Duplicate, stale, malformed, oversized and mismatched envelopes fail before provider side effects.
6. One provider exception does not erase other specialist results.
7. One instance crash does not corrupt peer evidence or state.
8. Timeout after start yields UNKNOWN, not a fabricated failure or automatic retry.
9. Replayed correlation IDs and idempotency keys are rejected or reconciled.
10. Evidence sequence and hash links are verifiable across restart.
11. Fusion-level evidence references all nine scoped evidence streams without making one stream authoritative for another.
12. A separate verifier can disagree with the coordinator and prevent VERIFIED status.
13. Policy, provider and function versions are pinned to the exact test commit.
14. Resource quotas, network egress policy and process sandbox controls are tested on the actual deployment host.

## 7. Ordered implementation tasks

| Order | Work item | Acceptance evidence |
|---:|---|---|
| 1 | Define JSON Schema for request, response, error and evidence-reference envelopes | **Schema draft committed** at `packages/ninefold-fusion-runtime/schemas/afi-prime-ipc-v1.schema.json`; schema-validator and compatibility-fixture tests remain required |
| 2 | Add typed IPC dispatch command to the Node worker and runtime | Unit tests for allowlist, validation, correlation and denial |
| 3 | Add a Python bridge client with strict timeout and UNKNOWN semantics | Contract tests against a deterministic local fixture |
| 4 | Bind provider registry entries to approved UMIC/capability assignments | Registry consistency tests; no inferred 99-lineage mappings |
| 5 | Bind per-instance evidence references to the fusion evidence event | Cross-ledger integrity and restart tests |
| 6 | Add independent verifier interface and adversarial disagreement tests | Verifier contract and false-VERIFIED prevention tests |
| 7 | Add OS-level sandbox, resource limits, egress policy, secret isolation and signed external checkpoints | Host-level security evidence and independent review |
| 8 | Run target-device/offline and load/fault campaigns | Reproducible benchmark and recovery report |

## 8. Implementation progress — 2026-11-25

- **Completed as a contract artifact:** added the strict JSON Schema draft for AFI PRIME IPC protocol v1. It defines request/response identity binding, nine UMIC target IDs, correlation and fusion IDs, policy/grant references, deadlines, payload/result digests, idempotency classification, evidence-chain references and explicit UNKNOWN-after-start semantics.
- **Not yet implemented:** transport-level byte limits, authenticated principal/grant verification, schema execution in the Node worker or Python bridge, duplicate-correlation storage, and end-to-end dispatch. JSON Schema is structural validation only; it does not establish identity, authority or network safety.
- **Next acceptance gate:** add a pinned schema validator and positive/negative compatibility fixtures, then wire the same contract into both runtimes before enabling dispatch.

## 9. Explicit non-goals for this work package

- No new fusion function, fusion authority or tenth instance.
- No inferred names or assignments for the 99 lineage placeholders.
- No automatic provider discovery, adoption or activation.
- No raw prompt/output persistence in the digest-only evidence ledger.
- No claim that Node child processes are a production security boundary.
- No Android screen/camera control, unrestricted browser, shell or network access.
- No production deployment or merge authorisation.

**Completion rule:** the Python coordinator and nine-instance process runtime are integrated only when the bridge contract, implementation, end-to-end tests, independent verification and host-security evidence all pass on one exact commit.