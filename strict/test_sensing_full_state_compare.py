"""Gate/schema tests; the separately saved real full30 receipt is the evidence."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np

spec=importlib.util.spec_from_file_location('sensing_full_state_compare',Path(__file__).with_name('compare_sensing_full_state.py'))
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)

class Model:
    M,N,targets,U=400,256,9,25
    def metric(self,z,objective):return np.ones((9,25))*10

class ComparisonGateTests(unittest.TestCase):
    def fixture(self):
        settings={'original':True};point={'full_scene':True}
        manifest={'settings':settings,'figure':{'id':'fig3','objective':'sinr','points':[point]},
                  'implementation_digest':'frozen','signature':'bank'}
        status={key:True for key in ('all_inner_tolerances_satisfied','prescribed_outer_budget_execution_complete',
                                    'original_problem_kkt_verified','convergence_verified')}
        status.update(inner_iteration_cap_exits=0,inner_failure_exits=0,original_problem_kkt_certificate={'verified':True})
        z={'phi':{'real':[1],'imag':[0]},'theta':{'real':[1],'imag':[0]},'X':(np.ones((9,25))/25).tolist(),'eta':10}
        metrics={'eta':10,'min_relaxed_metric':10,'min_binary_metric':10,'maximum_constraint':0}
        matlab={'settings':settings,'configuration':point,'start':10,'history':[{} for _ in range(30)],
                'state':z,'metrics':metrics,'solver_status':status}
        python=deepcopy(matlab);python.update(implementation_digest='frozen',bank_signature='bank',
            source_unchanged_during_run=True,summary={'start':10,'solver_status':deepcopy(status)})
        return manifest,matlab,python,status
    def evaluate(self,manifest,matlab,python,reevaluated):
        with patch.object(checker.sensing,'implementation_digest',return_value=('frozen',{})), \
             patch.object(checker.sensing,'make_model',return_value=Model()), \
             patch.object(checker.sensing,'solver_diagnostics',return_value=reevaluated):
            return checker.compare(manifest,matlab,python)
    def test_valid_actual_stop_fields_do_not_certify_bank_or_optimum(self):
        m,a,b,s=self.fixture();r=self.evaluate(m,a,b,s)
        self.assertTrue(r['all_same_state_metric_and_original_stop_checks_pass'])
        self.assertFalse(r['full6000_start_bank_completed']);self.assertFalse(r['original_figure_reproduction_certified'])
    def test_cap_cannot_be_erased_by_final_kkt(self):
        m,a,b,s=self.fixture();b['summary']['solver_status']['inner_iteration_cap_exits']=1
        self.assertFalse(self.evaluate(m,a,b,s)['all_same_state_metric_and_original_stop_checks_pass'])
    def test_saved_eta_must_match_actual_state(self):
        m,a,b,s=self.fixture();a['metrics']['eta']=11
        self.assertFalse(self.evaluate(m,a,b,s)['all_same_state_metric_and_original_stop_checks_pass'])
    def test_independent_bad_stop_cannot_be_hidden_by_saved_status(self):
        m,a,b,s=self.fixture();s=deepcopy(s);s['convergence_verified']=False
        self.assertFalse(self.evaluate(m,a,b,s)['all_same_state_metric_and_original_stop_checks_pass'])
    def test_changed_bank_is_rejected(self):
        m,a,b,s=self.fixture();b['bank_signature']='other'
        with self.assertRaises(ValueError):self.evaluate(m,a,b,s)
    def test_short_history_is_rejected(self):
        m,a,b,s=self.fixture();a['history'].pop()
        with self.assertRaises(ValueError):self.evaluate(m,a,b,s)

if __name__=='__main__':unittest.main()
