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
