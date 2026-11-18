import unittest

from universal_engine.contracts import ContractViolation
from universal_engine.lifecycle import CapabilityLifecycle, LifecycleState
from universal_engine.upn import (
    NetworkMode,
    NetworkPeer,
    NetworkPolicy,
    NetworkProfile,
    NetworkDecision,
    TransportKind,
    UPNPolicyEngine,
    UPNRegistry,
)


FINGERPRINT = "a" * 64
OTHER_FINGERPRINT = "b" * 64


class UPNContractTests(unittest.TestCase):
    def test_existing_private_https_profile_is_valid(self):
        profile = NetworkProfile(
            "upn.office", "Office network", NetworkMode.EXISTING_PRIVATE,
            TransportKind.HTTPS_API, "https://vpn.example.net/api", enabled=True,
        )
        self.assertEqual(profile.mode, NetworkMode.EXISTING_PRIVATE)

    def test_owned_private_profile_requires_wireguard(self):
        profile = NetworkProfile(
            "upn.home", "Home mesh", NetworkMode.OWNED_PRIVATE,
            TransportKind.WIREGUARD, "udp://vpn.example.net:51820",
        )
        self.assertEqual(profile.transport, TransportKind.WIREGUARD)
        with self.assertRaises(ContractViolation):
            NetworkProfile(
                "upn.bad", "Bad mesh", NetworkMode.OWNED_PRIVATE,
                TransportKind.HTTPS_API, "https://vpn.example.net",
            )

    def test_rejects_cleartext_https_api_endpoint(self):
        with self.assertRaises(ContractViolation):
            NetworkProfile(
                "upn.office", "Office", NetworkMode.EXISTING_PRIVATE,
                TransportKind.HTTPS_API, "http://vpn.example.net",
            )

    def test_rejects_credentials_query_and_fragment(self):
        for endpoint in (
            "https://user:secret@vpn.example.net/api",
            "https://vpn.example.net/api?token=secret",
            "https://vpn.example.net/api#fragment",
        ):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ContractViolation):
                    NetworkProfile(
                        "upn.office", "Office", NetworkMode.EXISTING_PRIVATE,
                        TransportKind.HTTPS_API, endpoint,
                    )

    def test_rejects_malformed_wireguard_endpoint(self):
        for endpoint in ("udp://vpn.example.net", "udp://user@vpn.example.net:51820",
                         "udp://vpn.example.net:99999", "tcp://vpn.example.net:51820"):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ContractViolation):
                    NetworkProfile(
                        "upn.home", "Home", NetworkMode.OWNED_PRIVATE,
                        TransportKind.WIREGUARD, endpoint,
                    )

    def test_local_only_profile_has_no_endpoint(self):
        profile = NetworkProfile(
            "upn.local", "Local catalogue", NetworkMode.EXISTING_PRIVATE,
            TransportKind.LOCAL_ONLY,
        )
        self.assertIsNone(profile.endpoint)
        with self.assertRaises(ContractViolation):
            NetworkProfile(
                "upn.local2", "Local", NetworkMode.EXISTING_PRIVATE,
                TransportKind.LOCAL_ONLY, "https://example.net",
            )

    def test_rejects_non_private_and_default_routes(self):
        for cidr in ("0.0.0.0/0", "::/0", "8.8.8.0/24", "127.0.0.0/8",
                     "169.254.0.0/16", "224.0.0.0/4", "2001:4860::/32"):
            with self.subTest(cidr=cidr):
                with self.assertRaises(ContractViolation):
                    NetworkPeer("peer.home", "upn.home", FINGERPRINT, (cidr,))

    def test_peer_requires_sha256_fingerprint(self):
        with self.assertRaises(ContractViolation):
            NetworkPeer("peer.home", "upn.home", "not-a-fingerprint", ("10.20.0.0/24",))

    def test_policy_rejects_internet_egress_in_v01(self):
        with self.assertRaises(ContractViolation):
            NetworkPolicy(
                "policy.home", ("upn.home",), (FINGERPRINT,),
                ("10.20.0.0/24",), allow_internet_egress=True,
            )


