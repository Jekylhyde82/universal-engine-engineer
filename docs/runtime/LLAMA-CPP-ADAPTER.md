# llama.cpp Inference Adapter

The first real provider adapter targets the llama.cpp OpenAI-compatible chat-completions endpoint.

## Scope
- Uses Python standard-library HTTP primitives; no additional runtime dependency.
- Supports non-streaming text chat completion only.
- Maps the shared ProviderRequest/ProviderResult contract.
- Requires an explicit policy allow decision.
- Limits upstream response bodies to 1 MiB.
- Does not enable built-in tools or MCP servers.

## Endpoint security
- Plain HTTP is accepted only for loopback addresses.
- Remote endpoints require HTTPS, a supplied API key and explicit allow_remote=True.
- Credentials in endpoint URLs are rejected.
- The default timeout is 30 seconds and is capped at 120 seconds.
- The adapter sends an Authorization bearer token only when configured.
- Upstream error bodies and transport details are not returned to callers.

## Known limitations
- This is a first adapter, not a production certification.
- It supports text messages with system/user/assistant roles only; no multimodal, tool-call, streaming, or embeddings support.
- Remote DNS/IP allowlisting, certificate pinning, rate limiting, retry policy, circuit breaking, metrics, and operational health checks remain future work.
- llama.cpp's OpenAI-compatible API is a compatibility subset; the exact target build and model chat template must be tested.
- Do not enable llama.cpp server tools or MCP in a production inference process unless separately threat-modelled and sandboxed.

## Test method
Unit tests use an ephemeral loopback HTTP server; they do not call an external endpoint or require a model download.
