# Capability Registry Chain — Remediation Overlay

**Disposition:** REMEDIATION PROPOSAL / NOT INTEGRATED / NOT DEPLOYED

## Provenance
Derived from the exact preserved source snapshot:
- Repository: `Jekylhyde82/7282ALLSPARXPRIME`
- Source branch: `allsparx/universal-capability-system`
- Source commit: `b271a166de17984aedb4c9a98a7273489c45b463`
- Preserved, unchanged copy: `extractions/quarantine/universal-capability-system/`

## Change
Corrects double-escaped regular-expression tokens in capability semantic-version and ISO timestamp validation. The unchanged source snapshot remains quarantined and retains its original blob hashes. This overlay is a separately reviewable remediation candidate.

## Validation boundary
The overlay must pass its targeted tests in GitHub Actions before further review. A passing unit test does not establish persistence security, authenticated evidence, independent verification, deployment readiness, or integration compatibility.


## Test execution
The targeted registry-chain contract suite is included in the master repository's Quarantine Validation workflow. The original quarantined tests remain unchanged and are run separately to preserve source-defect visibility.
