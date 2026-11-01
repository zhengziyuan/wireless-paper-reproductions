"""Synthetic unit tests only; no saved scientific case is read."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_saved_history import audit, audit_gradient_norm


def main():
    # production stop is recomputed and checked against its existing function.
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root/'strict'/'hotspot-satcom'))
    from termination import relative_stop, gradient_stop, stop_valid
    cases = [
        ([10.0, 10.0000005], True, True, True, 0),
        ([10.0, 10.0], True, True, True, 0),
        ([10.0, 9.9999995], True, True, False, 1),
        ([10.0, 9.0], True, True, False, 1),
        ([10.0, 9.9999995, 10.01], True, False, False, 1),
        ([10.0, 10.0000005], False, True, None, 0),
        ([10.0, 9.9999995], False, True, False, 1),
    ]
    for h, complete, old_expected, gate_expected, negative_count in cases:
        r = audit(h, 1e-5, complete)
        old = relative_stop(h, 20, 1e-5)
        assert r['production_signed_stop_recomputed'] is old_expected
        assert r['production_signed_stop_recomputed'] == old['converged']
        assert r['independent_recorded_stop_and_nondecrease_gate'] is gate_expected
        assert r['negative_increment_count'] == negative_count
    assert audit([10.0, 9.9999995], 1e-5, True)['negative_within_numerical_abs_tolerance_count'] == 1
    assert audit([10.0, 9.0], 1e-5, True)['negative_within_numerical_abs_tolerance_count'] == 0
    for h in ([], [10.0]):
        r = audit(h, 1e-5, True)
        assert r['independent_recorded_stop_and_nondecrease_gate'] is None
        assert r['production_signed_stop_recomputed'] is None
        assert relative_stop(h, 20, 1e-5)['converged'] is False
    for args in (([1.0, math.nan], 1e-5, True), ([1.0, math.inf], 1e-5, True),
                 ([1.0, 2.0], math.nan, True), ([1.0, 2.0], 1e-5, 1),
                 ([1.0, 2.0], 0.0, True), ([1.0, True], 1e-5, True)):
        try:
            audit(*args)
        except ValueError:
            continue
        raise AssertionError('invalid input accepted')
    for norm in (-1e-9, 0.0, 1e-6, 2e-6):
        r = audit_gradient_norm(norm, 1e-6)
        old = gradient_stop(norm, 1, 20, 1e-6)
        assert r['production_gradient_stop_recomputed'] == old['converged']
        assert stop_valid(old) == old['converged']
        assert r['independent_recorded_gradient_gate'] == (0 <= norm <= 1e-6)
    assert audit_gradient_norm(-1e-9, 1e-6)['production_gradient_stop_recomputed']
    assert not audit_gradient_norm(-1e-9, 1e-6)['independent_recorded_gradient_gate']
    for norm in (math.nan, math.inf):
        try:
            audit_gradient_norm(norm, 1e-6)
        except ValueError:
            continue
        raise AssertionError('invalid norm accepted')
    print('synthetic recorded-history audit tests passed; no scientific data run')


if __name__ == '__main__':
    main()
