"""Rebuild moments and inspect one saved hotspot AO design; no optimization.

Only the explicit result JSON is read. The geometry is reconstructed using
the saved settings and is not itself authenticated against a historical run.
"""
import argparse
import json
import math
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np


def jn_series(order, value):
    """J_n(x), n=1 or 3, via an independently summed decimal power series."""
    if order not in (1, 3) or not math.isfinite(value) or abs(value) > 30:
        raise ValueError('Bessel argument outside this documented check')
    with localcontext() as context:
        context.prec = 70
        x = Decimal.from_float(float(value)) / 2
        term = x**order / Decimal(math.factorial(order))
        total = term
        for k in range(1, 160):
            term *= -(x*x) / Decimal(k*(order+k))
            total += term
            if abs(term) < Decimal('1e-60'):
                break
        else:
            raise ValueError('Bessel series did not converge')
        return float(total)


def moments(configuration, phase):
    """Reconstruct current source-geometry moments, with no random samples."""
    p, t = configuration['reported'], configuration['tuned_not_reported']
    n, j, u, k, m = (int(p[x]) for x in ('N', 'J', 'U', 'K', 'M'))
    if (n, j) != (16, 16) or u+k != j or not (1 <= u <= 6):
        raise ValueError('unexpected source scenario dimensions')
    phase = np.asarray(phase, complex)
    if phase.shape != (m,) or not np.isfinite(phase).all():
        raise ValueError('invalid saved RIS phase')
    lam = 299792458 / p['frequency_hz']
    noise = 1.380649e-23 * p['temperature_k'] * p['bandwidth_hz']
    height = p['leo_height_m']
    centers = np.array([[x, y] for x in (-1.5, -.5, .5, 1.5)
                        for y in (-1.5, -.5, .5, 1.5)]) * t['feed_center_spacing_m']
    if u == 1:
        hu = np.zeros((1, 2))
    else:
        angle = np.arange(u)*2*np.pi/u
        hu = t['hu_cluster_radius_m']*np.column_stack((np.cos(angle), np.sin(angle)))
    order = sorted(range(n), key=lambda i: float(np.linalg.norm(centers[i])))
    nhu = centers[order[-k:]]
    ris = np.array([p['ris_hu_distance_m'], 0.])
    gain = 10**(p['satellite_gain_dbi']/10)
    receive = 10**(t['ground_receive_gain_dbi']/10)
    area = np.prod(p['subsurface_elements'])*np.prod(p['element_size_m'])
    ris_gain = 4*np.pi*area/lam**2
    max_argument = 0.

    def satellite(pos, receiver_gain):
        nonlocal max_argument
        pos = np.atleast_2d(pos)
        distance = np.sqrt(height**2+np.sum(pos**2, axis=1))
        theta = np.arctan(np.linalg.norm(centers[None, :, :]-pos[:, None, :], axis=2)/height)
        nu = np.pi*p['antenna_diameter_m']/lam*np.sin(theta)
        max_argument = max(max_argument, float(np.max(abs(nu))))
        pattern = np.ones_like(nu)
        for index in np.ndindex(nu.shape):
            x = float(nu[index])
            if abs(x) > 1e-8:
                pattern[index] = (jn_series(1, x)/(2*x)+36*jn_series(3, x)/x**3)**2
        amplitude = np.sqrt(pattern*gain*receiver_gain)*(lam/(4*np.pi*distance[:, None]))/np.sqrt(noise)
        beta = 10**(p['kappa_satellite_db']/10)
        mean = amplitude*np.sqrt(beta/(1+beta))*np.exp(-2j*np.pi*distance[:, None]/lam)
        return mean, amplitude**2/(1+beta)

    direct, direct_var = satellite(hu, receive)
    nhu_mean, nhu_var = satellite(nhu, receive)
    matrix_mean, matrix_var = satellite(ris, ris_gain)
    matrix_mean = np.tile(matrix_mean, (m, 1))
    matrix_var = np.tile(matrix_var, (m, 1))
    nr = int(np.sqrt(m))
    while m % nr:
        nr -= 1
    nc = m//nr
    coordinates = np.array([[a, b] for a in range(nr) for b in range(nc)])*np.sqrt(area)
    coordinates -= np.mean(coordinates, axis=0)
    beta_ground = 10**(p['kappa_ground_db']/10)
    out = []
    for i in range(u):
        direction = hu[i]-ris
        distance = np.linalg.norm(direction)
        if distance == 0:
            raise ValueError('degenerate RIS-user geometry')
        amplitude = lam/(4*np.pi*p['ris_hu_distance_m'])*np.sqrt(ris_gain*receive)
        ground = amplitude*np.sqrt(beta_ground/(1+beta_ground))*np.exp(-2j*np.pi*(distance+coordinates@direction/distance)/lam)
        ground_var = amplitude**2/(1+beta_ground)
        mean = direct[i]+np.sum(phase[:, None]*ground[:, None]*matrix_mean, axis=0)
        covariance = np.diag(direct_var[i].astype(complex))
        covariance += np.einsum('m,mn,mp->np', np.full(m, ground_var), np.conj(matrix_mean), matrix_mean)
        covariance += np.diag(np.sum(matrix_var*(abs(ground)**2+ground_var)[:, None], axis=0))
        out.append(covariance+np.outer(np.conj(mean), mean))
    out.extend(np.diag(nhu_var[i])+np.outer(np.conj(nhu_mean[i]), nhu_mean[i]) for i in range(k))
    return np.asarray(out), max_argument


