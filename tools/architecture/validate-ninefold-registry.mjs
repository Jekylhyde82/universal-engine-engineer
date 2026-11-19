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
assert(registry.fusion_function_role === "GLOBAL_INTRINSIC_FUSION", "fusion role mismatch.");
reservedLineages(registry.umic_domain_lineages, 9, "UMIC domain lineage");
reservedLineages(registry.master_core_lineages, 9, "Master Core lineage");
reservedLineages(registry.engine_lineages, 81, "Engine lineage");
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
  preserved_lineages: registry.lineage_counts,
  registers: registry.registers.length,
  status: registry.verification.status,
}, null, 2));
