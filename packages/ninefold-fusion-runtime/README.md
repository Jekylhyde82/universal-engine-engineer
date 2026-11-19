# NINEFOLD INTRINSIC — AFI PRIME Nine-Instance Runtime Proof of Capability

**Status: experimental proof of capability; not production-ready.**

This package demonstrates one shared canonical UNIFIED FUSION SYNERGY — AFI PRIME function running as nine separately spawned Node.js processes, one scoped to each UMIC.

## What the prototype demonstrates

- Nine distinct OS process IDs and isolated process memory.
- One shared versioned fusion-function implementation loaded by all nine processes.
- One unique state namespace per instance; state written in one process is not visible in another.
- One append-only JSONL evidence stream per instance, hash-chained and checked on restart. The stream is reopened under the same caller-supplied runtimeId; restart does not silently create a fresh empty ledger.
- Evidence files live under a private runtime subdirectory beneath the caller-supplied evidence root. The caller's parent-directory permissions are not changed; runtime directories use mode 0700 and evidence files mode 0600.
- Child processes receive a minimal environment allowlist; parent secrets, DATABASE_URL values and NODE_OPTIONS are not inherited.
- Instance handles are issued only after an injected actor-to-instance governance check. Cross-instance reads are denied by default. A separate parent-side governance callback must explicitly authorise each cross-instance read; both sides record the decision.
- Process-level fault containment: terminating one instance does not prevent healthy peer processes from operating.
- Fault injection is disabled unless the runtime is created with test mode enabled.

## CI validation

The nine-instance runtime suite passed **8 tests, 0 failures** in policy workflow `44474605496` at code commit `887e15bb85bd33f99e5c2f765aea17323e8b6e99`. The same workflow also passed the 132-test V.I.S.I.O.N./D.D. suite, registry validation, JavaScript syntax checks and real Chromium integration setup. CodeQL workflow `44474605505` completed successfully on that code commit. Later commits changed documentation only; this package source is unchanged. CodeQL success does not establish that the alert inventory is empty or reviewed.

## What it does not demonstrate

- This is a deterministic orchestration/state-boundary harness, **not** an intelligent AFI PRIME reasoning engine or the full NINEFOLD INTRINSIC runtime.
- Node child processes share the host OS identity and host kernel. This is not a container, VM, seccomp, cgroup or OS security boundary. Production requires a separately hardened process/container boundary and resource/network controls.
- State is process-local and is lost when an instance exits. Per-instance state is bounded to 1,024 keys and 1 MiB total, with a 16 KiB maximum value. Each evidence stream is bounded to 100,000 events or 16 MiB. IPC concurrency is bounded to 64 pending requests per instance. These are application-level bounds, not OS CPU/memory quotas.
- The evidence stream is durable locally, but it is not externally anchored or independently tamper-proof against a privileged host.
- The governance callback is an injected proof interface, not a production identity, authorisation or human-approval service.
- No runtime Master Core/Engine source-to-slot mapping is asserted. The 99 canonical lineage mappings remain pending approved source reconciliation.
- No staging, deployment, monitoring, incident response, penetration test or production approval is included.

## Runtime model

One canonical AFI PRIME function version is loaded into nine child processes:

- UMIC-01 through UMIC-09 each have their own process and in-memory state.
- Each process writes only its own evidence file.
- The parent runtime is the only cross-instance communication broker. It issues instance handles only after the injected actor-to-instance governance check.
- Cross-instance access is deny-by-default and must pass the injected governance decision.
- A failed child is marked FAULTED; it is not silently restarted with empty state.

## Run

Requires Node.js 22 or later.

```sh
npm run check
npm test
```

Use the same stable runtimeId with the same evidenceRoot when reopening an evidence stream after restart. Use a different runtimeId for a separate runtime namespace. Do not run two active runtimes against the same runtimeId concurrently. Tests create temporary evidence directories and remove them after completion.

**Proof discipline:** passing these tests proves only the behaviours exercised by this prototype. It does not prove production isolation or runtime intelligence.
