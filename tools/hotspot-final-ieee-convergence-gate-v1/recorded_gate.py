"""Conditional recorded-history gate; never changes an optimizer or its stops.

The output is a tri-state *evidence* assessment, not convergence or paper PASS.
An external, source-bound recorder must attest that all returned histories were
retained; that assertion itself is not authenticated by this module.
"""
import math


SCHEMES = ('NoRIS', 'TwoStage', 'AO')


def _number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _combine(states):
    if any(state is False for state in states):
        return False
    if not states or any(state is None for state in states):
        return None
    return True


def _observed_negative(history):
    # Even if a stop flag is missing, preserve a directly visible decrease.
    histories = list(history.values()) if isinstance(history, dict) else [history]
    for values in histories:
        if isinstance(values, list):
            for a, b in zip(values, values[1:]):
                if not (_number(a) and _number(b)):
                    continue
                if float(b) < float(a):
                    return True
    return False


def _observed_stop_failure(status):
    # Inspect only directly recognizable stop contradictions. This works even
    # when other fields or histories are absent, without inventing extra blocks.
    blocks = status.get('blocks') if isinstance(status, dict) else None
    if not isinstance(blocks, list):
        return False
    for stop in blocks:
        if not isinstance(stop, dict):
            continue
        if stop.get('converged') is False:
            return True
        residual, threshold, rule = stop.get('final_residual'), stop.get('threshold'), stop.get('stop_rule')
        if rule in ('Riemannian_gradient_norm', 'signed_relative_objective_increase') and _number(residual):
            if residual < 0:
                return True
            if stop.get('converged') is True and _number(threshold) and threshold > 0:
                if (rule == 'Riemannian_gradient_norm' and residual > threshold or
                        rule == 'signed_relative_objective_increase' and residual >= threshold):
                    return True
    return False


def _block(name, history, stop, expected_rule, capture_complete, declared_limits):
    out = {'name': name, 'recorded_gate': None, 'reason': None,
           'original_converged': stop.get('converged') if isinstance(stop, dict) else None,
           'negative_steps': None, 'history_count': None,
           'capture_complete_asserted': capture_complete}
    if not isinstance(history, list) or not all(_number(x) for x in history):
        if _observed_negative(history):
            out.update(recorded_gate=False, reason='recorded_objective_decrease'); return out
        # A missing history cannot hide a directly observed impossible norm or
        # an explicit unsuccessful original stop; neither establishes a pass.
        if isinstance(stop, dict) and stop.get('converged') is False:
            out.update(recorded_gate=False, reason='original_stop_not_reached'); return out
        if (expected_rule == 'Riemannian_gradient_norm' and isinstance(stop, dict)
                and stop.get('stop_rule') == expected_rule
                and _number(stop.get('final_residual')) and stop['final_residual'] < 0):
            out.update(recorded_gate=False, reason='negative_gradient_norm'); return out
        if (expected_rule == 'signed_relative_objective_increase' and isinstance(stop, dict)
                and stop.get('stop_rule') == expected_rule
                and _number(stop.get('final_residual')) and stop['final_residual'] < 0):
            out.update(recorded_gate=False, reason='negative_reported_relative_increment'); return out
        if _observed_stop_failure({'blocks':[stop]}):
            out.update(recorded_gate=False, reason='recorded_stop_failure'); return out
        out['reason'] = 'missing_or_invalid_history'; return out
    values = [float(x) for x in history]
    out['history_count'] = len(values)
    out['negative_steps'] = sum(b < a for a,b in zip(values,values[1:]))
    if out['negative_steps']:
        out.update(recorded_gate=False, reason='recorded_objective_decrease'); return out
    diffs = [b-a for a,b in zip(values, values[1:])]
    if not all(math.isfinite(d) for d in diffs):
        out['reason'] = 'nonfinite_difference'; return out
    if not isinstance(stop, dict) or stop.get('stop_rule') != expected_rule:
        out['reason'] = 'missing_or_incompatible_stop'; return out
    iterations, cap = stop.get('iterations'), stop.get('iteration_cap')
    residual, threshold = stop.get('final_residual'), stop.get('threshold')
    if (type(iterations) is not int or type(cap) is not int or iterations < 0 or
            cap < iterations or not _number(residual) or not _number(threshold) or threshold <= 0 or
            type(stop.get('converged')) is not bool):
        out['reason'] = 'invalid_stop_fields'; return out
    if expected_rule == 'Riemannian_gradient_norm' and residual < 0:
        out.update(recorded_gate=False, reason='negative_gradient_norm'); return out
    if expected_rule == 'signed_relative_objective_increase' and residual < 0:
        out.update(recorded_gate=False, reason='negative_reported_relative_increment'); return out
    if stop['converged'] is False:
        out.update(recorded_gate=False, reason='original_stop_not_reached'); return out
    expected_termination = ('gradient_tolerance' if expected_rule == 'Riemannian_gradient_norm'
                            else 'relative_improvement')
    if not isinstance(stop.get('termination'), str):
        out['reason'] = 'missing_original_termination'; return out
    if stop['termination'] != expected_termination:
        out.update(recorded_gate=False, reason='original_termination_inconsistent'); return out
    if not isinstance(declared_limits, dict):
        out['reason'] = 'declared_limits_missing'; return out
    tolerance_key = 'gradient_tolerance' if expected_rule == 'Riemannian_gradient_norm' else 'relative_tolerance'
    cap_key = 'rgd_max_iterations' if expected_rule == 'Riemannian_gradient_norm' else ('ao_max_iterations' if name == 'AO_outer' else 'qt_max_iterations')
    declared_tolerance, declared_cap = declared_limits.get(tolerance_key), declared_limits.get(cap_key)
    if (not _number(declared_tolerance) or declared_tolerance <= 0 or not _number(declared_cap)
            or declared_cap <= 0 or int(declared_cap) != declared_cap):
        out['reason'] = 'declared_limits_missing_or_invalid'; return out
    if threshold != declared_tolerance or cap != declared_cap:
        out.update(recorded_gate=False, reason='recorded_limits_mismatch'); return out
    if len(values) < 2 or len(values) != iterations+1:
        out['reason'] = 'history_missing_or_count_mismatch'; return out
    if expected_rule == 'Riemannian_gradient_norm':
        if residual > threshold:
            out.update(recorded_gate=False, reason='gradient_threshold_not_met'); return out
    elif len(values) >= 2:
        if residual >= threshold:
            out.update(recorded_gate=False, reason='reported_relative_threshold_not_met'); return out
        recomputed = (values[-1]-values[-2])/max(abs(values[-2]), 1e-12)
        if not math.isfinite(recomputed):
            out['reason'] = 'nonfinite_recomputed_residual'; return out
        if not math.isclose(recomputed, residual, rel_tol=1e-12, abs_tol=1e-15):
            out.update(recorded_gate=False, reason='residual_inconsistent'); return out
        if recomputed >= threshold:
            out.update(recorded_gate=False, reason='relative_threshold_not_met'); return out
    if capture_complete is not True:
        out['reason'] = 'complete_capture_not_attested'; return out
    out.update(recorded_gate=True, reason='conditional_recorded_checks_met')
    return out


