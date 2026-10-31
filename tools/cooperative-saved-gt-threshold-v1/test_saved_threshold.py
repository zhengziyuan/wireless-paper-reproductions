"""In-memory structural rejection tests; no scientific task or filesystem writes."""
import copy
from check_saved_threshold import EXPECTED_SCHEMES, analyze_result


def rejects(value):
    try:
        analyze_result(value, [0.01], [50, 50, 50])
    except ValueError:
        return
    raise AssertionError('invalid stored record accepted')


def main():
    data = {'configuration': {'tuned_not_reported': {'solver_objective_tolerance': 1e-5}},
            'results': [{'constraint_pass': True,
                         'schemes': [{'scheme': n, 'evaluation': {'gt_interference': [0.005],
                                                                    'satellite_power': [1., 2., 3.]}}
                                     for n in sorted(EXPECTED_SCHEMES)]}]}
    assert analyze_result(data, [0.01], [50, 50, 50])['stored_constraint_pass']
    duplicate = copy.deepcopy(data)
    duplicate['results'][0]['schemes'][0]['scheme'] = duplicate['results'][0]['schemes'][1]['scheme']
    rejects(duplicate)
    for field, bad in [('gt_interference', [-1.]), ('satellite_power', [1., -2., 3.])]:
        invalid = copy.deepcopy(data)
        invalid['results'][0]['schemes'][0]['evaluation'][field] = bad
        rejects(invalid)
    print('PASS: expected scheme uniqueness and nonnegative saved power/interference')


if __name__ == '__main__':
    main()
