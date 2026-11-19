# UAIE PRIME — LM Studio Model Catalog Fusion

**Canonical engine:** Universal Acquisition and Integration Engine (UAIE PRIME)  
**Parent architecture:** NINEFOLD INTRINSIC  
**Specialist intelligence and fusion:** AFI PRIME  
**First acquisition source:** [LM Studio Model Catalog](https://lmstudio.ai/models)  
**Status:** Governed candidate intake, AFI fusion, intrinsic acquisition-register persistence and local inventory adapter implemented; exact-head CI and live operational validation remain separate gates.

## Source and interface distinction

LM Studio provides three relevant surfaces:

1. **Public Model Catalog:** the website at `https://lmstudio.ai/models`, with model-family pages, descriptions, declared capabilities, local/cloud availability, artifact references, resource notes and licence statements where published.
2. **Official CLI:** `lms get` searches and downloads models. This is the supported user-facing acquisition route. The command requires an explicit model identifier and may present download choices.
3. **Native local REST API v1:** `GET /api/v1/models` inventories models already available on a specific LM Studio installation. It is not a complete public-catalog search API.

LM Studio's Hub terms restrict integrations to officially supported interfaces. UAIE therefore does **not** crawl or reverse-engineer the public website or Hub. It uses the officially supported `lms clone` command to obtain the catalog model's `model.yaml` metadata (which does not include model weights), safely parses that open specification, and then uses the documented local REST API to verify what is actually installed. A reviewed JSON candidate remains available when a user supplies metadata directly.

## Official metadata-only catalog acquisition

LM Studio documents that all models in its catalog are implemented using the cross-platform `model.yaml` specification. It defines the canonical `publisher/model` identity, concrete variants and sources, architectures, compatibility formats, parameter sizes, minimum memory, context lengths, vision/reasoning/tool-use declarations and runtime defaults.

The official command:

```bash
lms clone publisher/model
```

clones `model.yaml`, README and other metadata files without downloading model weights. UAIE provides `build_clone_command(candidate)` to prepare this command; it does not execute it.

After cloning, import the metadata:

```bash
uaie-lmstudio-model-yaml model.yaml --db uaie.sqlite3 --original-idea-value "Use UAIE PRIME and AFI PRIME to assimilate LM Studio model metadata."
```

This produces the UAIE assimilation record, AFI capability profile and acquisition-register entry. It preserves the original `model.yaml` metadata and maps the standard fields into the candidate profile. Model weights remain untouched.

## Implemented candidate intake

`universal_engine.lmstudio_catalog`:

- Validates a user-supplied model identifier, catalog detail URL, optional quantization, capability declarations, licence text, memory/context notes and artifact references.
- Rejects non-LM-Studio catalog URLs, credentials, query strings, fragments, invalid identifiers, unapproved capability keys and unapproved artifact hosts.
- Bounds metadata to 256 KiB and requires finite JSON-compatible data.
- Creates an official `lms get` command proposal without executing it.
- Persists the candidate through UAIE with the original catalog URL as provenance.
- Creates an intrinsic Universal Capability Acquisition Register entry linked to the UAIE record.
- Requires Original Idea Value and records potential market value, revenue models, development timeline, development/integration costs, risk assessment and evidence-verification status. Unassessed values are explicitly labelled.
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
    "original_idea_value": "Record the original user idea behind this acquisition.",
    "display_name": "Model Name",
    "catalog_url": "https://lmstudio.ai/models/model-name",
    "quantization": "Q4_K_M",
    "capabilities": {"vision": True, "reasoning": True, "tool_use": True},
    "metadata": {"reviewed_by": "operator"},
})

