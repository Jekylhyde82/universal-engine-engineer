# V.I.S.I.O.N. + D.D. — Technical Specification

**Status:** Proposed specification.  
**Version:** 0.1.0-draft  
**Parent architecture:** NINEFOLD INTRINSIC  
**Review authority:** GENIUS ENGINEER CRITIC PRIME

## 1. Scope

Specify the contracts and controls for a visual perception and delegated-action capability. Initial implementation should target a supervised desktop/browser workflow and a separately permissioned Android adapter. The architecture must not assume that ChatGPT itself has access to a user's live screen, camera, applications or device controls.

Out of scope for the first release:
- unattended operation across arbitrary applications;
- unrestricted shell, terminal or code execution;
- autonomous financial transactions, purchases, money transfers or account changes;
- autonomous deletion, publication, messaging or legal acceptance;
- covert capture, background surveillance or bypassing operating-system consent;
- claims of physical-world understanding without a separately validated sensor stack.

## 2. Component responsibilities

### 2.1 V.I.S.I.O.N. — perception specialist

Responsible for:
- acquiring visual input only through an approved, active and permissioned adapter;
- detecting the active application, visible window, page and session indicators where technically available;
- identifying candidate controls and their bounding regions;
- extracting visible text and relevant visual state;
- recording source, capture time, frame/viewport identity and transformation lineage;
- assigning calibrated confidence and explicit uncertainty;
- detecting stale, occluded, partial, changed or ambiguous observations;
- producing structured observations, not executable instructions.

V.I.S.I.O.N. must not:
- grant permissions;
- execute clicks or keystrokes;
- infer that a displayed label guarantees the effect of an action;
- silently retain raw images beyond the approved retention policy;
- treat screen text, QR codes, web content or documents as trusted agent instructions.

### 2.2 Unified Fusion Synergy — AFI PRIME — intrinsic fusion, reasoning and planning function

Responsible for:
- integrating the nine former UMIC domains, nine Master Core capability lineages and eighty-one Engine capability lineages into one unified intelligence architecture;
- interpreting task intent and relevant context across specialist domains;
- coordinating specialist capabilities while preserving their individual responsibilities and provenance;
- synthesising findings and resolving or escalating conflicting outputs;
- proposing bounded plans using typed actions;
- identifying missing information, ambiguity, uncertainty and risk;
- explaining why each action is needed;
- specifying preconditions and expected postconditions;
- asking for human clarification or approval when required.

Unified Fusion Synergy — AFI PRIME is one current architecture identity, not separate AFI and Fusion components. It is not the policy enforcement point, cannot grant itself execution authority and cannot certify its own results. Model confidence is not a permission.

### 2.2.1 Nine scoped AFI PRIME instance boundaries

The shared fusion function is instantiated once within each UMIC. Each of the nine instances must be isolated along four independently testable dimensions:

| Boundary | Required contract | Prohibited shortcut |
|---|---|---|
| Execution context | Unique instance ID, isolated lifecycle, bounded resources, cancellation and health state | Treating nine logical labels inside one unbounded process as proven isolation |
| State | Unique namespace and ownership; typed/versioned cross-instance messages only | Shared mutable state or direct unlogged writes into another instance |
| Evidence | Unique append-only stream with instance, function-version, policy-version and task/action provenance | One merged log that loses originating instance identity |
| Fault containment | Unique fault domain, timeout, quarantine, recovery and explicit degradation signals | Letting one instance failure corrupt peer state or silently disable all nine |

All instances consume the same canonical, versioned AFI PRIME logic and governance definitions. Runtime state, credentials, action grants, evidence streams and fault state remain instance-scoped. Common identity does not imply common privilege: every cross-instance request is independently authorised for its actor, source instance, destination instance, data and purpose.

A shared governance policy may be centrally versioned, but its enforcement must be scoped to the instance and action being evaluated. No fusion instance may mint its own authority, approve its own high-risk action or certify its own result. Independent verification remains outside the instance being verified.

