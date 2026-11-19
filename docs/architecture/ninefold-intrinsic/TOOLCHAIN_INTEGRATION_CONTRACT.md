# NINEFOLD INTRINSIC — Toolchain Integration Contract

**Authority:** NINEFOLD INTRINSIC  
**Execution delegate:** DESIGNATED DRIVER (D.D.)  
**Evidence discipline:** PROOF BEFORE CLAIM. EVIDENCE BEFORE CONFIDENCE. VERIFICATION BEFORE COMPLETION.  
**Status:** Architecture contract; integrations are not yet deployed as one automated pipeline.

## 1. Purpose and scope

This contract defines how the connected engineering services may support NINEFOLD INTRINSIC without becoming competing authorities or bypassing its governance. It covers GitHub, Lovable, Supabase, Vercel, Figma, Canva and Gmail.

A connected account or callable connector is an available tool surface, not proof that a production integration exists. Each service must be explicitly bound to a project, environment, identity, permission set and evidence record before operational use.

## 2. Canonical service responsibilities

| Service | Permitted responsibility | Must not become |
|---|---|---|
| GitHub | Canonical source, version history, code review, issues, CI, security scans, release provenance | A production approval authority merely because CI is green |
| Lovable | Rapid application scaffolding, UI iteration, prototype generation and preview | The canonical source of truth unless its output is exported, reviewed and committed to Git |
| Supabase | PostgreSQL data, Auth, Storage, Realtime and server-side functions where selected | A place for unreviewed public tables, broad service-role exposure or implicit trust |
| Vercel | Hosting and deployment for explicitly linked, approved projects | An automatic production release path from an unreviewed branch |
| Figma | Design source, component and interaction specifications, design review | Runtime authority or a substitute for implementation tests |
| Canva | Approved visual assets, diagrams, documents and presentation outputs | A source of executable code, secrets or authoritative engineering state |
| Gmail | Human correspondence, notifications and approval requests | A machine-verifiable approval token or an unattended execution channel |

## 3. Intrinsic specialist responsibilities

The following identities remain distinct inside the NINEFOLD INTRINSIC governance model:

- **GENIUS ENGINEER CRITIC PRIME:** challenges assumptions, detects omissions and tests the strength of claims. Critique does not itself authorise a change.
- **AFI PRIME:** performs analysis, evaluates alternatives and prepares evidence-backed recommendations. It cannot grant its own execution authority.
- **V.I.S.I.O.N.:** analyses only explicitly authorised visual inputs; observations carry source, timestamp, scope and uncertainty. Observation is not permission.
- **D.D.:** performs bounded, typed actions only after independent policy authorisation. It cannot widen its own permissions or convert a plan into authority.
- **EB9PRIME:** preserves governed continuity and approved evidence with provenance, minimisation, retention and correction controls. It is not a raw-data dumping ground.
- **UPN PRIME:** supplies the offline-first communications and local-service architecture. Public cloud services are optional upstream capabilities, not dependencies for core offline operation.

All components remain subordinate to NINEFOLD INTRINSIC policy, lifecycle governance and the evidence/verification registers. No service integration dissolves these specialist boundaries.

## 4. End-to-end delivery flow

1. **Discover:** identify a requirement, candidate capability or defect. Record its source and uncertainty.
2. **Critique:** challenge the requirement, assumptions, security implications, cost and alternatives.
3. **Design:** record the approved interaction and system design in Figma or a versioned architecture document.
4. **Prototype:** use Lovable where it accelerates exploration. Label generated work as prototype until reviewed.
5. **Implement:** move accepted source into the canonical GitHub repository and branch. Pin dependencies and preserve provenance.
6. **Backend:** use Supabase only after the project, data classification, schema, RLS policies, Auth model, secrets and backup model are approved.
7. **Validate:** run automated tests, static analysis, dependency/licence checks, security checks and independent acceptance tests against an exact commit and artifact digest.
8. **Review:** record human review, unresolved risks, policy decisions and required approvals. CI success is necessary but not sufficient.
9. **Deploy:** Vercel may deploy only the approved repository/project/environment and exact reviewed commit. Production requires a separate explicit release decision.
10. **Communicate:** Gmail may carry notifications and human approval requests. Approval must be recorded through an authenticated, scoped approval mechanism; email delivery or reply text alone is not cryptographic authority.
11. **Publish assets:** Canva outputs are versioned or archived with source and licence provenance where applicable.
12. **Verify and learn:** verify deployed identity, health, rollback and outcomes independently. Only minimised, verified records may be promoted into EB9PRIME.

