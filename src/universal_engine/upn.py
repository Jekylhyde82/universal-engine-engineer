"""UPN: governed, provider-neutral private-network control-plane contracts.

This module validates configuration and authorization decisions only. It does not
open sockets, configure routes, create keys, or establish VPN tunnels.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from ipaddress import ip_network
import re
from typing import Protocol
from urllib.parse import urlsplit

from .contracts import ContractViolation
from .lifecycle import LifecycleState

_SHA256_FINGERPRINT = re.compile(r"^[0-9a-fA-F]{64}$")
_PROFILE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,63}$")


class NetworkMode(StrEnum):
    """Whether the profile connects to an existing or project-owned network."""

    EXISTING_PRIVATE = "existing_private"
    OWNED_PRIVATE = "owned_private"


class TransportKind(StrEnum):
    """Reviewed transport families; no transport implementation is bundled."""

    WIREGUARD = "wireguard"
    HTTPS_API = "https_api"
    LOCAL_ONLY = "local_only"


def _required_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{label} is required")
    if any(ord(char) < 32 for char in value):
        raise ContractViolation(f"{label} must not contain control characters")
    return value.strip()


def _validate_profile_id(value: str, label: str) -> str:
    value = _required_text(value, label)
    if not _PROFILE_ID.fullmatch(value):
        raise ContractViolation(f"{label} must be 2-64 safe identifier characters")
    return value


def _validate_endpoint(transport: TransportKind, endpoint: str | None) -> str | None:
    if transport is TransportKind.LOCAL_ONLY:
        if endpoint is not None:
            raise ContractViolation("local-only transport must not define an endpoint")
        return None
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ContractViolation("remote transport endpoint is required")
    endpoint = _required_text(endpoint, "endpoint")
    try:
        parsed = urlsplit(endpoint)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ContractViolation("endpoint is malformed") from exc
    if not hostname or parsed.username is not None or parsed.password is not None:
        raise ContractViolation("endpoint host is required and embedded credentials are forbidden")
    if parsed.query or parsed.fragment:
        raise ContractViolation("endpoint query strings and fragments are forbidden")
    if transport is TransportKind.HTTPS_API:
        if parsed.scheme != "https":
            raise ContractViolation("remote API endpoints must use HTTPS")
        if port is not None and not 1 <= port <= 65535:
            raise ContractViolation("endpoint port must be between 1 and 65535")
        return endpoint
    if transport is TransportKind.WIREGUARD:
        if parsed.scheme != "udp" or port is None or not 1 <= port <= 65535:
            raise ContractViolation("WireGuard endpoint must use udp://host:port")
        if parsed.path not in ("",):
            raise ContractViolation("WireGuard endpoint must not contain a path")
        return endpoint
    raise ContractViolation("unsupported transport")


def _private_networks(values: tuple[str, ...] | list[str], label: str) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)) or not values:
        raise ContractViolation(f"{label} must contain at least one private CIDR")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ContractViolation(f"{label} entries must be CIDR strings")
        try:
            network = ip_network(value.strip(), strict=True)
        except ValueError as exc:
            raise ContractViolation(f"{label} contains an invalid CIDR: {value}") from exc
        address = network.network_address
        if (
            network.prefixlen == 0
            or not address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_unspecified
            or address.is_reserved
        ):
            raise ContractViolation(f"{label} permits only private unicast routes, not {value}")
        canonical = str(network)
        if canonical not in result:
            result.append(canonical)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class NetworkProfile:
    """A disabled-by-default description of a private network connection."""

    profile_id: str
    name: str
    mode: NetworkMode
    transport: TransportKind
    endpoint: str | None = None
    enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _validate_profile_id(self.profile_id, "profile_id"))
        object.__setattr__(self, "name", _required_text(self.name, "name"))
        if not isinstance(self.mode, NetworkMode):
            raise ContractViolation("mode must be a NetworkMode")
        if not isinstance(self.transport, TransportKind):
            raise ContractViolation("transport must be a TransportKind")
        if not isinstance(self.enabled, bool):
            raise ContractViolation("enabled must be a boolean")
        if self.mode is NetworkMode.OWNED_PRIVATE and self.transport is not TransportKind.WIREGUARD:
            raise ContractViolation("owned private profiles require the reviewed WireGuard transport")
        object.__setattr__(self, "endpoint", _validate_endpoint(self.transport, self.endpoint))


@dataclass(frozen=True, slots=True)
class NetworkPeer:
    """A peer pinned by a SHA-256 fingerprint of its public identity key."""

    peer_id: str
    public_key_fingerprint: str
    allowed_cidrs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "peer_id", _validate_profile_id(self.peer_id, "peer_id"))
        if not isinstance(self.public_key_fingerprint, str) or not _SHA256_FINGERPRINT.fullmatch(
            self.public_key_fingerprint
        ):
            raise ContractViolation("public_key_fingerprint must be a 64-character SHA-256 hex fingerprint")
        object.__setattr__(self, "public_key_fingerprint", self.public_key_fingerprint.lower())
        object.__setattr__(self, "allowed_cidrs", _private_networks(self.allowed_cidrs, "peer allowed_cidrs"))


@dataclass(frozen=True, slots=True)
class NetworkPolicy:
    """Explicit allowlists and conservative network-access defaults."""

    policy_id: str
    allowed_profile_ids: tuple[str, ...]
    trusted_peer_fingerprints: tuple[str, ...]
    allowed_cidrs: tuple[str, ...]
    allow_inbound_peers: bool = False
    allow_internet_egress: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", _validate_profile_id(self.policy_id, "policy_id"))
        if not isinstance(self.allowed_profile_ids, (tuple, list)) or not self.allowed_profile_ids:
            raise ContractViolation("allowed_profile_ids must not be empty")
        profiles = tuple(_validate_profile_id(item, "allowed_profile_id") for item in self.allowed_profile_ids)
        if len(set(profiles)) != len(profiles):
            raise ContractViolation("allowed_profile_ids must be unique")
        object.__setattr__(self, "allowed_profile_ids", profiles)
        if not isinstance(self.trusted_peer_fingerprints, (tuple, list)) or not self.trusted_peer_fingerprints:
            raise ContractViolation("trusted_peer_fingerprints must not be empty")
        fingerprints: list[str] = []
        for fingerprint in self.trusted_peer_fingerprints:
            if not isinstance(fingerprint, str) or not _SHA256_FINGERPRINT.fullmatch(fingerprint):
                raise ContractViolation("trusted peer fingerprints must be 64-character SHA-256 hex")
            fingerprints.append(fingerprint.lower())
        object.__setattr__(self, "trusted_peer_fingerprints", tuple(dict.fromkeys(fingerprints)))
        object.__setattr__(self, "allowed_cidrs", _private_networks(self.allowed_cidrs, "policy allowed_cidrs"))
        if not isinstance(self.allow_inbound_peers, bool) or not isinstance(self.allow_internet_egress, bool):
            raise ContractViolation("network policy flags must be booleans")
        if self.allow_internet_egress:
            raise ContractViolation("internet egress and default-route tunnelling are not supported in UPN v0.1")


@dataclass(frozen=True, slots=True)
class NetworkDecision:
    allowed: bool
    reason: str
    policy_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise ContractViolation("allowed must be a boolean")
        object.__setattr__(self, "reason", _required_text(self.reason, "reason"))
        object.__setattr__(self, "policy_id", _validate_profile_id(self.policy_id, "policy_id"))


class LifecycleReader(Protocol):
    def state_of(self, capability_id: str) -> LifecycleState: ...


class UPNRegistry:
    """In-memory profile allowlist; only lifecycle-integrated profiles register."""

    def __init__(self) -> None:
        self._profiles: dict[str, NetworkProfile] = {}

    def register(self, profile: NetworkProfile, lifecycle: LifecycleReader) -> NetworkProfile:
        if not isinstance(profile, NetworkProfile):
            raise ContractViolation("profile must be a NetworkProfile")
        if profile.profile_id in self._profiles:
            raise ContractViolation(f"network profile already registered: {profile.profile_id}")
        if lifecycle.state_of(profile.profile_id) is not LifecycleState.INTEGRATED:
            raise ContractViolation("only lifecycle-integrated network profiles may be registered")
        self._profiles[profile.profile_id] = profile
        return profile

    def get(self, profile_id: str) -> NetworkProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ContractViolation(f"network profile is not registered: {profile_id}") from exc

    def list(self) -> tuple[NetworkProfile, ...]:
        return tuple(self._profiles.values())


class UPNPolicyEngine:
    """Fail-closed policy evaluator; deliberately performs no network I/O."""

    def evaluate(
        self,
        profile: NetworkProfile,
        peer: NetworkPeer,
        policy: NetworkPolicy,
        *,
        operation: str = "connect",
    ) -> NetworkDecision:
        def deny(reason: str) -> NetworkDecision:
            return NetworkDecision(False, reason, policy.policy_id)

        if not isinstance(profile, NetworkProfile) or not isinstance(peer, NetworkPeer):
            raise ContractViolation("profile and peer must use UPN contract types")
        if not isinstance(policy, NetworkPolicy):
            raise ContractViolation("policy must be a NetworkPolicy")
        if operation not in ("connect", "accept_peer"):
            return deny("operation is not permitted by UPN v0.1")
        if not profile.enabled:
            return deny("network profile is disabled")
        if profile.transport is TransportKind.LOCAL_ONLY:
            return deny("local-only profiles cannot establish network peer connections")
        if profile.profile_id not in policy.allowed_profile_ids:
            return deny("network profile is not allowlisted")
        if peer.public_key_fingerprint not in policy.trusted_peer_fingerprints:
            return deny("peer public-key fingerprint is not trusted")
        if operation == "accept_peer" and not policy.allow_inbound_peers:
            return deny("inbound peer acceptance is disabled")
        for route in peer.allowed_cidrs:
            network = ip_network(route, strict=True)
            if not any(
                network.version == (allowed := ip_network(cidr, strict=True)).version
                and network.subnet_of(allowed)
                for cidr in policy.allowed_cidrs
            ):
                return deny(f"peer route is outside policy scope: {route}")
        return NetworkDecision(True, "profile, peer and routes satisfy policy", policy.policy_id)
