# Read-only Verification Agent — Preserved Source Snapshot

**Disposition:** PRESERVED / QUARANTINED / NOT INTEGRATED  
**Source repository:** https://github.com/Jekylhyde82/7282ALLSPARXPRIME  
**Source branch:** `syphon/agent-foundation-promptfoo`  
**Source commit:** `e454c8429b686819d85b07124027c50d119b0e17`  
**Source PR:** https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/18  
**Licence:** MIT; shared source notice at `../syphon-provider-foundation/LICENSE.source`.

## Preserved components
- `src/agents/verification-agent.mjs`: deterministic, read-only evidence-claim evaluator.
- `tests/verification-agent.test.mjs`: status-ladder and false-success contract tests.
- `promptfooconfig.yaml`: pinned deterministic Echo-provider evaluation fixture.
- `.github/workflows/agent-evals.yml`: test/evaluation workflow with short-retention artifact.
- `docs/AGENT-FOUNDATION.md`: status semantics, boundaries and staged future-runtime plan.

## Engineering value
The module distinguishes PLANNED, IMPLEMENTED, INSTALLED, TESTED and VERIFIED. It rejects a VERIFIED claim unless the supplied evidence includes implementation, tests and an independent review marked durable and safety-passed. It is a useful starting point for the master proof-before-claim governance invariant.

## Critical limitations
- The evaluator trusts caller-supplied fields such as `trustworthy`, `independent`, `durable` and `safetyPassed`. It does not retrieve or authenticate evidence sources. A caller can forge these booleans unless a separate trusted evidence collector and verifier are implemented.
- The module does not run tests, fetch GitHub checks, inspect deployment state, verify reviewer identity, validate checkpoint signatures or independently establish durability/safety.
- The Promptfoo configuration uses the Echo provider and explicitly makes no model calls. It tests configuration/rendering/assertions, not model quality or red-team resistance.
- The PR #18 description says the latest Promptfoo run was still in progress and the preceding run was cancelled by a subsequent commit. Do not claim a fully completed Promptfoo evaluation from that description.
- Cloudflare Agents SDK and Workflows are planned only; they are not installed or operational in this source slice.
- No network, credentials, merge or deployment capability is implemented by the verification module.

This is a deterministic evidence-policy primitive, not an autonomous verifier or agent runtime. Integrate only after replacing caller-asserted trust flags with authenticated, provenance-bound evidence and independent verification adapters. Keep it quarantined until that review and target-side tests pass.
