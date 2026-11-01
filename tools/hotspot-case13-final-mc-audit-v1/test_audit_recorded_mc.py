"""Synthetic inputs only, including failure and missing-start cases."""
import copy
import importlib.util
import math
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('mc_audit',Path(__file__).with_name('audit_recorded_mc.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    checks={k:True for k in m.GATES}
    starts=[{'start_id':i,'executed':True,'checks':checks.copy(),
             'recorded_status':{'converged':True,'algorithm_success':True,'termination':'original'},
             'exception_present':False} for i in (0,1)]
    ensemble={'required_start_ids':[0,1],'executed_start_ids':[0,1],'selected_start_id':[0],
              'all_required_starts_executed':True,'all_required_starts_pass':True,'checks':checks.copy()}
    x=[1.0,2.0,3.0,4.0]
    mc={'count':4,'hu_rate_samples':x,'exact_ergodic_sum_rate_estimate':2.5,
        'standard_error':math.sqrt(5.0/3.0)/2}
    scheme={'independent_MC':mc,'recorded_starts':starts,'ensemble':ensemble}
    return {'schema':'CASE13_FINAL_RESULT_BOUNDED_PROJECTION_V1','historical_source_authenticated':False,
            'whole_event_atomic_snapshot_verified':False,'full_paper_pass':False,
            'case':{'U':1,'kappa_satellite_db':20},
            'schemes':{k:copy.deepcopy(scheme) for k in m.NAMES},
            'case_checks_recorded':checks.copy(),'closed_checks_recorded':checks.copy()}


class Tests(unittest.TestCase):
    def test_exact_n_minus_one_statistics(self):
        r=m.audit(fixture())['schemes']['AO']
        self.assertEqual(r['recomputed_mean'],2.5)
        self.assertAlmostEqual(r['recomputed_sample_standard_error'],math.sqrt(5.0/3.0)/2)
        self.assertEqual(r['mean_difference'],0)
        self.assertTrue(r['recorded_count_matches_vector'])
        self.assertFalse(r['saved_budget_is_1000'])

    def test_count_mismatch_is_visible(self):
        d=fixture();d['schemes']['AO']['independent_MC']['count']=1000
        r=m.audit(d)['schemes']['AO']
        self.assertFalse(r['recorded_count_matches_vector'])
        self.assertFalse(r['saved_budget_is_1000'])

    def test_three_scheme_sample_mapping_and_full_count(self):
        d=fixture()
        for i,name in enumerate(m.NAMES):
            mc=d['schemes'][name]['independent_MC']
            mc['count']=1000;mc['hu_rate_samples']=[float(i+1)]*1000
            mc['exact_ergodic_sum_rate_estimate']=float(i+1);mc['standard_error']=0.0
        r=m.audit(d)
        for i,name in enumerate(m.NAMES):
            self.assertEqual(r['schemes'][name]['recomputed_mean'],float(i+1))
            self.assertTrue(r['schemes'][name]['saved_budget_is_1000'])
            self.assertEqual(r['schemes'][name]['recomputed_sample_standard_error'],0.0)
            self.assertIn(name,r['schemes'][name]['sample_source_in_projection'])

    def test_missing_or_failed_start_cannot_pass_summary(self):
        d=fixture();d['schemes']['AO']['recorded_starts'].pop()
        r=m.audit(d)['schemes']['AO']
        self.assertFalse(r['all_required_start_records_present_and_executed'])
        self.assertFalse(r['no_recorded_start_failures'])
        self.assertFalse(r['recorded_ensemble_pass_agrees_with_start_reports'])
        d=fixture();d['schemes']['AO']['recorded_starts'][1]['checks']['convergence_pass']=False
        r=m.audit(d)['schemes']['AO']
        self.assertFalse(r['no_recorded_start_failures'])
        self.assertFalse(r['recorded_ensemble_pass_agrees_with_start_reports'])

    def test_empty_and_nonfinite_vectors_rejected(self):
        for x in ([],[float('nan'),2.0],[1.0,float('inf')]):
            d=fixture();d['schemes']['NoRIS']['independent_MC']['hu_rate_samples']=x
            with self.assertRaises(ValueError):m.audit(d)

    def test_wrong_case_and_invalid_flags_rejected(self):
        d=fixture();d['case']['U']=True
        with self.assertRaises(ValueError):m.audit(d)
        d=fixture();d['schemes']['AO']['ensemble']['all_required_starts_pass']='true'
        with self.assertRaises(ValueError):m.audit(d)

    def test_selection_and_source_limitations(self):
        d=fixture();d['schemes']['TwoStage']['ensemble']['selected_start_id']=[7]
        r=m.audit(d)
        self.assertFalse(r['schemes']['TwoStage']['selected_id_belongs_to_recorded_starts'])
        self.assertFalse(r['historical_source_authenticated'])
        self.assertFalse(r['independent_draws_proven'])
        self.assertFalse(r['physical_feasibility_proven'])
        self.assertFalse(r['full_paper_pass'])


if __name__=='__main__':unittest.main()
