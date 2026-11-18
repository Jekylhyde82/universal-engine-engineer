# UPN Implementation Status — v0.1

**Architecture:** U.N.I.V.E.R.S.A.L. E.N.G.I.N.E. / E.N.G.I.N.E.E.R.  
**Foundation:** NINEFOLD INTRINSIC  
**Governing invariant:** INTRINSIC BY DESIGN  
**Capability:** UPN PRIME — Universal Private Network

## Purpose

UPN PRIME is one provider-neutral networking capability with two modes:

- **Existing private networks:** explicitly configured access to a network or service already operated by the user or another authorized organization.
- **Owned private infrastructure:** profiles for private network infrastructure operated and controlled by the Universal Engine project.

Its foundational operating invariant is **offline-first and internet-independent**: core local networking, local identity/policy, local naming, local services and access to locally preserved knowledge must continue without public internet connectivity. Public internet access is an optional upstream capability, not a dependency.

See the [UPN PRIME Offline-First Private Digital Infrastructure specification](UPN-OFFLINE-INTERNET-ARCHITECTURE.md) for the complete proposed architecture, nine-division responsibility map, network planes, offline service environment, storage/synchronization design, security boundaries, modes, acceptance tests and staged delivery plan.

UAIE can discover, assimilate and evaluate networking technologies for either UPN mode. UAIE acquisition does not authorize a connection. UPN policy and lifecycle governance control any future connection.

## v0.1 control-plane scope

The feature branch contains immutable profile and peer contracts, strict endpoint and private-route validation, profile-bound peer identity, a deny-by-default policy evaluator, lifecycle-gated registration with retirement re-checks, and a provider-neutral NETWORK adapter kind/interface. Unit tests are present. Exact-head CI verification is pending; do not mark the increment CI-tested until the current feature-head workflow passes.

It does not open sockets, establish VPN tunnels, provision servers, create keys, change routes, configure firewalls or add Android network permissions. It does not implement cryptography.

## Offline-first requirements

- Local control-plane and essential local services must not depend on cloud authentication, public DNS or remote APIs.
- Local catalogue, repository content and indexes remain readable without synchronization.
- Offline writes and acquisition requests are durably queued; sync is asynchronous and resumable.
- Reconnection does not automatically trust peers, execute queued content or overwrite conflicting data.
- Local services report when data is a preserved snapshot and show its source/revision/capture time.
- An isolated acceptance test must physically disconnect all public internet paths and verify local service discovery, browsing/search, repository access and recovery.

## Security defaults

- Profiles disabled until explicitly enabled.
- Only allowlisted profile IDs.
- Explicit trusted peer SHA-256 public-key fingerprints.
- Encrypted remote transports only.
- Private unicast routes only; no default route.
- Inbound peer acceptance disabled.
- Internet egress disabled.
- Registration requires lifecycle state `integrated`.
- No acquired content or external instructions are executed.
- Mesh transit and inter-site routing are separate opt-in policies, not implicit peer privileges.

## Evidence status

The code and test status must be updated only from exact revision test/CI evidence. A valid profile is configuration data, not proof of a working or secure network. Live operation requires a reviewed transport adapter, external key custody, authenticated identity, peer enrollment/revocation, isolated-network tests and independent security review.

The offline-first architecture in the linked specification is proposed, not yet operational. No live private network, mesh, offline internet appliance, distributed replication service or deployed Android UPN client is claimed.

## Planned increments

1. Reconcile provider-neutral contracts and establish a local-only network lab acceptance harness.
2. Build a local UPN core with local addressing, naming, service discovery and operator interface; prove operation with WAN disconnected.
3. Connect UAIE and Universal Repository storage; add local web serving and source-linked full-text search.
4. Complete device identity, enrolment, revocation, key custody and network segmentation design.
5. Implement a reviewed transport adapter (WireGuard candidate) behind the UPN contract.
6. Add authenticated, resumable, conflict-aware synchronization and opt-in Android client support.
7. Evaluate hardware-specific mesh options and pilot only after security and regulatory review.
8. Add optional local AI after device-specific resource benchmarks and no-cloud-fallback tests.
9. Complete backup/restore, observability, incident response and independent security review.
