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
    AcquisitionRegisterEntry, AssimilationRecord, UAIEError, UniversalAcquisitionIntegrationEngine,
    UniversalAssimilationEngine,
)
from .lmstudio import (
    CatalogAssimilationResult, LMStudioDownloadJob, LMStudioError, LMStudioModel,
    assimilate_catalog, download_model, get_download_status, list_models,
)
from .afi import AFIModelCapabilityProfile, AFIPrimeFusionAdapter

__all__ += [
    "AcquisitionRegisterEntry", "AssimilationRecord", "UAIEError", "UniversalAcquisitionIntegrationEngine",
    "UniversalAssimilationEngine", "CatalogAssimilationResult", "LMStudioError",
    "LMStudioModel", "LMStudioDownloadJob", "assimilate_catalog",
    "download_model", "get_download_status", "list_models",
    "AFIModelCapabilityProfile", "AFIPrimeFusionAdapter",
]

from .lmstudio_catalog import (
    LMStudioCatalogCandidate, LMStudioCatalogError,
    assimilate_catalog_candidate, assimilate_model_yaml_file,
    build_clone_command, build_download_command, candidate_from_mapping,
    candidate_from_model_yaml, download_catalog_candidate,
)

__all__ += [
    "LMStudioCatalogCandidate", "LMStudioCatalogError",
    "assimilate_catalog_candidate", "assimilate_model_yaml_file",
    "build_clone_command", "build_download_command", "candidate_from_mapping",
    "candidate_from_model_yaml", "download_catalog_candidate",
]
