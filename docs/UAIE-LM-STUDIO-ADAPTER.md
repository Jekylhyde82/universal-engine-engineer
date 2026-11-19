# UAIE PRIME — LM Studio Model Catalog Fusion

**Canonical engine:** Universal Acquisition and Integration Engine (UAIE PRIME)  
**Parent architecture:** NINEFOLD INTRINSIC  
**Specialist intelligence and fusion:** AFI PRIME  
**Primary acquisition target:** [LM Studio Model Catalog](https://lmstudio.ai/models)  
**Status:** Implemented adapters and automated tests in this branch; exact-head CI, live smoke testing and independent verification pending.

## Correct source distinction

LM Studio exposes two different resources:

1. **Public Model Catalog** at `https://lmstudio.ai/models`: discoverable model families, descriptions, model-page details, capability tags, local/cloud availability, downloads, update information, memory notes, artifact links and licence statements where published.
2. **Local LM Studio inventory** at `GET /api/v1/models`: models already downloaded or otherwise available on a specific LM Studio installation, with runtime-oriented metadata such as type, publisher, key, quantization, size, context, capabilities and loaded instances.

These are separate sources and are not interchangeable. The public website currently renders a searchable/filterable catalogue with individual model detail pages. LM Studio's native v1 REST API is documented for local model inventory and model management; it is not documented as a full public catalogue-search API.

## Implemented public-catalog adapter

`universal_engine.lmstudio_catalog`:

- Starts from the official public catalogue page.
- Discovers same-origin model detail links.
- Fetches detail pages only from HTTPS `lmstudio.ai`.
- Rejects credentials, query strings, fragments, invalid ports and cross-origin redirects.
- Enforces timeouts, response-size limits and a maximum model count.
- Extracts page title, summary, declared capability tags, local/cloud availability, parameter-size strings, context and memory notes, download/star counts, update text, licence text and approved artifact links.
- Fails closed when model links disappear or the page structure no longer yields catalogue entries.
- Stores each acquired entry in UAIE with its original model-page URL as provenance.

This is a bounded HTML adapter, not an official LM Studio public API. The website markup can change; parser fixtures and a live smoke test are required before operational promotion.

## AFI PRIME fusion

For each validated catalog entry, `AFIPrimeFusionAdapter` extracts an AFI capability profile and persists it as a separate UAIE record under an `afi-prime://` provenance identifier.

AFI preserves the model key and reported facts, and explicitly labels them as publisher/catalog metadata. Catalog capability tags are recorded as declarations, not as independently proven capabilities.

Every generated profile remains:
- `METADATA_ONLY_NOT_BENCHMARKED`
- `performance_verified = false`
- `integration_approved = false`

AFI is therefore performing a real, testable metadata-to-capability-profile fusion. This does not falsely claim that a complete autonomous AFI reasoning runtime, benchmark suite or model-selection policy has already been deployed.

## Local inventory adapter

`universal_engine.lmstudio` separately reads the native v1 local endpoint `GET /api/v1/models`. It is read-only and loopback-only by default. It never downloads weights, loads/unloads models, executes inference or changes LM Studio configuration.

Optional bearer-token authentication is read from the process environment and is never written to the register.

## Run

Public catalog discovery:

```bash
python -m universal_engine.lmstudio_catalog
```

Local inventory:

```bash
LM_API_TOKEN='your-token' python -m universal_engine.lmstudio
```

Persist public catalogue entries and AFI profiles from Python:

```python
from universal_engine.lmstudio_catalog import assimilate_public_catalog
from universal_engine.uaie import UniversalAcquisitionIntegrationEngine

uaie = UniversalAcquisitionIntegrationEngine("uaie.sqlite3")
catalog_records, afi_profile_records = assimilate_public_catalog(uaie)
```

## Governance and lifecycle

Discovery and assimilation do not authorise acquisition of model weights, execution, deployment or integration into the Universal Engine. Each candidate must separately undergo provenance, licence, security, resource/hardware compatibility, independent benchmark and value assessment. Human approval and the existing UAIE lifecycle remain mandatory.

Model cards, capability tags, download counts and vendor-reported benchmarks are untrusted third-party claims until independently verified. Do not infer licence permissions from the fact that a model is listed in the catalog.

## Verification gates

- Unit tests use deterministic HTML/JSON fixtures and do not require network access or model downloads.
- Exact-head GitHub Actions must pass.
- Live smoke test must compare parser output with the live public catalogue and detail pages.
- Local API smoke test requires a reachable LM Studio instance and user-authorised token if authentication is enabled.
- Production readiness additionally requires parser drift monitoring, retries/backoff, rate limiting, catalogue snapshot/versioning, licence evidence capture, security review, hardware suitability analysis, independent model benchmarks, audit/retention policy, and an operational deployment plan.

**Evidence rule:** specified, implemented, CI-tested, live-smoke-tested, independently verified and production-operational are distinct states.