## 5. Data and authority boundaries

### Source of truth
- GitHub is the canonical source for code, policy files, migrations, tests and release manifests.
- Supabase is authoritative only for the data actually stored in the selected project; its schema and migration history must be version-controlled.
- Figma and Canva are design/asset sources. Their approved outputs must be referenced by version or exported artifact in the engineering record.
- Lovable previews are non-production evidence until the source is exported, reviewed and tested.
- Gmail is correspondence, not an audit ledger.

### Secrets and identity
- No service-role key, private signing key, OAuth refresh token, approval secret or production credential may enter Git, browser storage, prompts, screenshots, Canva or ordinary email.
- Use provider-managed secret storage and least-privilege scoped credentials.
- Frontend code may contain only intentionally public publishable configuration.
- Authentication, authorisation and human approval are separate controls.
- User-editable profile metadata must not be used as an authorisation claim.
- A connector being authenticated does not authorise every action exposed by that connector.

### Data minimisation
- Do not send personal, sensitive, confidential or customer data to a third-party service unless the data classification, provider terms, region, retention and purpose have been approved.
- Visual captures must be consented, minimised and redacted before durable storage.
- EB9PRIME stores only approved records with provenance, expiry/retention and correction paths.
- UPN PRIME must preserve useful local operation and queue synchronisation without requiring cloud connectivity.

## 6. Required project binding before implementation

Every connected service must be bound to a named project using a recorded mapping:

| Binding | Required record |
|---|---|
| GitHub | owner/repository, canonical branch, CODEOWNERS/review rules, CI workflows |
| Lovable | workspace/project ID, prototype purpose, source-export path and owner |
| Supabase | organisation/project ID, environment, region, database role model, migration path |
| Vercel | team/project ID, linked repository, branch/environment mapping, domains and deployment protection |
| Figma | team/file IDs, design owner, approved page/component references |
| Canva | design IDs, asset owner, export/version and licensing evidence |
| Gmail | approved notification identity, recipient rules, data classification and retention |

No project may be guessed from a similarly named project. In particular, an existing Vercel project for another programme must not be repurposed without explicit project binding and approval.

## 7. Supabase baseline controls

Before any production data is introduced:

- Enable RLS on every table in exposed schemas.
- Define explicit row ownership/tenant boundaries; authenticated role membership alone is not authorisation.
- Use both USING and WITH CHECK for ownership-preserving UPDATE policies.
- Never use user-editable user metadata for authorisation.
- Avoid SECURITY DEFINER unless a reviewed design requires it; keep privileged functions out of exposed schemas and restrict EXECUTE.
- Treat views as a separate security boundary; use security_invoker where supported or restrict access.
- Keep service-role and secret keys server-side only.
- Test policies as anonymous, authenticated, cross-tenant and privileged actors.
- Verify backups, restore, retention, region and deletion behaviour.
- Commit reviewed migrations and run available database security advisors before release.

## 8. Vercel release controls

- Link only the approved GitHub repository and project.
- Separate preview, staging and production environments.
- Require protected production branches and successful exact-commit checks.
- Keep secrets in the platform's environment-secret controls, scoped by environment.
- Verify build output, runtime logs, domains, access protection and rollback target.
- No production deployment is implied by a successful preview or a connector call.

