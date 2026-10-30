"""Independent, read-only finite-arithmetic check of one saved ISAC state.

The result is conditional on the supplied geometry and on this model's
far-field, diagonal RIS assumptions. It does not authenticate historic source,
prove interval feasibility, run an optimizer, or establish figure agreement.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import numpy as np


def _load(path):
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('input exceeds 128 MiB')
    with path.open(encoding='utf-8-sig') as source:
        return json.load(source, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def _axis_rotation(rotation):
    x, y, z = rotation
    cx, cy, cz, sx, sy, sz = np.cos(x), np.cos(y), np.cos(z), np.sin(x), np.sin(y), np.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rx @ ry @ rz


def _array_field(coords, center, direction, matrix, job):
    cosine = float(np.dot(matrix[:, 2], direction))
    if cosine <= 0:
        return np.zeros(len(coords), dtype=complex)
    gain = np.sqrt(job['maximum_gain']) * cosine ** (job['directivity_exponent']/2)
    # Compute each physical element directly, without the source channel helper.
    return np.array([gain * np.exp(2j * np.pi * np.dot(matrix @ x + center, direction)
                                   / job['wavelength']) for x in coords])


def inspect(job, result):
    scheme = 'Rot-BS & Fix-RIS'
    state = result['metrics'][scheme]
    w = np.asarray(state['w_re'], dtype=float) + 1j*np.asarray(state['w_im'], dtype=float)
    theta = np.asarray(state['theta_re'], dtype=float) + 1j*np.asarray(state['theta_im'], dtype=float)
    angles = np.asarray(state['rotation'], dtype=float)
    cb, cr = np.asarray(job['bs_coordinates'], dtype=float), np.asarray(job['ris_coordinates'], dtype=float)
    ob, oris = np.asarray(job['bs_center'], dtype=float), np.asarray(job['ris_center'], dtype=float)
    noise, targets = np.asarray(job['noise'], dtype=float), np.asarray(job['desired_pattern'], dtype=float)
    k, sensing = len(noise), len(job['bt_directions'])
    if w.ndim != 2 or w.shape[0] != len(cb) or w.shape[1] < k or theta.shape != (len(cr),) or angles.shape != (6,):
        raise ValueError('unexpected saved state dimensions for this case')
    if len(targets) != sensing or not np.all(noise > 0):
        raise ValueError('invalid noise or sensing geometry')
    if not all(np.isfinite(a).all() for a in (w, theta, angles, cb, cr, noise, targets)):
        raise ValueError('nonfinite input')
    qb, qr = _axis_rotation(angles[:3]), _axis_rotation(angles[3:])
    def gain(re, im, idx):
        return complex(job[re][idx], job[im][idx])
    h = np.zeros((len(cb), k+sensing), complex)
    g = np.zeros((len(cr), k+sensing), complex)
    for u in range(k):
        for p, direction in enumerate(job['bu_directions'][u]):
            a = complex(job['bu_gain_re'][u][p], job['bu_gain_im'][u][p])
            h[:, u] += a*_array_field(cb, ob, np.asarray(direction), qb, job)
        for p, direction in enumerate(job['ru_directions'][u]):
            a = complex(job['ru_gain_re'][u][p], job['ru_gain_im'][u][p])
            g[:, u] += a*_array_field(cr, oris, np.asarray(direction), qr, job)
    for p in range(sensing):
        h[:, k+p] = _array_field(cb, ob, np.asarray(job['bt_directions'][p]), qb, job)
        g[:, k+p] = _array_field(cr, oris, np.asarray(job['rt_directions'][p]), qr, job)
    bridge = np.zeros((len(cb), len(cr)), complex)
    for p in range(len(job['br_directions'])):
        ab = _array_field(cb, ob, np.asarray(job['br_directions'][p]), qb, job)
        ar = _array_field(cr, oris, np.asarray(job['rb_directions'][p]), qr, job)
        bridge += gain('br_gain_re','br_gain_im',p)*np.outer(ab, ar.conj())
    field = h + bridge @ (theta[:, None]*g)
    sinrs = []
    for u in range(k):
        received = [float(abs(np.vdot(field[:, u], w[:, j]))**2) for j in range(w.shape[1])]
        interference = math.fsum(received[j] for j in range(len(received)) if j != u) + noise[u]
        sinrs.append(received[u] / interference)
    pattern = np.array([math.fsum(float(abs(np.vdot(field[:, k+t], w[:, j]))**2)
                                 for j in range(w.shape[1])) for t in range(sensing)])
    iota = float(state['iota'])
    if not math.isfinite(iota) or iota <= 0:
        raise ValueError('invalid sensing scale')
    overlap = float(np.dot(pattern, targets))
    if not math.isfinite(overlap) or overlap <= float(job['iota_denominator_epsilon']):
        raise ValueError('stored sensing scale undefined at this overlap')
    derived_iota = float(np.dot(pattern, pattern)/overlap)
    nmse = float(np.dot(pattern-iota*targets, pattern-iota*targets)/(iota*iota*np.dot(targets, targets)))
    rate = math.fsum(math.log1p(x)/math.log(2) for x in sinrs)
    utility = rate - float(job['rho'])*nmse
    # Convert the original serialized binary64 values directly to rationals.
    exact_power = sum((Fraction.from_float(float(a))**2 + Fraction.from_float(float(b))**2
                       for a,b in zip(w.real.flat, w.imag.flat)), Fraction())
    budget = Fraction.from_float(float(job['power']))
    mod_errors = [abs(Fraction.from_float(float(a))**2 + Fraction.from_float(float(b))**2 - 1)
                  for a,b in zip(theta.real, theta.imag)]
    bs_limit = float(job.get('rotation_bs_half_width', job.get('rotation_half_width', np.pi/2)))
    if bs_limit < 0 or not math.isfinite(bs_limit):
        raise ValueError('invalid rotation width')
    history = result['history'][scheme]
    return {'scope': 'one stored Rot-BS & Fix-RIS state; independent finite-arithmetic channel reconstruction',
            'recomputed_utility': utility, 'saved_utility': float(state['utility']),
            'utility_difference': utility-float(state['utility']), 'recomputed_sum_rate': rate,
            'recomputed_nmse': nmse, 'sinr': sinrs, 'min_noise': float(noise.min()),
            'saved_iota': iota, 'recomputed_iota': derived_iota,
            'iota_difference': derived_iota-iota,
            'exact_binary64_power': float(exact_power), 'exact_binary64_power_limit': float(budget),
            'exact_binary64_power_excess': float(exact_power-budget),
            'exact_binary64_power_constraint': exact_power <= budget,
            'power_with_saved_tolerance': exact_power <= budget+Fraction.from_float(float(job['verification_tolerance'])),
            'max_exact_binary64_modulus_squared_error': float(max(mod_errors)),
            'fixed_ris_angles_exact_zero': bool(np.all(angles[3:] == 0)),
            'bs_rotation_limit': bs_limit, 'bs_rotation_margin_float': float(bs_limit-np.max(abs(angles[:3]))),
            'stored_outer_converged': history['converged'], 'stored_inner_converged': history['inner_all_converged'],
            'stored_full_converged': history['full_converged'], 'stored_termination': history['termination_reason'],
            'historical_source_authenticated': False, 'physical_interval_proof': False,
            'matlab_or_reference_verified': False, 'full_paper_pass': False,
            'limitations': ['exact comparisons apply only to serialized binary64 values',
                            'channel reconstruction and angles use floating arithmetic',
                            'model/configuration and historical source are not independently authenticated',
                            'single endpoint, not a convergence or original-figure proof']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args=parser.parse_args()
    print(json.dumps(inspect(_load(args.job), _load(args.result)), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