def check(record):
    config, sample = record['contract']['configuration'], record['actual_start']
    p = config['reported']
    state = sample['final_state']
    if state['no_ris'] is not False:
        raise ValueError('this check is for a saved RIS-enabled design')
    phi = np.asarray(state['phi']['real'])+1j*np.asarray(state['phi']['imag'])
    w = np.asarray(state['W']['real'])+1j*np.asarray(state['W']['imag'])
    j, n, u = p['J'], p['N'], p['U']
    if w.shape != (n, j) or not np.isfinite(w).all():
        raise ValueError('invalid saved beam dimensions')
    matrices, max_arg = moments(config, phi)
    ratios = []
    for i in range(j):
        received = [float(np.real(np.vdot(w[:, z], matrices[i]@w[:, z]))) for z in range(j)]
        if min(received) < 0:
            raise ValueError('negative individual received power')
        denominator = 1. + math.fsum(received[z] for z in range(j) if z != i)
        ratios.append(received[i]/denominator)
    ratios = np.asarray(ratios)
    saved = np.asarray(sample['evaluation']['sinr'], float)
    if saved.shape != (j,) or not np.isfinite(saved).all():
        raise ValueError('invalid saved SINR vector')
    if 'nhu_statistical_sinr_db' not in p:
        raise ValueError('saved statistical NHU threshold is missing')
    target = 10**(p['nhu_statistical_sinr_db']/10)
    power = float(np.sum(abs(w)**2))
    return {'scope': 'one saved AO state under reconstructed source geometry',
            'users': j, 'nhu_count': j-u, 'max_bessel_argument': max_arg,
            'max_phase_unit_modulus_error': float(np.max(abs(abs(phi)-1))),
            'max_abs_sinr_difference': float(np.max(abs(ratios-saved))),
            'max_rel_sinr_difference': float(np.max(abs(ratios-saved)/np.maximum(abs(saved), 1e-300))),
            'power': power, 'saved_power': sample['evaluation']['total_power'],
            'power_limit': p['power_w'], 'min_nhu_ratio': float(np.min(ratios[u:])),
            'nhu_target': target, 'nhu_floating_margin': float(np.min(ratios[u:])-target),
            'hu_rate': float(np.log2(1+ratios[:u]).sum()),
            'saved_hu_rate': sample['evaluation']['hu_sum_rate'],
            'min_eigenvalue': float(np.min(np.linalg.eigvalsh(matrices))),
            'historical_source_authenticated': False, 'interval_proof': False,
            'convergence_or_full_paper_pass': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', required=True, type=Path)
    args = parser.parse_args()
    if args.result.stat().st_size > 4*1024*1024:
        raise ValueError('result exceeds bounded input size')
    result = check(json.loads(args.result.read_text(encoding='utf-8-sig')))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
