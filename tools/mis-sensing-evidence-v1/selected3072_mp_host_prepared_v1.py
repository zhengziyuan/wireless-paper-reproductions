"""Disabled host for one saved MIS sensing state, not a science admission.

The optional host performs no work on import.  A future guarded revision must
bind the exact source, input and mpmath bytes, hold a unique output directory,
control the process tree, and enforce the existing storage policy.  Current
CLI execution is deliberately disabled and never opens the real inputs.
"""
from __future__ import annotations

import argparse
import math
import sys
from decimal import Decimal, localcontext
from fractions import Fraction

sys.dont_write_bytecode = True
REAL_EXECUTION_ENABLED = False


def prepare(best, field_evidence):
    """Extract fixed input without projection, search, random draws or I/O."""
    if best.get('original_start') != 3072:
        raise ValueError('wrong saved start')
    if best.get('configuration') != {'ms1': [20, 20], 'ms2': [16, 16], 'Kphi': 3, 'Ktheta': 3}:
        raise ValueError('wrong saved scenario')
    s, state, metric = best['settings'], best['state'], best['metrics']
    required = (-73.88, 'inverse_watt', 'raw_per_PRI', 1, 30)
    actual = (s['reference_echo_db'], s['reference_echo_unit'],
              s['reference_echo_noise_domain'], s['effective_reference_gain_factor'], s['power_dbm'])
    if actual != required or s['spacing_over_wavelength'] != 1/3 or s['incidence_direction_cosines'] != [0, 0]:
        raise ValueError('normalization or geometry contract differs')
    def phase(name, count):
        z = state[name]
        if len(z['real']) != count or len(z['imag']) != count:
            raise ValueError('phase dimension')
        pairs = list(zip(z['real'], z['imag']))
        if any(type(v) not in (int, float) or not math.isfinite(float(v)) for pair in pairs for v in pair):
            raise ValueError('nonfinite phase')
        return pairs
    rows = state['X']; saved = metric['binary_schedule']
    if len(rows) != 9 or len(saved) != 9:
        raise ValueError('wrong target count')
    selections = []
    for row, binary in zip(rows, saved):
        if (len(row) != 25 or len(binary) != 25 or row != binary or
                any(type(v) not in (int, float) or v not in (0, 1) for v in row+binary) or sum(row) != 1):
            raise ValueError('saved schedule is not identical one-hot')
        selections.append(row.index(1))
    observed = field_evidence['observed_target_SINR_linear']
    if len(observed) != 9 or any(type(v) not in (int, float) or not math.isfinite(float(v)) or v < 0 for v in observed):
        raise ValueError('invalid saved field values')
    return {'ms1': (20, 20), 'ms2': (16, 16),
            'phi': phase('phi', 400), 'theta': phase('theta', 256),
            'selections': selections, 'azimuth_deg': [0, 45, 90] * 3,
            'elevation_deg': [30]*3 + [50]*3 + [70]*3,
            'spacing': s['spacing_over_wavelength'],
            'incidence': s['incidence_direction_cosines'],
            'echo_db': s['reference_echo_db'], 'power_dbm': s['power_dbm'],
            'saved_native_min': metric['min_binary_metric'],
            'saved_eta': state['eta'], 'saved_field_sinr': list(observed),
            'feasibility_tolerance': s['feasibility_tolerance']}


def evaluate(prepared, target_sinrs):
    """Compare two MP results and saved values; does not certify forward error."""
    keys = ('ms1','ms2','phi','theta','selections','azimuth_deg','elevation_deg',
            'spacing','incidence','echo_db','power_dbm')
    kwargs = {k: prepared[k] for k in keys}
    v80 = target_sinrs(**kwargs, dps=80)
    v100 = target_sinrs(**kwargs, dps=100)
    if len(v80) != 9 or len(v100) != 9:
        raise ValueError('checker did not return nine targets')
    with localcontext() as ctx:
        ctx.prec = 130
        a = [Decimal(v) for v in v80]; b = [Decimal(v) for v in v100]
        if not all(v.is_finite() and v >= 0 for v in a+b):
            raise ValueError('nonfinite MP output')
        saved = [Decimal(Fraction.from_float(float(v)).numerator) /
                 Decimal(Fraction.from_float(float(v)).denominator)
                 for v in prepared['saved_field_sinr']]
        native = Decimal(Fraction.from_float(float(prepared['saved_native_min'])).numerator) / Decimal(Fraction.from_float(float(prepared['saved_native_min'])).denominator)
        eta = Decimal(Fraction.from_float(float(prepared['saved_eta'])).numerator) / Decimal(Fraction.from_float(float(prepared['saved_eta'])).denominator)
        tol = Decimal(Fraction.from_float(float(prepared['feasibility_tolerance'])).numerator) / Decimal(Fraction.from_float(float(prepared['feasibility_tolerance'])).denominator)
        if not tol.is_finite() or tol <= 0: raise ValueError('invalid tolerance')
        return {'schema': 'MIS3072_SELECTED_TARGET_MP_REPORT_PREPARED_V1',
                'mp80_sinr': v80, 'mp100_sinr': v100,
                'mp80_mp100_max_abs': str(max(abs(x-y) for x,y in zip(a,b))),
                'mp100_saved_field_max_abs': str(max(abs(x-y) for x,y in zip(b,saved))),
                'mp100_min_minus_saved_native': str(min(b)-native),
                'eta_minus_mp100_min': str(eta-min(b)),
                'all_targets_eta_within_saved_tolerance': all(eta-v <= tol for v in b),
                'assumptions': 'inverse watt reference; raw per PRI; effective gain one',
                'normalization_author_unit_confirmed': False,
                'independent_interval_certificate': False,
                'full_scenario_or_paper_pass': False}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    if not REAL_EXECUTION_ENABLED:
        raise SystemExit('Real execution disabled pending source/guard admission.')
    raise SystemExit('No admitted real-input driver is implemented in this version.')


if __name__ == '__main__':
    main()
