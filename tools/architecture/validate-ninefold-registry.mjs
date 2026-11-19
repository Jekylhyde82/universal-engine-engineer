import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const registryPath = resolve(here, "../../docs/architecture/ninefold-intrinsic/registry/capability-lineage.registry.json");
const registry = JSON.parse(await readFile(registryPath, "utf8"));

function assert(condition, message) {
  if (!condition) throw new Error("Registry validation failed: " + message);
}
function uniqueIds(items, label) {
  const ids = items.map((item) => item.id);
  assert(new Set(ids).size === ids.length, label + " IDs must be unique.");
  assert(ids.every((id) => typeof id === "string" && id.length > 0), label + " IDs must be non-empty.");
}
function reservedLineages(items, expected, label) {
  assert(Array.isArray(items) && items.length === expected, label + " count must equal " + expected + ".");
  uniqueIds(items, label);
  for (const item of items) {
    assert(item.canonical_name === null, label + " placeholder must not invent a canonical name.");
    assert(item.name_status === "UNMAPPED", label + " name status must remain explicitly unmapped.");
    assert(item.responsibility_status === "UNMAPPED", label + " responsibility must remain explicitly unmapped.");
    assert(item.lineage_status === "PRESERVED_PENDING_CANONICAL_MAPPING", label + " lineage status is invalid.");
  }
}

