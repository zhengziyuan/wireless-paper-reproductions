"""Fabricated audit events only; never opens saved campaign data."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepared_mc_trace_scan import Audit, SCHEMES


def ctx(draw=0, scheme=''):
    return {'case_id': 13, 'U': 1, 'beta': 20, 'MC_draw': draw, 'scheme': scheme}


class SyntheticAudit(unittest.TestCase):
    def setUp(self):
        self.refs = {s: [float(i + 1) for i in range(3)] for s in SCHEMES}
        self.a = Audit(self.refs, draws=3)

    def populate(self, *, bad_rate=False, chain_gap=False, omit_one=False, bad_nhu=False):
        self.a.accept('MC_begin', ctx(), {'rng': b'R0', 'count': 3, 'names': SCHEMES})
        for d in range(1, 4):
            self.a.accept('MC_draw', ctx(d), {'draw': d})
            before = b'gap' if chain_gap and d == 2 else ('R%d' % (d-1)).encode()
            self.a.accept('geometry_begin', ctx(d), {'rng': before})
            self.a.accept('geometry_G', ctx(d), {})
            self.a.accept('geometry_ground', ctx(d), {})
            self.a.accept('geometry_end', ctx(d), {'rng': ('R%d' % d).encode(), 'nhu': (bytes([d]), bytes([d]))})
            for s in SCHEMES:
                if omit_one and d == 3 and s == 'AO':
                    continue
                rate = -1.0 if bad_rate and d == 2 and s == 'AO' else float(d)
                matrix = (b'x', b'y') if bad_nhu and d == 2 and s == 'AO' else (bytes([d]), bytes([d]))
                self.a.accept('MC_evaluation', ctx(d, s), {'draw': d, 'scheme': s, 'rate': rate, 'nhu': matrix})
        import struct
        self.a.accept('MC_end', ctx(), {'rng': b'R3', 'count': 3,
                                      'samples': b''.join(struct.pack('<d', float(d)) for _ in SCHEMES for d in range(1,4))})
        return self.a.result()

    def test_complete(self):
        r = self.populate()
        self.assertTrue(r['draw_and_geometry_id_coverage'])
        self.assertTrue(r['scheme_draw_record_coverage'])
        self.assertTrue(r['geometry_G_and_ground_record_coverage'])
        self.assertTrue(r['reported_draw_counts_match_expected'])
        self.assertEqual(r['rate_mismatch_count'], 0)
        self.assertEqual(r['negative_saved_rate_count'], 0)
        self.assertEqual(r['MC_boundary_position_mismatch_count'], 0)
        self.assertEqual(r['draw_group_order_mismatch_count'], 0)
        self.assertEqual(r['MC_end_array_mismatch_count'], 0)
        self.assertEqual(r['geometry_rng_changed_pairs'], 3)
        self.assertEqual(r['saved_direct_NHU_mismatch_count'], 0)
        self.assertEqual(r['adjacent_saved_NHU_different_pairs'], 2)
        self.assertEqual(r['adjacent_rng_chain_mismatch_count'], 0)
        self.assertTrue(r['MC_rng_before_matches_first_geometry'])
        self.assertTrue(r['last_geometry_rng_matches_MC_end'])
        self.assertFalse(r['statistical_independence_proven'])
        self.assertFalse(r['common_underlying_channel_across_schemes_proven'])

    def test_missing_scheme_is_not_coverage(self):
        self.assertFalse(self.populate(omit_one=True)['scheme_draw_record_coverage'])

    def test_exact_rate_mismatch_is_retained(self):
        r = self.populate(bad_rate=True)
        self.assertEqual(r['rate_mismatch_count'], 1)
        self.assertEqual(r['rate_mismatch_first_20'], [[2, 'AO']])
        self.assertEqual(r['negative_saved_rate_count'], 1)
        self.assertEqual(r['negative_saved_rate_first_20'], [[2, 'AO']])

    def test_misordered_MC_boundaries_are_reported(self):
        import struct
        self.a.accept('MC_draw', ctx(1), {'draw': 1})
        self.a.accept('MC_begin', ctx(), {'rng': b'R0', 'count': 3, 'names': SCHEMES})
        self.a.accept('MC_end', ctx(), {'rng': b'R3', 'count': 3,
             'samples': b''.join(struct.pack('<d', float(d)) for _ in SCHEMES for d in range(1,4))})
        self.assertEqual(self.a.result()['MC_boundary_position_mismatch_count'], 2)

    def test_misordered_draw_groups_are_reported(self):
        self.a.accept('MC_begin', ctx(), {'rng': b'R0', 'count': 3, 'names': SCHEMES})
        self.a.accept('MC_draw', ctx(2), {'draw': 2})
        self.a.accept('MC_draw', ctx(1), {'draw': 1})
        self.assertGreater(self.a.result()['draw_group_order_mismatch_count'], 0)

    def test_rng_chain_difference_reported_not_fabricated(self):
        r = self.populate(chain_gap=True)
        self.assertEqual(r['adjacent_rng_chain_mismatch_count'], 1)
        self.assertFalse(r['statistical_independence_proven'])

    def test_nhu_mismatch_is_recorded(self):
        r = self.populate(bad_nhu=True)
        self.assertEqual(r['saved_direct_NHU_mismatch_count'], 1)
        self.assertEqual(r['saved_direct_NHU_mismatch_first_20'], [[2, 'AO']])

    def test_duplicate_event_rejected(self):
        self.a.accept('MC_draw', ctx(1), {'draw': 1})
        with self.assertRaises(ValueError):
            self.a.accept('MC_draw', ctx(1), {'draw': 1})

    def test_negative_or_wrong_draw_rejected(self):
        with self.assertRaises(ValueError):
            self.a.accept('MC_draw', ctx(-1), {'draw': -1})

    def test_geometry_end_must_match_open_draw(self):
        self.a.accept('geometry_begin', ctx(1), {'rng': b'before'})
        with self.assertRaises(ValueError):
            self.a.accept('geometry_end', ctx(2), {'rng': b'after'})

    def test_wrong_case_rejected(self):
        c = ctx(1)
        c['case_id'] = 12
        with self.assertRaises(ValueError):
            self.a.accept('MC_draw', c, {'draw': 1})

    def test_wrong_reference_and_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            Audit({'AO': [1.0]}, draws=1)
        with self.assertRaises(ValueError):
            Audit({s: [float('nan')] for s in SCHEMES}, draws=1)


if __name__ == '__main__':
    unittest.main()
