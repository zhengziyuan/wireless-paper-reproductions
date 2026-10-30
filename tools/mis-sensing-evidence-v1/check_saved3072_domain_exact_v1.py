"""Exact rational checks on one saved binary64 sensing state; no solver run."""
import argparse
import json
from fractions import Fraction
from pathlib import Path


def check(data):
    best = data['best']
    if best['original_start'] != 3072:
        raise ValueError('expected saved original start 3072')
    state, settings, metrics = best['state'], best['settings'], best['metrics']
    tolerance = Fraction.from_float(float(settings['feasibility_tolerance']))
    if tolerance <= 0:
        raise ValueError('invalid feasibility tolerance')
    phases = {}
    for key, n in [('phi', 400), ('theta', 256)]:
        z = state[key]
        if len(z['real']) != n or len(z['imag']) != n:
            raise ValueError('unexpected phase dimensions')
        residual = [Fraction.from_float(float(a))**2 + Fraction.from_float(float(b))**2 - 1
                    for a, b in zip(z['real'], z['imag'])]
        maximum = max(abs(v) for v in residual)
        phases[key] = {'count': n, 'strict_nonunit_count': sum(v != 0 for v in residual),
                       'max_absolute_squared_modulus_error': float(maximum),
                       # |sqrt(x)-1| <= |x-1| for x>=0.
                       'modulus_error_below_feasibility_tolerance': maximum <= tolerance}
    x = state['X']
    if len(x) != 9 or any(len(row) != 25 for row in x):
        raise ValueError('unexpected schedule dimensions')
    values = [[Fraction.from_float(float(v)) for v in row] for row in x]
    is_onehot = all(all(v in (0, 1) for v in row) and sum(row) == 1 for row in values)
    binary = metrics['binary_schedule']
    identical = values == [[Fraction.from_float(float(v)) for v in row] for row in binary]
    dual = [Fraction.from_float(float(v)) for v in metrics['multipliers']]
    if len(dual) != 9:
        raise ValueError('unexpected multiplier dimensions')
    eta = Fraction.from_float(float(state['eta']))
    saved_min = Fraction.from_float(float(metrics['min_binary_metric']))
    return {'scope': 'Saved native start 3072 only. Exact rational comparisons on serialized binary64 values; no new model evaluation.',
            'phases': phases, 'schedule_exact_onehot': is_onehot,
            'stored_binary_schedule_matches_state': identical,
            'saved_dual_multipliers_nonnegative': all(v >= 0 for v in dual),
            'saved_eta_minus_saved_min_binary_metric': float(eta-saved_min),
            'saved_binary_metric_within_tolerance': eta-saved_min <= tolerance,
            'tolerance': float(tolerance),
            'limits': ['Computed norm-squared bounds are exact for stored binary64 components, not a forward-model interval.',
                       'The saved minimum SINR was not recomputed and cannot prove physical SINR agreement.',
                       'This is not stationarity, convergence, MATLAB/Python, full figure or paper verification.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = check(json.loads(args.input.read_text(encoding='utf8')))
    with args.output.open('x', encoding='utf8', newline='\n') as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write('\n')


if __name__ == '__main__':
    main()
