# UAIE + UPN Intrinsic Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested, dependency-free UPN control-plane foundation alongside the existing UAIE prototype, with both existing-network and owned-network profiles governed by the Engine's lifecycle and deny-by-default policy.

**Architecture:** Add immutable contracts and a registry in `src/universal_engine/upn.py`. Do not implement VPN cryptography or open sockets. UPN profiles describe reviewed transports and private routes; policy authorizes only integrated, enabled, allowlisted profiles and trusted peers.

**Tech Stack:** Python 3.11+, standard library (`ipaddress`, `urllib.parse`, `dataclasses`, `enum`), existing lifecycle primitives, unittest.

**Spec:** `docs/superpowers/specs/2026-11-18-uaie-upn-intrinsic-design.md`

## Global Constraints

- Python >=3.11; no new mandatory dependencies.
- UAIE acquisition remains local-first and never executes acquired content.
- UPN supports `existing_private` and `owned_private` modes.
- Remote transports must be encrypted; embedded credentials, query strings and fragments are rejected.
- Only private unicast routes are accepted; default routes are rejected.
- Network policy is deny-by-default; inbound peer acceptance and internet egress are off by default.
- Registration requires `LifecycleState.INTEGRATED`.
- This increment performs no network I/O, infrastructure mutation, key generation or Android permission change.

## Review Focus

- Malformed or credential-bearing endpoint URLs must be rejected.
- IPv4/IPv6 default routes, loopback, link-local and multicast routes must be rejected.
- Unknown peer fingerprints and unapproved CIDRs must be denied.
- A profile not in the integrated lifecycle state must not be registered.
- Inbound peer acceptance must remain denied unless explicitly enabled by policy.

---

### Task 1: UPN contracts and policy tests

**Files:**
- Create: `tests/test_upn.py`
- Create: `tests/test_upn_provider.py`
- Create: `src/universal_engine/upn.py`
- Modify: `src/universal_engine/__init__.py`
- Modify: `src/universal_engine/providers/registry.py`
- Modify: `src/universal_engine/providers/interfaces.py`
- Create: `tests/test_upn_provider.py`

**Interfaces:**
- `NetworkMode`: `EXISTING_PRIVATE`, `OWNED_PRIVATE`.
- `TransportKind`: `WIREGUARD`, `HTTPS_API`, `LOCAL_ONLY`.
- `NetworkProfile(profile_id, name, mode, transport, endpoint=None, enabled=False)`.
- `NetworkPeer(peer_id, profile_id, public_key_fingerprint, allowed_cidrs)`.
- `NetworkPolicy(policy_id, allowed_profile_ids, trusted_peer_fingerprints, allowed_cidrs, allow_inbound_peers=False, allow_internet_egress=False)`.
- `NetworkDecision(allowed, reason, policy_id)`.
- `UPNRegistry.register(profile, lifecycle)`, `get(profile_id)`, `list()`; `get` and `list` re-check lifecycle state so retirement revokes availability.
- `ProviderKind.NETWORK` requires `execute`, `connect`, `disconnect` and `status`; `NetworkProvider` defines that structural contract.
- `UPNPolicyEngine.evaluate(profile, peer, policy, operation="connect")`.

- [ ] **Step 1: Write failing tests** for valid existing/owned profiles, HTTPS and WireGuard endpoint validation, no credentials/query/fragment, private route validation, default-route rejection, disabled profile denial, untrusted and cross-profile peer denial, route-scope denial, inbound denial, lifecycle-gated registration/retirement and network-provider registration.
- [ ] **Step 2: Run the focused test file** and confirm the expected import/behavior failures.
- [ ] **Step 3: Implement minimal immutable contracts, validation, registry and policy evaluation** in `src/universal_engine/upn.py`; bind each peer to one profile and re-check lifecycle state on lookup.
- [ ] **Step 4: Add `ProviderKind.NETWORK` and its required methods to the provider registry, define `NetworkProvider`, and export the public UPN types** from the package.
- [ ] **Step 5: Run focused and full Python test suites**; require all tests green.
- [ ] **Step 6: Commit** as `feat: add governed UPN control-plane contracts`.

### Task 2: Architecture and operational boundary documentation

**Files:**
- Create: `docs/network/UPN-IMPLEMENTATION-STATUS.md`
- Modify: `docs/UAIE-PROTOTYPE.md`

- [ ] **Step 1:** Document UPN's two profile modes, policy gates, and explicit absence of live transport.
- [ ] **Step 2:** Update UAIE prototype documentation to describe UAIE as intrinsic and explain its governed relationship with UPN.
- [ ] **Step 3:** Re-read both documents and verify no specified/implemented/operational status is conflated.
- [ ] **Step 4: Commit** as `docs: define intrinsic UAIE and UPN operating boundary`.

### Task 3: Verification and handoff

**Files:**
- No new source files.

- [ ] **Step 1:** Run `python -m compileall -q src tests`.
- [ ] **Step 2:** Run `PYTHONPATH=src python -m unittest discover -s tests -v`.
- [ ] **Step 3:** Inspect the exact feature-head GitHub Actions result and ensure it tests that SHA.
- [ ] **Step 4:** Record implemented scope, tests, CI evidence and remaining live-network/security gates in the pull request.
- [ ] **Step 5:** Keep the pull request unmerged; merge and live infrastructure provisioning remain separate approvals.

## Completion boundary

This plan completes the first UPN control-plane software increment and documents UAIE's intrinsic position. It does not complete live private-network provisioning, VPN tunnel operation, remote sync, autonomous discovery crawling, production Android release or independent security certification.