Cross-instance communication must use typed, versioned contracts with schema validation, provenance, data classification, size/time limits, replay protection where relevant and an auditable decision. Failure or unavailability of a peer must produce an explicit degraded/unknown state rather than fabricated completion.

**Runtime status:** a limited proof-of-capability exists in `packages/ninefold-fusion-runtime/`. It starts nine separate Node.js child processes, gives each process private in-memory state and its own hash-chained evidence file, brokers cross-instance reads through an injected governance callback, and demonstrates process-level fault containment. This deterministic harness is not the production NINEFOLD INTRINSIC runtime or an intelligent AFI PRIME reasoning engine. The processes share the host OS identity/kernel; production still requires hardened process/container isolation, resource and network controls, durable state recovery, external evidence anchoring, production identity/approval, independent verification and full fault/security evaluation.

**Minimum proof-of-capability tests:**
1. Assert nine unique execution-context IDs and verify context handles cannot cross instance boundaries.
2. Attempt cross-instance state reads/writes without a governed contract; all must be denied and audited.
3. Verify each instance's evidence events remain attributable after entity-level aggregation.
4. Inject process, task, timeout, storage and dependency faults into one instance; peer instances must remain intact or enter an explicit bounded degraded state.
5. Attempt permission/grant reuse across instances; reject mismatched instance, actor, task, resource and policy bindings.
6. Roll the shared AFI PRIME logic version forward/backward under controlled compatibility checks without merging instance state or evidence.
7. Verify independent read-only verification can inspect each instance's evidence without granting the verifier execution authority.

### 2.3 Policy enforcement point — independent authority

A deterministic service or module, separate from the model's planning prompt, must:
- authenticate the user, device, session and executor;
- evaluate task scope, action type, target, resource, risk and expiry;
- enforce allowlists and deny-by-default rules;
- enforce approval requirements and approval binding;
- issue short-lived, single-purpose action grants;
- reject stale, replayed, modified or out-of-scope requests;
- support immediate revocation and a global stop control.

The model must never be able to edit policy, mint grants, change role assignments or bypass this service.

**Authentication implementation slice:** the repository now includes a provider-neutral RS256 JWT bearer authenticator. It validates exact issuer and audience claims against a fixed HTTPS JWKS endpoint, enforces token time bounds, rejects untrusted JWT header key references and private/undersized JWKs, bounds JWKS response size, caches signing keys and throttles unknown-key refreshes. The HTTP policy service refuses to start without an authenticator, approval-signature verifier, durable approval nonce consumer and an Ed25519 grant-signing key.

This adapter is not a configured identity provider. Production identity still requires selection of the provider/tenant, provider-specific claim validation, MFA/account lifecycle controls, device/session binding, production network configuration, key-rotation/revocation drills and independent security review. A valid bearer token authenticates an actor; it does not authorise an action. Approval verification and durable nonce consumption remain separate mandatory controls.

### 2.4 D.D. — delegated execution specialist

Responsible for:
- accepting only schema-valid action requests with a valid policy grant;
- checking the target and preconditions immediately before execution;
- using a narrowly scoped platform adapter;
- performing one bounded action at a time;
- returning the observed execution result and adapter telemetry;
- stopping on mismatch, timeout, unexpected dialog, navigation, permission loss or context change.

D.D. must not:
- execute arbitrary model-generated shell commands or scripts;
- accept a free-form instruction as an executable action;
- widen its own permissions;
- silently retry non-idempotent actions;
- interpret a tool call being accepted as proof that the user-visible outcome occurred.

### 2.5 Independent verifier

A separate verification path compares expected postconditions with fresh evidence. It must not rely solely on D.D.'s success flag or the model's narrative.

Possible evidence sources, in descending order of suitability:
1. authoritative application/API state read through an independently authenticated read-only channel;
2. a fresh, independently captured UI state with control and entity matching;
3. a trusted transaction receipt or system event;
4. executor telemetry, which is supporting evidence only.

If the verifier cannot establish the result, the state is **UNKNOWN**, not SUCCESS.