class UPNPolicyTests(unittest.TestCase):
    def setUp(self):
        self.profile = NetworkProfile(
            "upn.home", "Home mesh", NetworkMode.OWNED_PRIVATE,
            TransportKind.WIREGUARD, "udp://vpn.example.net:51820", enabled=True,
        )
        self.peer = NetworkPeer("peer.phone", "upn.home", FINGERPRINT, ("10.20.0.0/24",))
        self.policy = NetworkPolicy(
            "policy.home", ("upn.home",), (FINGERPRINT,), ("10.20.0.0/16",),
        )

    def test_allows_enabled_profile_trusted_peer_and_scoped_route(self):
        decision = UPNPolicyEngine().evaluate(
            self.profile, self.peer, self.policy, operation="connect",
        )
        self.assertIsInstance(decision, NetworkDecision)
        self.assertTrue(decision.allowed)

    def test_denies_disabled_profile(self):
        disabled = NetworkProfile(
            "upn.home", "Home mesh", NetworkMode.OWNED_PRIVATE,
            TransportKind.WIREGUARD, "udp://vpn.example.net:51820", enabled=False,
        )
        decision = UPNPolicyEngine().evaluate(disabled, self.peer, self.policy)
        self.assertFalse(decision.allowed)

    def test_denies_profile_not_allowlisted(self):
        policy = NetworkPolicy(
            "policy.other", ("upn.other",), (FINGERPRINT,), ("10.20.0.0/16",),
        )
        self.assertFalse(UPNPolicyEngine().evaluate(self.profile, self.peer, policy).allowed)


    def test_denies_peer_bound_to_a_different_profile(self):
        peer = NetworkPeer("peer.phone", "upn.other", FINGERPRINT, ("10.20.0.0/24",))
        self.assertFalse(UPNPolicyEngine().evaluate(self.profile, peer, self.policy).allowed)

    def test_denies_untrusted_peer(self):
        peer = NetworkPeer("peer.unknown", "upn.home", OTHER_FINGERPRINT, ("10.20.0.0/24",))
        self.assertFalse(UPNPolicyEngine().evaluate(self.profile, peer, self.policy).allowed)

    def test_denies_route_outside_policy_scope(self):
        peer = NetworkPeer("peer.outside", "upn.home", FINGERPRINT, ("10.30.0.0/24",))
        self.assertFalse(UPNPolicyEngine().evaluate(self.profile, peer, self.policy).allowed)

    def test_denies_inbound_peer_by_default(self):
        decision = UPNPolicyEngine().evaluate(
            self.profile, self.peer, self.policy, operation="accept_peer",
        )
        self.assertFalse(decision.allowed)

    def test_denies_unknown_operation_and_local_only_transport(self):
        engine = UPNPolicyEngine()
        self.assertFalse(engine.evaluate(self.profile, self.peer, self.policy, operation="admin").allowed)
        local = NetworkProfile(
            "upn.local", "Local", NetworkMode.EXISTING_PRIVATE, TransportKind.LOCAL_ONLY,
        )
        self.assertFalse(engine.evaluate(local, self.peer, self.policy).allowed)


class UPNRegistryTests(unittest.TestCase):
    def test_registration_requires_integrated_lifecycle(self):
        profile = NetworkProfile(
            "upn.home", "Home mesh", NetworkMode.OWNED_PRIVATE,
            TransportKind.WIREGUARD, "udp://vpn.example.net:51820",
        )
        lifecycle = CapabilityLifecycle()
        lifecycle.discover(profile.profile_id)
        registry = UPNRegistry()
        with self.assertRaises(ContractViolation):
            registry.register(profile, lifecycle)

        lifecycle.advance(profile.profile_id, LifecycleState.PROPOSED)
        lifecycle.advance(profile.profile_id, LifecycleState.UNDER_EVALUATION)
        lifecycle.advance(profile.profile_id, LifecycleState.APPROVED)
        lifecycle.advance(profile.profile_id, LifecycleState.INTEGRATED)
        registered = registry.register(profile, lifecycle)
        self.assertEqual(registered, profile)
        self.assertEqual(registry.get(profile.profile_id), profile)
        self.assertEqual(registry.list(), (profile,))


    def test_retired_profile_is_no_longer_available(self):
        profile = NetworkProfile(
            "upn.home", "Home mesh", NetworkMode.OWNED_PRIVATE,
            TransportKind.WIREGUARD, "udp://vpn.example.net:51820",
        )
        lifecycle = CapabilityLifecycle()
        lifecycle.discover(profile.profile_id)
        lifecycle.advance(profile.profile_id, LifecycleState.PROPOSED)
        lifecycle.advance(profile.profile_id, LifecycleState.UNDER_EVALUATION)
        lifecycle.advance(profile.profile_id, LifecycleState.APPROVED)
        lifecycle.advance(profile.profile_id, LifecycleState.INTEGRATED)
        registry = UPNRegistry()
        registry.register(profile, lifecycle)
        lifecycle.advance(profile.profile_id, LifecycleState.RETIRED)
        with self.assertRaises(ContractViolation):
            registry.get(profile.profile_id)

    def test_duplicate_profile_registration_is_rejected(self):
        profile = NetworkProfile(
            "upn.home", "Home mesh", NetworkMode.OWNED_PRIVATE,
            TransportKind.WIREGUARD, "udp://vpn.example.net:51820",
        )
        lifecycle = CapabilityLifecycle()
        lifecycle.discover(profile.profile_id)
        lifecycle.advance(profile.profile_id, LifecycleState.PROPOSED)
        lifecycle.advance(profile.profile_id, LifecycleState.UNDER_EVALUATION)
        lifecycle.advance(profile.profile_id, LifecycleState.APPROVED)
        lifecycle.advance(profile.profile_id, LifecycleState.INTEGRATED)
        registry = UPNRegistry()
        registry.register(profile, lifecycle)
        with self.assertRaises(ContractViolation):
            registry.register(profile, lifecycle)


if __name__ == "__main__":
    unittest.main()
