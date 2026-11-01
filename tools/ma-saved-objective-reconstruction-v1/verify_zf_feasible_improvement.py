"""Read-only finite-step witness for one saved MA ZF endpoint.

This evaluates the existing scenario's theoretical ZF rate.  It does not run
the optimizer, regenerate any sample, authenticate historical source provenance,
or claim an error in the paper's stopping rule.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'strict' / 'two-timescale-ma'))
from core import los, zf_statistics
from run import scenario


def load(path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('selected input exceeds 64 MiB')
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


def exact_scalar(x):
    x = float(x)
    if not math.isfinite(x):
        raise ValueError('finite input required')
    return Fraction.from_float(x)


def inspect(job, config, result):
    expected = {'figure': 5, 'realization': 0, 'N': 6, 'M': 5,
                'kappa': 100, 'power': 1, 'A': 2, 'point': 30}
    metadata = result['job_metadata']
    if any(job.get(k) != v or metadata.get(k) != v for k, v in expected.items()):
        raise ValueError('specific saved case metadata mismatch')
    c, _ = scenario(config, job['N'], job['M'], job['kappa'], job['power'],
                    job['A'], job['geometry'])
    history = result['history']['zf']
    positions = np.asarray(history['positions'][-1], dtype=float)
    if positions.shape != (6, 2) or not np.isfinite(positions).all():
        raise ValueError('invalid saved positions')
    if len(history['objective']) < 2:
        raise ValueError('missing stopping history')
    candidate = positions.copy()
    candidate[3, 0] += 0.001
    exact = [[exact_scalar(x) for x in row] for row in candidate]
    lower, upper = list(map(exact_scalar, c['region_lower'])), list(map(exact_scalar, c['region_upper']))
    box_margin = min(min(row[d]-lower[d], upper[d]-row[d]) for row in exact for d in range(2))
    min_distance = exact_scalar(c['minimum_distance'])
    distances = [(sum((exact[i][d]-exact[j][d])**2 for d in range(2)), i, j)
                 for i in range(6) for j in range(i)]
    distance2, i, j = min(distances)
    distance_squared_slack = distance2-min_distance**2
    original_value = zf_statistics(positions, c)[0]
    candidate_value = zf_statistics(candidate, c)[0]
    stored = float(history['objective'][-1])
    if not math.isclose(original_value, stored, rel_tol=1e-11, abs_tol=1e-11):
        raise ValueError('saved terminal objective differs from current scenario model')
    previous = float(history['objective'][-2])
    fractional_gain = (stored-previous)/abs(previous)
    threshold = float(c['fractional_increase_threshold'])
    # Independently differentiate the Gram inverse with d(A^-1)=-A^-1(dA)A^-1.
    h = los(positions, c)
    n, m = h.shape
    kap, beta = np.asarray(c['rician']), np.asarray(c['beta'])
    scale = np.sqrt(kap/(kap+1))
    sigma = np.diag(1/(kap+1)) + h.conj().T@h*scale[:,None]*scale[None,:]/n
    inverse = np.linalg.solve(sigma, np.eye(m))
    dh = np.zeros_like(h)
    dh[3, :] = h[3, :] * (2j*np.pi/c['wavelength']) * np.asarray(c['directions'])[:, 0]
    ds = (dh.conj().T@h + h.conj().T@dh) * scale[:,None]*scale[None,:]/n
    d_inverse = -inverse@ds@inverse
    diag = np.real(np.diag(inverse))
    eta = c['power']*beta*(n-m)/(m*np.asarray(c['noise']))
    derivative = float(np.sum(-eta*np.real(np.diag(d_inverse))/(np.log(2)*diag*(diag+eta))))
    return {'scope': 'one saved Fig5 case; theoretical ZF endpoint and one candidate only',
            'old_coordinate_antenna4': positions[3].tolist(),
            'candidate_coordinate_antenna4': candidate[3].tolist(),
            'old_objective': float(original_value), 'candidate_objective': float(candidate_value),
            'objective_increase': float(candidate_value-original_value),
            'candidate_box_margin_exact_binary64': float(box_margin),
            'candidate_min_distance': math.sqrt(float(distance2)),
            'candidate_min_distance_squared_slack_exact_binary64': float(distance_squared_slack),
            'minimum_pair_zero_based': [i, j],
            'last_fractional_sweep_gain': fractional_gain, 'stopping_threshold': threshold,
            'stored_termination': history['termination'], 'stored_converged': history['converged'],
            'stored_fractional_rule_met': fractional_gain < threshold,
            'candidate_feasible_exact_binary64': box_margin >= 0 and distance_squared_slack >= 0,
            'candidate_improves_float_model': bool(candidate_value > original_value),
            'analytic_directional_derivative_float': derivative,
            'limitations': ['exact constraints refer to stored binary64 values, not source uncertainty',
                'objective and derivative use floating arithmetic, not interval arithmetic',
                'one improvement does not prove a paper error or global optimality gap',
                'fractional stopping is not a stationarity or convergence proof',
                'no optimization, new samples, MATLAB or original-figure verification']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('job', 'config', 'result'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    report = inspect(load(args.job), load(args.config), load(args.result))
    print(json.dumps(report, indent=2, allow_nan=False))
    if not report['candidate_feasible_exact_binary64'] or not report['candidate_improves_float_model']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
