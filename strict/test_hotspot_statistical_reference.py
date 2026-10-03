"""Synthetic parser/coverage tests, not scientific reproduction receipts."""
import copy
import unittest
from audit_hotspot_statistical_reference import LABELS,extract,compare


def fixture():
    parts=['52 479 M\n568 98 L']
    parts += [f'({v}) t' for v in list(range(1,7))+list(range(2,14))]
    parts += [f'({name}, ) t\n(={beta}) t' for beta in (1,10,100) for name in ('AO','Two-Stage','No-RIS')]
    for k in range(9):
        parts.append('N\n'+'\n'.join(f'{52+103.2*u:g} {479-(k+u/10)*381/11:g} '+('M' if u==0 else 'L') for u in range(6))+'\nS')
    return '\n'.join(parts)


class ReferenceParser(unittest.TestCase):
    def test_all_nine_curves_and_explicit_linear_rician_labels(self):
        curves=extract(fixture());self.assertEqual([c['label'] for c in curves],LABELS)
        self.assertEqual(sum(len(c['y']) for c in curves),54)
        self.assertAlmostEqual(curves[0]['y'][0],2)

    def test_exact_grid_comparison_not_automatic_agreement(self):
        ref=extract(fixture());doc={'paper_id':'hotspot-satcom','figure':10,'full_execution_verified':True,'panels':[{'curves':copy.deepcopy(ref)}]}
        result=compare(ref,doc);self.assertEqual(result['maximum_absolute_error'],0)
        self.assertFalse(result['original_curve_closeness_verified'])
        self.assertFalse(result['acceptance_tolerance_invented'])

    def test_missing_or_duplicate_legends_fail(self):
        for text in (fixture().replace('(AO, ) t','(Unknown, ) t',1),fixture()+'\n(AO, ) t'):
            with self.assertRaises(ValueError):extract(text)

    def test_no_partial_or_interpolated_computed_bank(self):
        ref=extract(fixture());doc={'paper_id':'hotspot-satcom','figure':10,'full_execution_verified':True,'panels':[{'curves':copy.deepcopy(ref)}]}
        doc['panels'][0]['curves'][0]['x'][2]=3.1
        with self.assertRaises(ValueError):compare(ref,doc)
        doc['full_execution_verified']=False
        with self.assertRaises(ValueError):compare(ref,doc)


if __name__=='__main__':unittest.main()
