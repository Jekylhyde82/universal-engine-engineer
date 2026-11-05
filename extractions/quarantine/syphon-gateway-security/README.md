# SYPHON Gateway Security — Preserved Extraction Snapshot

**Disposition:** PRESERVED / QUARANTINED / NOT INTEGRATED  
**Source repository:** https://github.com/Jekylhyde82/7282ALLSPARXPRIME  
**Source branch:** `syphon/server-gateway-security`  
**Source commit:** `8ac4095cfc83eb26f282b387a7d0c25792c40a42`  
**Source pull request:** https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/17  
**Licence:** MIT; see `../syphon-provider-foundation/LICENSE.source`.

## Preserved components
- `worker.mjs`: Cloudflare Worker gateway and server-side provider execution boundary.
- `auth.ts`: browser-side Supabase session/token helper.
- `tests/auth.test.mjs`: authentication contract tests.
- `tests/gateway.test.mjs`: gateway request, auth and provider contract tests.

## Required review before reuse
This branch is explicitly stacked on PR #13 and is still a draft. Its description reports a successful CI run (35 tests, Astro checks, build and Wrangler dry-run), but also states that Supabase asymmetric JWT signing/JWKS, production configuration, provider secrets, live endpoint verification and deployment remain pending.

A dry-run is not a deployment. Mocked tests do not prove live authentication, rate-limit behavior under concurrency, provider spend controls or production security. The source also contains Cloudflare/Supabase-specific bindings and requires careful adaptation to the master architecture's least-privilege, privacy, identity, recovery and independent-verification requirements.

Do not deploy or activate this snapshot. Keep its source PR, branch, project boundaries and history intact until an independent security review and target-specific tests are complete.
