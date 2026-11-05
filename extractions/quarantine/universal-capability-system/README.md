# Universal Capability System — Preserved Source Snapshot

**Disposition:** PRESERVED / QUARANTINED / NOT INTEGRATED  
**Source repository:** https://github.com/Jekylhyde82/7282ALLSPARXPRIME  
**Source branch:** `allsparx/universal-capability-system`  
**Source commit:** `b271a166de17984aedb4c9a98a7273489c45b463`  
**Source pull request:** https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/16  
**Licence:** MIT; shared source notice at `../syphon-provider-foundation/LICENSE.source`.

## Why this is preserved

The PR description characterizes this change as an architecture/documentation specification and says no runtime registry, extractor, installer or sandbox runner exists. However, the PR changed-file inventory includes executable discovery, manifest-validation, policy, registry, continuous-improvement and repository-snapshot modules, a Cloudflare Worker, JSON schemas, configuration and dedicated tests. The GitHub workflow lookup for the exact PR head returned a failed SYPHON baseline run (#142); the failure details were not available through this inspection.

The architecture document also begins with a proposed/not-enabled status while later sections describe Phase 2 and Phase 6 implementations. This is a material status/documentation discrepancy. The code is preserved as evidence for review, not assumed complete or operational.

## Preserved contents

- `src/lib/allsparxPrime/`: read-only capability discovery, manifest validation, deny-by-default policy, hash-chained registry, improvement assessment/pipeline and repository snapshot acquisition.
- `src/worker/index.mjs`: Cloudflare webhook/snapshot Worker source.
- `schemas/`: capability and source-repository schemas plus examples.
- `tests/`: corresponding module, registry, policy, snapshot and Worker tests.
- `docs/`: architecture and Cloudflare snapshot-worker documentation.
- `package.json`, `pnpm-lock.yaml`, `wrangler.toml`, nested workflow: original build/deployment context only; not active master configuration.

## Initial engineering observations

The discovery module describes a bounded, read-only local scan of declarative manifests and package metadata. It explicitly avoids executing package code, skips symlinks and applies file/depth/manifest-size bounds.

The policy module uses deny-by-default evaluation and requires manifest validity, explicit permissions/destinations, verification, licence approval, security review, explicit secret-access denial and a package digest.

The registry module requires an injected store with atomic compare-and-append semantics and performs read-after-write verification. This is a useful contract, but correctness depends on the concrete storage adapter and its concurrency behavior.

The snapshot Worker documentation describes signed GitHub webhook verification, source repository and licence allowlists, immutable commit pinning, bounded archive acquisition, digest calculation and R2 metadata. It also states that no extraction, installation or execution occurs during acquisition.

## Unresolved review gates

- Reconcile the PR description, architecture status and actual executable changed-file inventory.
- Inspect all modules and schemas for path traversal, archive bombs, symlink handling, webhook replay, signature timing, allowlist bypass, TOCTOU, storage concurrency and trust-boundary flaws.
- Confirm the capability registry adapter actually provides atomic compare-and-append under concurrent requests.
- Review dependency and licence posture, including the captured package/lockfile.
- Review Cloudflare Worker permissions, R2 lifecycle/retention, Durable Object migration and webhook secret custody.
- Confirm source allowlist and per-repository licence policy fail closed.
- Run the complete source test suite and security checks on the exact source commit; then adapt and rerun in the destination.
- Independently test snapshot integrity, idempotency, retries, malformed archives and hostile archive entries.
- Do not enable the nested workflow or deploy the Worker from this snapshot.
- Keep privileged installation, code execution, automatic merge and production deployment disabled pending separate approval and verification.

This snapshot is not a working Universal Capability System, autonomous installer or production repository crawler. It is preserved source material for controlled engineering review. The original source repository, branch and PR remain untouched.
