# Promptfoo local inference smoke test

This harness checks basic endpoint wiring and exact prompt behaviour against a running OpenAI-compatible llama.cpp server.

## Requirements
- Node.js 24 (see repository .nvmrc; Promptfoo currently documents Node.js >=22.22).
- A running llama.cpp server exposing /v1/chat/completions.
- The served model must accept the model name configured in the YAML or ignore it according to the server's model configuration.

## Run
Set the OpenAI-compatible base URL. For local development:

```bash
export OPENAI_BASE_URL=http://127.0.0.1:8080/v1
./scripts/run-promptfoo-eval.sh
```

If the server requires authentication, also set OPENAI_API_KEY in the shell or secret manager. Do not commit secrets or .env files.

## Scope
This is a deterministic wiring smoke test, not a comprehensive quality benchmark or red-team suite. Expand it with reviewed datasets, regression assertions, adversarial probes and thresholds before using it as a release gate.
