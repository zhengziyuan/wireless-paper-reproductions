"""Exact numerical functions from the actual saved-state field evaluator; no optimizer."""
import copy
import numpy as np
from frozen_deterministic_Model_fields_v5 import Model
from frozen_normalization_v5_exact import normalization_contract

def reconstruct_model_config(best):
    point = best['configuration']
    settings = best['settings']
    required = ['reference_echo_db', 'reference_echo_unit', 'reference_echo_noise_domain',
                'effective_reference_gain_factor', 'power_dbm', 'spacing_over_wavelength',
                'incidence_direction_cosines']
    if any(key not in settings for key in required):
        raise ValueError('Saved physical settings required for deterministic fields are missing')
    if point != {'ms1': [20, 20], 'ms2': [16, 16], 'Kphi': 3, 'Ktheta': 3}:
        raise ValueError('Selected state is not the exact frozen Fig3 point')
    if (settings['reference_echo_db'], settings['reference_echo_unit'], settings['reference_echo_noise_domain'],
        settings['effective_reference_gain_factor'], settings['power_dbm']) != (-73.88, 'inverse_watt', 'raw_per_PRI', 1, 30):
        raise ValueError('Only the disclosed literal inverseW/singlePRI/gain1 saved cohort is admitted')
    azimuth = np.linspace(0, 90, point['Kphi'])
    elevation = np.linspace(30, 70, point['Ktheta'])
    contract = normalization_contract(settings, settings['power_dbm'])
    return {'ms1': point['ms1'], 'ms2': point['ms2'],
            'azimuth_deg': np.tile(azimuth, point['Ktheta']).tolist(),
            'elevation_deg': np.repeat(elevation, point['Kphi']).tolist(),
            'spacing_over_wavelength': settings['spacing_over_wavelength'],
            'incidence_direction_cosines': settings['incidence_direction_cosines'],
            'number_of_targets': 9, 'reference_snr': 0.01,
            'normalization_contract': contract, 'echo_beta_squared': contract['echo_beta_squared'],
            'noise_over_power': contract['noise_over_power']}

def saved_state(best):
    state = best['state']
    phi = np.asarray(state['phi']['real'], dtype=float).reshape(-1) + 1j * np.asarray(state['phi']['imag'], dtype=float).reshape(-1)
    theta = np.asarray(state['theta']['real'], dtype=float).reshape(-1) + 1j * np.asarray(state['theta']['imag'], dtype=float).reshape(-1)
    X = np.asarray(state['X'], dtype=float)
    binary = np.asarray(best['metrics']['binary_schedule'], dtype=float)
    if phi.shape != (400,) or theta.shape != (256,) or X.shape != (9, 25) or binary.shape != (9, 25):
        raise ValueError('Saved state/schedule shape is missing or incompatible; no reconstruction fallback')
    if not all(np.isfinite(array).all() for array in (phi, theta, X, binary)):
        raise ValueError('Actual saved state/schedule has nonfinite values')
    # No projection or phase normalization: the exact returned phases are used.
    z = {'phi': phi, 'theta': theta, 'X': X, 'eta': state['eta']}
    # np.argmax, like the frozen MATLAB max, retains the first tied placement.
    return z, np.argmax(binary, axis=1)

def evaluate(best):
    config = reconstruct_model_config(best)
    model = Model(config)
    z, selected = saved_state(best)
    az = np.arange(-180, 181, dtype=float)
    el = np.arange(0, 91, dtype=float)
    grid_config = copy.deepcopy(config)
    grid_config['azimuth_deg'] = np.repeat(az, len(el)).tolist()
    grid_config['elevation_deg'] = np.tile(el, len(az)).tolist()
    grid_config['echo_beta_squared'] = 1
    grid_config['number_of_targets'] = len(az) * len(el)
    grid = Model(grid_config)
    powers = grid.fields(z)[3]
    original = model.fields(z)[3]
    echo = model.beta[:, None] * original ** 2
    maps = []
    for k in range(9):
        placement = int(selected[k])
        raw = powers[:, placement].reshape((len(el), len(az)), order='F')
        peak = float(np.max(raw))
        denominator = float(np.sum(echo[np.arange(9) != k, placement])) + config['noise_over_power']
        if not np.isfinite(peak) or peak <= 0 or not np.isfinite(denominator) or denominator <= 0:
            raise ValueError('Actual deterministic field normalization/denominator is undefined')
        gain = raw / peak
        sinr = model.beta[k] * raw ** 2 / denominator
        target = float(echo[k, placement] / denominator)
        if not np.isfinite(sinr).all() or not np.isfinite(target):
            raise ValueError('Actual deterministic field contains nonfinite results')
        maps.append({'target': k, 'pattern': placement,
                     'target_azimuth_deg': config['azimuth_deg'][k],
                     'target_elevation_deg': config['elevation_deg'][k],
                     'normalized_gain': gain.tolist(), 'sinr': sinr.tolist(),
                     'target_metric_name': 'SINR', 'target_metric': target})
    return {'scope': 'full_front_hemisphere_independent_samples', 'resolution_deg': 1,
            'objective': 'sinr', 'azimuth_deg': az.tolist(), 'elevation_deg': el.tolist(), 'maps': maps}
