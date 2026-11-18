#!/usr/bin/env sh
set -eu

if [ -z "${OPENAI_BASE_URL:-}" ]; then
  echo "Set OPENAI_BASE_URL to the OpenAI-compatible /v1 endpoint." >&2
  exit 2
fi

node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (major < 22 || (major === 22 && minor < 22)) { console.error("Promptfoo requires Node.js >=22.22.0; use Node.js 24."); process.exit(2); }'

exec npx --yes promptfoo@0.125.1 eval --config evaluation/promptfoo/promptfooconfig.yaml "$@"
