# Repository Capability Scout v0.1

A small browser-based repository discovery prototype for the Universal Engine / Engineer capability-acquisition workflow.

## What it does

- Searches GitHub public repositories across AI agents, coding agents, LLMs, local inference, tools and MCP, memory/RAG, orchestration, vision/computer use, evaluation, security, robotics, offline and edge AI.
- Displays repository identity, description, language, stars, forks, licence metadata, archive state and last push.
- Saves selected candidates to browser-local storage.
- Records intended capability, evidence notes, risks and a provisional disposition.
- Imports and exports candidate records as JSON.

## Run it

Open index.html in a modern browser. No build step, package installation, API key or backend is required. Internet access is needed for GitHub search.

## Safety and evidence boundaries

This is discovery and triage only. It does not clone, download, install, execute or modify repositories. It does not verify licences, security, maintenance quality or capability claims. Stars are context only, not a quality score. GitHub unauthenticated search has rate limits and may return incomplete results. Candidate records remain in browser local storage until exported.

All evaluation gates begin NOT_ASSESSED. A repository search result is not an integration approval. Follow UCA-REG-001 and UCEE-SPEC-001 before importing code, installing dependencies, granting credentials or changing production systems.

## Gate alignment

G0 source identity; G1 licence and provenance; G2 maintenance and compatibility; G3 security and governance; G4 resource and deployment; G5 proof of capability; G6 integration approval; G7 operational verification.

## Known limitations

- GitHub is the only discovery provider.
- Search is metadata-based and can miss relevant projects.
- README, source tree, releases, advisories, dependency manifests and commit-pinned licence evidence are not automatically inspected.
- Local browser storage is not synchronised across devices.
- No autonomous agent or code execution is involved.

## Next increments

1. Inspect selected repositories: README, releases, licence files, dependency manifests and pinned commit SHA.
2. Add provider-neutral GitLab and Codeberg discovery adapters.
3. Add a server-side scheduled discovery queue with deduplication and change detection.
4. Add isolated proof-of-capability runners only after policy and sandbox enforcement are independently established.


## v0.2 hardening in review

- Imported records are validated as a complete batch; invalid imports are rejected without partial writes.
- Repository links are restricted to canonical HTTPS `github.com/owner/repository` URLs.
- Imports are limited to 2 MB and 500 records; browser register storage is limited to 500 records.
- Existing browser-stored records are revalidated when loaded.
- A restrictive Content Security Policy allows outbound connections only to the GitHub API.
- The candidate JSON Schema rejects unknown properties and constrains disposition and evaluation-gate states.
- Static smoke tests compile the embedded script and check key security invariants in CI. These are not browser end-to-end tests.

## Remaining production blockers

This remains a client-side discovery tool. It has no authenticated provider adapter, server-side durable database, repository-content inspection service, licence analysis, dependency/advisory scanner, sandboxed runner, identity/approval service, audit log, monitoring, backup/restore service or independent security review. Do not use it to execute or integrate third-party code. Production approval remains blocked until these controls are implemented and independently tested.


### CI evidence

GitHub Actions run `44459781958` completed successfully for PR head `a86f72f28e3d918162dca9731676597c2532ca2a` (merge test commit `b900f8d`): **5 tests passed, 0 failed, 0 skipped**. The workflow uses commit-pinned checkout and setup-node actions. The tests compile the embedded script and check selected security invariants. They do not replace browser end-to-end testing, penetration testing or independent security review.