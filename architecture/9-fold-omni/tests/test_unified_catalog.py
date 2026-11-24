import json
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / '9_FOLD_OMNI_UNIFIED_CAPABILITY_CATALOG_v1.0.json'

class UnifiedCapabilityCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG.read_text(encoding='utf-8'))

    def test_one_canonical_fusion_and_nine_scoped_instances(self):
        self.assertEqual(self.data['canonical_fusion_function'], 'UNIFIED FUSION SYNERGY — AFI PRIME')
        self.assertEqual(self.data['governance']['canonical_afi_instances'], 9)
        self.assertEqual(self.data['governance']['additional_fusion_authorities'], 0)
        self.assertEqual(self.data['governance']['additional_umic_instances'], 0)

    def test_catalogue_ids_are_unique(self):
        for key in ('external_candidates', 'intrinsic_capabilities', 'visual_capability_domains'):
            ids = [item['id'] for item in self.data[key]]
            self.assertEqual(len(ids), len(set(ids)), key)

    def test_external_candidates_deduplicated_by_repository(self):
        repos = [item['repository'].rstrip('/').lower() for item in self.data['external_candidates']]
        self.assertEqual(len(repos), len(set(repos)))
        self.assertGreaterEqual(len(repos), 25)

    def test_candidate_provenance_and_disposition_retained(self):
        for item in self.data['external_candidates']:
            self.assertTrue(item.get('name'))
            self.assertTrue(item.get('repository', '').startswith('https://'))
            self.assertTrue(item.get('initial_disposition'))

    def test_catalogue_does_not_promote_candidates_to_operational(self):
        self.assertFalse(self.data['external_candidate_summary']['all_candidates_installed_or_approved'])
        for item in self.data['external_candidates']:
            self.assertNotIn(item.get('initial_disposition'), {'IMPLEMENTED', 'TESTED', 'INDEPENDENTLY_VERIFIED', 'OPERATIONAL'})

    def test_nine_visual_domains(self):
        self.assertEqual(len(self.data['visual_capability_domains']), 9)

    def test_99_slots_preserved_without_fabricated_mappings(self):
        slots = self.data['lineage_capacity']
        self.assertEqual((slots['total'], slots['umic_domains'], slots['master_core_slots'], slots['engine_slots']), (99, 9, 9, 81))
        self.assertEqual((slots['mapped_slots'], slots['unmapped_slots']), (0, 99))
        self.assertEqual(slots['mapping_status'], 'UNRESOLVED_PENDING_APPROVED_CANONICAL_REGISTER_EVIDENCE')

    def test_internal_capabilities_have_no_invented_slot_mapping(self):
        for item in self.data['intrinsic_capabilities'] + self.data['visual_capability_domains']:
            self.assertIsNone(item['lineage_mapping'])

    def test_closed_unmerged_variants_remain_distinct(self):
        prs = {item['number']: item for item in self.data['repository_work_portfolio']}
        self.assertEqual(prs[21]['state'], 'closed_unmerged')
        self.assertEqual(prs[22]['state'], 'closed_unmerged')
        self.assertEqual(prs[35]['state'], 'open')

if __name__ == '__main__':
    unittest.main()
