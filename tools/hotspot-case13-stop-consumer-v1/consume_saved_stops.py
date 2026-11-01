"""Inspect *recorded* case-13 stops without running any optimization.

This reader is deliberately descriptive: a complete projection is not proof
that the historical writer retained a complete optimization trajectory.
"""
import argparse
import json
import math
from pathlib import Path

MAX_STREAM = 512 * 1024
MAX_SUMMARY = 4096
EXPECTED = {
    'QT_loop_end': (1327161, 1327226, 1327397, 1327567),
    'phase_end': (1327318, 1327488, 1327665, 1327712, 1327754,
                  1327777, 1327875, 1327925, 1327963, 1328003),
    'AO_iteration': (1327666, 1327713, 1327755, 1327778,
                     1327876, 1327926, 1327964, 1328004),
    'execute_final': (1327162, 1327227, 1327398, 1327568, 1327779, 1328005),
}
CONTEXT_BY_ORDINAL = {
    **{n: ('NoRIS', 0) for n in (1327161, 1327162)},
    **{n: ('NoRIS', 1) for n in (1327226, 1327227)},
    **{n: ('TwoStage', 0) for n in (1327318, 1327397, 1327398)},
    **{n: ('TwoStage', 1) for n in (1327488, 1327567, 1327568)},
    **{n: ('AO', 0) for n in (1327665, 1327666, 1327712, 1327713,
                              1327754, 1327755, 1327777, 1327778, 1327779)},
    **{n: ('AO', 1) for n in (1327875, 1327876, 1327925, 1327926,
                              1327963, 1327964, 1328003, 1328004, 1328005)},
}


def need(test, text):
    if not test:
        raise ValueError(text)


def no_dupes(pairs):
    result = {}
    for k, v in pairs:
        need(k not in result, 'duplicate JSON key')
        result[k] = v
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=no_dupes,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def numeric(node, *, real=True):
    need(isinstance(node, dict) and node.get('tag') == 'N', 'expected numeric node')
    h = node['header']
    need(h.get('class') == 'double' and h.get('order') == 'MATLAB_column_major', 'numeric ABI')
    values = node['real']
    need(isinstance(values, list) and h.get('numel') == len(values), 'numeric count')
    need(all(type(v) in (int, float) and math.isfinite(v) for v in values), 'nonfinite numeric')
    need(not real or h.get('isreal') is True, 'complex history or scalar')
    imag = node.get('imag')
    if h.get('isreal') is False:
        need(isinstance(imag, list) and len(imag) == len(values) and
             all(type(v) in (int, float) and math.isfinite(v) for v in imag), 'invalid imaginary numeric')
    elif imag is not None:
        raise ValueError('imaginary value on real numeric')
    return [float(x) for x in values], None if imag is None else [float(x) for x in imag]


def scalar(node):
    vals, _ = numeric(node)
    need(len(vals) == 1, 'expected numeric scalar')
    return vals[0]


def struct_one(node):
    need(isinstance(node, dict) and node.get('tag') == 'S' and
         node.get('header', {}).get('class') == 'struct', 'expected struct')
    vals = node.get('values')
    need(isinstance(vals, list) and len(vals) == 1 and isinstance(vals[0], dict), 'expected scalar struct')
    return vals[0]


def boolean(node):
    need(node.get('tag') == 'L' and node.get('header', {}).get('class') == 'logical', 'expected logical')
    vals = node.get('values')
    need(isinstance(vals, list) and len(vals) == 1 and type(vals[0]) is bool, 'expected logical scalar')
    return vals[0]


def char(node):
    need(node.get('tag') == 'H' and node.get('header', {}).get('class') == 'char' and
         isinstance(node.get('value'), str), 'expected char')
    return node['value']


def stop_fields(node):
    s = struct_one(node)
    return {'converged': boolean(s['converged']), 'termination': char(s['termination']),
            'iterations': scalar(s['iterations']), 'iteration_cap': scalar(s['iteration_cap']),
            'stop_rule': char(s['stop_rule']), 'threshold': scalar(s['threshold']),
            'final_residual': scalar(s['final_residual'])}


