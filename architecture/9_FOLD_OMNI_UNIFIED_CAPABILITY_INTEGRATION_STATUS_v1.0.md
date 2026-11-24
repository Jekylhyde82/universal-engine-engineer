# 9 FOLD OMNI — Unified Capability Inventory and Integration Status

**Document ID:** UEE-9FO-UCAT-001  
**Status:** Source-backed partial inventory; integration reconciliation in progress  
**Canonical fusion:** One UNIFIED FUSION SYNERGY — AFI PRIME function, nine UMIC-scoped instances.

## Reconciled inventory

The source-backed Universal Capability Acquisition Register contains 30 records. Two are explicitly marked duplicate references, leaving 28 unique provider records. The nine-technology integration register adds two distinct provider records not present in that acquisition register: the separate OpenHands/OpenHands repository and Goose. The canonical provider catalogue therefore contains 30 unique external providers, deduplicated by repository URL while retaining source register IDs and integration metadata.

The catalogue also records known intrinsic capability identities, all nine OMNISIGHT visual domains, the upstream-change audit capability and the current repository engineering portfolio. These records preserve identity and provenance; they do not imply approval, installation, integration or operational readiness.

## Existing repository work to consolidate

| PR | Workstream | Branch | State |
|---:|---|---|---|
| 2–4 | Quarantined Universal Capability System, SYPHON and Verification Agent sources | extraction branches | Open draft; preserve provenance and quarantine boundaries |
| 7 | Capability registry validation remediation | genius-engineer/capability-registry-remediation | Open draft |
| 8–9, 14–15 | Provider research, acquisition register and upstream audit | research/integration branches | Open draft; candidates, not adoption approval |
| 10–13 | Performance Lab, runner, evidence and hardening | performance-lab branches | Open draft; independent evidence chain required |
| 16 | Provider-neutral Python runtime and four adapters | runtime/core-contracts-v0.1 | Open draft; exact-head CI passed on source commit |
| 18, 20 | UAIE prototype and Android intake alpha | uaie/android branches | Open; prototype/alpha, not production |
| 21–22 | Earlier UAIE/UPN foundation variants | uaie/upn branches | Closed unmerged; historical variants, not integrated |
| 23–24 | UPN control plane and offline-first architecture | uaie/upn branches | Open draft |
| 25 | V.I.S.I.O.N. + D.D. architecture | architecture/vision-dd-production-spec | Open draft; parent architecture for PR 35 |
| 26–27 | Repository Capability Scout prototype and hardening | prototype/production branches | Open draft; CI passed on PR 27 head |
| 29–30 | LM Studio catalog, acquisition and AFI adapter | uaie/lm-studio branches | Open draft; PR 30 exact-head CI not found in queried runs |
| 31 | CHRONOS VELOCITY PRIME × AFI PRIME | ninefold/chronos-velocity-afi-fusion-v0.1 | Open draft |
| 32 | STARWIRE discovery and SYPHON extraction | starwire/ninefold-intrinsic-syphon-v0.1 | Open draft; CI passed on source commit |
| 33 | EUPN node identity, retries and TLS tests | build/first-substantial-network-node | Open draft |
| 34 | Production readiness master blueprint | docs/production-readiness-master-blueprint-v1.0 | Open draft |
| 35 | OMNISIGHT PRIME / 9 FOLD OMNI foundation | architecture/omnisight-ninefold-intrinsic-v0.1 | Open draft; exact-head CI passed after inventory addition |

The complete branch names, base relationships and source URLs are recorded in the JSON catalogue. The branch forest is not one integrated codebase: PR dependencies and overlapping package, README and workflow files require deliberate consolidation.

## Integration order

1. Reconcile capability identities and provenance; preserve duplicates as aliases rather than separate engines.
2. Consolidate provider-neutral runtime contracts and the policy/lifecycle ledger into the NINEFOLD INTRINSIC branch without copying quarantined source directly into the execution path.
3. Integrate existing AFI PRIME provider adapters through one manifest and dispatch contract; keep providers replaceable.
4. Bring UAIE, LM Studio and repository discovery in as governed acquisition providers; keep external code read-only/quarantined until review.
5. Integrate Performance Lab, GENESIS evidence and independent verification as the validation plane; no component certifies itself.
6. Integrate CHRONOS, STARWIRE, SYPHON, V.I.S.I.O.N./D.D., UPN and EUPN through versioned interfaces and isolated tests.
7. Reconcile the 99 lineage slots from approved canonical records. Do not invent IDs or responsibilities to fill the count.
8. Run cross-capability, fault-isolation, permission, privacy, dependency, performance and target-device tests before activation.

## Verification evidence observed

- PR 35 exact head `0f4a75950d9beada2bccb6af6fc9afd3f9420684`: all six current-head PR workflows passed — Python Core `45497045250` (**164 tests**, including AFI PRIME coordination and digest-only evidence persistence, plus 11 STARWIRE tests and 21 Performance Lab tests), OMNISIGHT PRIME contract validation `45497045197` (schema, provider-neutral runtime, STARWIRE, Performance Lab, unified capability catalogue and evidence-ledger runtime), Performance Lab validation `45497045091`, Repository Capability Scout `45497045050`, V.I.S.I.O.N./D.D. policy core `45497045131`, and NINEFOLD AFI PRIME runtime proof `45497044992` (registry validation, syntax checks and 13 nine-instance isolation/fault-containment tests).
- PR 16 source commit `b203fe639b154d7337e37be450a5f62ca16cced6`: Python Core workflow `44291437259` passed.
- PR 27 source commit `ca87a08e020d71ea7e191a645542d67ea113c7c2`: Repository Capability Scout checks `44460118557` passed.
- PR 32 source commit `53809085703e9f0d96b20f848334d8aec96c3e09`: STARWIRE CI `44619132868` passed.

These runs validate only their respective commits and test scopes. They do not prove that the branches have been merged together or that the integrated system is operational.

## Hard constraints

- No additional fusion authority or tenth UMIC instance.
- No automatic activation from discovery or inventory inclusion.
- No copying unreviewed source snapshots into production execution paths.
- No unrestricted coding-agent, browser, shell, network or credential access.
- No merge, release or deployment implied by this catalogue.
- Preserve full capability potential while enforcing evidence, permissions, isolation, rollback and independent verification.

**ONE ARCHITECTURE. ONE CANONICAL AFI PRIME. NINE GOVERNED INSTANCES. NO INVENTED LINEAGE MAPPINGS.**
