#!/usr/bin/env python3
"""Check inferred coordinate-boundary positions from a retained MA trajectory.

The inference requires one coordinate update per antenna per sweep, in the
recorded order, and no changes to other antennas. Per-update positions were
not independently saved; objective agreement is only a consistency check.
"""
import argparse
import json
import math
from fractions import Fraction
from pathlib import Path
import numpy as np


def score(t, data, mode):
    t = np.asarray(t, dtype=float)
    beta = np.asarray(data['beta'], dtype=float)
    k = np.asarray(data['rician'], dtype=float)
    directions = np.asarray(data['directions'], dtype=float)
    n, m = len(t), len(beta)
    h = np.exp(2j * np.pi / data['wavelength'] * (t @ directions.T))
    noise = np.asarray(data['noise'], dtype=float)
    if mode == 'zf':
        f = np.sqrt(k / (k + 1))
        sigma = np.diag(1 / (k + 1)) + (h.conj().T @ h) * f[:, None] * f[None, :] / n
        inverse = np.linalg.solve(sigma, np.eye(m))
        eta = data['power'] * beta * (n - m) / (m * noise)
        return float(np.log2(1 + eta / np.real(np.diag(inverse))).sum())
    num = beta**2 * (n*n + n*(2*k+1)/(k+1)**2)
    den = noise * n * beta.sum() / data['power']
    gram = np.abs(h.conj().T @ h)**2
    for u in range(m):
        for v in range(m):
            if u != v:
                den[u] += beta[u]*beta[v]*(k[u]*k[v]*gram[u,v] + n*(k[u]+k[v]+1))/((k[u]+1)*(k[v]+1))
    return float(np.log2(1 + num / den).sum())


def analyze(data):
    if data['schema'] != 'MA_FIG5_CASE7_INFERRED_COORDINATE_INPUT_V1':
        raise ValueError('Wrong input schema')
    n = data['N']; lo = [Fraction(float(x)) for x in data['box_lower']]
    hi = [Fraction(float(x)) for x in data['box_upper']]
    d2 = Fraction(float(data['minimum_spacing']))**2
    summary = {}
    for mode in ('mrt', 'zf'):
        x = data['modes'][mode]; boundaries = x['positions']; records = x['records']; objective = x['objective']
        if len(records) != n * (len(boundaries)-1): raise ValueError('Incomplete recorded steps')
        if len(objective) != len(boundaries): raise ValueError('Incomplete saved objectives')
        pair_fail = box_fail = checks = 0
        max_error = 0.0
        min_d2 = None
        for sweep in range(len(boundaries)-1):
            if (records[sweep*n]['before'] != objective[sweep] or
                records[sweep*n+n-1]['after'] != objective[sweep+1]):
                raise ValueError('Saved sweep objectives differ from records')
            state = [list(row) for row in boundaries[sweep]]
            final = boundaries[sweep+1]
            for antenna in range(n):
                index = sweep*n+antenna; record = records[index]
                if (record['sweep'], record['antenna']) != (sweep, antenna): raise ValueError('Unexpected update order')
                if index and records[index-1]['after'] != record['before']:
                    raise ValueError('Saved update objectives do not chain')
                before = score(state, data, mode)
                state[antenna] = list(final[antenna])
                after = score(state, data, mode)
                for computed, stored in ((before, record['before']), (after, record['after'])):
                    error = abs(computed-stored)
                    max_error = max(max_error, error)
                    if not math.isfinite(error) or error > 1e-10 * max(1, abs(stored)):
                        raise ValueError('Reconstructed objective differs from saved record')
                exact = [[Fraction(float(v)) for v in row] for row in state]
                for p in exact:
                    box_fail += int(any(p[k] < lo[k] or p[k] > hi[k] for k in range(2)))
                for i in range(n):
                    for j in range(i):
                        q = sum((exact[i][k]-exact[j][k])**2 for k in range(2))
                        pair_fail += int(q < d2)
                        min_d2 = q if min_d2 is None or q < min_d2 else min_d2
                checks += 1
            if state != final: raise ValueError('Boundary reconstruction failed')
        summary[mode] = {'inferred_update_states': checks,
                         'pair_checks': checks*n*(n-1)//2,
                         'box_checks': checks*n,
                         'spacing_violations': pair_fail, 'box_violations': box_fail,
                         'minimum_squared_spacing': float(min_d2),
                         'max_saved_objective_absolute_discrepancy': max_error}
    return {'schema':'MA_INFERRED_COORDINATE_BOUNDARIES_V1', 'modes':summary,
            'scope':'Conditional reconstruction from saved sweep boundaries and recorded one-update-per-antenna order, checked against saved objective values.',
            'limits':['Intermediate positions were not directly recorded.', 'Score consistency does not uniquely prove historical intermediate positions or historical code identity.', 'Does not certify numerical optimizer, cross-language result, complete figure or paper.'],
            'optimizer_or_random_draws':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('geometry',type=Path);p.add_argument('parameters',type=Path);p.add_argument('records',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    geo=json.loads(a.geometry.read_text(encoding='utf8'))
    params=json.loads(a.parameters.read_text(encoding='utf8'))
    rec=json.loads(a.records.read_text(encoding='utf8'))
    if rec['schema']!='MA_FIG5_CASE7_COORDINATE_RECORDS_V1' or geo['job']['N']!=params['N'] or geo['job']['M']!=params['M']:
        raise ValueError('Incompatible saved input documents')
    if params['mrt_positions'] != geo['result']['history']['mrt']['positions'][-1]:
        raise ValueError('MRT saved positions differ')
    n=geo['job']['N']; m=geo['job']['M']; shape=geo['config']['antenna_factorization'][str(n)]; area=geo['job']['A']
    data={'schema':'MA_FIG5_CASE7_INFERRED_COORDINATE_INPUT_V1','N':n,'wavelength':params['wavelength'],
          'beta':params['beta'],'rician':params['rician'],'directions':params['directions'],
          'noise':[1e-11]*m,'power':geo['job']['power'],
          'box_lower':[-shape[0]*area/2,-shape[1]*area/2], 'box_upper':[shape[0]*area/2,shape[1]*area/2],
          'minimum_spacing':0.5,'modes':{mode:{'positions':geo['result']['history'][mode]['positions'],
          'objective':geo['result']['history'][mode]['objective'], 'records':rec['modes'][mode]} for mode in ('mrt','zf')}}
    report=analyze(data)
    with a.output.open('x',encoding='utf8',newline='\n') as f: json.dump(report,f,indent=2,allow_nan=False);f.write('\n')

if __name__=='__main__': main()
