"""Read-only scalar checks on the saved MIS sensing KKT fields.

The residual vector is taken from the saved last-outer summary.  Nothing here
re-evaluates physical SINR, phase gradients, the schedule gradient, or the
original reference units.  The file is not a full KKT or convergence test.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path


def load(path):
    if path.stat().st_size > 1_048_576:
        raise ValueError('selected saved state exceeds 1 MiB')
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('duplicate JSON key')
            out[key] = value
        return out
    with path.open(encoding='utf-8-sig') as stream:
        return json.load(stream, object_pairs_hook=unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def real_fraction(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('finite scalar required')
    # Saved binary64 components, not the unknown exact physical values.
    return Fraction.from_float(float(value))


def inspect(data):
    best = data['best']
    if best['original_start'] != 3072 or data['selection_complete_over6000'] is not True:
        raise ValueError('expected saved start 3072 of selected 6000-start population')
    metrics, history, status = best['metrics'], best['history'], best['solver_status']
    final = history[-1]
    if final['outer_iteration'] != 30 or final['eta'] != metrics['eta']:
        raise ValueError('last history does not match final stored eta/outer index')
    q, lam = list(map(real_fraction, final['q'])), list(map(real_fraction, metrics['multipliers']))
    if len(q) != 9 or len(lam) != 9:
        raise ValueError('expected nine saved targets')
    certificate = status['original_problem_kkt_certificate']
    primal = max([Fraction(0)] + q)
    dual = max([Fraction(0)] + [-a for a in lam])
    complementarity = max(abs(a*b) for a, b in zip(q, lam))
    eta_stationarity = abs(sum(lam) - 1)
    feas_tol = real_fraction(certificate['feasibility_tolerance'])
    stat_tol = real_fraction(certificate['stationarity_tolerance'])
    # Recorded maxima are rounded binary64 numbers, so compare at their
    # representation precision; rational calculations themselves are exact.
    rounded_match = (float(primal) == certificate['maximum_positive_primal_residual']
                     and float(dual) == certificate['maximum_negative_dual_residual']
                     and float(complementarity) == certificate['maximum_absolute_complementarity'])
    if not rounded_match:
        raise ValueError('saved scalar residual summaries do not match saved q/lambda')
    return {'scope': 'one saved sensing start: scalar q and multiplier fields only',
            'start': 3072, 'targets': 9,
            'eta_stationarity_absolute_exact_binary64': float(eta_stationarity),
            'eta_stationarity_below_reported_tolerance': eta_stationarity < stat_tol,
            'maximum_positive_saved_q_exact_binary64': float(primal),
            'maximum_negative_saved_multiplier_exact_binary64': float(dual),
            'maximum_absolute_q_lambda_exact_binary64': float(complementarity),
            'saved_scalar_primal_dual_complementarity_within_tolerance':
                primal <= feas_tol and dual <= feas_tol and complementarity <= feas_tol,
            'saved_certificate_scalar_values_match': rounded_match,
            'stored_outer_budget': len(history),
            'stored_inner_iteration_cap_exits': status['inner_iteration_cap_exits'],
            'stored_all_inner_tolerances_satisfied': status['all_inner_tolerances_satisfied'],
            'stored_convergence_verified': status['convergence_verified'],
            'limitations': ['q and multipliers are stored fields, not independent forward-model calculations',
                            'eta derivative is only one stationarity component; phase and schedule gradients are not evaluated',
                            'stored q may not independently establish correspondence to final physical state',
                            'no proof of physical feasibility, full KKT, convergence, MATLAB, reference units or whole-paper PASS']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-state', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(load(args.saved_state)), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
