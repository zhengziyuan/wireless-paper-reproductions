"""Check all nine full-scene MATLAB/Python analytical panels independently.

Direct finite one-padded array equations are rebuilt here without importing
either production solver. This certifies declared numerical calculations, not
the unpublished historical phase/normalization convention or original plots.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
RTOL, ATOL = 1e-10, 1e-10


def require(value, message):
    if not value:
        raise ValueError(message)


def close(actual, expected, label):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape and np.all(np.isfinite(a)) and np.all(np.isfinite(b)),
            f'{label}: complete same-shaped finite values required')
    error = np.abs(a-b)
    require(np.all(error <= ATOL + RTOL*np.abs(b)), f'{label}: fixed numerical gate failed')
    return float(np.max(error)) if error.size else 0.


def complex_state(raw, key, length):
    item = raw[key]
    value = np.asarray(item['real'], float).reshape(-1) + 1j*np.asarray(item['imag'], float).reshape(-1)
    require(value.shape == (length,), f'All original {length} {key} elements required')
    return value


def fields(azimuth, elevation, coordinates, phases, spacing, incidence):
    az, el = np.deg2rad(azimuth), np.deg2rad(elevation)
    direction = np.column_stack((np.sin(el)*np.cos(az), np.sin(el)*np.sin(az)))
    result = np.empty((len(az), phases.shape[1]), float)
    # Exact sum over every element; chunks change storage only, not the scene.
    for first in range(0, len(az), 1024):
        steering = np.exp(2j*np.pi*spacing*((direction[first:first+1024]+incidence) @ coordinates.T))
        result[first:first+1024] = np.abs(steering @ phases)**2
    return result


def evaluate(settings):
    require(settings['kind'] == 'sensing' and settings['reference_echo_unit'] == 'inverse_watt'
            and settings['reference_echo_noise_domain'] == 'raw_per_PRI'
            and settings['effective_reference_gain_factor'] == 1
            and settings['bs_antennas'] == 1 and settings['power_dbm'] == 30
            and settings['reference_echo_db'] == -73.88,
            'Declared literal inverse-W, 1-W, single-PRI full source case required')
    spacing = float(settings['spacing_over_wavelength'])
    require(spacing == 1/3, 'Original wavelength/3 spacing required')
    coordinates = np.asarray([(r,c) for r in range(20) for c in range(20)])
    small = np.asarray([(r,c) for r in range(16) for c in range(16)])
    coefficient = np.pi/spacing/4
    phi = np.exp(-1j*coefficient*spacing**2*np.sum(coordinates**2, axis=1))
    theta = np.exp(1j*coefficient*spacing**2*np.sum(small**2, axis=1))
    phases = np.repeat(phi[:,None], 25, axis=1)
    for u, (row,col) in enumerate((r,c) for r in range(5) for c in range(5)):
        indices = np.asarray([(row+r)*20+col+c for r in range(16) for c in range(16)])
        phases[indices,u] *= theta
    azimuth = np.tile([0.,45.,90.],3)
    elevation = np.repeat([30.,50.,70.],3)
    row = np.clip(np.floor(np.pi/(coefficient*spacing)*np.sin(np.deg2rad(elevation))*np.cos(np.deg2rad(azimuth))+.5),0,4).astype(int)
    col = np.clip(np.floor(np.pi/(coefficient*spacing)*np.sin(np.deg2rad(elevation))*np.sin(np.deg2rad(azimuth))+.5),0,4).astype(int)
    chosen = row*5+col
    schedule = np.eye(25)[chosen]
    incidence = np.asarray(settings['incidence_direction_cosines'], float)
    require(incidence.shape == (2,) and np.all(incidence == 0), 'Declared normal incidence required')
    target_power = fields(azimuth, elevation, coordinates, phases, spacing, incidence)
    beta = 10**(-73.88/10)
    target_echo = beta*target_power**2
    denominator = np.asarray([np.sum(target_echo[np.arange(9)!=k, chosen[k]])+1 for k in range(9)])
    target_metric = target_echo[np.arange(9),chosen]/denominator
    az_axis, el_axis = np.arange(-180.,181.), np.arange(0.,91.)
    grid_power = fields(np.repeat(az_axis,91),np.tile(el_axis,361),coordinates,phases[:,chosen],spacing,incidence)
    panels = []
    for k in range(9):
        raw = grid_power[:,k].reshape(361,91).T
        panels.append(dict(target=k,pattern=int(chosen[k]),target_azimuth_deg=float(azimuth[k]),
            target_elevation_deg=float(elevation[k]),target_metric=float(target_metric[k]),
            normalized_gain=raw/np.max(raw),sinr=beta*raw**2/denominator[k]))
    return dict(phi=phi,theta=theta,X=schedule,chosen=chosen,azimuth=az_axis,elevation=el_axis,
                panels=panels,minimum_sinr=float(np.min(target_metric)))


def compare(python, matlab):
    require(python['settings'] == matlab['settings'], 'Both languages must use identical declared settings')
    expected = evaluate(python['settings'])
    errors = []
    for language, document in (('python',python),('matlab',matlab)):
        require(document['paper_id'] == 'mis-sensing' and document['figure'] == 'fig2'
                and document['full_figure_execution_complete'] is True and document['overall_full_success'] is True
                and document['original_figure_reproduction_certified'] is False,
                'Actual complete analytical figure required; no historical-reference certification')
        require(len(document['points']) == 1, 'Exactly one original full scene required')
        point = document['points'][0]
        require(point['configuration'] == dict(ms1=[20,20],ms2=[16,16],Kphi=3,Ktheta=3),
                'Full 400/256/25/9 original dimensions required')
        result, samples = point['result'], point['beampattern_samples']
        require(result['available'] is True and result['original_figure_reproduction_certified'] is False,
                'Actual analytical calculation must be available and honestly labeled')
        require(result['coordinate_origin'] == 'both_layers_zero_based_shared_reference_no_MS2_only_offset'
                and result['scheduling_rule'] == 'source_positive_displacement_law_nearest_admissible_index_not_SINR_search'
                and result['closed_form_convention'] == 'same_reference_conjugated_chirps_for_positive_array_exponent',
                'No optimized schedule, single-layer chirp conjugation or hidden origin change')
        require(result['selected_positions'] == expected['chosen'].tolist(), 'All nine original nearest-grid displacements required')
        item = dict(language=language,phi_error=close(complex_state(result['state'],'phi',400),expected['phi'],'phi'),
            theta_error=close(complex_state(result['state'],'theta',256),expected['theta'],'theta'),
            schedule_error=close(result['state']['X'],expected['X'],'schedule'),
            minimum_metric_error=close(result['minimum_sinr'],expected['minimum_sinr'],'minimum SINR'))
        require(samples['objective'] == 'sinr' and samples['resolution_deg'] == 1 and len(samples['maps']) == 9,
                'All nine complete original-scene panels required')
        close(samples['azimuth_deg'],expected['azimuth'],'complete azimuth axis')
        close(samples['elevation_deg'],expected['elevation'],'complete elevation axis')
        panel_errors = []
        for saved, panel in zip(samples['maps'],expected['panels']):
            require(all(saved[key] == panel[key] for key in ('target','pattern','target_azimuth_deg','target_elevation_deg'))
                    and saved['target_metric_name'] == 'SINR', 'Original target order/metric/pattern required')
            panel_errors.append(dict(target=panel['target'],normalized_gain_error=close(saved['normalized_gain'],panel['normalized_gain'],'whole 91x361 gain map'),
                sinr_error=close(saved['sinr'],panel['sinr'],'whole 91x361 SINR map'),
                target_metric_error=close(saved['target_metric'],panel['target_metric'],'target SINR')))
        item['panels'] = panel_errors
        errors.append(item)
    return dict(scope='independent_direct_finite_array_all_nine_full_scene_analytical_panels_NOT_historical_figure_certificate',
        original_dimensions=dict(ms1=400,ms2=256,positions=25,targets=9),angular_samples_per_panel=91*361,
        all_nine_maps_both_languages_independently_verified=True,errors=errors,
        fixed_numerical_gate=dict(relative=RTOL,absolute=ATOL),
        target_sinr_db=(10*np.log10([p['target_metric'] for p in expected['panels']])).tolist(),
        production_solver_imported=False,unpublished_normalization_or_origin_recovered=False,
        original_figure_reproduction_certified=False,all_iterative_paper_figures_completed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('python','matlab','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    own_path=Path(__file__);before=hashlib.sha256(own_path.read_bytes()).hexdigest()
    inputs={name:getattr(args,name).read_bytes() for name in ('python','matlab')}
    result=compare(*(json.loads(inputs[name].decode('utf-8-sig')) for name in ('python','matlab')))
    require(before == hashlib.sha256(own_path.read_bytes()).hexdigest(), 'Independent evaluation source changed')
    result['input_file_sha256']={name:hashlib.sha256(value).hexdigest() for name,value in inputs.items()}
    result['independent_evaluator_sha256']=before
    result['independent_evaluation_source_unchanged']=True
    result['prior_execution_interval_identity_not_added_post_hoc']=True
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('all_nine_maps_both_languages_independently_verified','target_sinr_db','original_figure_reproduction_certified')}))


if __name__ == '__main__':main()
