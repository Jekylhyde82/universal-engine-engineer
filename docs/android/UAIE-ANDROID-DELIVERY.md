# UAIE Android Client — Delivery Specification v0.1

**Status:** Native offline-intake alpha implemented; CI build and unit tests verified. Production release gates remain open.  
**Canonical system:** MULTIVERSAL OMNIVELOCITY PRIME — GENIUS ENGINEER PRIME  
**Foundation:** NINEFOLD INTRINSIC  
**Governing invariant:** INTRINSIC BY DESIGN  
**Related work:** UAIE prototype PR #18; runtime foundation PR #16; Android delivery issue #19.

## 1. User outcome

Deliver an installable, downloadable Android application that provides useful UAIE acquisition and catalogue functions on-device, including when the handset has no network connection. The app must be small, resource-bounded, privacy-conscious and usable on the target OPPO A6 / Android 16 / 4 GB RAM class device.

The first deliverable is a signed APK suitable for direct installation after the user enables Android's normal sideload permission. A Play-distribution AAB is a separate later deliverable. A debug APK is not a production release.

## 2. Architecture decision to validate

Use a native Kotlin Android client rather than bundling Python, a model runtime, vector database or autonomous coding agent into the handset.

The Android client is an offline-capable acquisition, review and control terminal. The existing Python UAIE/runtime remains the service-side capability engine. The phone must not be treated as the production host for crawlers, large models, Qdrant or sandboxed agent execution without measured evidence.

### On-device responsibilities

- Import user-selected files through Android Storage Access Framework and Android Sharesheet.
- Record source URI (where available), display name, MIME type, byte size, SHA-256, acquisition timestamp and local provenance.
- Apply configurable size and storage quotas; stream hashing and copying rather than loading arbitrary files entirely into memory.
- Preserve original bytes in app-private storage; do not execute imported content.
- Maintain a durable local catalogue and searchable metadata.
- Queue explicitly selected records for synchronization; retain a clear pending/synced/failed state.
- Continue local intake and catalogue search offline.
- Provide visible controls for pause/resume, retry, cancellation, export and deletion.

### Service-side responsibilities

- Authenticated identity and authorization.
- Permission-scoped network/repository/API acquisition.
- Rich parsing, code/dependency analysis, semantic indexing and capability evaluation.
- Approval-gated integration into the runtime.
- Central audit, quotas, policy enforcement, backups and operations.

The client must not bypass service-side policy. Local acquisition never means approval, integration or execution.

## 3. Security and privacy requirements

- No embedded API keys, credentials, signing keys or privileged tokens.
- Android Keystore-backed protection for locally stored session material.
- TLS-only remote API transport; reject cleartext remote endpoints.
- Least-privilege permissions; do not request broad storage access when the system document picker suffices.
- Treat imported files, MIME types, filenames, metadata and server responses as untrusted.
- Never execute imported APKs, scripts, macros, binaries, models or code.
- Bounded file size, storage, parsing time, concurrency, memory and network use.
- Redact secrets and personal data from logs; avoid logging file contents.
- Explicit user consent for synchronization and transparent endpoint/account configuration.
- Revocation and logout must invalidate local session material and prevent further synchronization.
- Define retention, export, deletion, backup and uninstall behaviour before release.

## 4. Offline and synchronization contract

- All core local catalogue functions remain available offline.
- Imports are durable before the UI reports success.
- Sync is resumable, idempotent and safe after process death or network loss.
- Server acknowledgements are bound to content hashes and record IDs.
- Failed or partial transfers remain queued with actionable status; never silently discard user data.
- Sync uses explicit configured service endpoints and scopes.
- No background network transfer before the user has configured and authorized it.

## 5. Build and release

- Pin Android Gradle Plugin, Gradle wrapper, Kotlin plugin and all library versions.
- Use a least-privilege GitHub Actions workflow with immutable action SHAs and no persisted checkout credentials.
- Build debug/test APKs on pull requests and release candidates from exact commit SHAs.
- Produce checksum, dependency/SBOM and build provenance records.
- Keep production signing material outside the repository and outside logs; use a protected signing process.
- Verify package ID, version, min/target SDK, manifest permissions, signature and checksum.
- Publish a downloadable production APK only after security, privacy, device, independent verification and explicit release approval.

## 6. Required test matrix

### Automated
- Unit tests for hashing, metadata, catalogue state and queue transitions.
- Instrumentation tests for document picker, share sheet, persistence and lifecycle.
- API contract tests for authentication, authorization, idempotency, retries and revocation.
- Hostile input tests: oversized files, malformed MIME, unusual filenames, truncated files, duplicate content and binary payloads.
- Resilience tests: offline/online transitions, interrupted transfer, process death, duplicate retry, server timeout, revoked token, storage exhaustion and cancellation.
- Static analysis, dependency vulnerability and licence review, secret scanning and manifest permission checks.

### Device acceptance
Test on an emulator and a physical OPPO A6 / Android 16 class device:
- Install, launch, upgrade and uninstall.
- Import via picker and share sheet.
- Offline intake, search, restart and persistence.
- Sync after reconnecting; interrupt and resume.
- Low-memory behaviour, storage quota, battery/network use and accessibility.
- Export/delete and logout/revocation behaviour.

## 7. Release gates

The APK is **NOT READY** until all applicable gates pass with evidence attached to the exact source revision:

1. Architecture and threat model reviewed.
2. Native implementation and pinned build environment complete.
3. Automated tests and API contracts pass.
4. Reproducible APK build and artifact integrity verified.
5. Physical-device acceptance passes.
6. Security and privacy review independently completed.
7. Signing, release notes, checksum, SBOM and rollback/support plan complete.
8. Authorized human release approval recorded.

## 8. Current implementation status (2026-11-18)

### Implemented on `android/uaie-client-v0.1` (PR #20)

- Native Kotlin Android app, Gradle build and Android CI.
- Android Storage Access Framework picker and single-item Sharesheet intake.
- Streamed file copy and SHA-256 hashing; 10 MiB per-file limit.
- App-private original-byte storage; imported content is never executed.
- SQLite catalogue with unique content hash, display name, MIME type, byte size, source URI and import timestamp.
- Schema migration from catalogue v1 to v2.
- Duplicate-content detection and a 100 MiB catalogue quota.
- Temporary-file staging, fsync and same-directory rename before catalogue insertion; failed catalogue insertion cleans up the staged destination.
- Unit tests for per-file limits, quota boundaries and hash formatting.
- CI build at commit `e445a4ac2d95c8b091c2de346d6476736f90b628` passed, including four unit tests. A later hardening commit adds three additional policy tests and must be revalidated by CI before it is considered verified.

### Known limitations / acceptance blockers

- No remote sync, backend authentication, identity, authorization or connector integration.
- No full-text search, export, resumable/background transfer, cancellation or visible progress.
- The current catalogue quota is a fixed 100 MiB policy, not a user-configurable setting.
- The UI uses a basic worker thread; lifecycle/process-death recovery and concurrent import stress tests remain outstanding.
- A database/file reconciliation routine for orphaned files is not yet implemented.
- Sharesheet currently handles one `ACTION_SEND` item, not `ACTION_SEND_MULTIPLE`.
- Automated unit tests do not substitute for Android instrumentation tests.
- Physical OPPO A6 / Android 16 acceptance remains outstanding.

No production API endpoint, account, credentials, signing key, cloud service or billing resource is assumed to exist. Provisioning and production deployment require their own security and approval gates. The downloadable debug APK is a test artifact, not a production release.