assert(registry.schema_version === "1.0.0", "unsupported schema version.");
assert(registry.architecture_identity === "NINEFOLD INTRINSIC", "canonical identity mismatch.");
assert(registry.entity_model === "ONE_UNIFIED_ENTITY", "entity model must be unified.");
assert(registry.fusion_function === "UNIFIED FUSION SYNERGY — AFI PRIME", "fusion identity mismatch.");
assert(registry.fusion_function_count === 1, "there must be exactly one global fusion function.");
assert(registry.fusion_function_role === "SHARED_INTRINSIC_FUSION_FUNCTION", "fusion role mismatch.");
assert(registry.fusion_core_instance_count === 9, "exactly nine scoped fusion core instances are required.");
assert(registry.unified_umic_model.umic_count === 9, "unified UMIC count must equal nine.");
assert(registry.unified_umic_model.master_core_slots_per_umic === 1, "each UMIC must contain one Master Core slot.");
assert(registry.unified_umic_model.engine_slots_per_umic === 9, "each UMIC must contain nine Engine slots.");
assert(registry.unified_umic_model.fusion_core_instances_per_umic === 1, "each UMIC must contain one scoped fusion core.");
assert(registry.unified_umic_model.fusion_core_instances_total === 9, "nine scoped fusion cores are required.");
assert(registry.unified_umic_model.final_entity_count === 1, "the nine unified UMICs must form one final entity.");
assert(registry.unified_umic_model.slot_membership_status === "STRUCTURE_DEFINED_SOURCE_LINEAGE_MAPPING_PENDING", "source lineage mapping must remain explicitly pending.");
assert(registry.unified_umic_model.runtime_status === "NOT_IMPLEMENTED", "registry must not claim runtime fusion.");
reservedLineages(registry.umic_domain_lineages, 9, "UMIC domain lineage");
reservedLineages(registry.master_core_lineages, 9, "Master Core lineage");
reservedLineages(registry.engine_lineages, 81, "Engine lineage");
assert(Array.isArray(registry.fusion_core_instances) && registry.fusion_core_instances.length === 9, "exactly nine scoped fusion core instances are required.");
uniqueIds(registry.fusion_core_instances, "Fusion core instance");
assert(registry.instance_isolation_contract.execution_context === "DEDICATED_SCOPED_CONTEXT_PER_INSTANCE", "each instance requires its own execution context.");
assert(registry.instance_isolation_contract.state_boundary === "INSTANCE_LOCAL_STATE_WITH_GOVERNED_CROSS_INSTANCE_CONTRACTS_ONLY", "instance state boundaries must be explicit.");
assert(registry.instance_isolation_contract.evidence_trail === "INSTANCE_SCOPED_APPEND_ONLY_EVIDENCE_STREAM", "each instance requires its own evidence trail.");
assert(registry.instance_isolation_contract.fault_containment === "INSTANCE_SCOPED_FAULT_DOMAIN_WITH_BOUNDED_DEGRADATION", "each instance requires its own fault-containment domain.");
assert(registry.instance_isolation_contract.shared_logic === "ONE_VERSIONED_CANONICAL_AFIPRIME_FUNCTION_IDENTITY", "instances must share one canonical versioned fusion function.");
assert(registry.instance_isolation_contract.shared_governance === "ONE_CANONICAL_GOVERNANCE_POLICY_WITH_INSTANCE_SCOPED_ENFORCEMENT", "instances must share canonical governance with scoped enforcement.");
assert(registry.instance_isolation_contract.shared_mutable_state === false, "instances must not share mutable execution state.");
assert(registry.instance_isolation_contract.implicit_permission_inheritance === false, "permissions must not be implicitly inherited across instances.");
assert(registry.instance_isolation_contract.implementation_status === "PROTOTYPE_IMPLEMENTED_PRODUCTION_NOT_IMPLEMENTED", "registry must not claim instance isolation is implemented.");
const instanceFieldIds = ["execution_context_id", "state_namespace", "evidence_stream_id", "fault_domain_id"];
for (const field of instanceFieldIds) {
  const values = registry.fusion_core_instances.map((core) => core[field]);
  assert(values.every((value) => typeof value === "string" && value.length > 0), field + " must be present for every instance.");
  assert(new Set(values).size === 9, field + " values must be unique across all nine instances.");
}
for (const core of registry.fusion_core_instances) {
  assert(core.execution_context_status === "PROTOTYPE_IMPLEMENTED_PRODUCTION_NOT_IMPLEMENTED", "execution context status must distinguish prototype from production.");
  assert(core.state_boundary_status === "PROTOTYPE_IMPLEMENTED_PRODUCTION_NOT_IMPLEMENTED", "state boundary status must distinguish prototype from production.");
  assert(core.evidence_trail_status === "PROTOTYPE_IMPLEMENTED_PRODUCTION_NOT_IMPLEMENTED", "evidence trail status must distinguish prototype from production.");
  assert(core.fault_containment_status === "PROTOTYPE_IMPLEMENTED_PRODUCTION_NOT_IMPLEMENTED", "fault containment status must distinguish prototype from production.");
}
for (let index = 0; index < registry.fusion_core_instances.length; index += 1) {
  const core = registry.fusion_core_instances[index];
  const ordinal = String(index + 1).padStart(2, "0");
  assert(core.id === "FUSION-CORE-UMIC-" + ordinal, "fusion core instance ordering is invalid.");
  assert(core.umic_domain_id === "UMIC-DOMAIN-" + ordinal, "fusion core must be scoped to its matching UMIC.");
  assert(core.fusion_function === registry.fusion_function, "all UMICs must use the same canonical fusion function.");
  assert(core.master_core_slots === 1 && core.engine_slots === 9, "each fusion core must unify one Master Core slot and nine Engine slots.");
  assert(core.top_level_entity === false, "scoped fusion cores must not become separate top-level entities.");
  assert(core.membership_status === "STRUCTURE_DEFINED_SOURCE_LINEAGE_MAPPING_PENDING", "source lineage membership must remain pending.");
  assert(core.runtime_status === "NOT_IMPLEMENTED", "registry must not claim an implemented fusion runtime.");
}
assert(registry.lineage_counts.umic_domains === 9, "UMIC declared count mismatch.");
assert(registry.lineage_counts.master_cores === 9, "Master Core declared count mismatch.");
assert(registry.lineage_counts.engines === 81, "Engine declared count mismatch.");
assert(registry.lineage_counts.total_preserved_lineages === 99, "total lineage count must equal 99.");
assert(registry.umic_domain_lineages.every((item) => item.top_level_entity === false), "UMIC lineages must not be independent top-level entities.");
assert(registry.engine_lineages.every((item) => item.domain_assignment === null), "unverified domain assignments must remain null.");
assert(Array.isArray(registry.registers) && registry.registers.length === 9, "exactly nine register definitions are required.");
uniqueIds(registry.registers, "Register");
assert(registry.mapping_policy.do_not_invent_canonical_names === true, "canonical names must not be fabricated.");
assert(registry.mapping_policy.do_not_infer_domain_assignments === true, "domain assignments must not be inferred.");
assert(registry.verification.runtime_fusion_implemented === false, "registry must not claim runtime fusion.");
assert(registry.verification.full_registry_reconciled === false, "bootstrap registry must not claim full reconciliation.");
assert(registry.verification.independently_verified === false, "bootstrap registry must not claim independent verification.");

console.log(JSON.stringify({
  valid: true,
  identity: registry.architecture_identity,
  fusion_function: registry.fusion_function,
  fusion_core_instances: registry.fusion_core_instance_count,
  unified_umic_model: registry.unified_umic_model,
  preserved_lineages: registry.lineage_counts,
  registers: registry.registers.length,
  status: registry.verification.status,
}, null, 2));
