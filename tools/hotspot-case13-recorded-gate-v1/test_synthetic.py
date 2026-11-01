"""Synthetic association failures; no original trajectory or paper data."""
import copy
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


under = load(HERE / 'check_recorded_gate.py', 'case_gate_association')
gate = load(HERE.parent / 'hotspot-final-ieee-convergence-gate-v1/recorded_gate.py', 'gate')


def stop(phase=False):
    return {'converged': True, 'termination': 'gradient_tolerance' if phase else 'relative_improvement',
            'iterations': 1.0, 'iteration_cap': 9.0,
            'stop_rule': 'Riemannian_gradient_norm' if phase else 'signed_relative_objective_increase',
            'threshold': 0.1, 'final_residual': 0.01,
            'numerical_controls': 'toy', 'total_backtracks': 3.0,
            'gradient_threshold_unchanged': True}


def status(blocks):
    return {'reported_converged': True,
            'blocks': {'tag': 'C', 'header': {'class': 'cell'}, 'values': blocks}}


def fixture():
    rows = []
    expected = {k: [] for k in ('QT_loop_end', 'phase_end', 'AO_iteration', 'execute_final')}
    expected_context = {}
    starts = {name: [] for name in ('NoRIS', 'TwoStage', 'AO')}

    def add(action, ordinal, name, sid, fields):
        expected[action].append(ordinal)
        expected_context[ordinal] = (name, sid)
        rows.append({'action': action, 'ordinal': ordinal,
                     'context': {'scheme': name, 'start_id': sid}, 'fields': fields})

    for sid in (0, 1):
        for name in starts:
            starts[name].append({'start_id': float(sid), 'executed': True,
                                 'checks': {'convergence_pass': True},
                                 'recorded_status': {'converged': True}})
        q = 10 + 10*sid
        add('QT_loop_end', q, 'NoRIS', sid, {'history': [1., 2.], 'stop': stop()})
        add('execute_final', q+1, 'NoRIS', sid,
            {'history': [1., 2.], 'status': status([stop()])})
        p = 30 + 10*sid
        add('phase_end', p, 'TwoStage', sid, {'actual_history': [1., 2.], 'actual_stop': stop(True)})
        add('QT_loop_end', p+1, 'TwoStage', sid, {'history': [1., 2.], 'stop': stop()})
        add('execute_final', p+2, 'TwoStage', sid,
            {'history': {'phase': [1., 2.], 'QT': [1., 2.]},
             'status': status([stop(True), stop()])})
        p = 100 + 100*sid
        for i in range(4):
            add('phase_end', p+2*i, 'AO', sid, {'actual_history': [1., 2.], 'actual_stop': stop(True)})
            add('AO_iteration', p+2*i+1, 'AO', sid,
                {'history': [float(n) for n in range(i+2)], 'phase_stop': stop(True)})
        final_stop = stop()
        final_stop['iterations'] = 4.0
        add('execute_final', p+10, 'AO', sid,
            {'history': [0., 1., 2., 3., 4.],
             'status': status([stop(True) for _ in range(4)] + [final_stop])})

    def inspect(r):
        if r['ordinal'] not in expected[r['action']]:
            raise ValueError('event')
        c = r['context']
        if (c['scheme'], c['start_id']) != expected_context[r['ordinal']]:
            raise ValueError('context')
        result = {'scheme': c['scheme'], 'start_id': c['start_id'], 'ordinal': r['ordinal']}
        if r['action'] == 'execute_final':
            s = r['fields']['status']
            result['final_status_report'] = {'reported_converged': s['reported_converged'],
                                             'blocks': s['blocks']['values']}
        return result

    consumer = SimpleNamespace(EXPECTED=expected, inspect_event=inspect,
                               numeric=lambda x: (x, None), struct_one=lambda x: x,
                               stop_fields=lambda x: x)
    mc = {'schema': 'CASE13_FINAL_RESULT_BOUNDED_PROJECTION_V1', 'case': {'U': 1.0},
          'schemes': {name: {'recorded_starts': rs} for name, rs in starts.items()}}
    return rows, mc, consumer


