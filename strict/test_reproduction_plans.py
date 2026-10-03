"""Source routing tests only; never numerical reproduction certificates."""
import unittest
from pathlib import Path
from reproduce import plan,HERE,statistical_matlab_call,corrected_ma_matlab_call


class Routing(unittest.TestCase):
    def test_sensing_explicit_corrected_default_and_printed_override(self):
        corrected=plan('mis-sensing',3)
        self.assertTrue(corrected['runnable'])
        self.assertEqual(Path(corrected['settings_path']).name,'settings_corrected.json')
        self.assertEqual(corrected['settings']['number_of_starts'],6000)
        self.assertEqual(corrected['settings']['outer_iterations'],30)
        self.assertEqual(corrected['settings']['rcg_max_iterations'],4000)
        self.assertTrue(corrected['paper_error_correction_is_explicit'])
        printed=plan('mis-sensing',3,HERE/'mis-sensing'/'settings.json')
        self.assertFalse(printed['paper_error_correction_is_explicit'])
        for figure in (5,6):self.assertEqual(plan('mis-sensing',figure)['execution_figure'],3)

    def test_ma_corrected_original_model_not_historical_formula(self):
        for figure in (14,16):
            p=plan('two-timescale-ma',figure)
            self.assertTrue(p['runnable'])
            self.assertFalse(p['printed_undefined_formula_recovered'])
            self.assertFalse(p['historical_figure_recovery_claimed'])
            self.assertEqual(p['settings']['geometry_realizations'],100)
            self.assertEqual(p['settings']['nlos_realizations_per_geometry'],1000)
            self.assertEqual(p['settings']['maximum_AO_iterations'],10000)
            self.assertIn('run_corrected_ma_figure_matlab_source_v2',p['executor'])

    def test_corrected_matlab_routing_uses_actual_v2_schema_and_full_source_gate(self):
        expression=corrected_ma_matlab_call(Path('input-bank'),Path('new-output'))
        self.assertIn('run_matlab_bank_checked',expression)
        self.assertIn('matlab-corrected-source-v2',expression)
        self.assertIn('run_corrected_ma_figure_matlab_source_v2(',expression)
        self.assertNotIn('run_corrected_ma_figure_matlab(',expression)
        self.assertTrue(expression.endswith(',false);'))
        self.assertLess(expression.index('run_matlab_bank_checked'),expression.index('run_corrected_ma_figure_matlab_source_v2'))
        adapter=(HERE/'matlab-corrected-source-v2'/'run_corrected_ma_figure_matlab_source_v2.m').read_text()
        self.assertIn('manifest.expected_jobs==300',adapter)
        self.assertIn('config.nlos_realizations_per_geometry==1000',adapter)
        self.assertLess(adapter.index('if ~all(valid),return;end'),adapter.index('evaluate_correlated_zf_matlab_source_v2(path'))

    def test_matlab_statistical_durable_default_and_explicit_legacy(self):
        output=Path('out');result=output/'statistical-matlab.json'
        expression,target=statistical_matlab_call(HERE/'hotspot-satcom'/'statistical_validated_config.json',output,result)
        self.assertIn('run_hotspot_validated_bank_checked',expression)
        self.assertEqual(target,output/'checkpoints'/'statistical'/'matlab'/'full18-matlab.json')
        expression,target=statistical_matlab_call(HERE/'hotspot-satcom'/'statistical_geometry_config.json',output,result)
        self.assertIn('run_strict_hotspot_statistical_geometry',expression);self.assertEqual(target,result)
        with self.assertRaises(ValueError):
            statistical_matlab_call(Path('elsewhere/statistical_validated_config.json'),output,result)

    def test_exhaustive_original_axes_not_one_short_common_grid(self):
        p=plan('two-timescale-ma',19);q=plan('two-timescale-ma',20)
        self.assertEqual(p['original_per_axis_grid'],list(range(3,19)))
        self.assertEqual(q['original_per_axis_grid'],list(range(3,13)))
        self.assertFalse(p['historical_exhaustive_objective_uniquely_recovered'])
        self.assertFalse(q['historical_exhaustive_objective_uniquely_recovered'])

    def test_all_hotspot_subpanels_and_shared_trace(self):
        self.assertEqual(plan('hotspot-satcom',2)['execution_sweeps'],['cdf_kS20'])
        self.assertEqual(plan('hotspot-satcom',4)['execution_sweeps'],['hu_count_kS10','hu_count_kS20'])
        p=plan('hotspot-satcom',7)
        self.assertEqual(p['execution_sweeps'],['cdf_kS20','cdf_kS10'])
        self.assertIn('not uniquely resolved',p['caption_conflict'])
        self.assertEqual(plan('hotspot-satcom',8)['execution_sweeps'],['rician_u6','rician_u1'])

    def test_statistical_full18_route_and_unresolved_count_contract(self):
        p=plan('hotspot-satcom',10)
        self.assertTrue(p['runnable'])
        self.assertEqual(p['execution_sweeps'],['statistical'])
        self.assertFalse(p['printed_invalid_SOC_recovered'])
        self.assertEqual(Path(p['settings_path']).name,'statistical_validated_config.json')
        self.assertIn('validated',p['executor'])
        self.assertFalse(p['all_original_source_constraints_verified'])
        self.assertEqual(p['settings']['tuned_not_reported']['rgd_max_iterations'],100000)
        count=plan('hotspot-satcom',9)
        self.assertTrue(count['runnable'])
        self.assertFalse(count['original_author_center_geometry_recovered'])
        self.assertFalse(count['row_column_factorization_inferred'])
        self.assertFalse(plan('hotspot-satcom',1)['runnable'])

    def test_cooperative_all_six_multi_single_subsweeps(self):
        p=plan('cooperative-satcom',11)
        self.assertTrue(p['runnable'])
        self.assertEqual(p['execution_sweeps'],[
            'multi_vs_single_multi_kL20','multi_vs_single_single_1.25_kL20','multi_vs_single_single_2.5_kL20',
            'multi_vs_single_multi_kL0','multi_vs_single_single_1.25_kL0','multi_vs_single_single_2.5_kL0'])
        self.assertEqual(len(p['specification'][0]['curves']),12)

    def test_no_plan_is_execution_or_original_agreement(self):
        for paper,figure in [('mis-communications',7),('mis-sensing',2),('rotatable-isac',3),
                             ('two-timescale-ma',14),('hotspot-satcom',10),('cooperative-satcom',11)]:
            p=plan(paper,figure)
            self.assertFalse(p['executed'])
            self.assertFalse(p['full_reproduction_passed'])
            self.assertFalse(p['original_curve_agreement_verified'])
            self.assertFalse(p['automatic_downsizing'])


if __name__=='__main__':unittest.main()