## 9. D.D. authority model for tool use

D.D. may prepare and execute low-risk, reversible, explicitly scoped work where the tool contract and user authorisation permit it. The following always require explicit confirmation or a separately approved policy: destructive changes, merging, production deployment, purchases, billing changes, public publication, external communications, credential/permission changes and irreversible data operations.

A valid execution record must bind:
- actor and authenticated identity;
- project and environment;
- task and action digest;
- policy version and risk classification;
- approval reference where required;
- expiry and one-use/replay protection;
- executor result;
- independent postcondition evidence;
- audit record and rollback reference.

The executor cannot certify itself as VERIFIED. Unknown outcomes must be reconciled, not blindly retried.

## 10. Current connection discovery snapshot

The following is a discovery snapshot, not a permanent account guarantee:

- GitHub connector is available for the repository `Jekylhyde82/universal-engine-engineer`.
- Lovable workspace `Roy's Lovable` contains existing projects including **Proof Before Claims**, **Butterfly Core**, **The Missing Page** and **SOLO SUTRA**. Do not duplicate or repurpose them without an explicit decision.
- Supabase organisation **Creator Core** was visible. No project binding is recorded in this contract yet.
- Vercel team **Roy** exposed a linked project for `Jekylhyde82/project-butterfly-pinocchio`; that is not the Universal Engine / Engineer repository and must not be treated as its deployment target.
- Figma authenticated access was visible. No approved design file binding is recorded here.
- No Canva design matching “Universal Engine Engineer” was returned by the initial title search; this does not prove no relevant design exists.
- Gmail search connector invocation did not return a usable result in the initial discovery attempt; no mail workflow is established.

Re-run connection and project discovery before any future consequential operation. Do not hard-code account identifiers from this snapshot into production configuration.

## 11. Acceptance tests for the integrated toolchain

The toolchain is not considered integrated until all applicable tests pass:

1. Project identity: each connector is bound to the correct project and environment; wrong-project operations are rejected.
2. Least privilege: each integration has only the scopes and roles required for its assigned task.
3. Source provenance: every generated or manually edited code artifact is traceable to a reviewed Git commit.
4. Secrets: automated scans confirm no secrets in source, artifacts, logs, prompts, screenshots or client bundles.
5. Supabase isolation: RLS tests prove tenant isolation and deny unauthorised reads/writes.
6. Deployment: staging deploys only from the approved commit; production requires separate release authorisation.
7. Visual consent: V.I.S.I.O.N. receives only explicitly authorised inputs and cannot authorise D.D.
8. Execution: D.D. cannot bypass policy, replay grants, expand scope or self-verify.
9. Audit: actions and approvals have attributable, tamper-evident records and independently verified outcomes.
10. Offline operation: core local capabilities remain useful without public internet; cloud synchronisation is queued and conflict-aware.
11. Recovery: backup/restore, rollback, credential revocation and kill-switch exercises pass.
12. Independent review: an independent reviewer checks the release evidence and residual risks.

## 12. Release posture

**Current posture: NOT INTEGRATED / NOT APPROVED FOR PRODUCTION.**

This document establishes a target contract. It does not claim that a unified pipeline, Supabase schema, Vercel deployment, native Android visual-perception runtime, production identity provider, EB9PRIME persistence or autonomous D.D. service has been implemented. Those require project-specific work, security controls, test evidence and approvals.

The next implementation increments are:
1. Complete the V.I.S.I.O.N./D.D. prototype acceptance evidence and production blockers.
2. Bind the correct Supabase project and design the least-privilege schema only after project purpose and data model are confirmed.
3. Create a dedicated Vercel project linked to the Universal Engine repository only after explicit project/environment approval.
4. Build the read-only Repository Capability Scout analysis adapter with commit-pinned evidence and bounded API calls.
5. Add an end-to-end integration test harness proving source provenance, policy gates, deployment isolation and offline queue behaviour.