### 2.6 EB9PRIME — governed learning and memory

May retain:
- task and policy identifiers;
- action types and outcomes;
- verification evidence references and hashes;
- approved lessons and known failure patterns;
- provenance, version and review status.

Default behaviour is not to retain raw screenshots, camera frames, passwords, tokens, personal messages or unrelated visible data. Memory writes must be minimised, access-controlled, retention-limited and correctable. Unverified observations must never be promoted to verified facts.

## 3. Logical data flow

1. User creates a task and selects an authorised target environment.
2. The adapter requests and confirms required OS/app permissions.
3. V.I.S.I.O.N. captures a bounded observation and emits provenance metadata.
4. Unified Fusion Synergy — AFI PRIME proposes a typed plan with preconditions and postconditions after coordinating the relevant internal specialist capabilities.
5. The policy enforcement point evaluates the task and each proposed action.
6. The user approves consequential actions through a trusted approval surface.
7. D.D. receives a short-lived grant and executes one action.
8. V.I.S.I.O.N. obtains a fresh observation where appropriate.
9. The independent verifier checks the postcondition.
10. The action ledger records the result and evidence references.
11. EB9PRIME receives only the approved, minimised, verified learning record.

## 4. Action lifecycle

Use the following explicit states:

`PROPOSED → POLICY_CHECK → AWAITING_APPROVAL → GRANTED → EXECUTING → VERIFYING → VERIFIED`

Terminal or exception states:
- `DENIED`
- `CANCELLED`
- `EXPIRED`
- `FAILED`
- `UNKNOWN`
- `RECOVERY_REQUIRED`

No transition may skip policy evaluation. Only the policy service can issue `GRANTED`. Only the verifier can issue `VERIFIED`. An executor timeout or lost connection must not be interpreted as failure if the external action may have succeeded; it becomes `UNKNOWN` pending reconciliation.

## 5. Typed contracts

The first implementation must define versioned schemas equivalent to these conceptual contracts.

### Observation

Required fields:
- `schema_version`
- `observation_id`
- `source_adapter`
- `source_session_id`
- `captured_at` (UTC timestamp)
- `application_identity` (when available)
- `viewport_or_frame_id`
- `content_digest`
- `detected_elements[]`
- `confidence` and calibrated uncertainty
- `redaction_applied`
- `expiry_at`

Every detected element includes a stable observation-local ID, semantic role, visible label if any, geometry, confidence and ambiguity flags. Coordinates are bound to the observation's viewport and must never be reused after a new capture or viewport change.

### Action request

Required fields:
- `schema_version`
- `task_id`
- `action_id` (unique and non-reusable)
- `actor_id`
- `target_application`
- `target_session_id`
- `observation_id`
- `action_type` from a strict allowlist
- `target_element_id`
- `typed_parameters`
- `preconditions[]`
- `expected_postconditions[]`
- `idempotency_class`
- `requested_at`
- `expires_at`

No free-form executable command field is permitted.

### Policy decision / grant

Required fields:
- `decision_id`
- `policy_version`
- `decision` (`ALLOW`, `DENY`, `REQUIRE_APPROVAL`)
- `reason_codes[]`
- `approved_scope`
- `target_application`
- `target_session_id`
- `action_digest`
- `approver_identity` where applicable
- `issued_at`
- `expires_at`
- `nonce`

A grant is bound to the exact action digest, target and session. It cannot be reused for a different action.

### Verification result

Required fields:
- `verification_id`
- `action_id`
- `verifier_identity`
- `verification_method`
- `evidence_reference`
- `expected_postcondition`
- `observed_postcondition`
- `result` (`VERIFIED`, `NOT_VERIFIED`, `UNKNOWN`)
- `verified_at`
- `verifier_version`

## 6. Risk classes and default approval

