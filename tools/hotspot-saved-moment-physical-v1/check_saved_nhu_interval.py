"""Conditional interval check of saved NHU ratio constraints, no optimizer.

Requires mpmath interval arithmetic. It evaluates the real-valued reconstructed
geometry model, not the historic floating-point execution. Its guarantee is
conditional on the interval library enclosing its elementary functions and on
the stated source/model inputs being the ones intended. No source identity,
unit-modulus phase equality, author reference or full paper PASS is asserted.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path

import mpmath as mp


def check(record):
    iv = mp.iv
    iv.dps = 65
    p = record['contract']['configuration']['reported']
    t = record['contract']['configuration']['tuned_not_reported']
    state = record['actual_start']['final_state']
    if state['no_ris'] is not False:
        raise ValueError('requires the saved RIS-enabled state')
    n, j, u, k = (p[x] for x in ('N', 'J', 'U', 'K'))
    if (not all(type(x) is int for x in (n, j, u, k)) or
            (n, j) != (16, 16) or not 1 <= u <= 6 or k != 16-u or
            t['feed_center_spacing_m'] != 50000 or
            type(p['kappa_satellite_db']) not in (int, float) or
            p['kappa_satellite_db'] not in (0, 10, 20)):
        raise ValueError('requires the declared U1..U6, beta 0/10/20 dB, 16-stream geometry')
    re, im = state['W']['real'], state['W']['imag']
    if len(re) != n or len(im) != n or any(len(row) != j for row in re + im):
        raise ValueError('beam dimensions do not match the declared case')

    def f(x):
        # JSON numbers were decoded as binary64. iv.mpf(float) captures those
        # exact floating values; integers are exact.
        if type(x) not in (int, float) or not math.isfinite(x):
            raise ValueError('expected a real scalar')
        return iv.mpf(x)

    # The original centered 4x4 grid is symmetric; source sorting is stable.
    # Exact squared grid radii preserve ties and the original enumeration.
    positions = [(Fraction(a, 2), Fraction(b, 2))
                 for a in (-3, -1, 1, 3) for b in (-3, -1, 1, 3)]
    order = sorted(range(n), key=lambda i: sum(x*x for x in positions[i]))
    chosen = order[-k:]
    spacing = f(t['feed_center_spacing_m'])
    centers = [(f(float(a))*spacing, f(float(b))*spacing) for a, b in positions]
    wavelength = iv.mpf(299792458) / f(p['frequency_hz'])
    height = f(p['leo_height_m'])
    diameter = f(p['antenna_diameter_m'])
    noise = f(1.380649e-23) * f(p['temperature_k']) * f(p['bandwidth_hz'])
    sat_gain = iv.power(10, f(p['satellite_gain_dbi'])/10)
    rx_gain = iv.power(10, f(t['ground_receive_gain_dbi'])/10)
    beta = iv.power(10, f(p['kappa_satellite_db'])/10)
    target = iv.power(10, f(p['nhu_statistical_sinr_db'])/10)
    if not (wavelength.a > 0 and height.a > 0 and noise.a > 0 and beta.a >= 0):
        raise ValueError('nonpositive source parameters')

    def pattern_argument(x):
        """Entire even B(x), with a proven geometric bound on omitted terms."""
        if not (x.a >= 0 and x.b < 30):
            raise ValueError('Bessel argument outside the 0..30 proof range')
        x2 = x*x
        a, b = iv.mpf(1)/4, iv.mpf(3)/4
        total = a+b
        # Terms through k=160. For either tail, all subsequent absolute term
        # ratios are bounded by 30^2/[4*161*162] < 1.
        for index in range(1, 161):
            a = -a*x2/(4*index*(index+1))
            b = -b*x2/(4*index*(index+3))
            total += a+b
        next_a = -a*x2/(4*161*162)
        next_b = -b*x2/(4*161*164)
        ratio = iv.mpf(900)/(4*161*162)
        bound = (abs(next_a).b + abs(next_b).b)/(1-ratio)
        return total + iv.mpf([-1, 1])*bound

    wre = [[f(re[a][b]) for b in range(j)] for a in range(n)]
    wim = [[f(im[a][b]) for b in range(j)] for a in range(n)]
    margins = []
    for offset, center_index in enumerate(chosen):
        x, y = centers[center_index]
        distance = iv.sqrt(height*height+x*x+y*y)
        common = wavelength/(4*iv.pi*distance)/iv.sqrt(noise)
        amplitude = []
        for cx, cy in centers:
            rho2 = (cx-x)*(cx-x)+(cy-y)*(cy-y)
            # sin(atan(rho/height)) = rho/sqrt(height²+rho²).
            arg = iv.pi*diameter/wavelength * iv.sqrt(rho2)/iv.sqrt(height*height+rho2)
            # The source has a numerically constant branch close to zero.
            if arg.b <= iv.mpf('1e-8'):
                pattern = iv.mpf(1)
            elif arg.a > iv.mpf('1e-8'):
                pattern = pattern_argument(arg)**2
            else:
                raise ValueError('argument interval crosses source branch threshold')
            amplitude.append(iv.sqrt(pattern*sat_gain*rx_gain)*common)
        received = []
        for stream in range(j):
            diagonal = iv.mpf(0)
            sr, si = iv.mpf(0), iv.mpf(0)
            for feed in range(n):
                a = amplitude[feed]
                wr, wi = wre[feed][stream], wim[feed][stream]
                diagonal += a*a*(wr*wr+wi*wi)
                sr += a*wr
                si += a*wi
            # The common propagation phase cancels in this second moment.
            received.append((diagonal+beta*(sr*sr+si*si))/(1+beta))
        user = u+offset
        denominator = 1 + sum((received[z] for z in range(j) if z != user), iv.mpf(0))
        if not denominator.a > 0:
            raise ValueError('interval denominator is not strictly positive')
        margin = received[user]/denominator-target
        margins.append(margin)
    return {
        'scope': f'{k} NHU QoS ratios, one saved binary64 beam, reconstructed geometry',
        'arithmetic': 'mpmath.iv 65 decimal digits, entire Bessel series with explicit geometric tail',
        'model_conditions': ['exact decoded binary64 inputs, ideal real arithmetic',
                             'current geometry and all-J interference, not authenticated historic inputs',
                             'interval elementary function correctness is assumed'],
        'target_interval': str(target),
        'nhu_margin_intervals': [str(m) for m in margins],
        'all_margin_lower_bounds_positive': all(m.a > 0 for m in margins),
        'definitely_negative_count': sum(m.b < 0 for m in margins),
        'zero_crossing_count': sum(m.a <= 0 <= m.b for m in margins),
        'phase_unit_modulus_proven': False,
        'historical_source_authenticated': False,
        'convergence_or_full_paper_pass': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', required=True, type=Path)
    args = parser.parse_args()
    if args.result.stat().st_size > 4*1024*1024:
        raise ValueError('result exceeds bounded input size')
    def reject_constant(value):
        raise ValueError('nonfinite JSON constant: '+value)
    result = check(json.loads(args.result.read_text(encoding='utf-8-sig'),
                              parse_constant=reject_constant))
    print(json.dumps(result, indent=2, allow_nan=False))
    if not result['all_margin_lower_bounds_positive']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
