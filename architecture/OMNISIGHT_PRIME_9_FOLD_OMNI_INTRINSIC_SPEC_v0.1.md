# OMNISIGHT PRIME — 9 FOLD OMNI Intrinsic Architecture Specification

**Document ID:** UEE-OMNI-VISION-001  
**Version:** 0.1.0  
**Status:** Design specification; implementation not yet claimed  
**Parent architecture:** NINEFOLD INTRINSIC  
**Canonical fusion function:** UNIFIED FUSION SYNERGY — AFI PRIME  
**Canonical optimisation identity:** OMNIVELOCITY PRIME

> PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.

## 1. Purpose and scope

OMNISIGHT PRIME is the visual-perception and visual-intelligence capability lineage within 9 FOLD OMNI. It is designed as a fundamentally intrinsic part of NINEFOLD INTRINSIC: perception, adaptive fusion, provenance, governance, fault containment, resource awareness, verification and lifecycle traceability are architectural properties from inception, not optional plugins or later bolt-ons.

OMNI UNIVERSAL PERCEPTION INTELLIGENCE PRIME is the wider coordinating architecture for multiple authorised perception modalities. OMNISIGHT PRIME remains the specialist visual domain; the universal layer must not erase specialist boundaries or claim modalities that are not actually connected.

This document specifies architecture and contracts. It does not claim that the proposed visual runtime, Android application, camera pipeline, models, or integrations have been implemented or activated.

## 2. Constitutional invariants

1. **Intrinsic-by-design:** every applicable component is born with its required evidence, governance, security, lifecycle, observability, error-handling and AFI interoperability contracts.
2. **One canonical AFI PRIME function:** use the existing NINEFOLD INTRINSIC identity and model. Do not invent a competing AFI identity or treat AFI and Fusion Synergy as separate current components.
3. **Nine scoped instances:** the nine UMIC domains use the shared versioned fusion-function implementation through separately scoped instances, each with its own execution context, state boundary, evidence trail and fault-containment domain.
4. **No implicit authority:** fusion does not grant permissions. Cross-domain access is explicit, least-privilege, policy-checked and audited.
5. **Specialist independence:** engines retain their identities, provenance, performance measures, limitations and ability to disagree.
6. **Evidence before assertion:** direct observations, model interpretations, inferences and independently verified conclusions are distinct record types/statuses.
7. **Uncertainty is first-class:** confidence is calibrated where possible; uncertainty, missing data and conflicting interpretations remain visible.
8. **Fail safely:** unavailable or degraded components cannot silently lower assurance or broaden permissions.
9. **Evolution is governed:** discovery and proposal do not imply approval, integration, deployment or self-modification authority.
10. **No artificial capability ceiling:** the architecture can discover and evaluate future capabilities without bypassing governance, compatibility, security or verification gates.

## 3. Nine intrinsic visual capability domains

These are capability domains, not new Major Divisions or Systems. Their final register mapping must be approved through the independent 9 Major Division, 90 System, 184 Architecture Entry and 18 Responsibility Layer registers. Do not assign register numbers by symmetry.

1. **Acquisition:** authorised screen, image, video, camera and connected visual-source acquisition; session lifecycle; source identity; timestamps; orientation; frame scheduling; permission and revocation handling.
2. **Processing:** image normalisation, enhancement, denoising, cropping, segmentation, feature extraction, deduplication, change detection and resource-aware preprocessing.
3. **Recognition:** OCR, objects, icons, controls, documents, diagrams, charts, symbols, handwriting and anomaly candidates; outputs retain engine identity and confidence.
4. **Spatial intelligence:** image coordinates, bounding regions, relative geometry, layout, tracking, viewpoint alignment, depth estimates and 3D reconstruction where input evidence supports them.
5. **Perceptual reasoning:** scene and interface understanding, visual question answering, comparative reasoning, hypothesis generation, causal investigation and ambiguity management.
6. **Temporal intelligence:** frame-to-frame continuity, event sequences, state changes, movement tracks, before/after comparison and time-indexed observations.
7. **Context and memory:** evidence-linked entities, relationships, histories, user-approved retained context, retrieval, correction, expiry and deletion workflows.
8. **Interaction and autonomy:** goal-directed selection of regions and tools, requests for additional authorised evidence, user guidance and permission-gated actions.
9. **Assurance and evolution:** independent verification, calibration, red-team challenge, performance evaluation, lifecycle governance, rollback and capability discovery.

All nine domains interoperate through versioned contracts. A domain may be deployed separately for fault isolation, but it must not become architecturally isolated.

## 4. Intrinsic OMNI AFI PRIME fusion contract

Every specialist engine must expose a versioned capability manifest and accept/return validated, bounded messages. Minimum manifest fields:

- capability_id and semantic_version;
- owner/domain and supported operations;
- input/output schema references;
- supported modalities, formats and languages;
- model/algorithm identity and artifact digest where available;
- runtime requirements and resource estimates;
- known limitations and unsupported conditions;
- security classification and required permission scopes;
- test-suite and benchmark references;
- lifecycle state and provenance.

Minimum observation envelope:

