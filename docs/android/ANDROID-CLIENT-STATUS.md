# UAIE Android client — implementation status

**Branch:** `android/uaie-client-v0.1`  
**Milestone:** Offline local-intake alpha  
**Release classification:** Development/test build only.

## Implemented in source

- Native Kotlin Android application module using Android Gradle Plugin 9.5.0.
- Gradle 9.6.0 distribution pinned in CI and verified against the official SHA-256 checksum.
- Minimum Android API 26; target API 36; Java 17 toolchain.
- Android Storage Access Framework file picker and single-file Sharesheet intake.
- Streaming file copy and SHA-256 hashing with a 10 MiB per-file bound.
- App-private preservation of imported bytes.
- SQLite catalogue with SHA-256 uniqueness/deduplication.
- Local metadata listing and user-initiated deletion.
- No network permission, embedded credentials or imported-content execution.
- GitHub Actions debug APK build, checksum and short-retention test artifact.

## Not implemented

- Remote synchronization, identity, authentication and authorization.
- Full-text search, export workflow and total storage quota management.
- Resumable background transfers and multi-file share handling.
- Keystore-backed session storage (no session token exists yet).
- Instrumentation/device tests and physical OPPO A6 acceptance.
- Production signing, SBOM attestation and release publication.

## Known limitations and next acceptance work

- Initial UI uses platform widgets to minimize dependencies and memory footprint.
- Imports run on a worker thread; progress and cancellation controls are pending.
- Share intake currently handles a single URI.
- File quota is per item only; total app storage quota is not enforced.
- Android backup is disabled to avoid unintended copying of the private catalogue and imported files.
- The CI build currently uses a verified Gradle distribution directly; a checked-in Gradle Wrapper and wrapper-JAR verification remain to be added.
- CI debug APK is a test artifact, not a production-signed deliverable.
