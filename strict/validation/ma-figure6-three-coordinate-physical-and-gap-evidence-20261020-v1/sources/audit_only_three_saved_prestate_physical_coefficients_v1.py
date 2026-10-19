"""PREPARED saved-only physical coefficient derivation, not a coordinate solve."""
import argparse
import hashlib
import importlib.util
import json
import math
import traceback
from pathlib import Path

import mpmath as mp
import numpy as np
import independent_physical_MA_coefficient_reference_v1 as P


def require(value,message):
    if not value:raise ValueError(message)


def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path.resolve()),'SHA256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def read(path):return json.loads(Path(path).read_bytes())


def write(path,value):
    payload=json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(payload)


def vector(value):return np.asarray(value,dtype=np.float64).reshape(-1)


def flatten(value):
    if isinstance(value,mp.matrix):return [value[i,j] for i in range(value.rows) for j in range(value.cols)]
    if isinstance(value,(list,tuple)):
        return [v for row in value for v in flatten(row)]
    return [value]


def text(value):
    return [text(v) for v in value] if isinstance(value,list) else mp.nstr(value,mp.mp.dps,strip_zeros=False)


def comparison(reference,actual):
    expected=flatten(reference);observed=np.asarray(actual).reshape(-1)
    require(len(expected)==len(observed),'reference/actual scalar count mismatch')
    require(np.isfinite(observed).all(),'nonfinite actual captured operand')
    observed_mp=[mp.mpc(P.exact(v.real),P.exact(v.imag)) if np.iscomplexobj(observed) else P.exact(v) for v in observed]
    errors=[abs(x-y) for x,y in zip(expected,observed_mp)]
    scale=max([mp.mpf(0)]+[abs(x) for x in expected]);maximum=max([mp.mpf(0)]+errors)
    return {'actual_storage_dtype':np.asarray(actual).dtype.str,'actual_semantic_shape':list(np.asarray(actual).shape),
            'maximum_absolute_error':text(maximum),'maximum_error_over_reference_maximum':None if scale==0 else text(maximum/scale),
            'actual_all_finite':True,'coefficient_comparison_has_no_new_PASS_threshold':True,
            'per_component_absolute_errors':[text(x) for x in errors]}


def normalized_c(c):
    out={k:vector(c[k]).tolist() for k in ['beta','rician','noise']}
    out.update(directions=np.asarray(c['directions'],dtype=np.float64).tolist(),
               power=float(np.asarray(c['power']).reshape(-1)[0]),wavelength=float(np.asarray(c['wavelength']).reshape(-1)[0]))
    return out


def actual_intermediates(model,reference):
    events=model['events']
    if model['mode']=='MRT':
        observations=[data for stage,data in events if stage=='actual_original_MRT_statistics_return']
        require(observations,'actual pre-MRT statistics absent')
        actual=observations[0]
        return {k:comparison(v,actual[k]) for k,v in reference['intermediates'].items()}
    observations=[data for stage,data in events if stage=='actual_ZF_user_expansion']
    require(len(observations)==len(reference['user_intermediates']),'complete actual ZF expansion users required')
    aliases={'python':{'H':'h','Theta2':'theta2','inverse':'inv','Y':'y','a':'a','X':'x','b':'b','lmax':'lmax','q':'q','ratio':None},
             'native':{'H':'H','Theta2':'Theta2','inverse':'inverse','Y':'Y','a':'a','X':'X','b':'b','lmax':'lmax','q':'q','ratio':'ratio'}}
    result=[]
    for index,(actual,expected) in enumerate(zip(observations,reference['user_intermediates'])):
        require(int(np.asarray(actual['u']).reshape(-1)[0])==(index if model['lane']=='python' else index+1),'actual user order mismatch')
        comparison_rows={}
        for key,source_key in aliases[model['lane']].items():
            # Python ratio was not captured independently at this event; no
            # synthetic reconstruction is labelled an observed intermediate.
            if source_key is not None:comparison_rows[key]=comparison(expected[key],actual[source_key])
        X=np.asarray(actual[aliases[model['lane']]['X']])
        anti=mp.sqrt(mp.fsum(abs(mp.mpc(P.exact(X[i,j].real),P.exact(X[i,j].imag))-
                           mp.conj(mp.mpc(P.exact(X[j,i].real),P.exact(X[j,i].imag))))**2
                           for i in range(X.shape[0]) for j in range(X.shape[1])))
        result.append({'user_zero_based':index,'comparisons':comparison_rows,
            'actual_stored_X_antiHermitian_Fnorm':text(anti),
            'MP_derived_theoretical_X_antiHermitian_Fnorm':text(expected['X_antiHermitian_Fnorm']),
            'eigenvalue_scope':'MP eigenvalue is of the theoretically Hermitian physical formula. Original Python used eigvalsh(X) lower triangle; native used eig((X+XH)/2). Neither stored matrix is silently repaired here.'})
    return result


