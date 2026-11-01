"""Synthetic tests only: no optimizer, saved trajectory, or scientific run."""
import copy
import math
import unittest
from recorded_gate import assess_case, assess_start

LIMITS = {'relative_tolerance':1e-5, 'gradient_tolerance':1e-6,
          'qt_max_iterations':200, 'ao_max_iterations':200, 'rgd_max_iterations':200}


def qt(history):
    value = (history[-1]-history[-2])/max(abs(history[-2]), 1e-12)
    return {'converged': True, 'termination':'relative_improvement', 'iterations': len(history)-1, 'iteration_cap': 200,
            'stop_rule':'signed_relative_objective_increase',
            'threshold':1e-5, 'final_residual':value}


def phase(history):
    return {'converged': True, 'termination':'gradient_tolerance', 'iterations': len(history)-1, 'iteration_cap': 200,
            'stop_rule':'Riemannian_gradient_norm',
            'threshold':1e-6, 'final_residual':1e-7}


def start(name, start_id=0):
    h = [10., 10.1, 10.100001]
    if name == 'NoRIS':
        history, blocks = h, [qt(h)]
    elif name == 'TwoStage':
        hp = [1., 1.1, 1.2]
        history, blocks = {'phase':hp, 'QT':h}, [phase(hp), qt(h)]
    else:
        # Current production preserves AO outer history but drops each phase
        # history, retaining only the individual phase stop receipts.
        history, blocks = h, [phase([1., 1.1]), phase([1., 1.1]), qt(h)]
    return {'scheme':name, 'start_id':start_id, 'executed':True,
            'checks':{'convergence_pass':True},
            'status':{'converged':True, 'blocks':blocks}, 'history':history}


def case():
    return {'U':1, 'status':'executed', 'checks':{'convergence_pass':True},
            'schemes':{name:{'all_start_records':[start(name,0),start(name,1)]}
                       for name in ('NoRIS','TwoStage','AO')}}


