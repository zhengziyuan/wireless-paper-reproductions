"""Synthetic independent analytical-map validation gates, not figure runs."""
import unittest
from unittest.mock import patch
import numpy as np
from compare_sensing_closed_form import close, compare, evaluate


class AnalyticalMapGates(unittest.TestCase):
    def test_fixed_gate_has_no_broadcast_or_nonfinite_acceptance(self):
        self.assertEqual(close([1.,2.],[1.,2.],'exact'),0.)
        for actual in ([1.], [1.,float('nan')], [1.,2.00001]):
            with self.assertRaises(ValueError):close(actual,[1.,2.],'rejected')

    def test_different_settings_rejected_before_evaluation(self):
        with patch('compare_sensing_closed_form.evaluate') as evaluator:
            with self.assertRaises(ValueError):compare({'settings':{'a':1}},{'settings':{'a':2}})
            evaluator.assert_not_called()

    def test_original_full_dimension_case_only_not_other_normalization(self):
        values=dict(kind='sensing',reference_echo_unit='inverse_watt',reference_echo_noise_domain='raw_per_PRI',
            effective_reference_gain_factor=2,bs_antennas=1,power_dbm=30,reference_echo_db=-73.88)
        with self.assertRaises(ValueError):evaluate(values)

    def test_complete_actual_flags_required_before_panel_values(self):
        document=dict(settings={},paper_id='mis-sensing',figure='fig2',
            full_figure_execution_complete=False,overall_full_success=True,original_figure_reproduction_certified=False)
        with patch('compare_sensing_closed_form.evaluate',return_value={}):
            with self.assertRaises(ValueError):compare(document,document)

    def test_complex_fixed_gate(self):
        self.assertLess(close(np.array([1+1j]),np.array([1+1j+1e-12]),'complex'),2e-12)
        with self.assertRaises(ValueError):close([1+1j],[1+1.01j],'complex mismatch')


if __name__ == '__main__':unittest.main()
