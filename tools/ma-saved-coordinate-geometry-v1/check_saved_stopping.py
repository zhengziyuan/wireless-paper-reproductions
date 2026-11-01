#!/usr/bin/env python3
"""Check saved AO objective transitions and fractional stops; no optimizer run.

All numbers are interpreted as their serialized binary64 values.  This is a
numeric history check only, not an interval proof or a full convergence gate.
"""
import argparse
import json
import math
from fractions import Fraction
from pathlib import Path


def f(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Expected a finite number')
    return Fraction.from_float(float(value))


def analyze(geometry, records, config):
    if geometry['schema'] != 'MA_FIG5_CASE7_SAVED_SWEEP_GEOMETRY_INPUT_V1':
        raise ValueError('Incorrect saved geometry schema')
    if records['schema'] != 'MA_FIG5_CASE7_COORDINATE_RECORDS_V1':
        raise ValueError('Incorrect saved coordinate schema')
    if config['schema'] != 'MA_FIG5_CASE7_SAVED_STOP_CONFIG_V1':
        raise ValueError('Incorrect saved stopping configuration')
    job = geometry['job']
    if (job['figure'], job['point'], job['realization'], job['N'], job['M']) != (5, 30, 0, 6, 5):
        raise ValueError('Unexpected case')
    n = job['N']; cap = config['maximum_AO_iterations']; threshold = f(config['fractional_increase_threshold'])
    if type(cap) is not int or cap < 1 or threshold <= 0:
        raise ValueError('Invalid original configured controls')
    out = {}
    for mode in ('mrt', 'zf'):
        objectives = [f(x) for x in geometry['result']['history'][mode]['objective']]
        rows = records['modes'][mode]
        sweeps = len(objectives)-1
        if sweeps < 1 or sweeps > cap or len(rows) != n*sweeps:
            raise ValueError('Incomplete trajectory or exceeded configured budget')
        negative = zero = positive = 0
        for i, row in enumerate(rows):
            if (row['sweep'], row['antenna']) != divmod(i,n):
                raise ValueError('Unexpected coordinate update order')
            before, after = f(row['before']), f(row['after'])
            if i and before != f(rows[i-1]['after']):
                raise ValueError('Coordinate objective chain broken')
            if i % n == 0 and before != objectives[i//n]:
                raise ValueError('Sweep starting objective mismatch')
            if i % n == n-1 and after != objectives[i//n+1]:
                raise ValueError('Sweep ending objective mismatch')
            negative += after < before
            zero += after == before
            positive += after > before
        ratios = []
        for before, after in zip(objectives[:-1],objectives[1:]):
            if before == 0:
                raise ValueError('Fractional stopping rule undefined at saved zero objective')
            ratios.append((after-before)/abs(before))
        first = next((i for i,x in enumerate(ratios,1) if x < threshold),None)
        out[mode] = {'coordinate_updates':len(rows), 'negative_updates':negative, 'zero_updates':zero,
                     'positive_updates':positive, 'sweeps':sweeps,
                     'first_fractional_threshold_crossing_one_based':first,
                     'final_fractional_increase':float(ratios[-1]),
                     'configured_threshold':float(threshold),
                     'first_crossing_is_saved_final_sweep':first == sweeps,
                     'all_saved_steps_non_decreasing':negative == 0}
    return {'schema':'MA_FIG5_CASE7_SAVED_STOPPING_HISTORY_V1', 'modes':out,
            'scope':'One saved Python case; exact rational comparisons of serialized binary64 objectives and tolerance.',
            'limitations':['No proof of the mathematical limit, stationarity, global optimality, physical feasibility, MATLAB, paper reference or full figure.',
                           'The input histories are saved values; no historical loaded-code identity or forward error is certified.',
                           'Exact-rational ratio checks need not match floating comparison at a threshold boundary.'],
            'optimizer_or_random_draws':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('geometry',type=Path);p.add_argument('records',type=Path);p.add_argument('config',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=analyze(*(json.loads(x.read_text(encoding='utf8')) for x in (a.geometry,a.records,a.config)))
    with a.output.open('x',encoding='utf8',newline='\n') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')


if __name__ == '__main__':main()
