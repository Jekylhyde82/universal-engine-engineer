"""Public interfaces for the Universal Engine / Engineer core."""
from .contracts import ContractViolation, PolicyDecision, ProviderRequest, ProviderResult, ResultStatus
from .upn import (
    NetworkDecision,
    NetworkMode,
    NetworkPeer,
    NetworkPolicy,
    NetworkProfile,
    TransportKind,
    UPNPolicyEngine,
    UPNRegistry,
)

__all__ = [
    "ContractViolation", "PolicyDecision", "ProviderRequest", "ProviderResult", "ResultStatus",
    "NetworkDecision", "NetworkMode", "NetworkPeer", "NetworkPolicy", "NetworkProfile",
    "TransportKind", "UPNPolicyEngine", "UPNRegistry",
]

from .uaie import (
    AssimilationRecord, UAIEError, UniversalAcquisitionIntegrationEngine,
    UniversalAssimilationEngine,
)
from .lmstudio import (
    CatalogAssimilationResult, LMStudioError, LMStudioModel,
    assimilate_catalog, list_models,
)
from .afi import AFIModelCapabilityProfile, AFIPrimeFusionAdapter

__all__ += [
    "AssimilationRecord", "UAIEError", "UniversalAcquisitionIntegrationEngine",
    "UniversalAssimilationEngine", "CatalogAssimilationResult", "LMStudioError",
    "LMStudioModel", "assimilate_catalog", "list_models",
    "AFIModelCapabilityProfile", "AFIPrimeFusionAdapter",
]
