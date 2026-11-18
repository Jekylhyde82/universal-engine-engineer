# Durable Capability Lifecycle Ledger

The runtime includes a SQLite-backed lifecycle ledger using only the Python standard library.

## Behaviour
- Persists capability state and append-only lifecycle events.
- Applies the same explicit transition graph as the in-memory ledger.
- Uses SQLite transactions with immediate write locking and WAL for file-backed databases.
- Chains event records with SHA-256 hashes; verification checks sequence continuity, prior hashes, state transitions and current capability state.
- Exposes the same state_of lookup consumed by the provider registry.

## Limitations
- This is a single-process/local persistence option, not a distributed consensus or authorization service.
- A database administrator can rewrite the database and recompute the entire hash chain. Production deployments need external hash anchoring or a separately controlled append-only audit sink.
- Database encryption, filesystem permissions, backups, restore testing, retention, migrations and multi-instance coordination are not yet implemented.
- Do not treat a valid hash chain as proof that the original actor identity was authentic.

## Validation
Tests cover restart persistence, legal lifecycle transitions, rollback on invalid transitions, duplicate rejection and tamper detection.
