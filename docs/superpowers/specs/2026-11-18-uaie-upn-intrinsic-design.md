# UAIE + UPN Intrinsic Foundation — Design Specification

**Date:** 2026-11-18  
**Status:** Approved working direction; implementation slice in progress  
**Canonical architecture:** U.N.I.V.E.R.S.A.L. E.N.G.I.N.E. / E.N.G.I.N.E.E.R.  
**Foundation:** NINEFOLD INTRINSIC  
**Invariant:** INTRINSIC BY DESIGN

## Intent

Make UAIE a foundational, always-accommodated capability from the initial architecture, and establish UPN (Universal Private Network) as its secure networking foundation. UAIE discovers, acquires, assimilates, understands, evaluates and proposes capabilities. UPN supplies governed private-network connectivity between existing private networks and infrastructure owned by the project.

This specification defines the first executable UPN control-plane slice alongside the existing UAIE local-first acquisition prototype. It does not claim that a live private network, VPN tunnel, cloud service, Android sync endpoint or autonomous web crawler already exists.

## Goals

- Keep UAIE as one integrated capability with discovery, acquisition, assimilation, comprehension, decomposition, evaluation, governed integration, verification and evolution responsibilities.
- Preserve UAIE's existing local-first Python intake, SHA-256 provenance, SQLite catalogue and approval lifecycle.
- Establish UPN as one architecture with two modes: connect to existing private networks; define and govern project-owned private network profiles.
- Provide dependency-free, typed contracts for network profiles, peers, route scopes, policy decisions and lifecycle-gated registration.
- Fail closed: no profile is usable unless enabled, explicitly allowlisted, lifecycle-integrated and its peer identity and routes are trusted.
- Require encrypted transports for network connections; reject credential-bearing or unsafe endpoints.
- Bind every peer to one network profile and re-check lifecycle state at registry lookup so retirement revokes availability.
- Keep acquisition, discovery and network configuration separate from execution, connection and integration approval.
- Keep the Android client offline-first and least-privilege; future sync/network permission is a separate reviewed change.

## Non-goals for this increment

- Creating or provisioning cloud accounts, routers, servers, DNS, firewall rules, VPN keys or paid infrastructure.
- Opening network sockets, starting/stopping tunnels, changing device routes, installing WireGuard/Tailscale or modifying host networking.
- Implementing cryptography or inventing a VPN protocol. Use reviewed transport implementations through future adapters.
- Enabling inbound access, full-tunnel internet egress, automatic peer trust or automatic integration.
- Adding network permission or background synchronization to the Android app in this slice.
- Claiming production security, high availability, anonymity or operational readiness.

## Architecture

UAIE remains the universal intake and knowledge capability. It may discover network technologies and acquire their public documentation, but external material remains untrusted and is never executed. UPN is a separate, intrinsic networking capability consumed by UAIE and other approved Engine services.

UPN has two profile modes:
- `existing_private`: a governed connection profile for an existing private network or service.
- `owned_private`: a profile describing infrastructure the project owns and controls.

Both modes use explicit transport declarations, peer identity fingerprints, private route allowlists and a deny-by-default policy. The first implementation is a local control-plane library and registry; transport adapters remain unimplemented and must use established, audited encryption implementations.

## Alternatives considered

1. **Adopt one existing overlay provider only.** Fast to pilot, but ties the architecture to one provider and does not represent owned infrastructure consistently.
2. **Build a bespoke VPN/mesh protocol.** Rejected: creates unnecessary cryptographic and operational risk.
3. **Provider-neutral UPN control plane with reviewed transport adapters.** Selected: supports existing and owned networks while keeping protocol implementation replaceable and security reviewable.

## First-slice acceptance

- Python 3.11+, standard library only; no new mandatory dependencies.
- Validated immutable network profile and peer contracts.
- Endpoint validation rejects cleartext remote URLs, embedded credentials, query strings, fragments and malformed endpoints.
- Route validation rejects default routes and non-private, loopback, link-local, multicast or unspecified networks.
- Policy denies disabled/unregistered profiles, unknown peers, out-of-scope routes and inbound peer acceptance unless explicitly enabled.
- Registry requires the corresponding capability lifecycle state to be `integrated`.
- Unit tests cover positive and negative cases.
- Existing Python test suite remains green in GitHub Actions on the exact feature head.
- No network connection or infrastructure mutation occurs.

## Governance and evidence

Lifecycle remains Discovered → Proposed → Under Evaluation → Approved → Integrated, with Rejected and Retired outcomes. Discovery and assimilation never imply approval, execution or integration. A registered UPN profile is only a configuration record; it is not proof of a live tunnel or verified endpoint.

**Evidence rule:** distinguish specified, implemented, CI-tested, externally verified and operational. Never promote one state to another without its corresponding evidence.

## Next increments

1. Add read-only network capability discovery to UAIE using permission-scoped connectors.
2. Add a reviewed WireGuard adapter behind the UPN transport contract, with key generation and custody outside chat and outside source control.
3. Add authenticated service identity, authorization, revocation and audit anchoring.
4. Add a secure server-side sync API and Android opt-in sync queue; only then request Android network permission.
5. Pilot an isolated private network, test peer enrollment, route isolation, revocation, offline recovery and backup/restore.
6. Complete independent threat-model and security review before live use.
