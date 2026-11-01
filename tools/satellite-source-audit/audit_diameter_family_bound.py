"""NoRIS relaxation over every S.1428-covered diameter, with other inputs fixed.

This reuses the existing independently checked MP useful/leakage quotients.
GT second moments are linear in receive gain. Their positive scaling makes
each useful/leakage quotient exactly inverse-homogeneous; no new solve, random
draw or optimizer is needed. It tests the diameter-only explanation, not the
author's unrecovered geometry, satellite/terminal gains or other patterns.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mpmath as mp

from itu1428_oracle import binary, diameter_family_gain_floor, linear, stable_meridional_angle


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def need(test,message):
    if not test:
        raise ValueError(message)


def audit(directory,input_bank,geometry,output):
    need(not output.exists(),'Preserve previous bound evidence')
    repo=Path(__file__).resolve().parents[2]
    source_index=repo/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json'
    index_path=directory/'final-state-index.json'
    old_path=directory/'independent-NoRIS-input-bound-MP80-MP100.json'
    old=read(old_path); index=read(index_path); geo=read(geometry)
    need(index['case_scope']=='subsurfaces' and index['expected_case_ordinals']==list(range(48,66)),
         'Exactly the complete18 original RIS-size source slots are required')
    need(old['all_bound_evaluations_and_source_bindings_pass'] and old['all_actual_NoRIS_values_within_relaxation_bound'],
         'The actual original MP bound must already be independently checked')
    paths=[index_path,directory/'final-states.npz',old_path,source_index,geometry,Path(__file__),
        Path(__file__).with_name('itu1428_oracle.py'),directory/'python-curve-view.json',directory/'matlab-curve-view.json',
        directory/'reference-comparison/original-figure-6-vector-reference.json',
        directory/'reference-comparison/original-figure-7-vector-reference.json']
    watched={str(p):sha(p) for p in paths}
    need(index['array_bank_sha256']==sha(paths[1]) and index['source_case_index_sha256']==sha(source_index),
         'Actual input arrays or exact original case index changed')
    need(old['source_input_sha256']['0:final-state-index.json']==sha(index_path) and
         old['source_input_sha256']['1:final-states.npz']==sha(paths[1]),'Prior bound used different actual arrays')
    source_cases={c['ordinal']:c for c in read(source_index)['cases']}
    configurations={}
    fields=('earth_radius_m','gt_latitude_deg','satellite_latitudes_deg','gt_diameter_m')
    scene_fields=('frequency_hz','geo_longitude_deg','leo_height_m','geo_height_m','J','U','N','K')
    common=None
    for ordinal in range(48,66):
        p=input_bank/f'case-{ordinal:03d}/configuration.json'
        watched[str(p)]=sha(p)
        need(sha(p)==source_cases[ordinal]['configuration_sha256'],'A full original configuration differs')
        config=read(p); r,t=config['reported'],config['tuned_not_reported']
        need(r==source_cases[ordinal]['full_reported_scene'],'Original scenario association differs')
        selection={**{k:t[k] for k in fields},**{k:r[k] for k in scene_fields}}
        if common is None:
            common=selection
        need(selection==common,'Diameter-only family requires identical admitted GT geometry and baseline diameter')
        need((r['J'],r['U'],r['N'],r['K'])==(3,2,16,1) and
             t['gt_latitude_deg']==0 and t['satellite_latitudes_deg']==[-2.5,0,2.5],
             'This analytic family is restricted to the actual configured equatorial3-satellite geometry')
        configurations[ordinal]=config
    baseline=next(iter(configurations.values()))
    p,t=baseline['reported'],baseline['tuned_not_reported']
    q0=t['gt_diameter_m']/(299792458./p['frequency_hz'])
    need(q0==geo['q'] and len(geo['rows'])==3 and geo['GT_is_equatorial_and_tracks_collinear_GEO'],
         'Actual scalar geometry fixture is from a different original scene')
    need(geo['rows'][1]['original_binary64_acos_angle_deg']==0.,'Boresight equality is required by this exact proof')
    lanes,values={},{}
    for digits in (80,100):
        with mp.workdps(digits):
            factors=[]; floor_rows=[]
            for j,row in enumerate(geo['rows']):
                need(row['satellite']==j and row['latitude_degrees']==t['satellite_latitudes_deg'][j],
                     'Wrong original satellite/angle association')
                angle=binary(row['original_binary64_acos_angle_deg'])
                independently_derived=stable_meridional_angle(binary(t['earth_radius_m']),binary(p['leo_height_m']),
                    binary(t['satellite_latitudes_deg'][j]))
                need(abs(angle-independently_derived)<mp.mpf('1e-10'),'Independent angle geometry disagrees')
                gain0=linear(binary(q0),angle,conventions=angle==0)
                need(abs(gain0-binary(row['original_pattern_absolute_linear_gain']))<=
                    mp.mpf('1e-12')+mp.mpf('1e-12')*abs(gain0),'Actual original receive gain differs from official scalar oracle')
                floor,reason=diameter_family_gain_floor(angle)
                need(floor>0 and floor<=gain0,'Invalid global diameter-family relaxation')
                factor=gain0/floor
                factors.append(factor)
                floor_rows.append(dict(satellite=j,angle_degrees=mp.nstr(angle,105),
                    independent_geometry_angle_degrees=mp.nstr(independently_derived,105),
                    original_gain=mp.nstr(gain0,105),all_q_ge20_gain_floor=mp.nstr(floor,105),
                    inverse_leakage_relaxation_factor=mp.nstr(factor,105),analytic_reason=reason))
            rows={}; numeric=[]
            for key,group in old['lanes'][str(digits)].items():
                need(group['positive_definite_GT_second_moments_checked'] and
                    group['unit_interference_coefficient'] is False,'Actual positive-definite nonunit-INR baseline required')
                group_cases=[c for c in index['cases'] if c['input_group']==key]
                need(group_cases and sorted(c['ordinal'] for c in group_cases)==sorted(group['source_cases']),
                     'Prior coefficient group contains different source slots')
                result={}
                I=mp.mpf(group['shared_GT_limit'])
                for name,value in group['bounds'].items():
                    B=[[mp.mpf(v) for v in r] for r in value['per_user_satellite_useful_to_GT_ratios']]
                    offsets=[mp.mpf(v) for v in value['positive_noise_and_GEO_offsets']]
                    need(len(B)==2 and all(len(r)==3 for r in B) and len(offsets)==2,'Missing original useful/leakage coordinates')
                    relaxed=[[v*factors[j] for j,v in enumerate(r)] for r in B]
                    best=[max(r) for r in relaxed]
                    upper=I/mp.fsum(a/b for a,b in zip(offsets,best))
                    old_upper=mp.mpf(value['upper_bound'])
                    need(upper>=old_upper,'A claimed relaxation tightened the old independent bound')
                    result[name]=dict(original_bound=mp.nstr(old_upper,105),all_diameter_relaxed_bound=mp.nstr(upper,105),
                        relaxed_per_user_satellite_quotients=[[mp.nstr(v,105) for v in r] for r in relaxed],
                        selected_best_quotients=[mp.nstr(v,105) for v in best])
                    numeric.extend([upper,old_upper,*best,*(v for r in relaxed for v in r)])
                rows[key]=dict(language=group['language'],source_cases=group['source_cases'],bounds=result)
            lanes[str(digits)]=dict(gain_floors=floor_rows,groups=rows)
            values[digits]=numeric
    with mp.workdps(110):
        gap=max(abs(x-y) for x,y in zip(values[80],values[100]))
        need(gap<=mp.mpf('1e-40'),'Prior coefficient reuse and new family arithmetic are not precision stable')
    comparisons=[]
    for language in ('python','matlab'):
        for point in read(directory/(language+'-curve-view.json'))['results']:
            ordinal=point['source_case_ordinal']
            case=next(c for c in index['cases'] if c['language']==language and c['ordinal']==ordinal)
            figure,offset=(6,ordinal-48) if ordinal<57 else (7,ordinal-57)
            reference=read(directory/f'reference-comparison/original-figure-{figure}-vector-reference.json')
            refs={c['label']:c for c in reference['curves']}
            for name,bound in lanes['100']['groups'][case['input_group']]['bounds'].items():
                upper=float(bound['all_diameter_relaxed_bound'])
                original=refs[name]['y'][offset]
                # This only makes the upper bound more permissive. It is not a
                # change to any optimizer stop, physical constraint or audit.
                envelope=upper*(1+1e-10)+1e-12
                comparisons.append(dict(language=language,ordinal=ordinal,scheme=name,source_reference=original,
                    all_diameter_fixed_other_input_upper_bound=upper,conservative_numeric_upper_envelope=envelope,
                    original_EPS_coordinate_rounding=reference['maximum_ordinate_rounding_resolution'],
                    source_exceeds_even_numeric_envelope_after_EPS_rounding=bool(original>
                        envelope+reference['maximum_ordinate_rounding_resolution'])))
    need(len(comparisons)==108,'All54 original NoRIS points per language must be retained')
    unchanged=watched=={path:sha(Path(path)) for path in watched}
    need(unchanged,'A bound source, fixed coefficient or configuration changed')
    report=dict(scope='Diameter-only hypothesis: all18 actual RIS-size cases, NoRIS bounds for every S.1428 q>=20 with all other inputs fixed',
        original_case_ordinals=list(range(48,66)),configuration_count=18,source_input_sha256=watched,
        original_baseline_q=q0,actual_original_angles_degrees=[r['original_binary64_acos_angle_deg'] for r in geo['rows']],
        source_and_inputs_unchanged=unchanged,precisions=[80,100],maximum_MP80_MP100_difference=mp.nstr(gap,105),
        prior_full_matrix_MP_quotient_solves_reused_by_exact_input_hash=True,
        new_matrix_solve_optimizer_or_random_draw_calls=0,
        theorem='Replace each positive GT second-moment matrix by its smallest scalar-gain envelope over q>=20. This relaxes leakage; the saved useful/leakage quotients scale by gain(q0)/gain_floor. The existing min-SINR relaxation then upper-bounds every diameter.',
        simultaneous_diameter_attainability_of_independent_gain_floors_required=False,
        mathematical_bound_does_not_require_a_diameter_grid_search=True,
        conservative_relative_numeric_envelope=1e-10,conservative_absolute_numeric_envelope=1e-12,
        full_floating_point_interval_certificate=False,
        source_NoRIS_reference_points_per_language=54,
        source_points_exceeding_all_diameter_bound_after_rounding={l:sum(r['source_exceeds_even_numeric_envelope_after_EPS_rounding']
            for r in comparisons if r['language']==l) for l in ('python','matlab')},
        all_diameter_gain_floor_and_MP_arithmetic_checks_pass=True,lanes=lanes,comparisons=comparisons,
        author_original_geometry_gains_satellite_beam_pattern_or_reference_recovered=False,
        alternate_receive_pattern_outside_S1428_family_ruled_out=False,
        author_paper_error_or_original_curve_or_full_paper_pass=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('lanes','comparisons','source_input_sha256','theorem')}))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('directory','input-bank','geometry','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    audit(a.directory,a.input_bank,a.geometry,a.output)
