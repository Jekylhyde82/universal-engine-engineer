# UPN PRIME — Offline-First Private Digital Infrastructure

**Status:** PROPOSED — architecture specification; not an operational network  
**Parent architecture:** NINEFOLD INTRINSIC  
**Canonical identity:** MULTIVERSAL OMNIVELOCITY PRIME — GENIUS ENGINEER PRIME  
**Intrinsic capability:** UPN PRIME — Universal Private Network  
**Integrated capabilities:** UAIE, Universal Repository of Everything  
**Governing invariant:** INTRINSIC BY DESIGN

> The internet is a connection. It is not a dependency.

## 1. Purpose

UPN PRIME is a provider-neutral, privately governed networking architecture intended to keep authorised local services, devices, preserved information and selected computing capabilities useful when public internet connectivity is absent.

UPN does not create global connectivity from nothing. It provides independent local networking and services, and can use available private links or an optional internet gateway when those paths exist.

The architecture has two distinct objectives:

1. **Network independence:** local devices and services continue to communicate without public internet access.
2. **Offline internet-like utility:** users can browse, search and use previously acquired web content, software, documentation, maps, media and knowledge locally.

The second objective is delivered by local services and preserved content, not by pretending that a disconnected device is communicating with live websites.

## 2. Normative design invariants

The following are proposed requirements for every implementation increment:

- **Offline core:** essential local networking, identity, local naming, catalogue access and locally hosted services must not require public DNS, cloud authentication or an external control plane.
- **Local-first data:** new local records and queued work are committed locally before optional synchronisation.
- **Explicit connectivity:** internet egress, site-to-site links, mesh relaying and inbound access are separate capabilities with separate policy.
- **No silent loss:** interruption, quota pressure or sync conflict must not silently discard acquired material or provenance.
- **Fail closed:** unknown devices, peers, routes, credentials, profiles and policy states are denied.
- **Provenance:** acquired objects retain source, retrieval time, revision, rights evidence, content hash and integrity state where available.
- **No execution on intake:** acquired software, scripts, macros, models, archives and documents are data until separately reviewed and explicitly approved for a controlled operation.
- **Replaceable transports:** UPN defines provider-neutral contracts; it does not invent cryptographic protocols or require one radio, VPN vendor or mesh implementation.
- **Graceful degradation:** loss of an optional node or upstream link must not disable unrelated local services.
- **Evidence-led status:** specified, implemented, tested, security-reviewed and operational are distinct states.

## 3. Scope and limits

UPN can provide a local network, private services, local search and access to content already stored on reachable nodes. It can synchronise with remote systems when an authorised network path is available.

UPN cannot:
- retrieve a never-before-acquired page from a remote server while no route to that server exists;
- provide global internet connectivity without an upstream path;
- guarantee mesh reachability where radio range, power, compatible hardware, spectrum rules or routing paths do not permit it;
- guarantee that all public internet content can be archived, legally copied or kept current;
- make a phone's storage, battery, CPU or radio capacity unlimited.

Offline completeness is therefore measured against the local acquisition and preservation ledger, not against an unsupported claim that the entire live internet is present.

## 4. Unified nine-division responsibility map

The nine identities remain distinct specialist responsibilities inside one UPN PRIME architecture:

| Division | UPN responsibility |
|---|---|
| CORE PRIME | Local control plane, configuration, service orchestration and policy coordination |
| SECURITY PRIME | Device identity, authentication, authorisation, encryption integration, key custody policy, audit and isolation |
| MESH PRIME | Peer discovery, multi-hop routing and compatible mesh transport integration |
| QUANTUM PRIME | Research and evaluation of post-quantum cryptography and quantum-networking developments; no unreviewed cryptographic substitution |
| VELOCITY PRIME | Link selection, bandwidth/latency measurement, congestion and transfer scheduling |
| NEXUS PRIME | Protocol adapters, gateways, service discovery and interoperability |
| CHRONOS PRIME | Time sources, monotonic event ordering, timestamps, versioning and conflict chronology |
| AUTONOMY PRIME | Offline operation, local recovery, queued tasks and degraded-mode operation |
| EVOLUTION PRIME | Capability discovery, compatibility testing, controlled upgrades and rollback proposals |

This table assigns responsibilities; it does not claim that all nine divisions are implemented as executable services.

## 5. Network planes

UPN separates four planes so that loss or compromise of one does not silently grant authority over another.

### 5.1 Data plane

