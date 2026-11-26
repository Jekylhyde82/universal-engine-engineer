# Engineer — Personal FOSS Repository

**Status:** Established as a governed FOSS collection and acquisition workspace.  
**Owner:** Jekylhyde82  
**Parent system:** Universal Engine / Engineer  
**Purpose:** Discover, catalogue, preserve, assess, adapt and integrate useful free/open-source software (FOSS) into Engineer without losing upstream identity, provenance, licence obligations or verification evidence.

This directory is Engineer's personal FOSS repository **within the existing Engineer Git repository**. It is not a claim that the upstream projects listed here have already been cloned, mirrored, fully extracted, audited or integrated.

## Repository structure

| Path | Responsibility |
|---|---|
| `catalog/` | Machine-readable source and component catalogue |
| `sources/` | Per-project provenance, licence notes, snapshots and extraction records |
| `assessments/` | Security, quality, compatibility and usefulness assessments |
| `integrations/` | Engineer integration designs, adapters and verification records |
| `policies/` | Intake, licensing, security and contribution rules |
| `reports/` | Discovery, review and acquisition reports |

## Initial source collection

The first collection records the three upstream projects previously identified by STARWIRE:

1. [cloudcredits.io](https://github.com/t3-sh/cloudcredits.io) — source catalogue and programme-discovery implementation.
2. [Free for Open Source](https://github.com/MrZaKaRiA/free-for-open-source) — open-source project benefit discovery and eligibility matching.
3. [Startup Credits](https://github.com/sourcey/startup-credits) — structured startup-credit programme and offer data.

See [SOURCE REGISTER](SOURCES.md) for provenance and current review status.

## Intrinsic AFI OM + EVO PRIME integration\n\nThis FOSS workspace is not a detached collection. It is governed by the intrinsic AFI OM + EVO PRIME architecture of Engineer:\n\n- **AFI OM** fuses source intelligence, technical findings, provenance, licensing facts, dependency relationships and capability knowledge.\n- **EVO PRIME** identifies capability gaps, designs approved adaptations, engineers tests, evaluates outcomes and drives governed improvement.\n- Both responsibilities operate across discovery, capture, assessment, approval, integration, verification and lifecycle management.\n- Their authority remains bounded by licence, security, permission and evidence gates.\n\nThe complete system-wide contract is documented in [AFI OM + EVO PRIME intrinsic integration](../docs/AFI-OM-EVO-PRIME-INTRINSIC-INTEGRATION.md).\n\n## Intake lifecycle

Every candidate follows explicit gates:

**Discovered → Source captured → Provenance recorded → Licence reviewed → Security reviewed → Technical assessment → Approved → Integrated → Outcome verified**

Discovery is not approval. A repository being public or labelled open source does not automatically make every file, dataset, dependency, brand asset or external service reusable under the same terms.

## Operating principles

- Preserve upstream project identity and original attribution.
- Record exact source URL, revision/commit, retrieval date and applicable licence for every imported snapshot.
- Keep source snapshots distinct from Engineer-authored adaptations.
- Never silently overwrite upstream material with local modifications.
- Review dependencies, install scripts, workflows, build steps and generated artefacts before execution.
- Do not import secrets, credentials, personal data or unlicensed assets.
- Require explicit approval before spending money, accepting external terms, creating third-party accounts, deploying, or making external changes.
- Treat test results and security claims as unverified until independently reproduced and recorded.

## Current state

The repository structure and initial source register are being established on a dedicated feature branch. The three source projects are **catalogued, not yet fully mirrored or integrated**. File-level extraction, immutable source snapshots, licence verification, security review and capability tests remain open work.

## Next work

1. Capture upstream default branches, commit SHAs, complete file trees and licence files.
2. Create immutable source manifests and source-specific intake records.
3. Review code, data and dependencies separately against their actual licences.
4. Identify reusable capabilities and dependencies.
5. Build isolated adapters and tests before integrating approved components into Engineer.