def assess_start(record, *, complete_history_capture=False, declared_limits=None):
    """Assess actual execute_start fields. True is conditional on caller attestation.

    Current AO drops every inner phase history. Its phase blocks are therefore
    unknown even if their stored stop flags are true. No missing evidence is
    replaced with a successful result.
    """
    if type(complete_history_capture) is not bool:
        raise ValueError('complete_history_capture must be Boolean')
    if not isinstance(record, dict):
        return {'recorded_gate': None, 'reason': 'missing_start', 'blocks': []}
    name = record.get('scheme')
    status = record.get('status')
    out = {'scheme': name, 'start_id': record.get('start_id'),
           'original_convergence_check': record.get('checks', {}).get('convergence_pass')
               if isinstance(record.get('checks'), dict) else None,
           'original_status_converged': status.get('converged') if isinstance(status, dict) else None,
           'recorded_gate': None, 'blocks': [], 'reason': None}
    if name not in SCHEMES or record.get('executed') is not True:
        out['reason'] = 'missing_or_unexecuted_start'; return out
    if out['original_convergence_check'] is False or out['original_status_converged'] is False:
        out.update(recorded_gate=False, reason='original_start_reported_failure'); return out
    if out['original_convergence_check'] is not True or out['original_status_converged'] is not True:
        if _observed_stop_failure(status):
            out.update(recorded_gate=False, reason='recorded_stop_failure'); return out
        if _observed_negative(record.get('history')):
            out.update(recorded_gate=False, reason='recorded_objective_decrease'); return out
        out['reason'] = 'missing_original_convergence_flags'; return out
    blocks = status.get('blocks') if isinstance(status, dict) else None
    if not isinstance(blocks, list):
        if _observed_negative(record.get('history')):
            out.update(recorded_gate=False, reason='recorded_objective_decrease'); return out
        out['reason'] = 'missing_original_blocks'; return out
    history = record.get('history')
    if name == 'NoRIS':
        if len(blocks) != 1:
            if _observed_stop_failure(status):
                out.update(recorded_gate=False, reason='recorded_stop_failure'); return out
            if _observed_negative(history):
                out.update(recorded_gate=False, reason='recorded_objective_decrease'); return out
            out['reason'] = 'unexpected_block_count'; return out
        out['blocks'] = [_block('QT', history, blocks[0], 'signed_relative_objective_increase', complete_history_capture, declared_limits)]
    elif name == 'TwoStage':
        if len(blocks) != 2 or not isinstance(history, dict):
            if _observed_stop_failure(status):
                out.update(recorded_gate=False, reason='recorded_stop_failure'); return out
            if _observed_negative(history):
                out.update(recorded_gate=False, reason='recorded_objective_decrease'); return out
            out['reason'] = 'missing_two_stage_histories_or_blocks'; return out
        out['blocks'] = [
            _block('phase', history.get('phase'), blocks[0], 'Riemannian_gradient_norm', complete_history_capture, declared_limits),
            _block('QT', history.get('QT'), blocks[1], 'signed_relative_objective_increase', complete_history_capture, declared_limits)]
    else:
        if not blocks:
            if _observed_negative(history):
                out.update(recorded_gate=False, reason='recorded_objective_decrease'); return out
            out['reason'] = 'missing_AO_blocks'; return out
        outer = _block('AO_outer', history, blocks[-1], 'signed_relative_objective_increase', complete_history_capture, declared_limits)
        # An AO start has one phase block per outer update; current execute_start
        # discards their histories. A future recorder may supply them explicitly.
        if not isinstance(history, list) or len(blocks)-1 != max(0, len(history)-1):
            out['blocks'] = [outer, {'name': 'AO_phase_histories',
                                     'recorded_gate': False if _observed_stop_failure(status) else None,
                                     'reason': 'phase_block_count_unknown_or_mismatched'}]
        else:
            phase_checks = []
            phase_histories = record.get('phase_histories')
            if not isinstance(phase_histories, list) or len(phase_histories) != len(blocks)-1:
                if isinstance(phase_histories, list):
                    phase_checks.append({'name':'AO_phase_history_count',
                        'recorded_gate':False if any(_observed_negative(h) for h in phase_histories) else None,
                        'reason':'phase_history_count_mismatch'})
                phase_histories = [None] * (len(blocks)-1)
            for i, block in enumerate(blocks[:-1]):
                phase_checks.append(_block('AO_phase_'+str(i+1), phase_histories[i], block,
                                           'Riemannian_gradient_norm', complete_history_capture, declared_limits))
            out['blocks'] = [outer] + phase_checks
    out['recorded_gate'] = _combine([b['recorded_gate'] for b in out['blocks']])
    out['reason'] = 'conditional_block_aggregation'
    return out


