# FOSS Source Register

This register records the three upstream repositories identified in the STARWIRE source-fusion work. Repository links are canonical upstream references; no claim is made that their current contents have been fully captured or reviewed.

| Source ID | Upstream project | Repository | Initial licence note | Intake state |
|---|---|---|---|---|
| FOSS-001 | cloudcredits.io | https://github.com/t3-sh/cloudcredits.io | Reported MIT; verify current root and file-level notices | Identified; full capture pending |
| FOSS-002 | Free for Open Source | https://github.com/MrZaKaRiA/free-for-open-source | Reported MIT; verify current root and file-level notices | Identified; full capture pending |
| FOSS-003 | Startup Credits | https://github.com/sourcey/startup-credits | Repository code/docs reported MIT; programme data reported CC BY 4.0; verify current terms and data boundaries | Identified; full capture pending |

## FOSS-001 — cloudcredits.io

- Upstream: https://github.com/t3-sh/cloudcredits.io
- Discovery focus: provider and programme catalogues, benefit tiers, eligibility, application steps, UI patterns and extraction utilities.
- STARWIRE capability themes: source discovery, content extraction, programme normalization and catalogue presentation.
- Required next evidence: default branch, exact commit SHA, full tree, LICENSE, NOTICE files, dependency manifests, asset licences and workflow review.

## FOSS-002 — Free for Open Source

- Upstream: https://github.com/MrZaKaRiA/free-for-open-source
- Discovery focus: open-source project benefit catalogue, project fingerprinting, matching rules, eligibility logic and export/site generation.
- STARWIRE capability themes: project-to-offer matching, eligibility assessment, duplicate detection and structured export.
- Required next evidence: default branch, exact commit SHA, full tree, LICENSE, data-source terms, dependency manifests and workflow review.

## FOSS-003 — Startup Credits

- Upstream: https://github.com/sourcey/startup-credits
- Discovery focus: structured startup-credit programmes and offers, provider/entity identifiers, aliases, offer hierarchy, eligibility and benefit qualifiers.
- STARWIRE capability themes: canonical entity modelling, programme/offer relationships, economic qualifiers, lifecycle metadata and evidence/revision tracking.
- Licence boundary: code, documentation, structured factual data and third-party assets may have different terms. The reported MIT and CC BY 4.0 terms must be checked against the exact upstream files and current licence notices before reuse.
- Required next evidence: default branch, exact commit SHA, full tree, root and data-specific licences, attribution requirements, schema and data provenance.

## Required provenance fields

Every captured source revision must record:

- Source ID and canonical upstream URL
- Retrieval timestamp (UTC)
- Default branch and exact commit SHA
- Licence file path, SPDX identifier where determinable, and licence text hash
- File inventory and per-file content hash
- Upstream attribution and NOTICE requirements
- Data provenance and data-specific terms
- Local modifications and their authorship
- Security/quality assessment references
- Approval decision, approver and date
- Integration destination and verification evidence

## Important distinction

The STARWIRE architecture document previously described the three-source capability fusion. That architecture record is not proof that every upstream file was extracted, copied, tested, merged or deployed. This register deliberately keeps those states separate.
