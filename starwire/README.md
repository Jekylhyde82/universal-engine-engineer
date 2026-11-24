# STARWIRE — Ninefold Intrinsic Discovery

STARWIRE coordinates nine autonomous crawler capabilities, nine structured importer capabilities, and SYPHON's nine extraction capabilities. This repository contribution is an initial, standard-library Python reference implementation—not a production deployment.

## Capability map

**Crawlers:** universal web, repository, technology, opportunity, AI/model, infrastructure, research, source-discovery, and change-monitoring scouts.

**Importers:** API payload, repository metadata, JSON, XML/RSS/Atom, CSV, research metadata, opportunity listings, database/catalogue exports, and universal structured-data adapters.

**SYPHON extraction:** source acquisition, web extraction, document text extraction, structured extraction, semantic term extraction, repository metadata extraction, multimedia metadata, provenance validation, and adaptive format classification.

The initial code implements safe primitives and capability registries. Provider-specific connectors remain disabled until their official endpoints, terms, and permissions are reviewed.

## Quick start

Python 3.11+; no third-party runtime dependencies.

```bash
python -m unittest discover -s starwire/tests -v
python -m starwire.cli import-json examples/opportunity.json --db starwire.db
python -m starwire.cli report --db starwire.db
```

## Safety model

- Network crawling is opt-in and requires explicit HTTPS host allowlisting.
- Rejects credentials, non-HTTP(S), localhost/private/link-local/reserved IP literals and resolved addresses.
- Redirects are disabled; each destination must be independently approved.
- Enforces response byte limits, timeouts, per-host delay, page limits and depth limits.
- Does not bypass authentication, paywalls, robots rules, access controls or licensing.
- Never executes downloaded content, scripts, macros or repository code.
- Importers accept bounded local input; they do not fetch arbitrary URLs.
- Every observation retains source, collection time and SHA-256 digest.
- Discovery records are candidates only. No automatic approval, acquisition, download or AFI/UAIE decision is performed.

**Important limitation:** Python's standard-library DNS validation is not a complete defence against DNS rebinding or hostile network environments. Run network collection in an isolated egress-restricted worker with DNS pinning, outbound firewall policy and independent security review before production.

## Governance hand-off

STARWIRE produces evidence-bearing candidate records for AFI PRIME evaluation. UAIE PRIME retains governance and verification authority. The Universal Capability Acquisition Register records only governed outcomes. Original Idea Value must be preserved by the register for user-originated ideas; STARWIRE must never invent a valuation.

## Status

This is a draft engineering foundation. Production readiness requires provider-specific legal/terms review, isolated deployment, secrets management, observability, backup/restore, independent security review, integration tests against approved sources, and successful CI.
