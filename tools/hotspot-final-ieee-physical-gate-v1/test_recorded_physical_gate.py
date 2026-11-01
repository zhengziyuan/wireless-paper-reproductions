"""Synthetic gate tests; no solver, repository data, or optimizer is used."""
import copy
import math
import unittest

from recorded_physical_gate import assess_case, assess_start


def make_start(name, start=0):
    return {'scheme': name, 'start_id': start, 'executed': True,
            'checks': {'physical_constraint_pass': True},
            'final_state': {'no_ris': name == 'NoRIS',
                            'phi': {'real': [1.0]*25, 'imag': [0.0]*25}}}


def make_case():
    return {'U': 1, 'status': 'executed', 'checks': {'physical_constraint_pass': True},
            'schemes': {name: {'all_start_records': [make_start(name, 0), make_start(name, 1)]}
                        for name in ('NoRIS', 'TwoStage', 'AO')}}


class GateTests(unittest.TestCase):
    def test_tolerance_required(self):
        with self.assertRaises(TypeError):
            assess_start(make_start('AO'), 'AO')
        for tol in (-1, math.nan, math.inf, True, None):
            with self.assertRaises(ValueError):
                assess_start(make_start('AO'), 'AO', squared_magnitude_tolerance=tol)

    def test_exact_and_tolerance_separate(self):
        row = make_start('AO')
        row['final_state']['phi']['real'][0] = 1.0 + 2**-52
        result = assess_start(row, 'AO', squared_magnitude_tolerance=1e-14)
        self.assertFalse(result['phase']['exact_unit'])
        self.assertTrue(result['phase']['within_tolerance'])
        self.assertTrue(result['gate'])
        self.assertFalse(result['power_or_sinr_independently_verified'])
        self.assertFalse(result['full_physical_or_paper_pass'])
        self.assertFalse(assess_start(row, 'AO', squared_magnitude_tolerance=0)['gate'])

    def test_strong_phase_violation_fails_despite_old_pass(self):
        row = make_start('TwoStage')
        row['final_state']['phi']['real'][0] = 2.0
        result = assess_start(row, 'TwoStage', squared_magnitude_tolerance=1e-6)
        self.assertTrue(result['original_reported_physical_constraint_pass'])
        self.assertFalse(result['gate'])

    def test_noris_phase_not_applicable(self):
        row = make_start('NoRIS')
        del row['final_state']['phi']
        result = assess_start(row, 'NoRIS', squared_magnitude_tolerance=0)
        self.assertEqual(result['phase']['status'], 'not_applicable')
        self.assertTrue(result['gate'])
        row['final_state']['no_ris'] = False
        self.assertFalse(assess_start(row, 'NoRIS', squared_magnitude_tolerance=0)['gate'])

    def test_missing_and_malformed(self):
        row = make_start('AO')
        del row['final_state']['phi']
        self.assertIsNone(assess_start(row, 'AO', squared_magnitude_tolerance=0)['gate'])
        row['final_state']['phi'] = {'real': [1.0], 'imag': [0.0]}
        self.assertFalse(assess_start(row, 'AO', squared_magnitude_tolerance=0)['gate'])

    def test_nonfinite_is_not_pass(self):
        row = make_start('AO')
        for value in (math.nan, math.inf, -math.inf, True, '1'):
            row['final_state']['phi']['imag'][4] = value
            self.assertFalse(assess_start(row, 'AO', squared_magnitude_tolerance=1e-6)['gate'])

    def test_no_ris_flag_missing_or_wrong(self):
        row = make_start('AO')
        del row['final_state']['no_ris']
        self.assertIsNone(assess_start(row, 'AO', squared_magnitude_tolerance=0)['gate'])
        row['final_state']['no_ris'] = True
        self.assertFalse(assess_start(row, 'AO', squared_magnitude_tolerance=0)['gate'])

    def test_original_false_and_known_failure_override_missing(self):
        row = make_start('AO')
        row['checks']['physical_constraint_pass'] = False
        del row['final_state']['phi']
        self.assertFalse(assess_start(row, 'AO', squared_magnitude_tolerance=0)['gate'])

    def test_case_only_conditional_true(self):
        case = make_case()
        before = copy.deepcopy(case)
        result = assess_case(case, 1, squared_magnitude_tolerance=0)
        self.assertTrue(result['conditional_reported_plus_phase_gate'])
        self.assertFalse(result['physical_model_or_paper_pass'])
        self.assertFalse(result['tolerance_source_authenticated'])
        self.assertEqual(case, before)

    def test_missing_start_cannot_pass(self):
        case = make_case()
        case['schemes']['AO']['all_start_records'].pop()
        self.assertIsNone(assess_case(case, 1, squared_magnitude_tolerance=0)['conditional_reported_plus_phase_gate'])

    def test_known_failure_not_hidden_by_missing_start(self):
        case = make_case()
        rows = case['schemes']['AO']['all_start_records']
        rows.pop()
        rows[0]['final_state']['phi']['real'][0] = 3.0
        self.assertFalse(assess_case(case, 1, squared_magnitude_tolerance=0)['conditional_reported_plus_phase_gate'])

    def test_duplicate_identity_cannot_pass(self):
        case = make_case()
        rows = case['schemes']['NoRIS']['all_start_records']
        rows[1]['start_id'] = 0
        self.assertIsNone(assess_case(case, 1, squared_magnitude_tolerance=0)['conditional_reported_plus_phase_gate'])

    def test_missing_case_identity_cannot_pass(self):
        case = make_case()
        del case['status']
        self.assertIsNone(assess_case(case, 1, squared_magnitude_tolerance=0)['conditional_reported_plus_phase_gate'])

    def test_non_bool_original_flag_cannot_pass(self):
        row = make_start('AO')
        row['checks']['physical_constraint_pass'] = 1
        self.assertIsNone(assess_start(row, 'AO', squared_magnitude_tolerance=0)['gate'])


if __name__ == '__main__':
    unittest.main()