Carries authorised traffic between local devices, services and remote private peers. It uses established operating-system networking and reviewed transport implementations.

### 5.2 Control plane

Maintains profiles, peer enrolment, routes, service registrations, health and policy. The initial repository implementation is a local control-plane library, not a live router or tunnel manager.

### 5.3 Knowledge plane

Provides the local catalogue, preserved repository objects, web snapshots, documentation, maps, media and search indexes. It integrates with UAIE and the Universal Repository.

### 5.4 Management plane

Provides operator interfaces, configuration export, health reports, backup/restore, audit and lifecycle approval. Management endpoints are not exposed to untrusted networks by default.

## 6. Connectivity environments

UPN supports multiple transport environments through adapters:

1. **Local segment:** Ethernet, Wi-Fi access point or another directly attached local link.
2. **Peer/mesh segment:** compatible radio or network nodes forwarding traffic under explicit routing policy.
3. **Private inter-site segment:** authorised site-to-site links, private WAN, VPN or other reviewed transports.
4. **Optional internet gateway:** controlled egress to public internet services.

A mesh is a transport topology, not a promise of unlimited range or internet access. Bluetooth, Wi-Fi, Ethernet, cellular, long-range radio and specialist mesh systems have different bandwidth, range, power and regulatory characteristics. Each adapter must declare its capabilities and constraints.

No default route, internet egress, inbound service exposure or transit forwarding is enabled merely because a peer is enrolled.

## 7. Offline service environment

The minimum useful disconnected environment should provide:

- local device and service discovery;
- local DNS or an equivalent local naming service;
- local time service with a clearly reported confidence/source state;
- local web interface and static-site hosting;
- local repository and file access;
- local full-text and metadata search;
- local documentation and knowledge retrieval;
- local software/package cache where licence and integrity requirements permit;
- local maps and media access where the data has been acquired;
- local status, diagnostics, audit and backup interfaces;
- optional local AI inference when a compatible model and adequate compute are installed.

Every local service must document its dependencies and demonstrate that it does not silently call an external API in offline mode. External calls must fail clearly or enter a durable retry queue.

## 8. Offline Internet Library and Universal Repository

The offline library is an information service hosted over UPN. It is not a second competing acquisition system.

The Universal Repository has two complementary storage layers:

- **Global catalogue:** records discovered repositories and objects, including metadata-only and reference-only entries that cannot be copied.
- **Content preservation store:** retains permitted content snapshots and Git objects in content-addressed storage.

Suggested acquisition levels:

| Level | Stored material | Offline use |
|---|---|---|
| Catalogue | Metadata, source pointers, relationships, rights and status | Search what is known; content may still require connectivity |
| Snapshot | Selected pages, files, release assets or revision snapshots | Read and search the acquired snapshot |
| Full permitted mirror | Complete permitted repository or dataset mirror, including relevant history | Browse and inspect the preserved mirror |
| Curated offline pack | A versioned, integrity-checked collection for a device/site | Portable offline knowledge package |

Preservation modes are rights-aware: full permitted mirror, revision snapshot, metadata-only, selective permitted capture or reference-only. Missing licence evidence is not permission to copy.

All offline search results must show source and capture date/revision. Stale content must be visibly labelled. Derived summaries and embeddings never replace the preserved source.

## 9. Storage, replication and sync

UPN supports single-node and multi-node deployment without requiring a cloud service.

Core requirements:
- content-addressed objects with cryptographic hashes;
- source identity kept separate from deduplicated content identity;
- append-only provenance and acquisition events;
- explicit replication policies and replica health;
- resumable chunked transfer with integrity checks;
- bandwidth-aware scheduling and pause/resume;
- quota accounting and operator-visible storage forecasts;
- conflict detection and reconciliation without blind overwrite;
- export/import of signed or verifiable offline packs;
- backup and restore tests, including catalogue-to-object consistency;
- retention and deletion workflows that preserve audit evidence where legally appropriate.

Offline writes are local-first. Synchronisation is asynchronous and must not be required to read local data. Conflicting changes are retained for reconciliation rather than silently choosing a winner.

## 10. Security and trust boundaries

- Each device and service has a distinct identity.
- Enrolment is explicit and revocable.
- Possession of a network connection does not imply trust.
- Peer identity is cryptographically authenticated using reviewed implementations.
- Secrets and private keys are never committed to source control or embedded in repository content.
- Key generation, backup, rotation, revocation and recovery require a separately reviewed custody design.
- Routes are allowlisted; default routes and broad transit are denied unless separately approved.
- Management interfaces are isolated from general user/service traffic.
- Network segmentation separates management, storage, user devices, guest devices and experimental workloads.
- Parsers and archive extractors are sandboxed and resource-limited.
- Network and acquisition logs must avoid unnecessary collection of sensitive content.
- Emergency isolation must be possible without destroying preserved data.
- No custom cryptography is to be implemented as a shortcut.

