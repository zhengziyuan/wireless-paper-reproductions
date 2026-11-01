"""Small synthetic checks; no actual trajectory or optimizer is used."""
import copy
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_saved_qt import analyze, EXPECTED


def n(values):
    return {'tag': 'N', 'header': {'class': 'double', 'isreal': True,
            'size': [len(values), 1]}, 'real': values}


def s(values):
    return {'tag': 'S', 'header': {'size': [1, 1]}, 'values': [values]}


def h(value):
    return {'tag': 'H', 'value': value}


def fixtures():
    params = {'schema': 'CASE13_AO_FINAL_PARAMETERS_IDENTITY_V1', 'events': []}
    rows = []
    for start in (0, 1):
        ctx = {'start_id': start, 'case_id': 13, 'U': 1, 'beta': 20,
               'scheme': 'AO', 'geometry_id': 12013}
        params['events'].append({'context': ctx, 'fields': {
            'target': {'shape': [15, 1], 'real': [.5] * 15},
            'power': {'shape': [1, 1], 'real': [100.]}}})
    for ordinal, start in EXPECTED.items():
        ctx = {'start_id': start, 'case_id': 13, 'U': 1, 'beta': 20,
               'scheme': 'AO', 'geometry_id': 12013}
        diag = s({'solver': h('toy'), 'status': h('Solved'),
                  'reported_solver_tolerance': n([1e-9]),
                  'constraint_max_relative_violation': n([0.]),
                  'qt_bound_max_violation': n([0.])})
        point = s({'hu_sum_rate': n([1.]), 'total_power': n([100.])})
        q = {'solver_status': h('Solved'), 'solver_diagnostics': diag,
             'before': point, 'after': copy.deepcopy(point), 'qos_lower_bounds': n([.6] * 15),
             'qos_auxiliaries_are_exact_vector_QT': {'tag': 'L', 'header': {'size': [1, 1]}, 'values': [True]},
             'qt_bound_max_violation': n([0.]), 'qt_tightness_error': n([0.])}
        rows.append({'action': 'AO_iteration', 'ordinal': ordinal, 'context': ctx,
                     'fields': {'QT_info': s(q)}})
    return rows, params


def rejected(rows, params):
    try:
        analyze(rows, params)
    except (KeyError, ValueError, TypeError):
        return
    raise AssertionError('malformed evidence accepted')


def main():
    rows, params = fixtures()
    report = analyze(rows, params)
    assert sum(x['strictly_positive_qos_lower_bound_gaps'] for x in report['records']) == 120
    assert not report['full_paper_pass']
    altered = copy.deepcopy(rows)
    q = altered[0]['fields']['QT_info']['values'][0]
    q['qos_lower_bounds']['real'][0] = .5
    q['solver_diagnostics']['values'][0]['status'] = h('Failed')
    q['after']['values'][0]['total_power'] = n([101.])
    a = analyze(altered, params)['records'][0]
    assert a['strictly_positive_qos_lower_bound_gaps'] == 14
    assert not a['statuses_match'] and a['power_after_binary64_minus_limit']['approx'] == 1.
    for mutation in ('ordinal', 'start', 'shape', 'nan', 'negative', 'duplicate'):
        bad = copy.deepcopy(rows)
        q = bad[0]['fields']['QT_info']['values'][0]
        if mutation == 'ordinal': bad[0]['ordinal'] = -1
        elif mutation == 'start': bad[0]['context']['start_id'] = 1
        elif mutation == 'shape': q['qos_lower_bounds']['header']['size'] = [1, 15]
        elif mutation == 'nan': q['qos_lower_bounds']['real'][0] = math.nan
        elif mutation == 'negative': q['qt_tightness_error'] = n([-1.])
        else: bad[-1] = copy.deepcopy(bad[0])
        rejected(bad, params)
    rejected(rows[:-1], params)
    print('synthetic QT diagnostic tests passed')


if __name__ == '__main__':
    main()
