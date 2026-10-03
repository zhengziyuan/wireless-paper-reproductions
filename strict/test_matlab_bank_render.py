"""Synthetic serialization/gate tests only, NOT executed scientific banks."""
import copy
import unittest
from render_matlab_bank import ISAC_NAMES,MA_NAMES,normalize_isac,normalize_ma,inner_complete,hold


def blocks():
    return {'W':dict(converged=True,capped_unconverged=False,iterations=3,iteration_budget=10,
        termination_reason='relative_objective_tolerance',relative_objective_improvement=1e-5,relative_tolerance=1e-4),
        'RIS':dict(converged=True,capped_unconverged=False,iterations=4,iteration_budget=500,
        termination_reason='gradient_tolerance',last_checked_normalized_gradient_norm=1e-7,gradient_tolerance=1e-6),
        'rotation':dict(converged=True,capped_unconverged=False,iterations=2,iteration_budget=10,
        termination_reason='relative_step_tolerance',relative_step=1e-7,relative_tolerance=1e-6)}


def isac_mock():
    return dict(mode='full_scenario',scheme_names=ISAC_NAMES,
        checks=[dict(status='executed',converged=True,inner_all_converged=True,full_converged=True,
                     power_feasible=True,rotation_feasible=True,unit_modulus_error=0) for _ in range(6)],
        metrics=[dict(utility=i,rate=i,nmse=.5) for i in range(6)],
        history=[dict(inner_all_converged=True,full_converged=True,blocks=[blocks()]) for _ in range(6)])


def ma_mock():
    flags=('mrt_converged','zf_converged','mrt_nominal_design_spacing_feasible','zf_nominal_design_spacing_feasible',
           'mrt_nominal_design_box_feasible','zf_nominal_design_box_feasible')
    return dict(mode='full_scenario',checks=dict.fromkeys(flags,True),
                metrics={'schemes':{k:dict(sample_sum_rates=[1.]*1000,mean_sum_rate=1.,nonconverged_samples=0) for k in MA_NAMES}},
                history={mode:dict(objective=[1.,2.],instantaneous_MC_mean=[1.,2.]) for mode in ('mrt','zf')})


class MatlabSchema(unittest.TestCase):
    def test_six_matlab_arrays_normalize_without_python_metric_substitution(self):
        raw=isac_mock();result=normalize_isac(raw)
        for index,name in enumerate(ISAC_NAMES):self.assertEqual(result['metrics'][name],raw['metrics'][index])
        self.assertIsInstance(raw['metrics'],list)

    def test_claimed_outer_flags_cannot_hide_capped_or_unmeasured_inner(self):
        for changes in ({'capped_unconverged':True},{'last_checked_normalized_gradient_norm':1e-3}):
            raw=isac_mock();raw['history'][1]['blocks'][0]['RIS'].update(changes)
            with self.assertRaises(ValueError):normalize_isac(raw)

    def test_all_five_ma_arrays_and1000_means_required(self):
        raw=ma_mock();result=normalize_ma(raw,{'figure':3},{'matlab_convex_solver':'conic'})
        self.assertEqual(set(result['metrics']['schemes']),set(MA_NAMES.values()))
        raw['metrics']['schemes']['FPA_OPT']['sample_sum_rates'].pop()
        with self.assertRaises(ValueError):normalize_ma(raw,{'figure':3},{})

    def test_no_undefined_correlated_zf_historical_curve(self):
        raw=ma_mock()
        with self.assertRaises(ValueError):normalize_ma(raw,{'figure':16,'correlated':True},{})

    def test_terminal_hold_requires100_real_histories(self):
        self.assertEqual(hold([[1.,2.]]*50+[[3.]]*50),[2.,2.5])
        with self.assertRaises(ValueError):hold([[1.,2.]]*99)

    def test_absent_ris_is_only_explicit_zero_iteration_not_applicable(self):
        item=blocks()['RIS'];item.update(applicable=False,iterations=0,termination_reason='not_applicable_no_RIS')
        self.assertTrue(inner_complete(item,'RIS'));item['iterations']=1;self.assertFalse(inner_complete(item,'RIS'))


if __name__=='__main__':unittest.main()