Quantum PRIME is a research/evaluation responsibility. Post-quantum algorithms may only be adopted after standards, implementation maturity, interoperability and independent security review are established.

## 11. Offline mode state machine

| Mode | Behaviour |
|---|---|
| ONLINE | Local services plus explicitly authorised upstream connectivity |
| OFFLINE | Local services and reachable local data only; no internet dependency |
| MESH | Peer communication over available, authorised mesh links |
| ISOLATED | No external egress or untrusted peer transit; local operator access only |
| RECOVERY | Restricted services for integrity checks, restore and incident handling |

Mode changes must be observable, auditable and reversible. An offline transition must not erase pending work. Reconnection must not automatically trust newly visible peers or execute queued content.

## 12. Device and deployment profiles

### Mobile control terminal

An Android device can configure UPN, browse local services, search selected indexes and consume offline packs. It should not be assumed to host the entire archive or large AI models. Mobile storage, battery, memory and thermal limits must be respected.

### Local core node

A low-power computer or existing desktop can host local DNS, catalogue, web services, search and synchronisation. The system should remain useful without paid cloud infrastructure.

### Storage node

External SSD/HDD or a network-attached storage device can hold large snapshots, Git mirrors, media and backups. Capacity, filesystem integrity, encryption-at-rest and backup policy must be explicit.

### Mesh/relay node

A compatible device can relay traffic only when the hardware, software, power, radio configuration and legal operating conditions support it.

### Multi-site node

A separately authorised site can exchange selected data through a reviewed private link. No site is trusted solely because it shares an owner or network name.

## 13. Provider-neutral software boundaries

UPN should expose contracts for:
- network interface and link inventory;
- local service discovery and registration;
- peer identity and enrolment;
- route policy and route-state observation;
- transport lifecycle (prepare, connect, status, disconnect);
- secure transfer and synchronisation;
- local service health;
- storage replication;
- time-source status;
- audit and recovery.

Adapters must report capability, limitations, health and evidence. A provider being registered does not prove a live connection.

Technology candidates for evaluation—not pre-approved dependencies—include:
- Linux networking and OpenWrt for local routing/access-point roles;
- WireGuard for a reviewed encrypted tunnel adapter;
- mDNS/DNS-SD and local DNS for service discovery/naming;
- Babel or BATMAN-adv for suitable IP mesh scenarios;
- standard Ethernet/Wi-Fi as the first local transport;
- SQLite for an initial single-node catalogue, with a later database only when measured scale requires it;
- Meilisearch/OpenSearch or a smaller local index after device benchmarks;
- Git and content-addressed storage for repository preservation;
- Qdrant or another local vector store only when semantic retrieval justifies its resource cost;
- llama.cpp or another compatible local inference runtime for optional offline AI.

Selection requires licence, maintenance, security, platform compatibility, resource and integration review. Do not install all candidates simultaneously.

## 14. Operational observability

The operator must be able to inspect:
- current connectivity mode and upstream status;
- reachable devices and authenticated peers;
- link type, signal/health and observed performance where available;
- routes and policy decisions;
- local services and their external dependencies;
- storage capacity, object counts and replication state;
- queued, paused, failed and completed sync jobs;
- catalogue coverage and acquisition gaps;
- stale indexes and source snapshots;
- backup age and last successful restore test;
- security events and revocation state.

A dashboard must distinguish observed facts from estimates and unknowns.

## 15. Acceptance and verification matrix

