"""Read-only check of saved MA MRT/ZF objective histories, not a paper gate.

The supplied result and job must be selected by the caller. This independently
recomputes the equations for stored sweep-boundary positions only; it does not
authenticate historical files, evaluate MC rates, or run any optimization.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np


def load(path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('input exceeds 64 MiB')
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError('duplicate JSON key')
            out[k] = v
        return out
    with path.open(encoding='utf-8-sig') as f:
        return json.load(f, object_pairs_hook=unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def independently_reconstruct(job, result):
    """Verify a source-model-specific stored history, with wavelength 1.

    This uses pairwise cosine sums for MRT and a fresh Gram inversion for ZF.
    The saved job's geometry and model units are assumptions, not authenticated
    provenance; these equations are those in the existing scenario builder.
    """
    n, m = job['N'], job['M']
    if type(n) is not int or type(m) is not int or not n > m > 0:
        raise ValueError('requires integer N>M>0')
    g = job['geometry']
    theta, phi, distance = (np.asarray(g[k], dtype=float) for k in ('elevation', 'azimuth', 'distances_m'))
    if any(x.shape != (m,) or not np.isfinite(x).all() for x in (theta, phi, distance)) or np.any(distance <= 0):
        raise ValueError('invalid geometry')
    directions = np.column_stack((np.cos(theta) * np.sin(phi), np.sin(theta)))
    beta = 1e-4 * distance**(-2.8)
    kap, power, noise = float(job['kappa']), float(job['power']), 1e-11
    if not all(math.isfinite(x) and x > 0 for x in (kap, power)):
        raise ValueError('nonpositive kappa or power')
    meta = result.get('job_metadata', {})
    for key in ('N', 'M', 'kappa', 'power', 'A', 'figure', 'point', 'realization'):
        if key not in meta or key not in job or meta[key] != job[key]:
            raise ValueError('job metadata mismatch: ' + key)

    def mrt(t):
        numerator = beta**2 * (n*n + n*(2*kap+1)/(kap+1)**2)
        denominator = np.full(m, noise*n*sum(beta)/power)
        for u in range(m):
            for v in range(m):
                if u == v:
                    continue
                phase = 2*np.pi*(t @ (directions[u] - directions[v]))
                csum = np.cos(phase[:, None]-phase[None, :]).sum()
                denominator[u] += beta[u]*beta[v]*(kap**2*csum+n*(2*kap+1))/(kap+1)**2
        return float(np.log1p(numerator/denominator).sum()/np.log(2))

    def zf(t):
        h = np.exp(2j*np.pi*(t @ directions.T))
        sigma = (np.eye(m) + kap*(h.conj().T @ h)/n)/(kap+1)
        inverse = np.linalg.inv(sigma)
        if np.any(np.real(np.diag(inverse)) <= 0):
            raise ValueError('invalid covariance inverse')
        eta = power*beta*(n-m)/(m*noise)
        return float(np.log1p(eta/np.real(np.diag(inverse))).sum()/np.log(2))

    out = {}
    for mode, fun in [('mrt', mrt), ('zf', zf)]:
        history = result['history'][mode]
        positions, saved = history['positions'], np.asarray(history['objective'], dtype=float)
        if len(positions) < 2 or saved.shape != (len(positions),) or not np.isfinite(saved).all():
            raise ValueError('invalid stored history')
        reconstructed = []
        for positions_at_sweep in positions:
            t = np.asarray(positions_at_sweep, dtype=float)
            if t.shape != (n, 2) or not np.isfinite(t).all():
                raise ValueError('invalid stored position')
            reconstructed.append(fun(t))
        reconstructed = np.asarray(reconstructed)
        max_error = float(np.max(np.abs(reconstructed - saved)))
        tolerance = 1e-10 * max(1.0, float(np.max(np.abs(saved))))
        out[mode] = {'sweep_boundaries': len(saved), 'max_absolute_error': max_error,
                     'comparison_tolerance': tolerance, 'objective_consistent': max_error <= tolerance,
                     'saved_first': float(saved[0]), 'saved_last': float(saved[-1]),
                     'saved_decreases': int(np.count_nonzero(np.diff(saved) < 0))}
    return {'scope': 'one saved job; sweep-boundary statistical objectives only',
            'results': out, 'model_assumptions': {'wavelength': 1.0, 'noise': 1e-11,
                'path_gain': '1e-4*distance**(-2.8)', 'equal_user_rician_from_job': True},
            'metadata_consistency_is_source_authentication': False,
            'physical_feasibility_rechecked': False, 'convergence_proven': False,
            'matlab_or_original_reference_verified': False, 'full_paper_pass': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--job', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True)
    args = p.parse_args()
    report = independently_reconstruct(load(args.job), load(args.result))
    print(json.dumps(report, indent=2, allow_nan=False))
    if not all(x['objective_consistent'] for x in report['results'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
