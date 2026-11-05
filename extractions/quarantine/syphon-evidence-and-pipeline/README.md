# SYPHON Evidence and Assurance Pipeline — Preserved Extraction Snapshot

**Disposition:** PRESERVED / QUARANTINED / NOT INTEGRATED  
**Purpose:** Retain evidence-ledger, offline verification and CI assurance source for independent review.

## Provenance
- Source repository: https://github.com/Jekylhyde82/7282ALLSPARXPRIME
- Source branch: `syphon/9-stage-independent-gates`
- Source commit: `91f0680f4d6828bf4374423a7abc49e7c0a28509`
- Related source work: PR #15 (evidence ledger) and PR #19 (nine-stage assurance pipeline).
- Source files are copied without intentional functional changes.
- Source licence: MIT; shared preserved notice at `../syphon-provider-foundation/LICENSE.source`.

## Preserved components
- `evidence-ledger.js`: Cloudflare Durable Object ledger implementation.
- `verify-evidence-export.mjs`: offline semantic/hash-chain export verifier.
- `tests/evidence-export.test.mjs`: offline evidence export contract tests.
- `allsparx-pipeline-evidence.mjs`: commit/run-bound pipeline evidence manifest tooling.
- `allsparx-prime-9-stage.yml`: nine-stage CI assurance workflow.

## Critical limitations
These are quarantined source snapshots, not a configured, deployed or production-ready system. The ledger requires Cloudflare Durable Objects, secrets, deployment metadata, trusted checkpoint custody and external retention arrangements. The workflow references the original application's dependency/build context and must not be activated in this repository without adaptation.

The offline verifier's test fixtures and the pipeline's own checks do not establish independent trust in the evidence source, signing-key custody, production runtime correctness or operational availability. The original PR #15 explicitly records a NO-GO deployment decision and outstanding blockers. PR #19 deliberately holds at Stage 9.

Do not merge, deploy, activate or represent these components as VERIFIED until dependencies, threat model, key custody, trust bootstrap, failure modes, tests and independent review are complete. Preserve the original repository, branches and pull requests intact.