- observation_id and correlation_id;
- source_id and source timestamp;
- capture/session reference and source provenance;
- region geometry in a declared coordinate frame;
- content type and structured result;
- producing engine and exact version;
- confidence/calibration metadata and uncertainty;
- evidence references and transformation history;
- limitations, warnings and status;
- schema version.

AFI responsibilities:

1. validate manifests and message schemas;
2. select eligible engines using policy, capability, latency, memory and quality constraints;
3. correlate observations without losing their provenance;
4. detect contradictions, duplicates, stale data and coordinate-frame mismatches;
5. preserve minority findings and unresolved disagreement;
6. request additional evidence when expected value justifies the cost and permission exists;
7. produce a fusion record that links every conclusion to source observations and transformations;
8. report degraded mode, unavailable engines and resource costs;
9. never approve its own high-impact action or certify its own result as independently verified.

Retrieved documents, images, model outputs and tool responses are untrusted data, never executable instructions. Tool selection and actions are governed outside model-generated content.

## 5. Visual Evidence Fabric (VEF)

The Visual Evidence Fabric is the authoritative evidence plane for visual claims. It is append-oriented and provenance-preserving. Corrections create linked superseding records; they do not silently rewrite historical observations.

Minimum record classes:

- **SourceRecord:** source identity, capture consent/session, timestamp, media metadata, content digest and retention classification.
- **ObservationRecord:** what a named engine reported, region, schema, confidence and limitations.
- **TransformationRecord:** crop, resize, enhancement, OCR preprocessing, conversion or other derived-media operation, with parameters and parent digest.
- **FusionRecord:** inputs, AFI version, selection rationale, conflict handling and resulting assertions.
- **InferenceRecord:** hypothesis, supporting and contradicting evidence, assumptions and uncertainty.
- **VerificationRecord:** verifier identity, independence boundary, method, test inputs, result and limitations.
- **DecisionRecord:** user or authorised governance decision, scope, timestamp and policy basis.

Evidence integrity requirements:

- cryptographic content digests for retained source artefacts;
- stable identifiers and explicit parent/child links;
- append-only event semantics with sequence checks;
- schema and algorithm version capture;
- access-control and retention audit;
- tamper-evident local records, with external anchoring only when separately designed and approved;
- deletion and privacy controls that can remove personal data where required while retaining only legally and ethically permissible audit metadata.

A hash chain detects certain modifications; it is not proof against a privileged host administrator and is not a substitute for independent storage, signatures, access controls or external anchoring.

## 6. Universal Visual World Model (UVWM)

The World Model is a versioned, evidence-linked graph/state model. It represents what has been observed and what is inferred without conflating the two.

Core entity types:

- Entity, Object, Component, Person, Document, InterfaceElement, Place and Environment;
- Attribute and State;
- SpatialRelation and FunctionalRelation;
- Event and Activity;
- Observation, Hypothesis, Assertion and Verification;
- Source and EvidenceArtifact.

Every assertion must include:

- assertion_id and schema version;
- subject, predicate and object/value;
- assertion type: observed, interpreted, inferred or verified;
- valid-time and recorded-time;
- supporting and contradicting evidence links;
- originating engine(s) and fusion record;
- uncertainty/confidence and calibration provenance;
- scope, source permissions and retention policy;
- supersession/retraction links where corrected.

Spatial values must declare coordinate frames and units. Depth, distance, dimensions, identity, intent and causality must not be asserted beyond what the input modality and calibration support. A single ordinary image does not guarantee metric depth or complete 3D reconstruction.

## 7. Active perception and investigation

OMNI VISUAL AUTONOMY PRIME is a goal-directed perception planner, not an unrestricted actor.

Cycle:

1. receive a user goal or authorised task;
2. inspect available evidence and permissions;
3. identify uncertainty and missing observations;
4. generate candidate observation actions;
5. estimate information gain, risk, latency, energy and memory cost;
6. choose a policy-permitted action;
7. request user approval when required;
8. acquire and process new evidence;
9. update the evidence fabric and world model;
10. stop when the task's evidence threshold is met, a limit is reached, or further action is not justified.

No action may bypass Android capture consent, application permissions, accessibility-service policy, user confirmation or platform security controls. Accessibility APIs are used only for legitimate, user-authorised accessibility purposes. Screen actions with external consequences require explicit confirmation and post-action verification.

## 8. Specialist capability ecosystem

The registry may host specialist engines for OCR, document understanding, diagram/blueprint interpretation, mechanical systems, electronics, materials, handwriting, charts, video, aerial/satellite imagery, scientific imaging, visual search, object tracking, segmentation, depth estimation, image forensics and visual simulation.

Each candidate is independently evaluated for:
- task accuracy and calibration;
- robustness and failure modes;
- latency, peak memory, energy and thermal impact;
- offline capability and network requirements;
- model/data provenance and licence compatibility;
- privacy, security and attack surface;
- Android ABI/runtime compatibility;
- maintenance, reproducibility and rollback.

No model family or vendor is mandatory. Model choice is replaceable and evidence-led.

## 9. Resilience, privacy and resource intelligence