def stand_alone_stop(node):
    """Preserve a stop's own report; without its history it cannot be verified."""
    s = stop_fields(node)
    need(s['threshold'] > 0 and s['iterations'] >= 0 and s['iterations'].is_integer() and
         s['iteration_cap'] >= s['iterations'] and s['iteration_cap'].is_integer(), 'invalid stop metadata')
    s['history_for_this_stop_provided'] = False
    if s['stop_rule'] == 'Riemannian_gradient_norm':
        s['nonnegative_norm'] = s['final_residual'] >= 0
        s['expression_on_reported_norm'] = 0 <= s['final_residual'] <= s['threshold']
    elif s['stop_rule'] == 'signed_relative_objective_increase':
        s['negative_reported_residual'] = s['final_residual'] < 0
        s['expression_on_reported_residual'] = s['final_residual'] < s['threshold']
    else:
        s['independent_interpretation'] = 'unsupported_stop_rule'
    return s


def final_status(node):
    s = struct_one(node)
    result = {'reported_converged': boolean(s['converged']),
              'reported_algorithm_success': boolean(s['algorithm_success']),
              'reported_termination': char(s['termination']),
              'blocks_interpreted_as_independent_scientific_pass': False}
    blocks = s.get('blocks')
    if not isinstance(blocks, dict) or blocks.get('tag') != 'C':
        result['blocks_status'] = 'unsupported_or_missing_cell'
        return result
    items = blocks.get('values')
    need(isinstance(items, list) and len(items) <= 256, 'invalid stop block list')
    result['blocks'] = []
    for index, item in enumerate(items):
        try:
            result['blocks'].append(stand_alone_stop(item))
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            result['blocks'].append({'index_one_based': index+1,
                'inspection_status': 'insufficient_or_invalid_fields', 'detail': str(exc)[:160]})
    return result


def check_history(values):
    diffs = [y - x for x, y in zip(values, values[1:])]
    need(all(math.isfinite(d) for d in diffs), 'nonfinite difference')
    negative = [{'index_one_based': i + 1, 'difference': d}
                for i, d in enumerate(diffs) if d < 0]
    return {'recorded_points': len(values), 'recorded_negative_differences': negative,
            'all_recorded_differences_nonnegative': None if not diffs else not negative}


def check_separate_histories(node):
    """Do not compare the end of a QT history to the start of a phase history."""
    fields = struct_one(node)
    need(set(fields) == {'QT', 'phase'}, 'unknown separate-history fields')
    blocks = {}
    combined_negatives = []
    saw_difference = False
    for name in ('QT', 'phase'):
        values, _ = numeric(fields[name])
        block = check_history(values)
        blocks[name] = block
        saw_difference = saw_difference or len(values) >= 2
        combined_negatives.extend({'block': name, **d} for d in block['recorded_negative_differences'])
    return {'kind': 'separate_QT_and_phase_histories', 'blocks': blocks,
            'recorded_negative_differences': combined_negatives,
            'all_recorded_differences_nonnegative': None if not saw_difference else not combined_negatives,
            'cross_block_difference_computed': False}


def same_number(a, b):
    # Reports tolerance and raw discrepancy; it does not overwrite either value.
    return abs(a-b) <= 1e-12 * max(1.0, abs(a), abs(b))


