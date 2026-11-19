# Capability lineage registry — reconciliation status

**Canonical identity:** NINEFOLD INTRINSIC  
**Entity model:** one unified entity  
**Fusion function:** one global UNIFIED FUSION SYNERGY — AFI PRIME  
**Registry status:** structural bootstrap only; not a completed canonical inventory

## What is recorded

The machine-readable registry reserves exactly:
- 9 former UMIC domain lineages;
- 9 Master Core capability lineages;
- 81 specialist Engine capability lineages;
- 99 preserved constituent lineages in total;
- 9 register definitions.

The register definitions are Major Division (target 9), System (target 90), Architecture (target 184), Responsibility Layer (target 18), Intelligence, Capability, Lifecycle, Evidence & Verification, and Cross-reference & Traceability.

## Nine scoped instance boundaries

The registry now reserves distinct execution-context IDs, state namespaces, evidence-stream IDs and fault-domain IDs for each of the nine scoped AFI PRIME instances. These identifiers express required boundaries; they do **not** prove that separate runtime processes, stores, streams or fault-isolation mechanisms exist.

All nine instances share one versioned canonical AFI PRIME function identity and one governance model. They must not share mutable runtime state or implicitly inherit permissions. Cross-instance communication requires an explicit governed contract. The registry marks each implementation status as not implemented until runtime evidence and independent tests exist.

## Important: placeholders are not invented identities

The source material available for this implementation confirms the counts and the one-entity fusion decision, but does not supply the approved canonical names, responsibility definitions or exact lineage-to-domain mappings for all 99 constituent lineages. The registry therefore uses neutral stable IDs and explicitly null names/mappings. These IDs reserve slots; they are not proposed subsystem names.

Do not populate names, responsibilities, or domain assignments from inference. Recover them from owner-approved architecture records, preserve source provenance, and independently reconcile duplicates and superseded entries before marking a lineage mapped.

## What this does not claim

- It does not claim the 99 capabilities are implemented.
- It does not claim the nine registers are populated or fully reconciled.
- It does not claim that runtime fusion exists.
- It does not claim independent verification or production readiness.

Run the structural validator:

```sh
node tools/architecture/validate-ninefold-registry.mjs
```

A successful result proves only that the bootstrap registry preserves the approved counts and does not fabricate missing names or mappings.
