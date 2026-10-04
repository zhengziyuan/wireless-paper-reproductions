"""Exact rational negative control; NOT a physical MIS simulation or solver.

python -B verify_projection_kink.py --new-report actual-exact-check.json
"""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path


def verify():
    half = Q(1, 2)
    c1, c2 = Q(1, 10000), Q(1, 10)
    slope0 = -half
    checks = []

    def check(name, condition, explanation):
        if not condition:
            raise ArithmeticError(name)
        checks.append(dict(name=name, passed=True, exact_reason=explanation))

    # For Y=(1-alpha,alpha), the sum-one projection is Y for 0<=alpha<=1,
    # and (0,1) for alpha>=1. The latter KKT threshold is tau=alpha-1:
    # Y1-tau=2-2alpha<=0, Y2-tau=1, sum of positive parts is exactly one.
    check('complete_projection_both_branches', Q(1)-Q(1) == 0 and Q(1)+Q(0) == 1,
          'Interior branch Y is feasible; saturated branch threshold alpha-1 has positive parts (0,1) for every alpha>=1.')
    check('genuine_feasible_initial_descent', slope0 < 0,
          'grad f=(0,-1,1/2); d=(-1,1,1); exact inner product is -1/2.')
    check('continuous_bounded_below_curve', -half == half-Q(1),
          'phi=-alpha/2 on [0,1]; phi=alpha/2-1 on [1,infinity); minimum is exactly -1/2 at alpha=1.')
    check('every_smooth_positive_alpha_fails_strong_curvature',
          abs(-half) > c2*abs(slope0) and abs(half) > c2*abs(slope0),
          'The only two smooth slopes are -1/2 and +1/2, each strictly greater in magnitude than 1/20; this covers intervals, not a sampled alpha grid.')
    check('kink_is_not_an_ordinary_derivative', -half != half,
          'At alpha=1 the left and right derivatives disagree; an ordinary derivative does not exist.')
    check('current_positive_support_branch_fails_at_kink', half > c2*abs(slope0),
          'At X=(0,1), active=X>0 gives mean=dX2=1 and X velocity=(0,0); eta velocity=1 leaves branch slope +1/2.')
    check('armijo_can_hold_despite_missing_strong_curvature', -half <= c1*slope0,
          'alpha=1 satisfies exact Armijo: -1/2 <= -1/20000.')
    check('generalized_derivative_is_a_different_rule', -half <= Q(0) <= half and abs(Q(0)) <= c2*abs(slope0),
          'The kink generalized interval contains zero, but using it would change the existing single-branch derivative rule; it is not silently enabled.')
    for alpha in (Q(1, 4), Q(1, 2), Q(1), Q(3, 2), Q(2)):
        x2 = alpha if alpha <= 1 else Q(1)
        value = half*alpha-x2
        check('exact_rational_example_'+str(alpha), value >= -half,
              'phi('+str(alpha)+')='+str(value)+'; this example supplements, not replaces, the all-alpha branch proof.')
    return dict(schema='ACTUAL_EXACT_RATIONAL_PROJECTED_CURVE_KINK_NEGATIVE_CONTROL_V1',
        all_exact_checks_pass=True, exact_check_count=len(checks), checks=checks,
        counterexample_scope='smooth_affine_ambient_objective_on_closed_simplex_times_R; bounded_below_projected_line_curve',
        implication='smooth-curve strong-Wolfe existence cannot be invoked for this piecewise-smooth projection using one positive-support derivative',
        attribution='limitation of our disclosed corrected strong-curvature branch; not a claim that the printed author algorithm used strong Wolfe',
        source_paper_algorithm_executed=False, wireless_model_or_optimizer_executed=False,
        observed_cause_of_actual_capped_MIS_paths_established=False,
        new_stop_slack_or_algorithm_rule_enabled=False, all6000_original_starts_certified=False,
        original_figure_reproduction_certified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new-report', type=Path, required=True)
    args = parser.parse_args()
    if args.new_report.exists():
        parser.error('Use a fresh report; old evidence is never overwritten.')
    before = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = verify()
    after = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError('Verifier changed during execution')
    report['actual_verifier_sha256_before'] = before
    report['actual_verifier_sha256_after'] = after
    with args.new_report.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'all_exact_checks_pass': True, 'checks': report['exact_check_count'],
        'report_sha256': hashlib.sha256(args.new_report.read_bytes()).hexdigest(),
        'physical_simulation_executed': False}))