def audit_precision(model,c,t,antenna,job,dps):
    with mp.workdps(dps):
        physical=P.reference(P.inputs(c,t,antenna),model['mode'])
        raw=P.reference(P.source_literal_geometry(job,c,t,antenna),model['mode'])
        coefficients={k:comparison(value,model['coeff'][k]) for k,value in physical['coefficients'].items()}
        raw_coefficients={k:comparison(value,model['coeff'][k]) for k,value in raw['coefficients'].items()}
        captured_tangent=([P.exact(x) for x in model['coeff']['g']] if model['mode']=='MRT' else
            [mp.fsum(P.exact(model['coeff']['G'][u,j])/P.exact(model['coeff']['a'][u]) for u in range(len(model['coeff']['a'])))/mp.log(2) for j in range(2)])
        direct_error=max(abs(captured_tangent[j]-physical['direct_gradient'][j]) for j in range(2))
        derived_identity=max(abs(physical['tangent'][j]-physical['direct_gradient'][j]) for j in range(2))
        before_error=abs(P.exact(model['objective_before'])-physical['direct_value'])
        # Existing independent complete-state reader used these two1e-9
        # numerical consistency tolerances. They are NOT paper stops, new
        # coefficient-error budgets, or a replacement for fixed-coeff gaps.
        atol=P.exact(1e-9)
        raw_inputs=P.source_literal_geometry(job,c,t,antenna)
        return {'decimal_precision':dps,
            'captured_physical_field_reference_coefficients':{k:text(v) for k,v in physical['coefficients'].items()},
            'common_source_literal_geometry_reference_coefficients':{k:text(v) for k,v in raw['coefficients'].items()},
            'captured_coefficients_vs_own_actual_physical_fields_MP':coefficients,
            'captured_coefficients_vs_common_raw_geometry_MP':raw_coefficients,
            'captured_directions_vs_original_angle_formula':comparison(raw_inputs['directions'],c['directions']),
            'captured_beta_vs_original_distance_formula':comparison(raw_inputs['beta'],c['beta']),
            'captured_physical_objective':text(physical['direct_value']),
            'common_raw_geometry_objective':text(raw['direct_value']),
            'captured_physical_direct_gradient':[text(x) for x in physical['direct_gradient']],
            'captured_coefficient_tangent':[text(x) for x in captured_tangent],
            'derived_MP_minorant_tangent':[text(x) for x in physical['tangent']],
            'MP_derived_tangent_vs_direct_gradient_max_error':text(derived_identity),
            'actual_captured_tangent_vs_direct_gradient_max_error':text(direct_error),
            'actual_objective_before_vs_direct_max_error':text(before_error),
            'existing_independent_consistency_atol':text(atol),
            'existing_independent_consistency_checks':{'actual_tangent_vs_direct_physical_gradient':bool(direct_error<atol),
                                                     'actual_objective_before_vs_direct_physical_value':bool(before_error<atol)},
            'actual_prestate_intermediate_comparisons':actual_intermediates(model,physical),
            'no_coordinate_candidates_roots_or_poststate_optimization_evaluated':True}