def inspect_event(row):
    action, fields = row['action'], row['fields']
    context = row['context']
    need(all(context.get(k) == v for k, v in
             {'case_id': 13, 'geometry_id': 12013, 'U': 1, 'beta': 20}.items()), 'case identity')
    need(type(context.get('start_id')) is int and
         (context.get('scheme'), context.get('start_id')) == CONTEXT_BY_ORDINAL[row['ordinal']], 'start context')
    history_key = {'QT_loop_end': 'history', 'phase_end': 'actual_history',
                   'AO_iteration': 'history', 'execute_final': 'history'}[action]
    history_node = fields[history_key]
    if action == 'execute_final' and isinstance(history_node, dict) and history_node.get('tag') == 'S':
        hist = None
        history_report = check_separate_histories(history_node)
    else:
        hist, _ = numeric(history_node)
        history_report = check_history(hist)
    result = {'action': action, 'ordinal': row['ordinal'], 'scheme': context['scheme'],
              'start_id': context['start_id'], 'history': history_report,
              'source_trajectory_complete_proven': False}
    if action == 'AO_iteration':
        try:
            result['phase_stop_report'] = stand_alone_stop(fields['phase_stop'])
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            result['phase_stop_report'] = {'inspection_status': 'insufficient_or_invalid_fields',
                                           'detail': str(exc)[:160]}
        try:
            qt = struct_one(fields['QT_info'])
            result['QT_solver_status_reported'] = char(qt['solver_status'])
            if 'qt_bound_max_violation' in qt:
                result['QT_bound_max_violation_reported'] = scalar(qt['qt_bound_max_violation'])
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            result['QT_solver_status_reported'] = None
            result['QT_info_inspection'] = 'insufficient_or_invalid_fields'
            result['QT_info_detail'] = str(exc)[:160]
        result['QT_info_proves_physical_feasibility'] = False
        return result
    if action == 'execute_final':
        try:
            result['final_status_report'] = final_status(fields['status'])
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            result['final_status_report'] = {'inspection_status': 'insufficient_or_invalid_fields',
                                             'detail': str(exc)[:160]}
        return result
    stop = stop_fields(fields['stop' if action == 'QT_loop_end' else 'actual_stop'])
    need(stop['threshold'] > 0 and stop['iterations'] >= 0 and stop['iterations'].is_integer() and
         stop['iteration_cap'] >= stop['iterations'] and stop['iteration_cap'].is_integer(), 'invalid stop metadata')
    stop['history_count_matches_reported_iterations'] = len(hist) == int(stop['iterations']) + 1
    stop['saved_history_completeness_proven'] = False
    stop['comparison_mixed_tolerance_formula'] = '1e-12*max(1,abs(a),abs(b))'
    if stop['stop_rule'] == 'signed_relative_objective_increase':
        residual = None if len(hist) < 2 else (hist[-1]-hist[-2])/max(abs(hist[-2]), 1e-12)
        need(residual is None or math.isfinite(residual), 'invalid computed residual')
        stop['recomputed_residual'] = residual
        stop['residual_matches_record'] = None if residual is None else same_number(residual, stop['final_residual'])
        stop['recomputed_expression_triggered'] = None if residual is None else residual < stop['threshold']
        stop['negative_final_residual'] = None if residual is None else residual < 0
    elif stop['stop_rule'] == 'Riemannian_gradient_norm':
        stop['nonnegative_norm'] = stop['final_residual'] >= 0
        stop['recomputed_expression_triggered'] = 0 <= stop['final_residual'] <= stop['threshold']
        if action == 'phase_end':
            gr, gi = numeric(fields['final_gradient'], real=False)
            if gi is None:
                gi = [0.0] * len(gr)
            norm = math.hypot(*(gr + gi))
            need(math.isfinite(norm), 'invalid gradient norm')
            stop['recomputed_gradient_norm'] = norm
            stop['gradient_matches_record'] = same_number(norm, stop['final_residual'])
    else:
        stop['independent_interpretation'] = 'unsupported_stop_rule'
    # A reported flag is shown as a fact only; mismatches never become PASS.
    stop['flag_agrees_with_recomputed_expression'] = (
        None if stop.get('recomputed_expression_triggered') is None else
        stop['converged'] == stop['recomputed_expression_triggered'])
    result['stop_check'] = stop
    return result


