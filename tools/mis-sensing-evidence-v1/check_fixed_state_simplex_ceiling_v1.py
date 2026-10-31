#!/usr/bin/env python3
"""Exact ceiling over row-stochastic schedules for saved, approximate SINRs.

For each row of X, X>=0 and sum(X)=1; hence its weighted sum of Gamma is
at most that row's maximum. Extra constraints on X can only lower the ceiling.
The stored finite decimal estimates are interpreted exactly as rationals; no
error bound for the physical forward model, phase optimization or experiment
is implied.
"""
import argparse
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path


def display(x):
    with localcontext() as c:
        c.prec = 80
        return str(Decimal(x.numerator) / Decimal(x.denominator))


def evaluate(obj):
    if obj['schema'] != 'MIS_NATIVE4736_FIXED_STATE_225_GAMMA_DIAGNOSTIC_V1':
        raise ValueError('Unexpected diagnostic schema')
    if obj['dimensions']['targets'] != 9 or obj['dimensions']['positions'] != 25:
        raise ValueError('Unexpected problem dimensions')
    eta = Fraction(obj['original_eta_exact_binary64'])
    lanes = {}
    for name in ('80', '100'):
        lane = obj['lanes'][name]
        matrix = [[Fraction(v) for v in row] for row in lane['Gamma_9x25']]
        if len(matrix) != 9 or any(len(row) != 25 for row in matrix):
            raise ValueError('Invalid Gamma dimensions')
        if any(v < 0 for row in matrix for v in row):
            raise ValueError('SINR estimate must be nonnegative')
        maxima = [max(row) for row in matrix]
        ceiling = min(maxima)
        gap = eta-ceiling
        tolerance = Fraction(lane['same_eta_feasibility_threshold_exact_binary64'])
        lanes[name] = {
            'global_over_rows_ceiling': display(ceiling),
            'limiting_row_one_based': maxima.index(ceiling)+1,
            'eta_minus_ceiling': display(gap),
            'strictly_below_eta': ceiling < eta,
            'tolerance': display(tolerance),
            'within_tolerance': gap <= tolerance,
            'rowwise_argmax_candidate_columns_one_based': [row.index(v)+1 for row,v in zip(matrix,maxima)],
            'per_row_simplex_upper_bound_applies_to_binary_and_fractional_X': True,
        }
    return {'schema':'MIS_FIXED_GAMMA_SIMPLEX_CEILING_V1',
            'figure':3, 'original_start':4736, 'eta':display(eta), 'lanes':lanes,
            'scope':'Exact rational bounds for the stored approximate fixed-phase Gamma; includes every row-simplex schedule and any subset with additional constraints.',
            'limitations':['No interval-certified physical forward-model error.',
                           'Rowwise argmax is a candidate, not a proof of any additional constraints.',
                           'No claim about other phases, other starts or global feasibility.',
                           'Tolerance-based feasibility differs from exact feasibility.',
                           'No MATLAB, full-figure, original-reference or paper acceptance.']}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('diagnostic',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    result=evaluate(json.loads(a.diagnostic.read_text(encoding='utf8')))
    with a.output.open('x',encoding='utf8',newline='\n') as f:
        json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')

if __name__=='__main__':main()
