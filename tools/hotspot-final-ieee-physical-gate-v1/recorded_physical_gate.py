"""Conditional post-hoc RIS phase check on final-IEEE saved start records.

No optimization is run and no original production check is changed. The
reported physical flag is not an independently verified power/SINR result.
"""
from fractions import Fraction
import math

SCHEMES = ('NoRIS', 'TwoStage', 'AO')
M = 25


def _combine(values):
    """Three-valued aggregation: a known failure dominates missing evidence."""
    if any(x is False for x in values):
        return False
    if any(x is None for x in values):
        return None
    return True


def _finite_rational(value):
    if type(value) not in (int, float):
        raise ValueError('finite real scalar required')
    if type(value) is int:
        return Fraction(value)
    if not math.isfinite(value):
        raise ValueError('finite real scalar required')
    return Fraction.from_float(value)


def _phase_assessment(phi, tolerance):
    if phi is None:
        return {'status': 'missing', 'exact_unit': None, 'within_tolerance': None}
    if not isinstance(phi, dict) or 'real' not in phi or 'imag' not in phi:
        return {'status': 'missing_or_invalid_encoding', 'exact_unit': None, 'within_tolerance': None}
    re, im = phi['real'], phi['imag']
    if not isinstance(re, list) or not isinstance(im, list):
        return {'status': 'invalid_shape', 'exact_unit': False, 'within_tolerance': False}
    if len(re) != M or len(im) != M:
        return {'status': 'invalid_shape', 'exact_unit': False, 'within_tolerance': False}
    try:
        entries = [(_finite_rational(a), _finite_rational(b)) for a, b in zip(re, im)]
    except ValueError:
        return {'status': 'invalid_or_nonfinite', 'exact_unit': False, 'within_tolerance': False}
    deviations = [abs(a*a+b*b-1) for a,b in entries]
    largest = max(deviations)
    return {'status': 'assessed', 'element_count': M,
            'max_squared_magnitude_error_exact': {'numerator': str(largest.numerator),
                                                  'denominator': str(largest.denominator)},
            'exact_unit': largest == 0,
            'within_tolerance': largest <= tolerance}


def assess_start(record, scheme, *, squared_magnitude_tolerance):
    """Assess observed final phase with an explicitly supplied tolerance.

    The tolerance is for max(abs(real^2+imag^2-1)); its input is interpreted
    exactly as the supplied binary64/int value. A Boolean reported physical
    flag is retained, never converted into independent power/SINR evidence.
    """
    tol = _finite_rational(squared_magnitude_tolerance)
    if tol < 0:
        raise ValueError('tolerance must be nonnegative')
    if scheme not in SCHEMES:
        raise ValueError('unknown scheme')
    if not isinstance(record, dict):
        return {'scheme': scheme, 'gate': None, 'reason': 'missing_start_record'}
    flags = record.get('checks')
    original = flags.get('physical_constraint_pass') if isinstance(flags, dict) else None
    original = original if type(original) is bool else None
    stated = record.get('scheme')
    executed = record.get('executed')
    state = record.get('final_state')
    no_ris = state.get('no_ris') if isinstance(state, dict) else None
    no_ris = no_ris if type(no_ris) is bool else None
    identity = (False if stated is not None and stated != scheme else
                False if executed is False else
                None if stated is None or executed is not True else True)
    expected_no_ris = scheme == 'NoRIS'
    flag_check = None if no_ris is None else no_ris == expected_no_ris
    if scheme == 'NoRIS':
        phase = {'status': 'not_applicable', 'exact_unit': None, 'within_tolerance': None}
        phase_gate = True
    else:
        phase = _phase_assessment(state.get('phi') if isinstance(state, dict) else None, tol)
        phase_gate = phase['within_tolerance']
    return {'scheme': scheme, 'start_id': record.get('start_id'),
            'original_reported_physical_constraint_pass': original,
            'input_identity_gate': identity, 'no_ris_flag_matches_scheme': flag_check,
            'phase': phase, 'squared_magnitude_tolerance': float(squared_magnitude_tolerance),
            'gate': _combine([identity, flag_check, original, phase_gate]),
            'gate_interpretation': 'conditional on original reported power/SINR check; phase checked separately',
            'power_or_sinr_independently_verified': False,
            'full_physical_or_paper_pass': False}


def assess_case(case, u, *, squared_magnitude_tolerance):
    """Aggregate unique prescribed starts; do not discard known failures."""
    if type(u) is not int or not 1 <= u <= 6:
        raise ValueError('U must be an integer from 1 through 6')
    tol = _finite_rational(squared_magnitude_tolerance)
    if tol < 0:
        raise ValueError('tolerance must be nonnegative')
    schemes = case.get('schemes') if isinstance(case, dict) else None
    results = []
    for name in SCHEMES:
        obj = schemes.get(name) if isinstance(schemes, dict) else None
        rows = obj.get('all_start_records') if isinstance(obj, dict) else None
        if not isinstance(rows, list):
            results.append({'scheme': name, 'starts': [], 'gate': None, 'reason': 'missing_records'})
            continue
        ids = [r.get('start_id') if isinstance(r, dict) else None for r in rows]
        complete = all(type(i) is int for i in ids) and sorted(ids) == list(range(u+1))
        starts = []
        for start in range(u+1):
            matches = [r for r in rows if isinstance(r, dict) and type(r.get('start_id')) is int
                       and r['start_id'] == start]
            if len(matches) != 1:
                starts.append({'start_id': start, 'gate': None, 'reason': 'missing_or_duplicate_start_id'})
            else:
                starts.append(assess_start(matches[0], name, squared_magnitude_tolerance=squared_magnitude_tolerance))
        results.append({'scheme': name, 'starts': starts,
                        'gate': _combine([s['gate'] for s in starts] + [True if complete else None]),
                        'reason': 'conditional_start_aggregation' if complete else 'missing_or_duplicate_start_ids'})
    identity = isinstance(case, dict) and type(case.get('U')) is int and case.get('U') == u and case.get('status') == 'executed'
    return {'schema': 'FINAL_IEEE_RECORDED_PHYSICAL_PHASE_GATE_V1',
            'caller_squared_magnitude_tolerance': float(squared_magnitude_tolerance),
            'tolerance_source_authenticated': False,
            'original_case_checks': case.get('checks') if isinstance(case, dict) else None,
            'case_identity_fields_match': identity,
            'conditional_reported_plus_phase_gate': _combine([s['gate'] for s in results] + [True if identity else None]),
            'schemes': results, 'power_or_sinr_independently_verified': False,
            'physical_model_or_paper_pass': False}