class RecordedGateTests(unittest.TestCase):
    def test_qt_positive_and_zero_increment_conditional_pass(self):
        for h in ([10.,10.1,10.100001],[10.,10.1,10.1]):
            r=start('NoRIS'); r['history']=h; r['status']['blocks']=[qt(h)]
            out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
            self.assertIs(out['recorded_gate'],True)
            self.assertEqual(r['status']['blocks'][0]['converged'],True)

    def test_negative_final_step_old_stop_true_but_gate_false(self):
        h=[10.,9.9999995]; r=start('NoRIS');r['history']=h;r['status']['blocks']=[qt(h)]
        self.assertTrue(r['status']['blocks'][0]['converged'])
        out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_gate'],False)
        self.assertEqual(out['blocks'][0]['reason'],'recorded_objective_decrease')

    def test_earlier_decrease_is_not_hidden_by_final_increase(self):
        h=[10.,9.9,10.000001];r=start('NoRIS');r['history']=h;r['status']['blocks']=[qt(h)]
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_phase_negative_and_negative_norm_fail(self):
        r=start('TwoStage');r['history']['phase']=[1.,0.9999999,1.2]
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)
        r=start('TwoStage');r['status']['blocks'][0]['final_residual']=-1e-9
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_missing_or_unattested_or_incomplete_history_unknown(self):
        r=start('NoRIS')
        self.assertIsNone(assess_start(r)['recorded_gate'])
        r['history']=r['history'][:-1]
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])
        r=start('TwoStage');del r['history']['phase']
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])

    def test_ao_discarded_inner_history_is_unknown(self):
        out=assess_start(start('AO'),complete_history_capture=True,declared_limits=LIMITS)
        self.assertIsNone(out['recorded_gate'])
        self.assertEqual([b['reason'] for b in out['blocks'][1:]],
                         ['missing_or_invalid_history','missing_or_invalid_history'])

    def test_ao_missing_history_cannot_hide_bad_gradient(self):
        r=start('AO');r['status']['blocks'][0]['final_residual']=-1e-9
        out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_gate'],False)
        self.assertEqual(out['blocks'][1]['reason'],'negative_gradient_norm')

    def test_missing_flags_or_mismatched_count_cannot_hide_bad_stop(self):
        r=start('AO');r['status']['blocks'][0]['final_residual']=-1e-9
        r['status']['blocks'].pop(1)  # phase count now mismatches outer history
        out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_gate'],False)
        r=start('AO');r['status']['blocks'][0]['converged']=False
        del r['checks']['convergence_pass']
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_future_supplied_phase_histories_can_be_assessed_conditionally(self):
        c=case()
        for r in c['schemes']['AO']['all_start_records']:
            r['phase_histories']=[[1.,1.1],[2.,2.1]]
        out=assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_convergence_evidence_gate'],True)
        self.assertFalse(out['capture_attestation_authenticated'])
        self.assertFalse(out['scientific_or_paper_pass'])
        # A truncated list with a witnessed decrease is a failure, not unknown.
        c['schemes']['AO']['all_start_records'][0]['phase_histories']=[[1.,0.9]]
        self.assertIs(assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)['recorded_convergence_evidence_gate'],False)

    def test_stop_fields_and_recorded_count_checked(self):
        r=start('NoRIS');r['status']['blocks'][0]['final_residual']+=0.01
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)
        r=start('NoRIS');r['status']['blocks'][0]['iterations']=1
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])
        r=start('NoRIS');r['status']['blocks'][0]['threshold']=math.nan
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])

    def test_declared_limits_required_and_must_match_record(self):
        r=start('NoRIS')
        self.assertIsNone(assess_start(r,complete_history_capture=True)['recorded_gate'])
        r['status']['blocks'][0]['threshold']=100.0
        out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_gate'],False)
        self.assertEqual(out['blocks'][0]['reason'],'recorded_limits_mismatch')
        r=start('NoRIS');r['status']['blocks'][0]['iteration_cap']=199
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_termination_contradiction_or_absence_cannot_pass(self):
        r=start('NoRIS');r['status']['blocks'][0]['termination']='configured_iteration_cap'
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)
        r=start('NoRIS');del r['status']['blocks'][0]['termination']
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])

    def test_negative_reported_relative_residual_cannot_hide_in_tolerance(self):
        r=start('NoRIS');r['history']=[10.,10.];r['status']['blocks']=[qt(r['history'])]
        r['status']['blocks'][0]['final_residual']=-1e-18
        out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_gate'],False)
        self.assertEqual(out['blocks'][0]['reason'],'negative_reported_relative_increment')

    def test_missing_history_does_not_hide_negative_or_invalid_stop(self):
        r=start('NoRIS');r['history']=None;r['status']['blocks'][0]['final_residual']=-1e-6
        out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_gate'],False)
        self.assertEqual(out['blocks'][0]['reason'],'negative_reported_relative_increment')
        r=start('NoRIS');r['history']=None;r['status']['blocks'][0]['final_residual']=1e-5
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_reported_relative_residual_at_or_above_threshold_is_failure(self):
        # Stored histories can differ in last-bit rounding from a reported value.
        # Both the recomputed and reported strict inequalities must be met.
        for residual in (1e-5, 1.00000000001e-5):
            h=[1.0,1.0000099999999998];r=start('NoRIS')
            r['history']=h;r['status']['blocks']=[qt(h)]
            r['status']['blocks'][0]['final_residual']=residual
            out=assess_start(r,complete_history_capture=True,declared_limits=LIMITS)
            self.assertIs(out['recorded_gate'],False)
            self.assertEqual(out['blocks'][0]['reason'],'reported_relative_threshold_not_met')

    def test_negative_history_not_hidden_by_missing_original_flags_or_blocks(self):
        r=start('NoRIS');r['history']=[10.,9.9999995];del r['checks']['convergence_pass']
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)
        r=start('NoRIS');r['history']=[10.,9.9999995];del r['status']['blocks']
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_nonfinite_missing_and_failed_original(self):
        r=start('NoRIS');r['history'][1]=math.nan
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])
        r=start('NoRIS');r['checks']['convergence_pass']=False
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)
        r=start('NoRIS');r['status']['blocks'][0]['converged']=False
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_invalid_point_does_not_hide_adjacent_valid_decrease(self):
        for h in ([1.,0.9,math.nan], [math.nan,1.,0.9], [1.,0.9,'bad']):
            r=start('NoRIS');r['history']=h
            self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)
        # Do not splice points across an invalid entry to manufacture a pair.
        r=start('NoRIS');r['history']=[1.,math.nan,0.9]
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])

    def test_finite_decrease_is_detected_even_if_subtraction_overflows(self):
        r=start('NoRIS');r['history']=[1e308,-1e308]
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)
        del r['checks']['convergence_pass']
        self.assertIs(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'],False)

    def test_case_requires_every_start_and_does_not_mutate(self):
        c=case();original=copy.deepcopy(c)
        out=assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIsNone(out['recorded_convergence_evidence_gate'])
        self.assertEqual(c,original)
        self.assertIs(out['original_case_checks']['convergence_pass'],True)
        self.assertFalse(out['scientific_or_paper_pass'])
        c['schemes']['NoRIS']['all_start_records'].pop()
        self.assertIsNone(assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)['recorded_convergence_evidence_gate'])

    def test_case_false_dominates_unknown(self):
        c=case();r=c['schemes']['NoRIS']['all_start_records'][0]
        h=[10.,9.9999995];r['history']=h;r['status']['blocks']=[qt(h)]
        self.assertIs(assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)['recorded_convergence_evidence_gate'],False)

    def test_missing_start_does_not_hide_unambiguous_failed_start(self):
        c=case(); records=c['schemes']['NoRIS']['all_start_records'];records.pop()
        records[0]['checks']['convergence_pass']=False
        out=assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIs(out['recorded_convergence_evidence_gate'],False)
        self.assertEqual(out['schemes'][0]['reason'],'missing_or_duplicate_start_ids')
        # Duplicate start IDs remain unknown rather than inventing an identity.
        c=case(); records=c['schemes']['NoRIS']['all_start_records']
        records[1]['start_id']=0;records[0]['checks']['convergence_pass']=False
        out=assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)
        self.assertIsNone(out['schemes'][0]['recorded_gate'])

    def test_identity_duplicate_and_attestation_type(self):
        c=case();c['schemes']['NoRIS']['all_start_records'][1]['start_id']=0
        out=assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)
        self.assertEqual(out['schemes'][0]['reason'],'missing_or_duplicate_start_ids')
        with self.assertRaises(ValueError):assess_case(c,1,complete_history_capture=1)

    def test_case_identity_and_extreme_nonfinite_number(self):
        c=case();del c['U']
        out=assess_case(c,1,complete_history_capture=True,declared_limits=LIMITS)
        self.assertFalse(out['case_identity_fields_match'])
        self.assertIsNone(out['recorded_convergence_evidence_gate'])
        r=start('NoRIS');r['history'][1]=10**1000
        self.assertIsNone(assess_start(r,complete_history_capture=True,declared_limits=LIMITS)['recorded_gate'])


if __name__ == '__main__':
    unittest.main()
