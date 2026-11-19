# UAIE PRIME — LM Studio Model Inventory Adapter

**Canonical name:** Universal Acquisition and Integration Engine (UAIE PRIME)  
**Parent architecture:** NINEFOLD INTRINSIC  
**Specialist fusion:** AFI PRIME  
**Increment:** LM Studio local model inventory adapter v0.1  
**Status:** Implemented in this branch; exact-head CI and independent verification pending.

## Purpose

Add LM Studio as a governed model-discovery and metadata-acquisition source inside UAIE PRIME. The first adapter reads the local LM Studio native REST API v1 model inventory at `GET /api/v1/models`.

This endpoint reports models available on the user's LM Studio installation, including model type, publisher, canonical key, architecture, quantization, size, parameter count, context limits, format, capabilities, variants and loaded instances. It is an inventory of locally available models, not a complete mirror of every model in the public LM Studio Hub.

## Implemented boundary

- Read-only HTTP GET to an explicitly configured loopback endpoint.
- Defaults to `http://127.0.0.1:1234`.
- Optional bearer token is supplied at runtime; it is never persisted in model records.
- Enforces a request timeout, bounded response size, model-count limit and response-shape validation.
- Rejects non-loopback hosts, URL credentials, query strings, fragments and unexpected base paths.
- Rejects malformed records and duplicate model keys.
- Normalizes native v1 model metadata into immutable records.
- Provides an assimilation function that stores normalized metadata through the existing UAIE SQLite/provenance pipeline.
- Does not download weights, load/unload models, execute inference, install software, change LM Studio settings or modify remote services.

## AFI PRIME relationship

AFI PRIME is the specialist intelligence and fusion capability within NINEFOLD INTRINSIC. This adapter supplies it with validated model inventory records through UAIE's governed acquisition path. This increment does not invent or claim an AFI runtime API. Model scoring, comparative evaluation, compatibility decisions and fusion approval remain separate governed work until their interfaces and independent evidence are implemented.

## Lifecycle

Discovery and metadata assimilation do not approve a model for use. Records must pass the existing UAIE lifecycle and subsequent capability, resource, licence, security and independent performance evaluations before integration. Model metadata is publisher-reported evidence, not proof of model performance or suitability.

## Run

Start LM Studio's local server and enable API authentication if desired. Then:

```bash
LM_API_TOKEN='your-token' python -m universal_engine.lmstudio
```

Optional endpoint override (loopback only):

```bash
LM_STUDIO_BASE_URL='http://localhost:1234' python -m universal_engine.lmstudio
```

To persist results from Python:

```python
from universal_engine.lmstudio import assimilate_catalog
from universal_engine.uaie import UniversalAssimilationEngine

engine = UniversalAssimilationEngine("uaie.sqlite3")
records = assimilate_catalog(engine)
```

## Verification required

- Unit tests use mocked HTTP responses; they do not require LM Studio or download models.
- Exact-head GitHub Actions must pass before this increment is marked CI-tested.
- A live local smoke test requires a reachable LM Studio installation and user-authorized endpoint/token.
- Production readiness additionally requires AFI integration contract, multi-source model discovery, licensing/provenance checks, hardware/resource estimation, independent benchmarks, audit/retention policy, packaging and operational security review.

**Evidence rule:** specified, implemented, CI-tested, live-smoke-tested, independently verified and production-operational are distinct states.