def action_summary(records):
    """Summarize records, without upgrading reported values into a pass."""
    answer = {}
    for action in EXPECTED:
        selected = [r for r in records if r['action'] == action]
        stats = {'records': len(selected), 'uninspectable_events': 0,
                 'recorded_negative_steps': 0, 'reported_stop_converged_true': 0,
                 'reported_stop_converged_false': 0, 'negative_reported_norms': 0,
                 'history_count_inconsistencies': 0, 'residual_inconsistencies': 0,
                 'declared_flag_inconsistencies': 0, 'nested_fields_uninspectable': 0,
                 'reported_final_algorithm_success_false': 0, 'unsupported_stop_rules': 0}
        def add_stop(s):
            if not isinstance(s, dict) or s.get('inspection_status'):
                stats['nested_fields_uninspectable'] += 1
                return
            if s.get('converged') is True:
                stats['reported_stop_converged_true'] += 1
            elif s.get('converged') is False:
                stats['reported_stop_converged_false'] += 1
            if s.get('nonnegative_norm') is False:
                stats['negative_reported_norms'] += 1
            if s.get('history_count_matches_reported_iterations') is False:
                stats['history_count_inconsistencies'] += 1
            if s.get('residual_matches_record') is False or s.get('gradient_matches_record') is False:
                stats['residual_inconsistencies'] += 1
            if s.get('flag_agrees_with_recomputed_expression') is False:
                stats['declared_flag_inconsistencies'] += 1
            if s.get('independent_interpretation') == 'unsupported_stop_rule':
                stats['unsupported_stop_rules'] += 1
        for r in selected:
            if r.get('inspection_status'):
                stats['uninspectable_events'] += 1
                continue
            stats['recorded_negative_steps'] += len(r['history']['recorded_negative_differences'])
            if action in ('QT_loop_end', 'phase_end'):
                add_stop(r.get('stop_check'))
            elif action == 'AO_iteration':
                add_stop(r.get('phase_stop_report'))
                if r.get('QT_info_inspection'):
                    stats['nested_fields_uninspectable'] += 1
            else:
                st = r.get('final_status_report')
                if not isinstance(st, dict) or st.get('inspection_status'):
                    stats['nested_fields_uninspectable'] += 1
                    continue
                if st.get('reported_algorithm_success') is False:
                    stats['reported_final_algorithm_success_false'] += 1
                if st.get('blocks_status'):
                    stats['nested_fields_uninspectable'] += 1
                for block in st.get('blocks', []):
                    add_stop(block)
        answer[action] = stats
    return answer


def consume(rows, summary, partial_tail=False):
    need(isinstance(rows, list) and len(rows) <= 28, 'record bound')
    seen = set()
    output = []
    for row in rows:
        need(isinstance(row, dict) and row.get('action') in EXPECTED, 'unknown event')
        identity = (row['action'], row['ordinal'])
        need(row['ordinal'] in EXPECTED[row['action']] and identity not in seen, 'duplicate or unknown event')
        seen.add(identity)
        try:
            output.append(inspect_event(row))
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            # Unsupported or invalid records stay visible; never treat as PASS.
            output.append({'action': row['action'], 'ordinal': row['ordinal'],
                           'inspection_status': 'insufficient_or_invalid_fields',
                           'detail': str(exc)[:160], 'source_trajectory_complete_proven': False})
    expected = {(a, n) for a, ords in EXPECTED.items() for n in ords}
    declared_complete = (isinstance(summary, dict) and summary.get('schema') == 'CASE13_STOP_HISTORY_CHILD_SUMMARY_V1'
                         and summary.get('status') == 'completed' and summary.get('complete_records') == 28)
    coverage = (declared_complete and not partial_tail and seen == expected and
                all(x.get('inspection_status') != 'insufficient_or_invalid_fields' for x in output))
    stats = action_summary(output)
    no_detected_nested_errors = all(s['nested_fields_uninspectable'] == 0 and
                                    s['unsupported_stop_rules'] == 0 for s in stats.values())
    return {'schema': 'CASE13_RECORDED_STOP_CONSUMER_V1',
            'extraction_summary_declares_completed': declared_complete,
            'expected_events_and_histories_present': coverage,
            'no_detected_nested_interpretation_errors': no_detected_nested_errors if coverage else None,
            'all_74_extracted_fields_independently_interpreted': False,
            'partial_final_line': partial_tail,
            'recorded_event_counts_by_action': stats,
            'records': output,
            'source_historical_content_authenticated': False,
            'source_whole_event_atomicity_proven': False,
            'complete_optimization_trajectory_proven': False,
            'mathematical_convergence_proved': False,
            'physical_feasibility_proved': False,
            'full_paper_pass': False}


def read_limited(path, cap):
    with Path(path).open('rb') as f:
        raw = f.read(cap + 1)
    need(len(raw) <= cap, 'input exceeds bound')
    return raw


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stream', type=Path, required=True)
    p.add_argument('--summary', type=Path)
    args = p.parse_args()
    raw = read_limited(args.stream, MAX_STREAM)
    partial = bool(raw) and not raw.endswith(b'\n')
    lines = raw.splitlines()
    if partial:
        lines = lines[:-1]
    rows = [parse(line) for line in lines]
    summary = parse(read_limited(args.summary, MAX_SUMMARY)) if args.summary else None
    print(json.dumps(consume(rows, summary, partial), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
