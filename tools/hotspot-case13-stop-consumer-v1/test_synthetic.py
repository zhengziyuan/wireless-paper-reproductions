"""Synthetic typed nodes only. No historical case or optimizer is opened."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import consume_saved_stops as m


def num(values, imag=None):
    return {'tag': 'N', 'header': {'class': 'double', 'order': 'MATLAB_column_major',
            'numel': len(values), 'isreal': imag is None}, 'real': values,
            **({} if imag is None else {'imag': imag})}


def logic(v):
    return {'tag': 'L', 'header': {'class': 'logical'}, 'values': [v]}


def chars(v):
    return {'tag': 'H', 'header': {'class': 'char'}, 'value': v}


def stop(rule, residual, count=1, converged=True, threshold=1e-5):
    fields = {'converged': logic(converged), 'termination': chars('synthetic'),
              'iterations': num([count]), 'iteration_cap': num([100]),
              'stop_rule': chars(rule), 'threshold': num([threshold]),
              'final_residual': num([residual])}
    return {'tag': 'S', 'header': {'class': 'struct'}, 'values': [fields]}


def event(action, ordinal, fields):
    scheme, start = m.CONTEXT_BY_ORDINAL.get(ordinal, ('AO', 0))
    return {'action': action, 'ordinal': ordinal, 'fields': fields,
            'context': {'case_id': 13, 'geometry_id': 12013, 'U': 1, 'beta': 20,
                        'scheme': scheme, 'start_id': start}}


class Tests(unittest.TestCase):
    def test_small_negative_old_stop_is_not_monotonic(self):
        h = [10.0, 9.9999995]
        residual = (h[1] - h[0]) / 10
        e = event('QT_loop_end', 1327161, {'history': num(h),
            'stop': stop('signed_relative_objective_increase', residual)})
        row = m.consume([e], None)['records'][0]
        self.assertEqual(len(row['history']['recorded_negative_differences']), 1)
        self.assertFalse(row['history']['all_recorded_differences_nonnegative'])
        self.assertTrue(row['stop_check']['recomputed_expression_triggered'])
        self.assertTrue(row['stop_check']['residual_matches_record'])
        self.assertFalse(row['stop_check']['saved_history_completeness_proven'])
        summary = m.consume([e], None)['recorded_event_counts_by_action']['QT_loop_end']
        self.assertEqual(summary['recorded_negative_steps'], 1)
        self.assertEqual(summary['reported_stop_converged_true'], 1)

    def test_phase_norm_independent_recompute(self):
        e = event('phase_end', 1327318, {'actual_history': num([1.0, 1.1]),
            'actual_stop': stop('Riemannian_gradient_norm', 5e-7, threshold=1e-6),
            'final_gradient': num([3e-7], [4e-7])})
        row = m.consume([e], None)['records'][0]['stop_check']
        self.assertAlmostEqual(row['recomputed_gradient_norm'], 5e-7)
        self.assertTrue(row['gradient_matches_record'])
        self.assertTrue(row['flag_agrees_with_recomputed_expression'])

    def test_negative_gradient_norm_is_not_accepted(self):
        e = event('phase_end', 1327318, {'actual_history': num([1.0, 1.1]),
            'actual_stop': stop('Riemannian_gradient_norm', -1e-9, threshold=1e-6),
            'final_gradient': num([1e-9])})
        s = m.consume([e], None)['records'][0]['stop_check']
        self.assertFalse(s['nonnegative_norm'])
        self.assertFalse(s['flag_agrees_with_recomputed_expression'])

    def test_incomplete_history_and_bad_residual_are_visible(self):
        e = event('QT_loop_end', 1327161, {'history': num([1.0, 1.01]),
            'stop': stop('signed_relative_objective_increase', 0.5, count=8)})
        r = m.consume([e], None)
        self.assertFalse(r['expected_events_and_histories_present'])
        s = r['records'][0]['stop_check']
        self.assertFalse(s['history_count_matches_reported_iterations'])
        self.assertFalse(s['residual_matches_record'])
        self.assertFalse(r['complete_optimization_trajectory_proven'])

    def test_nonfinite_or_missing_values_are_not_pass(self):
        e = event('QT_loop_end', 1327161, {'history': num([1.0, 'NaN']),
            'stop': stop('signed_relative_objective_increase', 0.1)})
        r = m.consume([e], None)['records'][0]
        self.assertEqual(r['inspection_status'], 'insufficient_or_invalid_fields')
        del e['fields']['stop']
        self.assertEqual(m.consume([e], None)['records'][0]['inspection_status'],
                         'insufficient_or_invalid_fields')

    def test_coverage_requires_summary_all_ids_and_no_partial_tail(self):
        rows = []
        for action, ids in m.EXPECTED.items():
            for ordinal in ids:
                rows.append(event(action, ordinal, {}))
        summary = {'schema': 'CASE13_STOP_HISTORY_CHILD_SUMMARY_V1',
                   'status': 'completed', 'complete_records': 28}
        r = m.consume(rows, summary)
        # Expected IDs with invalid records are insufficient projection coverage.
        self.assertFalse(r['expected_events_and_histories_present'])
        self.assertTrue(all(x.get('inspection_status') == 'insufficient_or_invalid_fields'
                            for x in r['records']))
        self.assertFalse(r['mathematical_convergence_proved'])
        self.assertFalse(m.consume(rows, summary, partial_tail=True)['expected_events_and_histories_present'])
        self.assertFalse(m.consume(rows[:-1], summary)['expected_events_and_histories_present'])

    def test_valid_ids_with_wrong_context_do_not_establish_coverage(self):
        e = event('AO_iteration', 1327666, {'history': num([1.0, 2.0])})
        e['context']['start_id'] = 1
        self.assertEqual(m.consume([e], None)['records'][0]['inspection_status'],
                         'insufficient_or_invalid_fields')

    def test_all_synthetic_ids_report_projection_coverage_only(self):
        status = {'tag': 'S', 'header': {'class': 'struct'}, 'values': [{
            'converged': logic(True), 'algorithm_success': logic(True),
            'termination': chars('all_original_stop_rules_reached'),
            'blocks': {'tag': 'C', 'values': [stop('signed_relative_objective_increase', 0.0)]}}]}
        qt = {'tag': 'S', 'header': {'class': 'struct'}, 'values': [{'solver_status': chars('Solved')}]}
        rows = []
        for action, ids in m.EXPECTED.items():
            for ordinal in ids:
                if action == 'QT_loop_end':
                    fields = {'history': num([1.0, 1.0]), 'stop': stop('signed_relative_objective_increase', 0.0)}
                elif action == 'phase_end':
                    fields = {'actual_history': num([1.0, 1.0]),
                              'actual_stop': stop('Riemannian_gradient_norm', 0.0),
                              'final_gradient': num([0.0])}
                elif action == 'AO_iteration':
                    fields = {'history': num([1.0, 1.0]), 'phase_stop': stop('Riemannian_gradient_norm', 0.0),
                              'QT_info': qt}
                else:
                    fields = {'history': num([1.0, 1.0]), 'status': status}
                rows.append(event(action, ordinal, fields))
        summary = {'schema': 'CASE13_STOP_HISTORY_CHILD_SUMMARY_V1',
                   'status': 'completed', 'complete_records': 28}
        r = m.consume(rows, summary)
        self.assertTrue(r['expected_events_and_histories_present'])
        self.assertTrue(r['no_detected_nested_interpretation_errors'])
        self.assertFalse(r['all_74_extracted_fields_independently_interpreted'])
        self.assertFalse(r['complete_optimization_trajectory_proven'])
        self.assertFalse(r['mathematical_convergence_proved'])
        self.assertFalse(r['physical_feasibility_proved'])
        self.assertFalse(r['full_paper_pass'])
        del next(x for x in rows if x['action'] == 'AO_iteration')['fields']['phase_stop']
        missing = m.consume(rows, summary)
        self.assertTrue(missing['expected_events_and_histories_present'])
        self.assertFalse(missing['no_detected_nested_interpretation_errors'])
        self.assertGreater(missing['recorded_event_counts_by_action']['AO_iteration']['nested_fields_uninspectable'], 0)

    def test_duplicate_or_wrong_identity_rejected(self):
        e = event('AO_iteration', 1327666, {'history': num([1.0, 2.0])})
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            m.consume([e, e], None)
        e['ordinal'] = 4
        with self.assertRaisesRegex(ValueError, 'unknown'):
            m.consume([e], None)

    def test_partial_history_never_proves_complete(self):
        e = event('AO_iteration', 1327666, {'history': num([1.0, 2.0])})
        r = m.consume([e], None, partial_tail=True)
        self.assertFalse(r['expected_events_and_histories_present'])
        self.assertTrue(r['partial_final_line'])
        self.assertFalse(r['records'][0]['source_trajectory_complete_proven'])

    def test_nested_phase_stop_is_reported_without_claiming_full_history(self):
        qt = {'tag': 'S', 'header': {'class': 'struct'}, 'values': [
              {'solver_status': chars('Solved'), 'qt_bound_max_violation': num([0.0])}]}
        e = event('AO_iteration', 1327666, {'history': num([1.0, 2.0]),
             'phase_stop': stop('Riemannian_gradient_norm', -1e-9), 'QT_info': qt})
        r = m.consume([e], None)['records'][0]
        self.assertFalse(r['phase_stop_report']['nonnegative_norm'])
        self.assertFalse(r['phase_stop_report']['history_for_this_stop_provided'])
        self.assertEqual(r['QT_solver_status_reported'], 'Solved')
        self.assertFalse(r['QT_info_proves_physical_feasibility'])

    def test_missing_nested_fields_are_counted_even_if_history_valid(self):
        e = event('AO_iteration', 1327666, {'history': num([1.0, 2.0])})
        stats = m.consume([e], None)['recorded_event_counts_by_action']['AO_iteration']
        self.assertEqual(stats['uninspectable_events'], 0)
        self.assertEqual(stats['nested_fields_uninspectable'], 2)

    def test_final_status_keeps_embedded_stop_as_report_only(self):
        nested = stop('signed_relative_objective_increase', -1e-9)
        status = {'tag': 'S', 'header': {'class': 'struct'}, 'values': [{
            'converged': logic(True), 'algorithm_success': logic(True),
            'termination': chars('all_original_stop_rules_reached'),
            'blocks': {'tag': 'C', 'values': [nested]}}]}
        e = event('execute_final', 1327162, {'history': num([1.0, 1.0]), 'status': status})
        r = m.consume([e], None)['records'][0]['final_status_report']
        self.assertTrue(r['reported_algorithm_success'])
        self.assertTrue(r['blocks'][0]['negative_reported_residual'])
        self.assertFalse(r['blocks_interpreted_as_independent_scientific_pass'])

    def test_two_stage_qt_and_phase_histories_remain_separate(self):
        history = {'tag': 'S', 'header': {'class': 'struct'}, 'values': [{
            'QT': num([5.0, 6.0]), 'phase': num([1.0, 2.0])}]}
        e = event('execute_final', 1327398, {'history': history})
        row = m.consume([e], None)['records'][0]
        self.assertTrue(row['history']['all_recorded_differences_nonnegative'])
        self.assertFalse(row['history']['cross_block_difference_computed'])
        self.assertEqual(row['history']['blocks']['QT']['recorded_points'], 2)
        self.assertEqual(row['history']['blocks']['phase']['recorded_points'], 2)
        self.assertEqual(row['history']['recorded_negative_differences'], [])
        history['values'][0]['phase'] = num([1.0, 0.9])
        row = m.consume([e], None)['records'][0]
        self.assertEqual(row['history']['recorded_negative_differences'][0]['block'], 'phase')
        self.assertEqual(m.consume([e], None)['recorded_event_counts_by_action']['execute_final']
                         ['recorded_negative_steps'], 1)

    def test_unknown_nested_history_is_not_misclassified(self):
        history = {'tag': 'S', 'header': {'class': 'struct'}, 'values': [{'other': num([1.0, 2.0])}]}
        e = event('execute_final', 1327398, {'history': history})
        self.assertEqual(m.consume([e], None)['records'][0]['inspection_status'],
                         'insufficient_or_invalid_fields')


if __name__ == '__main__':
    unittest.main()