uaie = UniversalAcquisitionIntegrationEngine("uaie.sqlite3")
catalog_record, afi_profile_record, acquisition_entry = assimilate_catalog_candidate(uaie, candidate)
print(build_download_command(candidate))  # proposal only; does not execute
```

A reviewed candidate can also be imported from a local JSON file:

```bash
pip install -e .
uaie-lmstudio-catalog candidate.json --db uaie.sqlite3
```

The installed `uaie-lmstudio-catalog` command creates the UAIE record, AFI profile and acquisition-register entry, then prints the official command proposal. The core engine is also available as `uaie`.

After independently evaluating the candidate, an operator can update its assessment and advance both governed lifecycles:

```bash
uaie --db uaie.sqlite3 acquisition assess <record-id> --risk-assessment "Reviewed" --evidence-verification-status "INDEPENDENT_CHECK_PENDING"
uaie --db uaie.sqlite3 state <record-id> approved
uaie --db uaie.sqlite3 acquisition status <record-id> proposed
uaie --db uaie.sqlite3 acquisition status <record-id> under_evaluation
uaie --db uaie.sqlite3 acquisition status <record-id> approved
```

Only then can an operator deliberately start the official REST download:

```bash
uaie-lmstudio-catalog candidate.json --db uaie.sqlite3 --download --approved --record-id <record-id>
```

For a quantized Hugging Face artifact, add `--huggingface-url` with the exact artifact URL already recorded in the candidate. For a catalog identifier with quantization, use the reviewed `lms get` command proposal instead. The model.yaml intake command supports the same `--download --approved --record-id` flags after both lifecycles are approved.

Poll a returned job with:

```bash
uaie-lmstudio-status <job-id>
```

Quantization through the REST API is accepted only with an explicitly selected Hugging Face artifact URL; for a catalog identifier with a quantization suffix, use the reviewed CLI proposal. No download occurs during discovery, candidate intake or AFI fusion.

## Universal Capability Acquisition Register

Every catalog candidate is linked to a structured `acquisition_register` row in the UAIE SQLite database. Its lifecycle is governed separately from assimilation: `discovered → proposed → under_evaluation → approved → integrated`, with rejection and retirement paths. Register approval requires the corresponding UAIE assimilation record to be approved; register integration requires the UAIE record to be integrated. No candidate is automatically approved or integrated.

The register retains Original Idea Value, potential market value, revenue models, development timeline, development cost, integration cost, risk assessment and evidence-verification status. Default values such as `NOT_ASSESSED`, `PENDING` and `UNVERIFIED` are explicit placeholders, not claims.

## AFI PRIME fusion

AFI extracts explicit model facts and preserves the candidate's source, declared capabilities, model identity, quantization, parameter-size notes, memory/context information, artifact references and licence statement.

The profile is labelled `USER_SUPPLIED_CATALOG_METADATA` and `METADATA_ONLY_NOT_BENCHMARKED`. Publisher claims are not converted into verified capability claims. `performance_verified` and `integration_approved` remain false.

## Explicitly approved acquisition API

The official LM Studio native API documents `POST /api/v1/models/download` and `GET /api/v1/models/download/status/{job_id}`. UAIE exposes these as `download_model`, `download_catalog_candidate` and `get_download_status`.

The download function refuses to make a network request unless the caller passes the literal `approved=True`. The candidate wrapper also checks that the exact model candidate is stored in the UAIE register and that both the UAIE assimilation record and acquisition-register lifecycle have reached `approved`. It validates model identifiers, Hugging Face artifact URLs, quantization, loopback server location and response shape. It never loads the model into memory. The candidate wrapper additionally requires a Hugging Face URL to be one of the artifact links already reviewed in that candidate.

Example (this starts a real download only when deliberately executed against a running LM Studio host):

```python
import json
import os
from universal_engine.lmstudio_catalog import (
    candidate_from_mapping, assimilate_catalog_candidate,
    download_catalog_candidate,
)
from universal_engine.uaie import UniversalAcquisitionIntegrationEngine

with open("candidate.json", encoding="utf-8") as source:
    candidate_data = json.load(source)
