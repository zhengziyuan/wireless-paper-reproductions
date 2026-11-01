"""Exact hypothetical input counterexamples, never a simulated solver result."""
from fractions import Fraction as F
import json


def norm_squared(x):
    return sum((v * v for v in x), F(0))


def candidate_counterexample():
    # U=1, K=1, N=2, Q=Psi=I2, D=I2, noise=1, P=10, target=1.
    noise, target, limit = F(1), F(1), F(10)
    old_hu, old_nhu = (F(0), F(0)), (F(1), F(0))
    hu, nhu = (F(0), F(1, 2)), (F(0), F(2))
    old_i = noise + norm_squared(old_hu)
    z = tuple(x / old_i for x in old_nhu)
    old_true_qos = norm_squared(old_nhu) / old_i
    old_lower = 2 * sum(x*y for x, y in zip(z, old_nhu)) - norm_squared(z)*old_i
    i = noise + norm_squared(hu)
    true_qos = norm_squared(nhu) / i
    lower = 2 * sum(x*y for x, y in zip(z, nhu)) - norm_squared(z)*i
    used_power = norm_squared(hu) + norm_squared(nhu)
    old_hu_sinr = norm_squared(old_hu) / (noise + norm_squared(old_nhu))
    new_hu_sinr = norm_squared(hu) / (noise + norm_squared(nhu))
    # Strictly increasing log2(1+x), so no float logarithm is needed.
    candidate_old_python_gate = (used_power / limit - 1 < F(1, 100000)
        and target - true_qos < F(1, 100000)
        and new_hu_sinr > old_hu_sinr)
    assert old_true_qos == old_lower == target
    assert candidate_old_python_gate and lower < target
    return {'old_qos': str(old_true_qos), 'old_fixed_qt_lower': str(old_lower),
            'candidate_power': str(used_power), 'power_limit': str(limit),
            'candidate_full_interference_qos': str(true_qos), 'target': str(target),
            'candidate_fixed_qt_lower': str(lower),
            'old_hu_sinr': str(old_hu_sinr), 'candidate_hu_sinr': str(new_hu_sinr),
            'existing_python_physical_and_objective_predicate_accepts': True,
            'candidate_violates_fixed_auxiliary_subproblem': True,
            'actual_solver_or_saved_run_examined': False}


def psd_counterexample():
    # Exact diagonal eigenvalues; this is intentionally NOT a valid covariance.
    positive, negative = F(1, 10**12), -F(9, 10**11)
    threshold = F(1, 10**10) * max(F(1), abs(positive), abs(negative))
    old_factor_accepts = negative >= -threshold
    original_norm_sq = positive**2 + negative**2
    clipped_error_sq = negative**2
    assert old_factor_accepts and negative < 0
    # Show relative Frobenius error is > 0.999 without a square root.
    assert clipped_error_sq * 10**6 > 998001 * original_norm_sq
    return {'matrix_diagonal': [str(positive), str(negative)],
            'old_negative_eigenvalue_threshold': str(threshold),
            'old_factor_accepts': old_factor_accepts,
            'relative_frobenius_clipping_error_exceeds': '0.999',
            'input_is_intentionally_invalid_covariance': True,
            'actual_physical_covariance_examined': False}


if __name__ == '__main__':
    print(json.dumps({'scope': 'hypothetical exact counterexamples only',
                      'candidate': candidate_counterexample(),
                      'psd_scale': psd_counterexample(),
                      'original_saved_results_modified': False,
                      'full_paper_pass': False}, indent=2))
