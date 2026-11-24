# AFI PRIME — Governed Multi-Specialist Coordination

**Canonical function:** UNIFIED FUSION SYNERGY — AFI PRIME  
**Implementation:** src/universal_engine/fusion.py  
**Status:** Executable coordination prototype; not a production intelligent reasoning runtime.

## Purpose

The coordinator dispatches an explicit batch of requests to already-registered specialist providers through the existing provider registry and policy-enforcing runtime. It preserves each specialist's identity, output, status and failure independently.

It does not create a second fusion authority. It is an implementation component of the canonical AFI PRIME function.

## Execution contract

1. The caller supplies an authenticated principal identifier and an explicit list of specialist invocations.
2. The coordinator resolves every provider and checks that each request's capability ID matches the provider's registered capability.
3. The entire batch is preflighted before any provider is called. Unknown providers, capability mismatches, invalid invocations or duplicate correlation IDs reject the batch without partial dispatch.
4. Each invocation passes through the existing dispatch boundary. Policy is evaluated separately for the principal, capability and operation. A denied request never reaches its provider.
5. Independent invocations execute concurrently, bounded by the configured max_workers value (default 9).
6. One provider exception is captured as a failed specialist outcome; healthy peers can still complete.
7. The result envelope preserves outcomes in caller-supplied order. It reports succeeded, partial, denied or failed without collapsing specialist findings into an unsupported consensus.

## Minimal usage

The public API is AFIPrimeFusionCoordinator, ProviderRequest and SpecialistInvocation from the universal_engine package.

1. Construct the existing ProviderRegistry and PolicyEngine from trusted application configuration.
2. Register only adapters whose capability lifecycle state is INTEGRATED.
3. Construct AFIPrimeFusionCoordinator(registry, policy_engine, max_workers=9).
4. Call coordinator.fuse([...], principal_id=authenticated_principal_id) with explicit SpecialistInvocation objects.
5. Inspect each returned outcome independently; do not treat the aggregate status as a correctness certificate.

A typical invocation contains a provider ID and a ProviderRequest with a unique UUID correlation ID, the registered capability ID, an operation and a JSON-compatible payload. The names in this example are illustrative; they do not imply production provider registrations.

## Boundaries and non-claims

- The coordinator is not an authentication service. principal_id must come from a trusted identity layer.
- It is not a policy authority. Existing policy rules decide each invocation; default deny remains in force.
- It cannot register, approve, activate or discover providers. Registration remains explicit and lifecycle-gated.
- It does not grant providers access to each other or to another instance's state.
- It does not synthesize semantic consensus, erase disagreement, certify correctness or replace an independent verifier.
- It does not automatically retry failed calls.
- Provider exceptions are represented by a generic failure class and exception type; raw exception text and stack traces are not exposed in the result.
- The request deadline is checked by the dispatch boundary before provider execution. It does not forcibly interrupt a provider that is already running.
- Concurrent execution uses in-process threads. It is not a process, container, VM or operating-system security boundary. Provider adapters must be safe for the configured concurrency level.
- The separate nine-process runtime proof demonstrates scoped process/state/evidence behaviour; it is not this Python coordinator and is not a production sandbox.

## Tests

tests/test_fusion.py covers multi-specialist dispatch, preservation of separate findings, per-specialist denial, preflight rejection without side effects, provider-failure isolation, duplicate correlation rejection and default-deny behaviour.

**Proof discipline:** passing these tests demonstrates only the tested coordination contract. It does not establish model quality, semantic reasoning, production security, operational readiness or independent verification.