uaie = UniversalAcquisitionIntegrationEngine("uaie.sqlite3")
candidate = candidate_from_mapping(candidate_data)  # reviewed JSON record
api_token = os.environ.get("LM_API_TOKEN")
catalog_record, afi_record, acquisition = assimilate_catalog_candidate(uaie, candidate)

# Approval is a deliberate operator action, not part of discovery.
uaie.set_state(catalog_record.record_id, "approved")
uaie.set_acquisition_lifecycle(catalog_record.record_id, "proposed")
uaie.set_acquisition_lifecycle(catalog_record.record_id, "under_evaluation")
uaie.set_acquisition_lifecycle(catalog_record.record_id, "approved")

job = download_catalog_candidate(
    uaie, candidate, catalog_record.record_id,
    approved=True, api_token=api_token,
)
print(job)
```

Do not set `approved=True` in unattended discovery or assimilation workflows.

## Local inventory adapter

`universal_engine.lmstudio` reads the documented native v1 endpoint `GET /api/v1/models` from an explicitly configured loopback server. It is read-only. It does not download weights, load/unload models, execute inference or change LM Studio configuration. Optional API tokens are read at runtime and never persisted.

The installed inventory command can inspect the local catalogue or persist the inventory and AFI profiles:

```bash
uaie-lmstudio-inventory
LM_API_TOKEN='your-token' uaie-lmstudio-inventory --ingest --db uaie.sqlite3
```

The `--ingest` mode is read-only with respect to LM Studio: it only reads model metadata and stores UAIE/AFI records. It does not download, load, unload or execute models.

This local API adapter is the post-acquisition verification step: it can confirm that a selected model appears in the local LM Studio inventory, but it does not by itself prove that the model performs well or is suitable for a particular Engine task.

## Governance and production gates

- Catalog discovery is user-directed until LM Studio provides an officially supported public catalog API or grants explicit integration permission.
- Model acquisition remains a human-approved action through LM Studio's official CLI.
- Licence text is captured as evidence only; it is not a legal determination.
- Hardware suitability, actual resource estimates, model performance and security must be independently evaluated.
- No model is integrated into the Universal Engine solely because it appears in the catalog or is downloaded.
- The user's mobile device is a control terminal; local model execution requires a supported LM Studio host.

## Verification required

- Deterministic unit tests cover candidate validation, command construction, provenance, AFI fusion and acquisition-register lifecycle gates without network access or downloads.
- Exact-head GitHub Actions must pass after the latest changes.
- A live local inventory smoke test requires a user-authorised LM Studio host and token if authentication is enabled.
- Production readiness requires an approved catalogue access method, robust register linkage, licence review, hardware/resource evaluation, independent model benchmarks, security review, audit/retention policy, backup/restore, monitoring and deployment documentation.

## Official references

- [LM Studio model.yaml specification](https://lmstudio.ai/docs/app/modelyaml) — the format used by catalog models, including variants and metadata overrides.
- [LM Studio: Publish a model.yaml](https://lmstudio.ai/docs/app/modelyaml/publish) — confirms that `lms clone` retrieves metadata only and does not download weights.
- [LM Studio Hub Terms of Use](https://lmstudio.ai/hub-terms) — integrations must use officially supported interfaces.
- [LM Studio CLI: `lms get`](https://lmstudio.ai/docs/cli/local-models/get) — official model search and download workflow.
- [LM Studio REST API: List Models](https://lmstudio.ai/docs/developer/rest/list) — official local model inventory contract.
- [LM Studio REST API: Download a Model](https://lmstudio.ai/docs/developer/rest/download) — official approval-gated model download job contract.
- [LM Studio REST API: Quickstart](https://lmstudio.ai/docs/developer/rest/quickstart) — API authentication and download-job overview.
- [LM Studio REST API overview](https://lmstudio.ai/docs/developer/rest) — supported local inference and model-management endpoints.

**Evidence rule:** specified, implemented, CI-tested, live-smoke-tested, independently verified and production-operational are distinct states.
