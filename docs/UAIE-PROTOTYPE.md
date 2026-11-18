# UAIE Working Prototype v0.1

**U.A.I.E. — Universal Assimilation and Integration Engine**  
Foundational architecture: NINEFOLD INTRINSIC  
Governing invariant: INTRINSIC BY DESIGN

## What this prototype does now

UAIE v0.1 is a working, local-first acquisition and assimilation engine. It can:

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
from universal_engine.uaie import UniversalAssimilationEngine

uaie = UniversalAssimilationEngine("uaie.sqlite3")
record = uaie.ingest_text(
    "A new API capability with security controls and tests",
    source="notes/candidate.md",
)
print(record)
```

## Honest capability boundary

This is a real executable prototype, not yet the full universal system. The first vertical slice is local file/object acquisition, persistence, provenance, basic understanding/classification, value triage, search and governed lifecycle.

Not yet implemented: broad web crawling, authenticated connector integrations, archive/document format extraction, OCR, audio/video understanding, source-code dependency analysis, semantic embeddings, autonomous tool acquisition, sandboxed capability execution, distributed storage, identity/authentication, multi-user authorization, external audit anchoring or production operations.

The value score is an explainable keyword heuristic, not an authoritative measure of usefulness or intelligence. Binary content is preserved but not semantically decoded. Acquired content is **never executed**. No network access or external system mutation is performed by this prototype.

## Safety model

- Intake is separate from approval, integration and execution.
- No acquired code, scripts, macros, models or binaries are run.
- File size is bounded (10 MiB by default).
- Symlinks are not followed during directory intake.
- Duplicate bytes map to one content record.
- Integration requires an explicit approval transition.
- The prototype does not claim that a stored item is safe, compatible, licensed or useful merely because it was acquired.

## Intrinsic architecture relationship

UAIE is a foundational capability of NINEFOLD INTRINSIC under the INTRINSIC BY DESIGN invariant. It is one integrated capability spanning discovery, acquisition, assimilation, comprehension, decomposition, evaluation, governed integration, verification and evolution. These responsibilities do not imply that every connector or autonomous process is already implemented.

UPN (Universal Private Network) is the complementary, intrinsic networking capability. It is designed to support both explicitly authorized connections to existing private networks and project-owned private infrastructure. UAIE may discover and assimilate networking technologies and their documentation; UPN policy and the Engine lifecycle govern whether a network profile may be registered or used. Acquisition never authorizes execution or connection.

The first UPN control-plane increment provides validated profile/peer contracts, private-route scope checks, deny-by-default policy evaluation and lifecycle-gated registration. It does not establish VPN tunnels, configure infrastructure, generate keys, open sockets or add Android network permissions. A profile being accepted by the library is not proof of a live or secure network.

## Next engineering increments

1. Add connector interface contracts and a permission-scoped web/repository acquisition adapter.
2. Add safe parsers for PDF, DOCX, XLSX, archives and source trees with decompression/resource limits.
3. Add semantic indexing and retrieval while preserving source citations.
4. Add compatibility/dependency analysis and isolated evaluation sandboxes.
5. Connect approved capabilities to the existing provider registry and policy-enforced runtime.
6. Add authentication, distributed authorization, audit anchoring, backup/restore and independent security review before production.

**PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**

## Next engineering increments

1. Add connector interface contracts and a permission-scoped web/repository acquisition adapter.
2. Add safe parsers for PDF, DOCX, XLSX, archives and source trees with decompression/resource limits.
3. Add semantic indexing and retrieval while preserving source citations.
4. Add compatibility/dependency analysis and isolated evaluation sandboxes.
5. Connect approved capabilities to the existing provider registry and policy-enforced runtime.
6. Add authentication, distributed authorization, audit anchoring, backup/restore and independent security review before production.

**PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**