- deny by default for unregistered capabilities and unauthorised actions;
- isolate untrusted parsers and model/tool outputs;
- enforce bounded input sizes, timeouts, cancellation and backpressure;
- use circuit breakers and explicit degraded-mode declarations;
- preserve evidence when a downstream reasoning engine fails;
- support local-first lightweight acquisition and processing;
- make remote inference optional, authenticated, encrypted and explicit;
- never expose credentials in client-side configuration or logs;
- provide user-visible capture indicators and immediate session revocation;
- apply data minimisation, retention limits and user-controlled deletion;
- measure RAM, CPU, GPU/NPU availability, battery, thermal state, latency and storage before scheduling workloads.

For the initial OPPO A6 4 GB target, treat the phone as a constrained control/perception endpoint: prioritise capture, frame sampling, change detection, lightweight OCR and compact local records. Benchmark before selecting any on-device VLM. Do not assume large vision models will fit or run responsively. Heavy inference may be delegated only through an explicitly configured and secure remote service.

OMNIVELOCITY PRIME optimises throughput subject to accuracy, safety, evidence integrity, privacy and resource constraints; speed never overrides these invariants.

## 10. Technology evaluation candidates (not commitments)

- Android capture: MediaProjection and ImageReader, subject to current Android version and consent lifecycle.
- Android application: Kotlin; Jetpack Compose for UI.
- Image processing: OpenCV.
- OCR: RapidOCR, PaddleOCR, Tesseract and platform-native options benchmarked against target devices and languages.
- Detection/stream processing: MediaPipe and compatible ONNX/LiteRT models.
- Model runtime: ONNX Runtime, LiteRT, llama.cpp or MLC only after device-specific compatibility and benchmark evaluation.
- Persistence: SQLite for local metadata and evidence indexes; content-addressed artefact storage with explicit retention controls.
- Contracts: versioned JSON Schema or equivalent typed schemas; validate at every trust boundary.

Licences, model weights, training-data terms, export restrictions, maintenance and security advisories must be checked for each selected version before integration.

## 11. Verification and acceptance gates

A capability is not complete because it has a manifest or a passing unit test. Each release candidate must include reproducible evidence.

Minimum acceptance suite:

1. capture requires consent and stops on revocation;
2. frame acquisition handles rotation, resize, lifecycle interruption and resource release;
3. OCR returns text, geometry, engine/version and calibrated or explicitly uncalibrated confidence;
4. all observations link to source evidence and transformation history;
5. fusion preserves provenance and exposes conflicting specialist outputs;
6. malformed, oversized and adversarial inputs fail safely;
7. coordinate transforms and spatial relations pass known-ground-truth fixtures;
8. temporal tracking handles dropped frames, occlusion and identity uncertainty;
9. world-model assertions distinguish observations, inferences and verified facts;
10. memory retention, access, correction and deletion controls work;
11. unregistered or unauthorised engines/actions are denied;
12. engine crash, timeout and offline scenarios preserve evidence and enter explicit degraded mode;
13. performance tests measure peak RAM, latency, energy, thermal behaviour and storage on the target phone;
14. independent verification is performed by a component/service that did not produce the result being certified.

Report false positives, false negatives, calibration, coverage, failure cases and environmental limits. No blanket claim of visual understanding is accepted from a narrow fixture suite.

## 12. Delivery batches

**Batch A — Contract and governance foundation**
- approve architecture/register mapping;
- define schemas, capability manifests and lifecycle rules;
- threat model and privacy/permission model;
- create fixtures and contract validators.

**Batch B — Evidence and world-model core**
- implement VEF record types and local persistence;
- implement UVWM entities/assertions and provenance links;
- implement conflict and supersession semantics;
- test integrity, access, retention and deletion.

**Batch C — Android acquisition vertical slice**
- Kotlin capture session using MediaProjection;
- frame sampling/backpressure and OpenCV preprocessing;
- OCR adapter and geometry;
- evidence records for every transformation and observation.

**Batch D — AFI orchestration**
- specialist registry and policy-filtered dispatch;
- correlation, fusion, contradiction handling and degraded mode;
- independent verification interface.

**Batch E — Active perception and advanced specialists**
- goal-directed evidence planning;
- temporal/spatial reasoning;
- document, diagram and mechanical specialist evaluations;
- optional remote inference with secure configuration.

**Batch F — Device validation and controlled release**
- benchmark on actual target hardware;
- accessibility, privacy and security review;
- regression, resilience and independent verification;
- staged release only after explicit approval.

Batches may be parallelised where dependencies permit. Shared schemas and governance contracts are prerequisites for downstream integration.

## 13. Definition of done

The architecture is not declared implemented or operational until:
- approved register mappings and traceability are present;
- the code implements the versioned contracts;
- reproducible automated and device tests pass;
- security, privacy, licence and dependency reviews are recorded;
- resource budgets are measured on target hardware;
- failure and rollback paths are demonstrated;
- independent verification evidence is recorded;
- release authority explicitly approves the deployment.

Until then, status remains **DESIGN SPECIFIED / IMPLEMENTATION PENDING**.
