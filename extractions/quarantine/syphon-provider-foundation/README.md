# SYPHON Provider Foundation — Preserved Extraction Snapshot

**Disposition:** PRESERVED / QUARANTINED / NOT INTEGRATED  
**Purpose:** Retain reusable provider-routing and hardened browser-runtime source for independent review before adaptation to UNIVERSAL ENGINE / ENGINEER.

## Provenance
- Source repository: https://github.com/Jekylhyde82/7282ALLSPARXPRIME
- Source branch: `syphon/multi-provider-foundation`
- Source commit: `5cf52325c9ff4e56a891cee1d3139b13a0e3ffa2`
- Source pull request: https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/13
- Source files are copied without intentional functional changes.

## Preserved components
- `providers.ts`: provider identifiers, task routing policy, strict explicit-provider selection.
- `runtime.ts`: bounded browser-to-gateway request contract and evidence envelope.
- `tests/provider-routing.test.mjs`: provider selection contract tests.
- `tests/runtime.test.mjs`: runtime input, endpoint, response and timeout contract tests.

## Important limitations
This is a source-preservation snapshot, not an operational engine or deployed gateway. The original implementation belongs to a CloudCredits.io Astro application and depends on that application's build/runtime context. Tests have not been run in this destination repository. Provider routing policy does not prove provider availability, quality, live connectivity, cost control or successful execution.

Do not import these files into a production runtime until compatibility, dependencies, security, licensing, tests and architecture ownership have been independently reviewed. Keep the original repository, branches and pull requests intact.

## Licence and attribution
The source repository declares MIT licensing. Preserve the source copyright and MIT licence notice with this extraction; do not remove upstream attribution. See the adjacent `LICENSE.source` file.
