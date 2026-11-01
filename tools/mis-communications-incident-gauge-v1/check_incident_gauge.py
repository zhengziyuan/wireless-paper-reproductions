"""Read-only gauge check of one saved Fig8 native endpoint population.

This verifies only the ideal plane-wave, continuous unit-modulus model. It
neither fits any reference curve nor reruns optimization or channel draws.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def cplx(z):
    return np.asarray(z['real'], dtype=float) + 1j*np.asarray(z['imag'], dtype=float)


def check(data):
    cfg = data['configuration']
    if cfg['ms1'] != [2, 2] or cfg['ms2'] != [1, 1]:
        raise ValueError('expected saved 2x2/1x1 Fig8 geometry')
    nr, nc = cfg['ms1']
    coords = np.array([[r, c] for r in range(nr) for c in range(nc)])
    positions = np.asarray(data['indices_zero_based'], dtype=int)
    if positions.shape != (4, 1) or sorted(positions[:, 0].tolist()) != list(range(4)):
        raise ValueError('expected four distinct one-element positions')
    old = np.asarray(cfg['incidence_direction_cosines'], float)
    spacing = float(cfg['spacing_over_wavelength'])
    if old.shape != (2,) or not np.isfinite(old).all() or spacing != 0.5:
        raise ValueError('unexpected saved incidence or spacing')
    # A fixed alternative physically valid direction cosine vector; no reference
    # samples, angle optimization, or historical parameter inference is used.
    new = np.array([0.35, -0.42])
    if np.linalg.norm(new) > 1:
        raise ValueError('alternative incidence is not a plane-wave direction')
    delta = np.exp(2j*np.pi*spacing*(coords @ (new-old)))
    az = np.deg2rad(np.linspace(-90., 90., 361))
    el = np.pi/4
    dirs = np.column_stack((np.sin(el)*np.cos(az), np.sin(el)*np.sin(az)))
    c_old = np.exp(2j*np.pi*spacing*(dirs @ coords.T + (coords @ old)[None,:]))
    c_new = np.exp(2j*np.pi*spacing*(dirs @ coords.T + (coords @ new)[None,:]))
    saved_c = cplx(data['coefficients'])
    user_az = np.asarray(cfg['azimuth_deg'], dtype=float)
    user_el = np.asarray(cfg['elevation_deg'], dtype=float)
    user_dirs = np.column_stack((np.sin(np.deg2rad(user_el))*np.cos(np.deg2rad(user_az)),
                                 np.sin(np.deg2rad(user_el))*np.sin(np.deg2rad(user_az))))
    actual_c = np.exp(2j*np.pi*spacing*(user_dirs @ coords.T + (coords @ old)[None,:]))
    steering_error = float(np.max(np.abs(saved_c - actual_c)))
    if saved_c.shape != actual_c.shape or steering_error > 1e-12:
        raise ValueError('saved steering does not match stated geometry')
    max_field = max_snr = max_norm = 0.
    for endpoint in data['endpoints']:
        state = endpoint['state']
        phi, theta = cplx(state['phi']), cplx(state['theta'])
        if phi.shape != (4,) or theta.shape != (1,) or not np.isfinite(phi).all() or not np.isfinite(theta).all():
            raise ValueError('bad endpoint phase')
        if max(np.max(np.abs(np.abs(phi)-1)), np.max(np.abs(np.abs(theta)-1))) > 1e-10:
            raise ValueError('saved phases are not unit modulus')
        bar = np.ones((4,4), dtype=complex)
        for u, ix in enumerate(positions):
            bar[u, ix] = theta
        original = c_old @ (bar*phi).T
        phi_new = phi/delta
        transformed = c_new @ (bar*phi_new).T
        max_field = max(max_field, float(np.max(np.abs(original-transformed))))
        max_snr = max(max_snr, float(np.max(np.abs(cfg['reference_snr']*(np.abs(original)**2-np.abs(transformed)**2)))))
        max_norm = max(max_norm, float(np.max(np.abs(np.abs(phi_new)-1))))
    if len(data['endpoints']) != 17 or max_field > 1e-12 or max_snr > 1e-12 or max_norm > 1e-12:
        raise ValueError('saved endpoint count or gauge identity did not pass')
    return {'scope':'one real saved native Fig8 start; all 17 saved continuation endpoints; 361 directions and 4 positions',
            'old_incidence':old.tolist(), 'alternative_incidence':new.tolist(),
            'saved_user_steering_max_error':steering_error,
            'max_field_absolute_difference':max_field,
            'max_linear_snr_absolute_difference':max_snr,
            'max_transformed_phase_norm_error':max_norm,
            'claim':'continuous-phase ideal plane-wave achievable beampattern sets are incidence-gauge invariant',
            'limitations':['not a reconstruction of author historical phases or the Fig8 selected winner',
                           'does not exclude nonideal amplitudes or phase quantization',
                           'same untransformed deterministic initialization can lead to a different finite-run local solution',
                           'no complete optimizer, measured physics, MATLAB/Python parity, or original-figure acceptance']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-native', required=True, type=Path)
    args = parser.parse_args()
    if args.saved_native.stat().st_size > 16*1024*1024:
        raise ValueError('saved file exceeds reader bound')
    with args.saved_native.open('r', encoding='utf-8-sig') as f:
        data = json.load(f, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    print(json.dumps(check(data), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