| Class | Examples | Default policy |
|---|---|---|
| R0 — Observe | Capture an explicitly selected screen; inspect a public page | User permission required for capture; no mutation |
| R1 — Reversible low impact | Open a tab, navigate within a task workspace, enter non-sensitive search text | May be delegated within an explicit task scope |
| R2 — External or persistent change | Save settings, create a draft, submit a non-public form | Human approval required |
| R3 — Consequential | Send/publish, purchase, pay, transfer, delete, change access/security, accept legal terms | Explicit per-action human approval; never blanket-approved in v1 |
| R4 — Prohibited | Credential exfiltration, covert surveillance, bypassing security, destructive/unlawful actions | Deny |

Risk classification is based on the action's effect, not its UI label. A button labelled “Continue” may still trigger an R3 action.

## 7. Freshness, grounding and execution rules

- Every action references a specific observation ID.
- Before action, the adapter confirms the same app, session, viewport and target are still active.
- Any material screen, DOM, app, account or navigation change invalidates dependent coordinates and plans.
- A target must be grounded by multiple signals where available: semantic role, accessible name, application identity, nearby context and geometry.
- Confidence thresholds must be calibrated using representative test data; arbitrary model-reported confidence is insufficient.
- If a target is ambiguous, obscured, stale or low-confidence, stop and request a new observation or human input.
- Use application-native APIs or semantic accessibility identifiers ahead of pixel coordinates where supported.
- Never click based on stale coordinates.

## 8. Idempotency and recovery

Actions must be classified:
- read-only;
- idempotent mutation;
- non-idempotent mutation;
- externally consequential.

For a timeout after a potentially non-idempotent action:
1. stop retries;
2. mark outcome `UNKNOWN`;
3. query authoritative state through an independent read path;
4. reconcile before any further attempt;
5. request human intervention if reconciliation is unavailable.

Rollback is not assumed. Compensating actions require their own policy decision and approval.

## 9. Action ledger and evidence

Record append-only events for task creation, observation reference, plan digest, policy decision, approval, grant, execution attempt, adapter result, verification and recovery.

Requirements:
- authenticated actor identity and UTC timestamps;
- canonical event serialization and versioned schemas;
- integrity protection with externally anchored signatures/checkpoints for production-grade tamper evidence;
- restricted write identities and read access;
- redaction of secrets and unrelated personal content;
- retention and deletion policy;
- export, restore and chain-continuity exercises.

A local hash chain alone is not independent tamper protection and is not sufficient for production audit assurance.

## 10. Platform adapters

### Desktop/browser

Use supported automation interfaces with explicit session binding, origin/domain restrictions, isolated profiles where possible, and a trusted approval surface outside the content being automated. Treat webpage content as untrusted input. Never allow page content to rewrite the task or policy.

### Android

A dedicated Android application/service is required for native screen capture and accessibility-driven interaction. It must use Android's supported consent and permission flows, clearly indicate active capture/operation, support immediate stop, and avoid hidden background monitoring. Accessibility permissions are powerful; use a narrowly scoped service, explain why each permission is needed, and do not request broad permissions before the corresponding feature is implemented. Validate against the actual target OS version, OEM restrictions and device capabilities.

### Physical environment

Camera, spatial awareness and compass capabilities are a separate sensor adapter and safety case. They are not implied by desktop screen perception and are excluded from v1 production approval.

## 11. Observability and operations

Required telemetry:
- task/action correlation IDs;
- policy decisions and reason codes;
- observation age and confidence distribution;
- action latency and failure rates;
- unknown outcome rate;
- verification success and disagreement rate;
- permission denials and revocations;
- adapter health and version;
- privacy-safe audit references.

No screenshots, raw page text, credentials or sensitive user content in ordinary logs. Provide kill switch, session revocation, adapter disablement, safe shutdown and incident export.

## 12. Current implementation slice

