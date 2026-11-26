# FOSS Intake and Integration Policy

## 1. Scope

Applies to all third-party repositories, packages, datasets, models, tools, scripts, workflows, documentation, images, fonts and other artefacts considered for Engineer.

## 2. Source capture

Before assessing or importing a source:

1. Record its canonical upstream location.
2. Record the retrieval date/time and exact revision/commit.
3. Capture the complete file tree and relevant licence/notice files.
4. Hash captured files and retain an immutable source manifest.
5. Record submodules, large-file pointers, generated files and external downloads separately.
6. Preserve upstream history where practical; never present a local snapshot as an upstream-authored release.

## 3. Licence review

- Identify the licence for the repository and, where relevant, individual files and datasets.
- Check attribution, notice-retention, modification, redistribution, patent, trademark and share-alike requirements.
- Do not infer that all assets or data share the repository's code licence.
- If licensing is missing, ambiguous, conflicting or incompatible, quarantine the material pending review.
- Do not remove copyright notices or upstream attribution.

## 4. Security and quality review

Before executing or integrating code, inspect:

- Install, build, release and post-install scripts
- CI/CD workflows and action references
- Dependency manifests and lockfiles
- Network access, telemetry and update mechanisms
- Credential, token and environment-variable handling
- File-system, process and privilege requirements
- Known vulnerabilities and abandoned dependencies
- Data collection, privacy and external service dependencies

Do not execute unreviewed scripts or workflows. Prefer isolated, least-privilege, reproducible test environments.

## 5. Approval gates

Human approval is required before:
- Creating external accounts or accepting third-party terms
- Spending money or consuming paid credits
- Using credentials or private account data
- Publishing, deploying or modifying production systems
- Sending data to external services
- Making external changes on the user's behalf

Local read-only inspection and documentation may proceed without those actions.

## 6. Integration

- Keep upstream snapshots separate from Engineer adapters and modifications.
- Prefer small, replaceable adapters over tightly coupled imports.
- Pin dependencies and source revisions.
- Document why a capability is useful, what it costs to maintain and how it can be removed.
- Add tests for expected behaviour, failure modes, security boundaries and provenance.
- Require independent verification; a component must not be its own sole evaluator.

## 7. Status vocabulary

Use only evidence-backed states:

- IDENTIFIED
- CAPTURED
- PROVENANCE_RECORDED
- LICENCE_REVIEWED
- SECURITY_REVIEWED
- ASSESSED
- APPROVED
- INTEGRATED
- VERIFIED
- REJECTED
- RETIRED

A state transition must include evidence. Never mark a source INTEGRATED or VERIFIED merely because it appears in a catalogue.
