# Qdrant Vector Store Adapter

The second real provider adapter uses Qdrant's REST API with standard-library HTTP primitives.

## Supported operations
- Upsert up to 1,000 points per request using PUT /collections/{collection}/points?wait=true.
- Query vectors using POST /collections/{collection}/points/query.
- Requires an existing collection; collection creation and dimension management remain operator responsibilities.

## Security
- Plain HTTP is loopback-only.
- Remote endpoints require HTTPS, an API key and explicit allow_remote=True.
- API keys are sent in the Qdrant api-key header.
- Requests require an allow decision and respect request deadlines.
- Response bodies are capped at 1 MiB.
- Errors are sanitized; upstream response bodies are not returned.

## Limitations
- Supports dense single-vector points only.
- No named/multi-vector, sparse, hybrid, payload filter, scroll, delete, collection administration or batch streaming.
- No remote DNS/IP allowlist, certificate pinning, retries, circuit breaker, metrics, or health checks.
- Qdrant's own documentation warns that local defaults may be unauthenticated and unencrypted; do not expose a default instance to an untrusted network.

## Test method
Tests use an ephemeral local HTTP server and do not require a Qdrant installation.