class TestAssociation(unittest.TestCase):
    def test_valid_is_unknown_not_pass(self):
        rows, mc, consumer = fixture()
        r = under.make_report(rows, mc, consumer, gate)
        self.assertEqual(r['ao_phase_histories_associated_from_separate_events'], 8)
        self.assertIsNone(r['case_gate'])
        self.assertTrue(all(s['recorded_gate'] is None for s in r['schemes']))

    def test_duplicate_event_rejected(self):
        rows, mc, consumer = fixture()
        rows[-1] = copy.deepcopy(rows[-2])
        with self.assertRaises(ValueError):
            under.make_report(rows, mc, consumer, gate)

    def test_wrong_phase_stop_rejected(self):
        rows, mc, consumer = fixture()
        next(r for r in rows if r['action'] == 'phase_end' and r['context']['scheme'] == 'AO')['fields']['actual_stop']['final_residual'] = 0.02
        with self.assertRaises(ValueError):
            under.make_report(rows, mc, consumer, gate)

    def test_extra_typed_stop_field_mismatch_rejected(self):
        rows, mc, consumer = fixture()
        p = next(r for r in rows if r['action'] == 'phase_end' and r['context']['scheme'] == 'AO')
        p['fields']['actual_stop']['total_backtracks'] = 4.0
        with self.assertRaises(ValueError):
            under.make_report(rows, mc, consumer, gate)

    def test_typed_float_bit_pattern_and_field_order(self):
        self.assertFalse(under.same_typed({'x': [0.0]}, {'x': [-0.0]}))
        self.assertFalse(under.same_typed({'tag': 'N', 'real': ['NaN']},
                                          {'tag': 'N', 'real': ['NaN']}))
        self.assertFalse(under.same_typed({'fields': ['a', 'b']}, {'fields': ['b', 'a']}))
        self.assertTrue(under.same_typed({'x': [1.0], 'y': True}, {'y': True, 'x': [1.0]}))

    def test_event_context_mismatch_rejected(self):
        rows, mc, consumer = fixture()
        next(r for r in rows if r['action'] == 'phase_end')['context']['start_id'] = 99
        with self.assertRaises(ValueError):
            under.make_report(rows, mc, consumer, gate)

    def test_wrong_outer_prefix_rejected(self):
        rows, mc, consumer = fixture()
        next(r for r in rows if r['action'] == 'AO_iteration')['fields']['history'][1] = 9.0
        with self.assertRaises(ValueError):
            under.make_report(rows, mc, consumer, gate)

    def test_qt_history_signed_zero_mismatch_rejected(self):
        rows, mc, consumer = fixture()
        q = next(r for r in rows if r['action'] == 'QT_loop_end')
        q['fields']['history'][0] = -0.0
        f = next(r for r in rows if r['action'] == 'execute_final' and r['context']['scheme'] == 'NoRIS')
        f['fields']['history'][0] = 0.0
        with self.assertRaises(ValueError):
            under.make_report(rows, mc, consumer, gate)

    def test_unknown_not_promoted_by_claim(self):
        rows, mc, consumer = fixture()
        mc['schemes']['AO']['recorded_starts'].pop()
        with self.assertRaises(ValueError):
            under.make_report(rows, mc, consumer, gate)

    def test_associated_negative_is_not_hidden_by_missing_limits(self):
        rows, mc, consumer = fixture()
        q = next(r for r in rows if r['action'] == 'QT_loop_end' and r['context']['scheme'] == 'NoRIS')
        f = next(r for r in rows if r['action'] == 'execute_final' and r['context']['scheme'] == 'NoRIS')
        q['fields']['history'] = [2.0, 1.0]
        f['fields']['history'] = [2.0, 1.0]
        r = under.make_report(rows, mc, consumer, gate)
        self.assertIs(r['case_gate'], False)
        self.assertIs(r['schemes'][0]['starts'][0]['recorded_gate'], False)

    def test_associated_AO_phase_decrease_is_not_hidden(self):
        rows, mc, consumer = fixture()
        p = next(r for r in rows if r['action'] == 'phase_end' and r['context']['scheme'] == 'AO')
        p['fields']['actual_history'] = [2.0, 1.0]
        r = under.make_report(rows, mc, consumer, gate)
        self.assertIs(r['case_gate'], False)
        self.assertIs(r['schemes'][2]['starts'][0]['recorded_gate'], False)


if __name__ == '__main__':
    unittest.main()
