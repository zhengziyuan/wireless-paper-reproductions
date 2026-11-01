"""Independent recorded-history audit. Does not alter optimizer stop behavior."""
import math


def audit(history, tolerance, complete, numerical_abs_tolerance=1e-6):
    """Inspect binary64 values, preserving the production signed-stop definition.

    complete is the caller's assertion, not proof of complete provenance. The
    strict gate requires this assertion and never ignores any negative step.
    """
    if type(complete) is not bool:
        raise ValueError('complete must be a Boolean assertion')
    if not isinstance(history, (list, tuple)):
        raise ValueError('history must be a sequence')
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in history):
        raise ValueError('history must contain finite real scalars')
    for x in (tolerance, numerical_abs_tolerance):
        if type(x) not in (int, float) or not math.isfinite(x):
            raise ValueError('tolerances must be finite real scalars')
    if tolerance <= 0 or numerical_abs_tolerance < 0:
        raise ValueError('invalid tolerances')
    h = [float(x) for x in history]
    differences = [h[i+1]-h[i] for i in range(len(h)-1)]
    if any(not math.isfinite(x) for x in differences):
        raise ValueError('nonfinite computed difference')
    signed = None if not differences else differences[-1]/max(abs(h[-2]), 1e-12)
    if signed is not None and not math.isfinite(signed):
        raise ValueError('nonfinite computed signed residual')
    old_stop = None if signed is None else signed < tolerance
    negatives = [d for d in differences if d < 0]
    # A witnessed decrease disproves recorded nondecrease even if incomplete.
    # With no witnessed decrease an incomplete history cannot prove it.
    recorded_nondecrease = False if negatives else (True if complete and differences else None)
    gate = False if negatives else (None if not complete or not differences else bool(old_stop))
    return {'history_complete_asserted': complete, 'record_count': len(h),
            'differences': differences, 'signed_relative_increment': signed,
            'production_signed_stop_recomputed': old_stop,
            'negative_increment_count': len(negatives),
            'negative_within_numerical_abs_tolerance_count': sum(d >= -numerical_abs_tolerance for d in negatives),
            'numerical_abs_tolerance': float(numerical_abs_tolerance),
            'recorded_nondecrease': recorded_nondecrease,
            'independent_recorded_stop_and_nondecrease_gate': gate,
            'source_provenance_authenticated': False,
            'mathematical_convergence_proved': False,
            'full_paper_pass': False}


def audit_gradient_norm(norm, tolerance):
    """Check the recorded gradient stop, including the norm's nonnegativity."""
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in (norm, tolerance)):
        raise ValueError('finite real norm and tolerance required')
    if tolerance <= 0:
        raise ValueError('positive tolerance required')
    return {'production_gradient_stop_recomputed': norm <= tolerance,
            'norm_nonnegative': norm >= 0,
            'independent_recorded_gradient_gate': 0 <= norm <= tolerance,
            'mathematical_convergence_proved': False,
            'source_provenance_authenticated': False,
            'full_paper_pass': False}
