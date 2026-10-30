"""Exact binary64 checks of one saved beam power and RIS phase vector.

This is not a QoS, convergence, source-provenance, or paper-acceptance check.
No channel or optimized state is recreated; the selected input is read only.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path


def finite_fraction(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('expected a finite numeric component')
    return Fraction(value)


def inspect(record):
    config = record['contract']['configuration']['reported']
    state = record['actual_start']['final_state']
    if state['no_ris'] is not False:
        raise ValueError('expected RIS-enabled state')
    n, j, m = (config[k] for k in ('N', 'J', 'M'))
    limit = finite_fraction(config['power_w'])
    if any(type(k) is not int or k <= 0 for k in (n, j, m)) or limit < 0:
        raise ValueError('invalid dimensions or power limit')
    phase = state['phi']; beams = state['W']
    pr, pi = phase['real'], phase['imag']
    wr, wi = beams['real'], beams['imag']
    if len(pr) != m or len(pi) != m or len(wr) != n or len(wi) != n:
        raise ValueError('invalid saved array dimensions')
    if any(len(row) != j for row in wr) or any(len(row) != j for row in wi):
        raise ValueError('invalid beam matrix dimensions')
    differences = [finite_fraction(x)**2 + finite_fraction(y)**2 - 1
                   for x, y in zip(pr, pi)]
    power = sum((finite_fraction(x)**2 + finite_fraction(y)**2
                 for xr, yi in zip(wr, wi) for x, y in zip(xr, yi)), Fraction(0))
    return {'scope': 'exact rational arithmetic on one serialized binary64 state',
            'phase_entries': m,
            'exact_unit_modulus_entries': sum(v == 0 for v in differences),
            'maximum_abs_unit_modulus_squared_error': float(max(map(abs, differences))),
            'exact_binary64_power_within_limit': power <= limit,
            'exact_power_limit_slack_watts': float(limit - power),
            'strict_qos_proven': False,
            'historical_source_authenticated': False,
            'full_paper_pass': False,
            'limitations': ['unit modulus deviations are representation-scale, not established physical failure',
                            'no channel, QoS, convergence, MATLAB, or original figure evaluation']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', required=True, type=Path)
    args = parser.parse_args()
    if args.result.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('result exceeds bounded input size')
    record = json.loads(args.result.read_text(encoding='utf-8-sig'),
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    print(json.dumps(inspect(record), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