def assess_case(case, u, *, complete_history_capture=False, declared_limits=None):
    """Gate every prescribed start 0..U without altering original case fields."""
    if type(u) is not int or not 1 <= u <= 6:
        raise ValueError('U must be an integer from 1 through 6')
    if type(complete_history_capture) is not bool:
        raise ValueError('complete_history_capture must be Boolean')
    schemes = case.get('schemes') if isinstance(case, dict) else None
    summaries = []
    for name in SCHEMES:
        s = schemes.get(name) if isinstance(schemes, dict) else None
        records = s.get('all_start_records') if isinstance(s, dict) else None
        if not isinstance(records, list):
            summaries.append({'scheme': name, 'recorded_gate': None, 'reason': 'missing_start_records', 'starts': []})
            continue
        ids = [r.get('start_id') if isinstance(r,dict) else None for r in records]
        identity_complete = (all(type(i) is int for i in ids) and sorted(ids) == list(range(u+1)))
        starts = []
        for start_id in range(u+1):
            matches = [r for r in records if isinstance(r,dict)
                       and type(r.get('start_id')) is int and r['start_id'] == start_id]
            if len(matches) != 1:
                starts.append({'recorded_gate': None, 'reason': 'missing_or_duplicate_start_id', 'start_id':start_id})
                continue
            r = matches[0]
            if r.get('scheme') != name:
                starts.append({'recorded_gate': None, 'reason': 'scheme_identity_mismatch', 'start_id':r['start_id']})
            else:
                starts.append(assess_start(r, complete_history_capture=complete_history_capture, declared_limits=declared_limits))
        summaries.append({'scheme': name,
                          'recorded_gate': _combine([s['recorded_gate'] for s in starts] +
                                                    [True if identity_complete else None]),
                          'reason': 'conditional_start_aggregation' if identity_complete else 'missing_or_duplicate_start_ids',
                          'starts': starts})
    case_identity_match = (isinstance(case, dict) and type(case.get('U')) is int
                           and case.get('U') == u and case.get('status') == 'executed')
    return {'schema': 'FINAL_IEEE_RECORDED_CONVERGENCE_GATE_V1',
            'original_case_checks': case.get('checks') if isinstance(case, dict) else None,
            'complete_history_capture_asserted': complete_history_capture,
            'declared_limits_authenticated': False,
            'capture_attestation_authenticated': False,
            'case_identity_fields_match': case_identity_match,
            'recorded_convergence_evidence_gate': _combine([s['recorded_gate'] for s in summaries] +
                                                         [True if case_identity_match else None]),
            'schemes': summaries,
            'mathematical_convergence_proved': False,
            'scientific_or_paper_pass': False}
