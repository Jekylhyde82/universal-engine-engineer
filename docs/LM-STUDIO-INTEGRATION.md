# UAIE × LM Studio Integration

**Status:** Implemented read-only adapter; production deployment validation pending.

UAIE includes LM Studio as a model-intelligence acquisition source. The adapter
uses LM Studio's native REST API v1, specifically `GET /api/v1/models`, to
inventory models available on a configured local LM Studio instance.

## Scope and safety boundary

The adapter currently:
- Retrieves model metadata (type, publisher, key, display name, architecture,
  quantization, size, parameter label, context limit and loaded-instance count).
- Validates response shape and required fields.
- Stores each model's source metadata in UAIE's SQLite acquisition register,
  retaining UAIE content hashing and provenance.
- Supports an optional API token through an environment variable.
- Restricts connections to loopback HTTP by default.
- Uses bounded timeouts and a 2 MiB response limit.

It does **not** download model weights, load/unload models, run inference, alter
LM Studio settings, or access a remote model server. Metadata inventory is not
proof that a model is suitable, safe, licensed for a use, or performant.

## Important distinction: local inventory vs public catalog

`GET /api/v1/models` lists models available on that LM Studio instance. It is
not a complete search of every model in the public LM Studio/Hugging Face
catalog. Public-catalog discovery and model acquisition require a separate,
explicitly permissioned adapter and should remain distinct from local inventory.
Model download/load actions are intentionally not implemented in this increment.

## Usage

Start the LM Studio server locally (default port 1234), then:

```bash
PYTHONPATH=src python -m universal_engine.lmstudio list
PYTHONPATH=src python -m universal_engine.lmstudio --db ./uaie.sqlite3 assimilate
```

If authentication is enabled, place the token in `LM_API_TOKEN`; do not put
secrets in command-line arguments or source control. Override the loopback
endpoint with `LM_STUDIO_BASE_URL` only for a supported loopback origin.

## Production gates still required

- Test against supported LM Studio release versions and real response fixtures.
- Add a separate public-catalog discovery adapter with source attribution,
  pagination, rate limits and licence metadata.
- Add explicit approval and cost/resource checks before any model download.
- Verify model checksums/signatures where publishers provide them.
- Evaluate model safety, task performance, hardware fit and licence terms before
  approval for integration.
- Complete independent security review and operational monitoring.

**No model is automatically trusted or integrated because LM Studio lists it.**
