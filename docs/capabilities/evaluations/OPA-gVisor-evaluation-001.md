# Preliminary Evaluation 001 — OPA + gVisor

**Evaluation ID:** UCEE-EVAL-OPA-GVISOR-001  
**Specification:** UCEE-SPEC-001 v0.1.0  
**Observed:** 2026-11-06  
**Disposition:** `EVIDENCE_INCOMPLETE` — advance to isolated proof planning only; not an integration approval.

## 1. Capability claim

Assess whether Open Policy Agent (OPA) and gVisor can provide two complementary control layers for agent/tool workloads:

- OPA: policy decision point (PDP) that evaluates an action request against policy.
- Enforcement gateway/runtime integration: policy enforcement point (PEP) that must actually allow or deny the action.
- gVisor: Linux workload isolation boundary for supported container workloads.

**Critical boundary:** OPA makes policy decisions; it does not, by itself, enforce those decisions. The calling gateway/PEP must fail closed and prevent the protected action when a decision is denied, undefined, malformed, unavailable or timed out. gVisor provides workload isolation, not user identity, business authorization or policy approval. These functions are complementary, not interchangeable.

## 2. Source identity snapshot

| Project | Observed release | Latest observed repository commit | Source |
|---|---|---|---|
| OPA | v1.22.1, published 2026-11-05 | `b10aaf8e89b477a2a2feee95a55ccc43a29c8c9b` (2026-11-05) | https://github.com/open-policy-agent/opa |
| gVisor | 20261102.0, published 2026-11-02 | `add07b5fa1fdf48d20ed9b39277e1ebcc75b0aaf` (2026-11-05) | https://github.com/google/gvisor |

The commit SHAs above are observed repository heads, not a claim that the listed release tags resolve to those same commits. Before a proof run or dependency pin, resolve and record the exact tag-to-commit relationship and select the intended immutable revisions.

## 3. Licence and provenance snapshot

- OPA root `LICENSE` fetched from the repository default branch on 2026-11-06; the file begins with Apache License 2.0.
- gVisor root `LICENSE` fetched from the repository default branch on 2026-11-06; the file begins with Apache License 2.0.
- OPA official deployment documentation identifies OPA as a PDP and the integrating application as the PEP.
- gVisor licensing policy includes an allowlist and explicit dependency exceptions; therefore root-license inspection alone is not a complete dependency/SBOM review.

**Gate status:** G0 partially evidenced; G1 incomplete. Root licence files are observed, but exact release-file verification, full dependency/asset inventory, notices and build/distribution boundary review remain outstanding.

## 4. Compatibility and deployment findings

- OPA documents sidecar/VM-node-agent and centralized-service deployment patterns. A local policy decision point can reduce network dependency; a centralized service introduces network latency and availability considerations.
- gVisor requires Linux and supports x86_64/AMD64 and ARM64. It is not a direct Android/ColorOS runtime for the user's phone.
- gVisor implements a large but incomplete portion of the Linux syscall surface. Compatibility must be tested with the actual workload; documentation explicitly says the only reliable way to know whether a workload works is to try it.
- gVisor releases are published on a weekly cadence. Pin a specific release and verify its published checksums; do not deploy a moving `latest` channel as a reproducible build input.

**Preliminary architecture fit:** OPA is a plausible provider-neutral policy decision service for a remote execution gateway. gVisor is a plausible candidate isolation runtime on a compatible remote Linux host. The OPPO Android device should remain a control terminal unless a separately verified supported runtime path is demonstrated.

## 5. Gate assessment

| Gate | Status | Evidence / outstanding work |
|---|---|---|
| G0 Source identity | PARTIAL | Current branch heads and release labels observed; exact release tag commit resolution and chosen immutable pins remain. |
| G1 Licence/provenance | INCOMPLETE | Root Apache-2.0 files observed; dependency SBOM, nested notices, release-specific files and distribution analysis remain. |
| G2 Maintenance/compatibility | PARTIAL | Recent releases/commits observed; target workload and supported-host compatibility untested. |
| G3 Security/governance | NOT ASSESSED | Need threat model, policy bypass analysis, gateway enforcement review, sandbox configuration review and negative tests. |
| G4 Resource/deployment | NOT ASSESSED | Need supported Linux host, CPU/RAM/storage/network and workload benchmarks. |
| G5 Proof of capability | NOT RUN | No software installed, no policies executed, no containers launched, no tests run. |
| G6 Integration approval | NOT APPROVED | No adapter contract or integration approval granted. |
| G7 Operational verification | NOT APPLICABLE | No implementation or deployment exists. |

## 6. Proposed isolated proof plan

Use a disposable, supported Linux host with no production credentials or sensitive data. Keep OPA and gVisor as separately replaceable providers behind a narrow execution gateway.

### OPA / enforcement tests
1. Allowed action: a known permitted request produces an allow decision and the PEP permits only the exact scoped action.
2. Denied action: prohibited request is blocked before execution.
3. Undefined/malformed decision: PEP denies by default.
4. OPA unavailable, timeout or invalid response: PEP fails closed; no protected action executes.
5. Policy revision change: the active revision is identifiable and decision logs preserve policy/version provenance.
6. Prompt-injection attempt: untrusted task content cannot modify policy or grant its own permissions.
7. Audit evidence: request identity, policy revision, decision, PEP enforcement result and timestamp correlate without logging secrets.

### gVisor / isolation tests
1. Confirm exact Linux kernel, host architecture, runtime version and supported configuration.
2. Run a minimal known-good workload and record compatibility.
3. Verify resource limits, filesystem boundaries, read-only mounts and process restrictions.
4. Verify network egress restrictions independently of application intent.
5. Test denied host filesystem, device and privileged operations.
6. Confirm workload termination and cleanup after timeout, crash and cancellation.
7. Record performance overhead and failure behavior against an unsandboxed baseline.

### Combined boundary tests
- OPA allow + sandbox healthy: only the approved workload starts inside the sandbox.
- OPA deny + sandbox healthy: workload does not start.
- OPA unavailable + sandbox healthy: workload does not start.
- OPA allow + sandbox unavailable: workload does not start.
- Policy changes during queued work: the gateway applies the defined policy-version consistency rule.
- Attempts to bypass the gateway or launch an unsandboxed workload are denied and auditable.

## 7. Preliminary recommendation

**Advance to proof-plan design, not installation or integration.**

This pair addresses a high-value architectural gap: external policy decisions plus isolated workload execution. The separation of concerns is sound in principle, but the security claim depends on the enforcement gateway, host configuration, policy lifecycle and tested sandbox boundary—not on the presence of OPA or gVisor alone.

No candidate is approved. No software was installed. No code was imported. No proof-of-capability tests, security tests or performance benchmarks were run. No operational or secure status is claimed.

## 8. Sources

- OPA release history: https://github.com/open-policy-agent/opa/releases
- OPA deployment model: https://www.openpolicyagent.org/docs/deploy
- OPA integration interfaces: https://www.openpolicyagent.org/docs/integration
- gVisor release history: https://github.com/google/gvisor/releases
- gVisor installation and release channels: https://gvisor.dev/docs/user_guide/install/
- gVisor compatibility: https://gvisor.dev/docs/user_guide/compatibility/
- gVisor platform FAQ: https://gvisor.dev/docs/user_guide/faq/
- gVisor dependency licensing policy: https://github.com/google/gvisor/blob/master/governance/licensing.yaml
