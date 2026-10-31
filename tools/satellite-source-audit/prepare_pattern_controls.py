"""Prepare scalar tests of the unchanged direction-pattern implementations."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import mpmath as mp
import numpy as np

from itu1428_oracle import binary, parameters, stable_meridional_angle


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def prepare(configuration, output):
    if output.exists():
        raise FileExistsError('Preserve previous controls')
    repo = Path(__file__).resolve().parents[2]
    original_py = repo/'strict/cooperative-satcom/scenario.py'
    original_m = repo/'strict/cooperative-satcom/strict_satcom_scenario.m'
    watched = {str(p):sha(p) for p in (configuration,original_py,original_m,Path(__file__),Path(__file__).with_name('itu1428_oracle.py'))}
    config = json.loads(configuration.read_bytes())
    p,t = config['reported'],config['tuned_not_reported']
    q_actual = t['gt_diameter_m']/(299792458./p['frequency_hz'])
    q_values = [20.,np.nextafter(25.,-np.inf),25.,np.nextafter(25.,np.inf),q_actual,
                100.,np.nextafter(100.,np.inf),101.,200.,1000.,1e6]
    rows = []
    for q in q_values:
        angles = [(x,'fixed_decimal') for x in (0.,.01,.1,.5,1.,2.,5.,10.,20.,30.,33.1,34.1,
            79.999999,80.,80.000001,119.999999,120.,120.000001,150.,180.)]
        with mp.workdps(100):
            _,_,main_end,plateau_end = parameters(binary(q))
            for name,boundary in (('phi_m',main_end),('plateau_end',plateau_end)):
                for side in (-1,1):
                    angles.append((float(boundary*(1+side*mp.mpf(2)**-30)),name+('_left' if side<0 else '_right')))
        for angle,origin in angles:
            for sign in (1,-1) if angle else (1,):
                value = float(sign*angle)
                rows.append(dict(index=len(rows),q=float(q),angle_deg=value,probe=origin,
                    exact_named_decimal_angle=str(abs(value)) if origin=='fixed_decimal' else None,
                    source_domain='continuous_boresight_convention' if angle==0 else
                        ('printed_small_q_33_1_gap_left_extension' if q<=25 and angle==33.1 else 'defined_standard_clause')))
    spec = importlib.util.spec_from_file_location('frozen_original_gt_pattern',original_py)
    production = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(production)
    results = np.array([[r['q'],r['angle_deg'],production.gt_pattern(r['angle_deg'],{'gt_diameter_m':r['q']},1.)]
                        for r in rows],dtype=float)
    geometry = []
    earth = t['earth_radius_m']
    gt = production.location(t['gt_latitude_deg'],p['geo_longitude_deg'],earth)
    geo = production.location(0,p['geo_longitude_deg'],earth+p['geo_height_m'])
    for j,latitude in enumerate(t['satellite_latitudes_deg']):
        sat = production.location(latitude,p['geo_longitude_deg'],earth+p['leo_height_m'])
        x,y = sat-gt,geo-gt
        angle = float(np.rad2deg(np.arccos(np.clip(np.dot(x,y)/np.linalg.norm(x)/np.linalg.norm(y),-1,1))))
        with mp.workdps(100):
            independent = stable_meridional_angle(binary(earth),binary(p['leo_height_m']),binary(latitude))
            difference = abs(binary(angle)-independent)
            if abs(latitude)>0:
                assert difference < mp.mpf('1e-10')
            else:
                assert angle <= 2e-6
        geometry.append(dict(satellite=j,latitude_degrees=latitude,
            original_binary64_acos_angle_deg=angle,independent_MP100_atan2_angle_deg=mp.nstr(independent,105),
            angular_difference_deg=mp.nstr(difference,105),
            original_pattern_absolute_linear_gain=production.gt_pattern(angle,t,299792458./p['frequency_hz'])))
    raw = original_m.read_bytes()
    marker = b'function gain=itu1428(angle,q)'
    assert raw.count(marker)==1
    unit = raw[raw.index(marker):]
    adapted = unit.replace(marker,b'function gain=itu1428_native_copy(angle,q)',1)
    assert adapted.replace(b'function gain=itu1428_native_copy(angle,q)',marker,1)==unit
    output.mkdir(parents=True)
    copied = output/'itu1428_native_copy.m'
    copied.write_bytes(adapted)
    csv = output/'scalar-inputs.csv'
    np.savetxt(csv,results[:,:2],delimiter=',',fmt='%.17g')
    np.savetxt(output/'actual-Python-scalar-observations.csv',results,delimiter=',',fmt='%.17g')
    (output/'original-configuration.json').write_bytes(configuration.read_bytes())
    write(output/'scalar-cases.json',dict(cases=rows,expected_cases=len(rows),
        native_and_Python_original_source_sha256=watched,
        convention_cases_are_not_claimed_printed_domain_coverage=True,
        exact_unrepresentable_algebraic_thresholds_not_certified=True,
        strict_sides_of_algebraic_thresholds_are_probed=True,
        scalar_original_solver_or_rng_calls=0))
    write(output/'actual-geometry-controls.json',dict(configuration_sha256=sha(configuration),
        q=q_actual,gt_diameter_m=t['gt_diameter_m'],carrier_hz=p['frequency_hz'],
        wavelength_m=299792458./p['frequency_hz'],rows=geometry,
        GT_is_equatorial_and_tracks_collinear_GEO=t['gt_latitude_deg']==0,
        hidden_author_geometry_or_diameter_recovered=False))
    write(output/'native-copy-source-proof.json',dict(original_source_sha256=sha(original_m),
        original_source='strict/cooperative-satcom/strict_satcom_scenario.m',
        original_function_unit_sha256=hashlib.sha256(unit).hexdigest(),
        adapted_function_sha256=sha(copied),only_function_name_changed=True,
        exact_inverse_reconstructs_original_function_bytes=True))
    plan = dict(original_native_path=str(original_m),original_native_sha256=sha(original_m),
        native_function_path=str(copied),native_function_sha256=sha(copied),
        input_csv=str(csv),expected_cases=len(rows),output_csv=str(output/'actual-native-scalar-observations.csv'),
        output_receipt=str(output/'actual-native-scalar-execution.json'))
    write(output/'native-scalar-plan.json',plan)
    assert watched=={path:sha(Path(path)) for path in watched}
    write(output/'prepare-receipt.json',dict(source_and_configuration_unchanged=True,source_sha256=watched,
        actual_cases=len(rows),native_execution_not_yet_claimed=True,optimizer_or_random_draw_calls=0,
        output_sha256={p.name:sha(p) for p in output.iterdir() if p.is_file()}))
    print(json.dumps(dict(prepared_cases=len(rows),q_actual=q_actual,actual_geometry=geometry,
        plan=str(output/'native-scalar-plan.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    a=parser.parse_args()
    prepare(a.configuration,a.output_dir)
