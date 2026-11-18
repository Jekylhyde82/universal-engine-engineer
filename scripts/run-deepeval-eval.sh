#!/usr/bin/env sh
set -eu

for name in LOCAL_MODEL_NAME LOCAL_MODEL_BASE_URL LOCAL_MODEL_API_KEY; do
  eval "value=\${$name:-}"
  if [ -z "$value" ]; then
    echo "Missing required environment variable: $name" >&2
    exit 2
  fi
done

exec deepeval test run evaluation/deepeval/test_local_rag.py "$@"
