# Repository Consolidation Register

**Authoritative master:** [Jekylhyde82/universal-engine-engineer](https://github.com/Jekylhyde82/universal-engine-engineer)  
**Default branch:** `main`  
**Working branch:** `foundation/master-repository-charter`  
**Audit snapshot:** 2026-11-05

## Consolidation policy

This is controlled consolidation, not a blind repository merge. Preserve original repositories, commit history, branches, pull requests, licences and provenance. Do not delete, archive, overwrite or merge source repositories as a shortcut.

Disposition values:
- **master** — authoritative architecture and governance;
- **candidate** — reviewed for possible migration;
- **subproject** — retained under a governed project boundary;
- **archive** — preserved for history/reference;
- **excluded** — not migrated, with a recorded reason.

## Account repository inventory

The connected GitHub account listing returned seven repositories. This inventory does not claim to cover repositories outside that account listing.

| Repository | Visibility / observed default branch | Observed contents | Disposition |
|---|---|---|---|
| [universal-engine-engineer](https://github.com/Jekylhyde82/universal-engine-engineer) | Public / `main` | Short README; separate foundation branch contains charter, registers and quarantined extraction snapshots | **Master** |
| [7282ALLSPARXPRIME](https://github.com/Jekylhyde82/7282ALLSPARXPRIME) | Public / `main` | 12,029 KB; substantial Astro application; confirmed fork of `t3-sh/cloudcredits.io`; 33 branches and 20 PRs | **Candidate / governed subproject pending full review** |
| [ALLSPARX-PRIME](https://github.com/Jekylhyde82/ALLSPARX-PRIME) | Private / `main` | README only; one initial commit; no PRs returned | **Preserve / inspect before disposition** |
| [ALLSPARXPRIME](https://github.com/Jekylhyde82/ALLSPARXPRIME) | Private / no default branch | Empty Git repository; no commits or PRs returned | **Preserve as empty shell pending owner decision** |
| [ALLSPARX-PRIME-](https://github.com/Jekylhyde82/ALLSPARX-PRIME-) | Public / `MAIN` | README only; one initial commit; no PRs returned | **Preserve / inspect before disposition** |
| [ALLSPARX.PRIME-](https://github.com/Jekylhyde82/ALLSPARX.PRIME-) | Private / `main` | README only; one initial commit; no PRs returned | **Preserve / inspect before disposition** |
| [UNIVERSAL-ENGINE.ENGINEER-](https://github.com/Jekylhyde82/UNIVERSAL-ENGINE.ENGINEER-) | Private / `main` | README only; one initial commit; no PRs returned | **Preserve / inspect before disposition** |

For the five small repositories, branch and default-tree inspection found no additional source tree beyond the single README or empty repository state. Their tags endpoints were not available through the connected inspection action, so tag absence is not asserted.

## Critical source finding: 7282ALLSPARXPRIME

The GitHub repository API confirms:
- `fork: true`;
- parent/source: `t3-sh/cloudcredits.io`;
- declared licence: MIT;
- default branch: `main`;
- 33 branches and 20 pull requests at inspection.

Its README identifies it as CloudCredits.io, an Astro-based startup-credit directory. It is not a clean, standalone UNIVERSAL ENGINE / ENGINEER implementation. Do not copy the whole application into the master root. Keep unrelated product code and upstream ownership boundaries intact.

### Pull-request and branch risk

Ten open PRs were identified in the source repository: #6, #7, #11, and #13–#19. Several are stacked on other feature branches. In particular:
- [#13 — vendor-neutral multi-provider foundation](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/13): provider policy and browser gateway contract; not a deployed gateway.
- [#14 — Cloudflare gateway](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/14): alternate gateway implementation stacked on #13.
- [#15 — evidence ledger](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/15): hash-chained evidence ledger and export; explicitly records a NO-GO deployment decision and outstanding operational/security blockers.
- [#16 — universal capability system](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/16): architecture specification only; no extractor, installer, runtime registry or sandbox is claimed to exist.
- [#17 — gateway and Supabase authentication](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/17): gateway implementation stacked on #13; PR description reports 35 tests, Astro checks, build and Wrangler dry-run passing, but live Auth/JWKS, provider secrets, deployment and endpoint verification remain pending.
- [#18 — Promptfoo and staged agent foundation](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/18): draft; Echo-provider evaluation is a fixture, not model-quality or live-gateway evaluation; latest complete run was not established.
- [#19 — nine-stage assurance pipeline](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/19): draft; Stage 9 intentionally records HOLD. Successful workflow automation is not production readiness.
- [#11 — runtime reconciliation](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/11): draft; its description records branch divergence and says not to merge without full reconciliation.
- [#7 — runtime hardening](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/7): endpoint hardening and mocked contract tests; live provider connectivity is separate.
- [#6 — live endpoint verification](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/6): workflow proposal; its recorded CI did not execute a live endpoint check.

PR #20 is a closed draft dependency-remediation preview; preserve it for history. Other closed PRs remain in the original repository.

### Source CI evidence inspected

GitHub Actions workflow-run lookup returned successful runs associated with:
- PR #13 head `5cf52325c9ff4e56a891cee1d3139b13a0e3ffa2`;
- PR #17 head `8ac4095cfc83eb26f282b387a7d0c25792c40a42`;
- PR #19 head `91f0680f4d6828bf4374423a7abc49e7c0a28509`.

This is evidence that named source-commit workflows completed successfully. It is not a test of the destination copies, a live service test, independent security approval, or deployment verification.

## Master working branch and preservation actions

The master repository's `main` branch initially contained only a short README. The working branch `foundation/master-repository-charter` contains the master charter, consolidation register, implementation-status document and extraction snapshots. [PR #1](https://github.com/Jekylhyde82/universal-engine-engineer/pull/1) is already open as a draft against `main`; new work is being added to that branch rather than creating a duplicate PR.

Three source-preservation groups have been added under `extractions/quarantine/`:
1. `syphon-provider-foundation/`;
2. `syphon-gateway-security/`;
3. `syphon-evidence-and-pipeline/`.

Thirteen copied source/code/test/workflow files were re-fetched from their exact source commits and destination Git blob SHA values matched exactly. Provenance notes and the source MIT licence notice were retained. These snapshots are quarantined, not integrated.

## Migration gates

For every candidate:
1. Inventory branches, tags, commits, PRs, issues, workflows, releases and deployment dependencies.
2. Identify upstream ownership, licence obligations, third-party code, secrets, personal data and generated/binary assets.
3. Map reusable components to master architecture registers and current naming constraints.
4. Decide: extract, integrate, retain as a governed subproject, archive or exclude.
5. Preserve source repository, source commit, file-level provenance and licence notices.
6. Migrate through a dedicated branch and reviewed PR.
7. Run target-side tests, security checks and build verification.
8. Record failures, limitations, residual risks and independent verification evidence.

## Current limitations

The connected GitHub actions used here can inspect repositories and create/update files, but do not provide a Git-preserving repository import that transfers all history, branches, tags, issues and PR metadata. File-level extraction is not a substitute for history-preserving migration. The original repositories and their open PRs remain intact.

The current audit covers all seven repositories returned by the connected account listing, their default-branch trees and branch listings, plus detailed source-branch/PR inspection for the principal code repository. It is not a forensic audit of every historical commit, every feature branch, every dependency alert, or every external deployment.