def run(plan_path,admission_path,output):
    metadata=[pin(plan_path),pin(admission_path)]
    plan,admission=read(plan_path),read(admission_path)
    require(admission.get('root_admitted_only_three_saved_prestate_physical_coeff_MP') is True,'false admission')
    require(admission['plan_SHA256']==metadata[0]['SHA256'],'plan admission mismatch')
    require(Path(admission['output_directory']).resolve()==output.resolve(),'output admission mismatch')
    before=metadata+plan['source_and_input_pins']
    require(all(pin(p['path'])['SHA256']==p['SHA256'] for p in before),'source/input mismatch')
    spec=importlib.util.spec_from_file_location('exact_existing_MA6_capture_codec_only',plan['existing_capture_loader']['path'])
    loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    # No loader MP or candidate/geometry evaluation is invoked, only typed IO.
    aggregate=read(plan['six_closed_capture_aggregate']['path'])
    require(not output.exists(),'fresh output required');output.mkdir(parents=True,exist_ok=False)
    rows=[]
    try:
        for row in aggregate['rows']:
            fixture=read(row['fixture']['path']);job=fixture['selected_original_job']
            require(fixture['optional_original_design_overrides']=={},'unexpected original design override')
            result={'case':row['case'],'mode':row['mode'],'lanes':{}}
            for lane in ['python','native']:
                model=loader.load_lane(row,lane)
                actual=loader.one_event(model['events'],'actual_complete_design_and_whole_saved_prestate')
                c=normalized_c(actual['c']);t=np.asarray(actual['t'],dtype=np.float64)
                require(t.shape==(6,2) and np.isfinite(t).all(),'actual full prestate required')
                require(t.tobytes(order='F')==np.asarray(fixture['actual_pre_state'],dtype=np.float64).tobytes(order='F'),'actual prestate does not match sealed fixture')
                require(np.asarray(c['directions']).shape==(5,2) and np.isfinite(c['directions']).all() and all(len(c[k])==5 for k in ['beta','noise','rician']),'actual finite physical dimensions')
                require(all(math.isfinite(x) for k in ['beta','noise','rician'] for x in c[k]),'nonfinite actual physical inputs')
                require(all(len(job['geometry'][k])==5 for k in ['distances_m','elevation','azimuth']),'raw geometry dimensions')
                require(job['N']==6 and job['M']==5 and c['power']==job['power'] and all(k==job['kappa'] for k in c['rician'])
                        and c['wavelength']==1. and all(x==1e-11 for x in c['noise']),'actual original physical control mismatch')
                antenna=fixture['antenna_zero_based']
                require(c['wavelength']>0 and c['power']>0 and min(c['noise'])>0 and min(c['beta'])>0 and min(c['rician'])>=0,'physical input domain')
                events=actual['c']['interpretations'];require(events['mrt_curvature']=='equation_29a_max_eigenvalue','different MRT curvature interpretation')
                result['lanes'][lane]={'precision_lanes':[audit_precision(model,c,t,antenna,job,dps) for dps in [80,100]],
                    'actual_physical_fields':c,'actual_common_prestate_Fbytes_SHA256':hashlib.sha256(t.tobytes(order='F')).hexdigest()}
            rows.append(result)
        after=[pin(p['path']) for p in before]
        require(all(a['SHA256']==b['SHA256'] for a,b in zip(before,after)),'source/input changed during reader')
        passed=all(all(p['existing_independent_consistency_checks'].values()) for row in rows for lane in row['lanes'].values() for p in lane['precision_lanes'])
        report={'schema':'actual-only-three-prestates-six-new-physical-coefficient-MP80-MP100-v1','source_and_input_before':before,
            'source_and_input_after':after,'source_input_interval_closed':True,'rows':rows,
            'existing_independent_tangent_and_value_consistency_checks_pass':passed,'all_coefficient_errors_diagnostic_only':True,
            'scope_and_limits':plan['scope_and_limits'],'old_three_stepwise_bit_flags_unchanged_not_extra_disqualification':True,
            'original_reference_match_claimed':False,'historical_internal_operands_recovered':False,'actual_exit_code':0 if passed else 2}
        write(output/'ACTUAL_ONLY_THREE_PRESTATES_SIX_PHYSICAL_COEFFICIENT_MP80_MP100_V1.json',report)
        return report['actual_exit_code']
    except Exception as error:
        write(output/'ACTUAL_PHYSICAL_COEFFICIENT_READER_FAILURE_V1.json',{'error':repr(error),'traceback':traceback.format_exc(),'completed_rows':rows,'no_automatic_retry':True})
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--admission',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--execute',action='store_true');a=p.parse_args()
    require(a.execute,'prepare only: --execute plus true root admission required')
    raise SystemExit(run(a.plan,a.admission,a.output_dir))
