# UAIE PRIME — LM Studio Model Catalog Fusion

**Canonical engine:** Universal Acquisition and Integration Engine (UAIE PRIME)  
**Parent architecture:** NINEFOLD INTRINSIC  
**Specialist intelligence and fusion:** AFI PRIME  
**First acquisition source:** [LM Studio Model Catalog](https://lmstudio.ai/models)  
**Status:** Governed candidate-intake and local inventory adapters implemented; automated tests pass on the previous exact head; current changes require fresh CI and operational validation.

## Source and interface distinction

LM Studio provides three relevant surfaces:

1. **Public Model Catalog:** the website at `https://lmstudio.ai/models`, with model-family pages, descriptions, declared capabilities, local/cloud availability, artifact references, resource notes and licence statements where published.
2. **Official CLI:** `lms get` searches and downloads models. This is the supported user-facing acquisition route. The command requires an explicit model identifier and may present download choices.
3. **Native local REST API v1:** `GET /api/v1/models` inventories models already available on a specific LM Studio installation. It is not a complete public-catalog search API.

LM Studio's Hub terms restrict integrations to officially supported interfaces. UAIE therefore does **not** crawl or reverse-engineer the public website or Hub. It accepts a user-reviewed catalog candidate record (or a record exported through an officially supported interface), prepares the official CLI command for review, and then uses the documented local REST API to verify what is actually installed.

## Implemented candidate intake

`universal_engine.lmstudio_catalog`:

- Validates a user-supplied model identifier, catalog detail URL, optional quantization, capability declarations, licence text, memory/context notes and artifact references.
- Rejects non-LM-Studio catalog URLs, credentials, query strings, fragments, invalid identifiers, unapproved capability keys and unapproved artifact hosts.
- Bounds metadata to 256 KiB and requires finite JSON-compatible data.
- Creates an official `lms get` command proposal without executing it.
- Persists the candidate through UAIE with the original catalog URL as provenance.
- Fuses the candidate through AFI PRIME into a separate capability profile.
- Keeps performance verification and integration approval false.

Example:

```python
from universal_engine.lmstudio_catalog import (
    candidate_from_mapping, build_download_command,
    assimilate_catalog_candidate,
)
from universal_engine.uaie import UniversalAcquisitionIntegrationEngine

candidate = candidate_from_mapping({
    "model_id": "publisher/model-name",
    "display_name": "Model Name",
    "catalog_url": "https://lmstudio.ai/models/model-name",
    "quantization": "Q4_K_M",
    "capabilities": {"vision": True, "reasoning": True, "tool_use": True},
    "metadata": {"reviewed_by": "operator"},
})

uaie = UniversalAcquisitionIntegrationEngine("uaie.sqlite3")
catalog_record, afi_profile_record = assimilate_catalog_candidate(uaie, candidate)
print(build_download_command(candidate))  # proposal only; does not execute
```

After a human reviews and approves the candidate, the operator may run the displayed `lms get` command in the LM Studio environment. UAIE does not run the command or download weights.

## AFI PRIME fusion

AFI extracts explicit model facts and preserves the candidate's source, declared capabilities, model identity, quantization, parameter-size notes, memory/context information, artifact references and licence statement.

The profile is labelled `USER_SUPPLIED_CATALOG_METADATA` and `METADATA_ONLY_NOT_BENCHMARKED`. Publisher claims are not converted into verified capability claims. `performance_verified` and `integration_approved` remain false.

## Local inventory adapter

`universal_engine.lmstudio` reads the documented native v1 endpoint `GET /api/v1/models` from an explicitly configured loopback server. It is read-only. It does not download weights, load/unload models, execute inference or change LM Studio configuration. Optional API tokens are read at runtime and never persisted.

This local API adapter is the post-acquisition verification step: it can confirm that a selected model appears in the local LM Studio inventory, but it does not by itself prove that the model performs well or is suitable for a particular Engine task.

## Governance and production gates

- Catalog discovery is user-directed until LM Studio provides an officially supported public catalog API or grants explicit integration permission.
- Model acquisition remains a human-approved action through LM Studio's official CLI.
- Licence text is captured as evidence only; it is not a legal determination.
- Hardware suitability, actual resource estimates, model performance and security must be independently evaluated.
- No model is integrated into the Universal Engine solely because it appears in the catalog or is downloaded.
- The user's mobile device is a control terminal; local model execution requires a supported LM Studio host.

## Verification required

- Deterministic unit tests cover candidate validation, command construction, provenance and AFI fusion without network access or downloads.
- Exact-head GitHub Actions must pass after the latest changes.
- A live local inventory smoke test requires a user-authorised LM Studio host and token if authentication is enabled.
- Production readiness requires an approved catalogue access method, robust register linkage, licence review, hardware/resource evaluation, independent model benchmarks, security review, audit/retention policy, backup/restore, monitoring and deployment documentation.

**Evidence rule:** specified, implemented, CI-tested, live-smoke-tested, independently verified and production-operational are distinct states.
