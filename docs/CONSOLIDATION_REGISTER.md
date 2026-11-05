# Repository Consolidation Register

**Target master:** [Jekylhyde82/universal-engine-engineer](https://github.com/Jekylhyde82/universal-engine-engineer)  
**Default branch:** `main`  
**Working foundation branch:** `foundation/master-repository-charter`

## Consolidation policy

This is a controlled consolidation, not a blind repository merge. Preserve original repositories, commit history, branches, pull requests, licences, and provenance until each source has been audited and a migration path approved. Do not delete, archive, or overwrite source repositories.

A source can be:
- **master** — authoritative architecture and governance;
- **candidate** — reviewed for possible migration;
- **subproject** — retained under a governed project boundary;
- **archive** — preserved for history/reference;
- **excluded** — not migrated, with a recorded reason.

## Initial inventory (GitHub connection inspection, 2026-11-05)

| Repository | Observed state | Initial disposition |
|---|---|---|
| [universal-engine-engineer](https://github.com/Jekylhyde82/universal-engine-engineer) | Public; default branch `main`; contained a short README at inspection | **Master** |
| [7282ALLSPARXPRIME](https://github.com/Jekylhyde82/7282ALLSPARXPRIME) | Public; approximately 12,029 KB; Astro; fork of CloudCredits.io; active SYPHON / ALLSPARX PR work | **Candidate / subproject pending audit** |
| [ALLSPARX-PRIME](https://github.com/Jekylhyde82/ALLSPARX-PRIME) | Private; reported size 0 | **Inspect before disposition** |
| [ALLSPARXPRIME](https://github.com/Jekylhyde82/ALLSPARXPRIME) | Private; reported size 0 | **Inspect before disposition** |
| [ALLSPARX-PRIME-](https://github.com/Jekylhyde82/ALLSPARX-PRIME-) | Public; reported size 0 | **Inspect before disposition** |
| [ALLSPARX.PRIME-](https://github.com/Jekylhyde82/ALLSPARX.PRIME-) | Private; reported size 0 | **Inspect before disposition** |
| [UNIVERSAL-ENGINE.ENGINEER-](https://github.com/Jekylhyde82/UNIVERSAL-ENGINE.ENGINEER-) | Private; reported size 0 | **Inspect before disposition** |

The inventory is limited to repositories returned by the connected GitHub account listing; it is not a claim about every repository that may exist elsewhere.

## Critical source finding: 7282ALLSPARXPRIME

The source README identifies the project as CloudCredits.io, a startup-credit directory built with Astro. The repository metadata identifies it as a fork. It contains a substantial application tree and active integration work. It is not a clean, standalone UNIVERSAL ENGINE / ENGINEER codebase.

Its open pull requests at inspection include:
- [#13 — vendor-neutral multi-provider gateway foundation](https://github.com/Jekylhyde82/7282ALLSPARXPRIME/pull/13) — open, 23 commits, 13 files changed; preserve and review.
- [#14–#19] — additional SYPHON / ALLSPARX work; several are based on other feature branches, so do not flatten or cherry-pick without dependency analysis.
- [#20] — closed draft dependency-remediation preview; retain for history.

**Decision:** Do not copy this entire application into the master root. First assess whether its reusable gateway, evidence, security, provider-routing, and testing components should be extracted into a governed subproject or integrated as bounded modules. Preserve the upstream CloudCredits attribution, licence obligations, fork relationship, and unrelated application code.

## Migration gates

For each candidate source:
1. Inventory branches, tags, commits, open/closed PRs, issues, workflows, releases, and deployment dependencies.
2. Identify upstream ownership, licence obligations, third-party code, secrets, personal data, and generated/binary assets.
3. Map reusable components to master architecture registers.
4. Decide: migrate, extract, retain as subproject, archive, or exclude.
5. Preserve provenance and source commit references.
6. Migrate through a dedicated branch and reviewed PR.
7. Run tests, security checks, and build verification in the target.
8. Record results and unresolved risks before accepting the migration.

## Current limitations

The connected GitHub actions available in this workflow can inspect repositories and create/update files, but do not expose a repository-import operation that transfers complete Git history, all branches, tags, issues, and PR metadata. A full Git-preserving migration therefore requires a Git clone/fetch/push workflow or an equivalent supported GitHub import process. File-by-file copying is not a substitute for history-preserving migration.
