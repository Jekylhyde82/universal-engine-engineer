# Extraction Register

**Destination:** `Jekylhyde82/universal-engine-engineer`  
**Working branch:** `foundation/master-repository-charter`  
**Disposition:** Source-preserved snapshots only; all packages quarantined.

## Package 1 — SYPHON provider foundation

**Destination:** `extractions/quarantine/syphon-provider-foundation/`  
**Source repository:** `Jekylhyde82/7282ALLSPARXPRIME`  
**Source branch:** `syphon/multi-provider-foundation`  
**Source commit:** `5cf52325c9ff4e56a891cee1d3139b13a0e3ffa2`  
**Source PR:** [#13](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/13)

| Destination file | Original source path |
|---|---|
| `providers.ts` | `src/lib/allsparxPrime/providers.ts` |
| `runtime.ts` | `src/lib/allsparxPrime/runtime.ts` |
| `tests/provider-routing.test.mjs` | `tests/syphon-provider-routing.test.mjs` |
| `tests/runtime.test.mjs` | `tests/syphon-runtime.test.mjs` |
| `README.md` | Authored provenance and quarantine record |
| `LICENSE.source` | Original source MIT licence notice |

## Package 2 — SYPHON gateway security

**Destination:** `extractions/quarantine/syphon-gateway-security/`  
**Source repository:** `Jekylhyde82/7282ALLSPARXPRIME`  
**Source branch:** `syphon/server-gateway-security`  
**Source commit:** `8ac4095cfc83eb26f282b387a7d0c25792c40a42`  
**Source PR:** [#17](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/17)

| Destination file | Original source path |
|---|---|
| `worker.mjs` | `src/worker.mjs` |
| `auth.ts` | `src/lib/allsparxPrime/auth.ts` |
| `tests/auth.test.mjs` | `tests/syphon-auth.test.mjs` |
| `tests/gateway.test.mjs` | `tests/syphon-gateway.test.mjs` |
| `README.md` | Authored provenance and quarantine record |

## Package 3 — SYPHON evidence and assurance pipeline

**Destination:** `extractions/quarantine/syphon-evidence-and-pipeline/`  
**Source repository:** `Jekylhyde82/7282ALLSPARXPRIME`  
**Source branch:** `syphon/9-stage-independent-gates`  
**Source commit:** `91f0680f4d6828bf4374423a7abc49e7c0a28509`  
**Related source work:** [PR #15](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/15) and [PR #19](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/19)

| Destination file | Original source path |
|---|---|
| `evidence-ledger.js` | `workers/allsparx-gateway/src/evidence-ledger.js` |
| `verify-evidence-export.mjs` | `scripts/verify-evidence-export.mjs` |
| `tests/evidence-export.test.mjs` | `tests/syphon-evidence-export.test.mjs` |
| `allsparx-pipeline-evidence.mjs` | `scripts/allsparx-pipeline-evidence.mjs` |
| `allsparx-prime-9-stage.yml` | `.github/workflows/allsparx-prime-9-stage.yml` |
| `README.md` | Authored provenance and quarantine record |

The source MIT notice is preserved at `../syphon-provider-foundation/LICENSE.source`.

## Package 4 — Universal Capability System

**Destination:** `extractions/quarantine/universal-capability-system/`  
**Source repository:** `Jekylhyde82/7282ALLSPARXPRIME`  
**Source branch:** `allsparx/universal-capability-system`  
**Source commit:** `b271a166de17984aedb4c9a98a7273489c45b463`  
**Source PR:** [#16](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/16)

All 33 changed source files were preserved, retaining their relative paths:
- `.github/workflows/syphon-baseline.yml`
- `docs/architecture/universal-capability-system.md`
- `docs/deployment/cloudflare-snapshot-worker.md`
- `package.json`, `pnpm-lock.yaml`, `wrangler.toml`
- `schemas/capability-manifest.schema.json`
- `schemas/capability-registry-record.schema.json`
- `schemas/source-repository-record.schema.json`
- `schemas/examples/capability-manifest.example.json`
- `schemas/examples/capability-registry-record.example.json`
- `schemas/examples/source-repository-record.example.json`
- `src/lib/allsparxPrime/capability-discovery.mjs`
- `src/lib/allsparxPrime/capability-manifest-validator.mjs`
- `src/lib/allsparxPrime/capability-policy.mjs`
- `src/lib/allsparxPrime/capability-registry-chain.mjs`
- `src/lib/allsparxPrime/capability-registry.mjs`
- `src/lib/allsparxPrime/continuous-improvement-pipeline.mjs`
- `src/lib/allsparxPrime/improvement-assessment.mjs`
- `src/lib/allsparxPrime/repository-snapshot-acquirer.mjs`
- `src/worker/index.mjs`
- `tests/capability-discovery.test.mjs`
- `tests/capability-manifest-validation.test.mjs`
- `tests/capability-manifest.test.mjs`
- `tests/capability-policy.test.mjs`
- `tests/capability-registry-chain.test.mjs`
- `tests/capability-registry-service.test.mjs`
- `tests/capability-registry.test.mjs`
- `tests/cloudflare-worker.test.mjs`
- `tests/continuous-improvement-pipeline.test.mjs`
- `tests/improvement-assessment.test.mjs`
- `tests/repository-snapshot-acquirer.test.mjs`
- `tests/source-repository-record.test.mjs`

The PR description calls this architecture/documentation only, but the changed-file list includes executable modules and tests. The architecture document contains mixed status statements. Source CI run #142 on this exact PR head failed at the append-only registry service test step: three subtests threw `Invalid capability semantic version.` Job logs point to `capability-registry-chain.mjs`. Static JavaScript checks confirm double-escaped semver and timestamp regex patterns reject valid fixtures `0.1.0` and `2026-10-30T03:00:00.000Z`. The semver defect explains the observed failures; the timestamp defect is separately confirmed. The snapshot is quarantined pending a full source review and target-specific tests.

## Integrity evidence

All 46 copied source artifacts (code, tests, workflows, docs, schemas, package/build context and configuration) have source-matching Git blob SHA values. The initial 13 artifacts were also re-fetched from source and destination and their contents compared. For every verified pair:
- source Git blob SHA equals destination Git blob SHA;
- fetched file contents are identical.

This proves byte-identical preservation of those files at inspection time. It does not prove correctness, safety, compatibility or operational readiness.

## Mandatory quarantine rules

- Do not import snapshots directly into production runtime.
- Do not activate copied workflows in the master repository without reviewing their permissions, secrets, triggers, branch protections and external side effects.
- Do not assume Cloudflare, Supabase, provider accounts, Durable Objects, secrets, budgets, signing keys or external checkpoints exist in the destination.
- Do not promote source CI results to destination verification.
- Preserve source commit, branch, PR and licence provenance through any future adaptation.
- Require target-side tests, security review, rollback plan and independent verification before promotion.