| ID | Test | Pass condition |
|---|---|---|
| OFF-001 | Disconnect upstream internet | Local UPN services remain available |
| OFF-002 | Disable public DNS access | Local names and local search still work |
| OFF-003 | External API unavailable | Local operations work; external-dependent functions fail clearly or queue |
| OFF-004 | Restart local core offline | Configured local services recover without cloud authentication |
| OFF-005 | Browse preserved web snapshot | Snapshot opens and displays capture date/source |
| OFF-006 | Search local archive | Results resolve to preserved source objects |
| MESH-001 | Remove one relay | Unaffected reachable nodes continue; route loss is reported |
| MESH-002 | Unknown peer attempts enrolment | Peer is denied |
| SEC-001 | Unauthorised route request | Denied and audited |
| SEC-002 | Revoked peer reconnects | Access remains denied |
| SEC-003 | Isolated mode | No external egress or unapproved transit |
| DATA-001 | Interrupt transfer | Resume verifies chunks and final object hash |
| DATA-002 | Conflicting offline updates | Both versions retained for reconciliation |
| DATA-003 | Restore backup | Catalogue and referenced objects pass integrity checks |
| DATA-004 | Duplicate content from two sources | Content deduplicates while both source records remain |
| SYNC-001 | Reconnect after offline changes | Approved sync resumes without silent overwrite |
| AI-001 | Local model available, internet absent | Local inference completes without external API |
| AI-002 | Local model absent | Capability reports unavailable; no cloud fallback unless explicitly enabled |
| OPS-001 | Storage quota reached | Acquisition pauses visibly; no silent deletion |
| OPS-002 | Clock source unavailable | Time uncertainty is reported; event ordering remains usable |

A test passes only with a recorded environment, exact revision, procedure, raw result and independent review appropriate to the risk.

## 16. Delivery roadmap

### Stage 0 — Reconcile and specify
- Reconcile this specification with the existing UPN control-plane proposal and Android intake work.
- Freeze provider-neutral interfaces and threat boundaries.
- Record dependencies, non-goals, acceptance tests and status vocabulary.

### Stage 1 — Offline local core
- Run a local network without internet.
- Provide local addressing, naming, service discovery and a minimal local operator interface.
- Demonstrate restart and operation with the WAN cable/upstream link disconnected.

### Stage 2 — Local knowledge services
- Connect UAIE catalogue and Universal Repository storage.
- Add local web serving, full-text search and source-linked browsing.
- Import an explicitly selected offline content pack and verify it offline.

### Stage 3 — Secure identity and transport
- Complete device identity, enrolment, revocation and key custody design.
- Implement a reviewed transport adapter behind UPN contracts.
- Test route isolation, segmentation, failure and recovery in an isolated lab.

### Stage 4 — Resumable synchronisation
- Add authenticated sync API, transfer queue, resumable chunks, conflict handling and replication policy.
- Keep Android sync opt-in and least-privilege; do not add permissions before the service and threat model are reviewed.

### Stage 5 — Mesh and multi-site
- Evaluate hardware-specific mesh candidates.
- Pilot a small number of nodes with documented range, throughput, power and regulatory constraints.
- Add site-to-site operation only after identity and revocation controls pass.

### Stage 6 — Offline intelligence
- Benchmark local search and optional AI against actual target hardware.
- Add local model/package management, resource budgets and explicit no-cloud-fallback mode.
- Verify offline behaviour by network isolation tests.

### Stage 7 — Operations and evolution
- Add monitoring, backup/restore, upgrade/rollback, incident response and independent security review.
- Expand providers and capabilities only through evidence-based lifecycle approval.

## 17. Cost, privacy and authority boundaries

- No paid cloud service, subscription, domain, hardware or recurring infrastructure is required to begin the local prototype.
- Any cost-bearing option must be presented with cost, alternatives and a clear approval gate.
- No private network, device, router, firewall, radio or account is configured without an explicit deployment-specific approval and access.
- No external content is copied beyond applicable licence, access and platform permissions.
- No source repository is modified by a runtime acquisition job.
- No autonomous network egress, peer acceptance, route change or deployment is permitted by discovery alone.

## 18. Current implementation truth

At specification time, the repository has a UAIE local-first file/object intake prototype, a proposed UPN control-plane slice with profile/peer/route policy contracts, and a separate offline-first Android intake alpha.

These are not yet a working private network or offline internet appliance.

Not yet demonstrated by this specification:
- live router/access-point configuration;
- live WireGuard or mesh connectivity;
- multi-node authenticated replication;
- a full offline web archive/search appliance;
- offline Android network operation against a deployed UPN core;
- local AI operation on the target phone;
- independent security certification or production readiness.

Every delivery stage must update this section only when exact-revision evidence exists.

## 19. Definition of done

UPN PRIME's offline foundation is not complete until an isolated acceptance test demonstrates that authorised devices can join the local network, resolve local services, access the local repository and search index, communicate within policy, preserve local changes, recover after restart and continue operating with all public internet paths physically disconnected.

Mesh, multi-site, AI and public internet gateway capabilities are separate extensions with their own acceptance gates.

**PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.**