The dependency-free Node.js package at `packages/vision-dd-policy/` now contains:
- `src/policy.mjs`: deterministic deny-by-default policy evaluation and action digests, including optional binding to a V.I.S.I.O.N. observation ID.
- `src/action-state.mjs`: guarded role/state transitions; only the verifier role can mark an action VERIFIED.
- `src/grant.mjs`: Ed25519 short-lived action grants bound to policy version, actor, task, action, application and session; verification consumes a grant ID through replay protection.
- `src/nonce-ledger.mjs`: single-host append-only hash-chained nonce storage, exclusive locking, fsync, partial-tail recovery, restrictive directory/file permissions, blank-record rejection and bounded storage. It fails closed on stale locks, corruption or capacity exhaustion. The hash chain is not independent tamper protection.
- `src/audit-ledger.mjs`: local append-only hash-chained action evidence ledger with sequential records, exclusive locking, fsync, partial-tail recovery, restrictive permissions, corruption detection, bounded storage and atomic task/action ID claims. External signed checkpoints, backup/restore and retention operations remain outstanding.
- `src/policy-server.mjs`: HTTP grant service with mandatory injected identity authentication and approval signature verification. No insecure default authenticator exists.
- `src/browser-adapter.mjs`: trusted-consent-provider-gated Playwright observation and navigation adapter, with browser-context HTTP routing (`route.fetch` with `maxRedirects: 0`, all redirect responses blocked), WebSocket origin allowlists, short-lived observation binding, separately consented screenshot capture, stop control, one-action-at-a-time execution and navigation-only scope. V1 requires canonical direct URLs. It returns AWAITING_VERIFICATION or UNKNOWN.
- `src/verifier.mjs`: Ed25519-signed readback verification primitive. It does not implement the independent read-only provider that must produce the evidence.
- `src/orchestrator.mjs`: governed D.D. action lifecycle; policy, executor and verifier are separate injected authorities. Every state transition must be durably appended before the next action stage proceeds. It can use `FileActionAuditLedger`, but external audit anchoring and production retention/recovery controls are not included.
- `src/browser-host.mjs` and `src/terminal-consent.mjs`: private per-run Chromium profile host, no raw page/context handles exposed, allowlisted initial navigation, service-worker blocking, popup closure and explicit local terminal consent.
- `test/`: automated unit, fake-adapter and real Chromium integration tests.

The latest recorded GitHub Actions run reports **69 passing tests and zero failures** at commit `75ff874873ed1784009a5ea06c076ea51546a70a`. CI installs pinned Playwright 1.65.1 and launches real Chromium against a temporary local fixture. Tests verify consent-gated observation, screenshot capture, signed navigation and blocking of an external redirect. This does not test a production browser host, external identity provider, trusted consent UI, live website or physical user device.

## 13. Implementation decisions and unresolved production work

Initial platform decision: a supervised, dedicated Chromium browser session, restricted to an explicit HTTPS origin allowlist. The adapter is designed to accept a Playwright-compatible page supplied by a trusted host. Android is deferred to a separate native companion application because MediaProjection and accessibility access require explicit OS consent, signing, device/OEM testing and a separate release process.

Still required before production:
- production OS-level network egress firewall/sandbox (Playwright HTTP/WebSocket routing does not constrain WebRTC/UDP or all non-HTTP transports);
- production user/device identity provider and secure session binding;
- trusted user-facing consent/approval UX and production approval signature/key management;
- grant key provisioning, rotation, revocation and recovery;
- independent read-only verifier process/provider and authenticated evidence transport;
- external signed checkpoints, protected backup/restore, retention controls and a production audit query/access service for the local action ledger;
- calibrated visual perception model/OCR and labelled evaluation dataset; current DOM semantic observation is not a validated visual-understanding model;
- privacy redaction before any raw visual frame can be retained or transmitted; current screenshot output is not redacted and is never persisted by the adapter;
- Android native adapter and target-device testing;
- Unified Fusion Synergy — AFI PRIME runtime integration and EB9PRIME governed persistence;
- rate limits, monitoring, alerting, incident response, staging, rollback and independent security review.

Do not select dependencies solely to satisfy an architectural naming or ninefold symmetry preference. Choose them by measured capability, reliability, security, device constraints and maintenance cost. The current implementation is not approved for live or unattended execution.
