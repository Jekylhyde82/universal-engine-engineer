# UAIE Working Prototype v0.1

**U.A.I.E. — Universal Acquisition and Integration Engine**  
Foundational architecture: NINEFOLD INTRINSIC  
Governing invariant: INTRINSIC BY DESIGN

## What this prototype does now

UAIE v0.1 is a working, local-first acquisition and integration engine. It can:

- Ingest individual files or recursively ingest a directory.
- Accept text and JSON-compatible structured objects through its Python API.
- Preserve original bytes, SHA-256 content identity, source provenance, media type and timestamps in SQLite.
- Deduplicate identical content.
- Classify common source, documentation, structured-data and tabular formats.
- Retain binary/unparsed files as acquired artifacts without pretending to understand their contents.
- Run transparent keyword-based value triage and searchable discovery.
- Enforce a lifecycle: discovered/assimilated → approved → integrated, or rejected.
- Persist its catalogue across restarts.
- Operate using Python's standard library only.
- Optionally inventory models from a local LM Studio instance through a separate, read-only adapter (see `docs/LM-STUDIO-INTEGRATION.md`).

## Quick start

Python 3.11+:

```bash
python -m pip install .
python -m universal_engine.uaie --db ./uaie.sqlite3 ingest ./inbox
python -m universal_engine.uaie --db ./uaie.sqlite3 search security
python -m universal_engine.uaie --db ./uaie.sqlite3 show uaie_<record-id>
python -m unittest discover -s tests -v
```

The default database is `uaie.sqlite3` in the current directory. Use `--db` to select another location.

## Python API

```python
from universal_engine.uaie import UniversalAcquisitionEngine

uaie = UniversalAcquisitionEngine("uaie.sqlite3")
record = uaie.ingest_text(
    "A new API capability with security controls and tests",
    source="notes/candidate.md",
)
print(record)
```

## Honest capability boundary

This is a real executable prototype, not yet the full universal system. The first vertical slice is local file/object acquisition, persistence, provenance, basic understanding/classification, value triage, search and governed lifecycle.

Not yet implemented: broad web crawling, authenticated connector integrations, archive/document format extraction, OCR, audio/video understanding, source-code dependency analysis, semantic embeddings, autonomous tool acquisition, sandboxed capability execution, distributed storage, identity/authentication, multi-user authorization, external audit anchoring or production operations.

The value score is an explainable keyword heuristic, not an authoritative measure of usefulness or intelligence. Binary content is preserved but not semantically decoded. Acquired content is **never executed**. The core intake engine performs no network access or external system mutation. The optional LM Studio adapter makes one bounded, read-only request to a loopback LM Studio API; it does not download models or mutate LM Studio.

## Safety model

- Intake is separate from approval, integration and execution.
- No acquired code, scripts, macros, models or binaries are run.
- File size is bounded (10 MiB by default).
- Symlinks are not followed during directory intake.
- Duplicate bytes map to one content record.
- Integration requires an explicit approval transition.
- The prototype does not claim that a stored item is safe, compatible, licensed or useful merely because it was acquired.

## Next engineering increments

1. Add permission-scoped web/repository and public model-catalog discovery adapters; LM Studio local model inventory is implemented separately.
2. Add safe parsers for PDF, DOCX, XLSX, archives and source trees with decompression/resource limits.
3. Add semantic indexing and retrieval while preserving source citations.
4. Add compatibility/dependency analysis and isolated evaluation sandboxes.
5. Connect approved capabilities to the existing provider registry and policy-enforced runtime.
6. Add authentication, distributed authorization, audit anchoring, backup/restore and independent security review before production.

**PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**


## Universal Capability Acquisition Register — required portfolio fields

The register is the governed portfolio record for candidate capabilities. Each assessed candidate must preserve:
- **Original Idea Value** — the original concept, wording or contribution and its attribution; never silently overwrite it with an AI-generated reformulation.
- **Potential market value** — an evidence-labelled estimate or explicitly marked unknown.
- **Revenue models** — one or more candidate models, or an explicit not-assessed status.
- **Development timeline** — estimate, assumptions and confidence, or unknown.
- **Risk assessment** — identified risks, severity, mitigations and unresolved issues.
- **Evidence and verification status** — source references, test evidence and current verification state.

Missing evidence must remain missing/unknown rather than being invented. The current prototype's heuristic value score is triage only and must not be substituted for these fields or treated as a commercial valuation.
