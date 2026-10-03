"""Independent actual native-v4 state audit; read-only, no optimization.

The source route is explicitly MATLAB MAT-v7.3, not Python recording NPZ.
Reuses the previously independently executed scalar/matrix Python audit oracle
WITHOUT editing it. Native randn bitwise replay is a separate MATLAB receipt;
absence of that actual receipt remains a false, not a fabricated success.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / 'wireless-paper-reproductions/strict/cooperative-satcom'
sys.path.insert(0, str(BASE))
from mat73_readonly_v2_work import read as read_mat73, dependency_metadata
import audit_recording_v4_actual_work as oracle

EXPECTED = ('AP-NoRIS', 'AP-AO', 'MR-S-NoRIS', 'MR-S-PA', 'MR-S-TS',
            'MR-TTS-NoRIS', 'MR-TTS-PA', 'MR-TTS-TS')
FROZEN = {'run_strict_cooperative_v4_recording_work.m': '49fada43f6db98188944c6bff4b47076761080442a1f2fbca60c7ea06ef500f7',
    'strict_satcom_algorithms_v4_recording_work.m': '7219d3fb9e92dc46d70ab6026ca2c6698f7a55dde7ebafe757534b417496cd7f',
    'strict_satcom_recording_v4_work.m': 'dd3776b251cc935f5e04a2ddae94b4ad783954d18770e8e376a9c1070b4db9ab',
    'run_cooperative_v4_native_checked_work.m': '8457710bb920ac8c4ec04db658a4ac9a1b2a69176b7873e4dbd7a33da51408f3'}
ORACLE_SHA = 'de132fed06811d95bcc08f0a954b406704b4cf9d7a933785a5728a5f07d204b7'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def items(x):
    return x if isinstance(x, list) else [x]


def arr(x, shape):
    a = np.asarray(x)
    if a.size != np.prod(shape):
        raise ValueError(f'Actual MATLAB numeric size {a.shape} incompatible with {shape}')
    # MATLAB drops trailing singleton dimensions. Preserve original column order.
    if a.shape != tuple(shape):
        a = a.reshape(shape, order='F')
    return a


def vec(x, size):
    return arr(x, (size,))


def plain(x):
    if isinstance(x, np.ndarray):
        return plain(x.tolist())
    if isinstance(x, np.generic):
        return plain(x.item())
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, list):
        return [plain(v) for v in x]
    return x


def data_arrays(data, J, U, N, M, K):
    shapes = {'d_mean': (J,U,N), 'd_var': (J,U), 'G_mean': (J,U,N,M), 'G_var': (J,U),
        'r_mean': (U,M), 'r_var': (U,), 'gt_second': (J,K,N,N),
        'geo_d_mean': (U,), 'geo_d_var': (U,), 'geo_G_mean': (U,M), 'geo_G_var': (U,)}
    assert set(data) == set(shapes)
    return {k: arr(data[k], shape) for k, shape in shapes.items()}


def metric_vectors(metric, J, U, K):
    return {key: vec(metric[key], size) for key, size in
            [('sinr',U), ('denominator',U), ('satellite_power',J), ('gt_interference',K)]}


def assert_same_bindings(before, after):
    assert plain(before) == plain(after), 'Actual source/runtime interval differs'


def audit(args):
    start = time.perf_counter()
    assert not args.output.exists()
    assert sha(HERE/'audit_recording_v4_actual_work.py') == ORACLE_SHA
    for name, digest in FROZEN.items():
        assert sha(HERE/name) == digest, name
    auditor_paths=[Path(__file__),HERE/'mat73_readonly_v2_work.py',HERE/'audit_recording_v4_actual_work.py',
        BASE/'models.py',BASE/'scenario.py',BASE/'core.py']
    auditor_before={path.name:sha(path) for path in auditor_paths}
    result = json.loads(args.actual_result.read_text(encoding='utf-8-sig'))
    native_binding = json.loads(args.runtime_binding.read_text(encoding='utf-8-sig'))
    config = json.loads(args.configuration.read_text(encoding='utf-8-sig'))
    state_path = Path(str(args.actual_result)+'.states.mat')
    before_inputs = {p.name: sha(p) for p in [args.actual_result, state_path, args.runtime_binding, args.configuration]}
    assert native_binding['actual_full_result_sha256'] == sha(args.actual_result)
    assert native_binding['actual_recorded_states_sha256'] == sha(state_path)
    assert native_binding['source_and_selected_backend_interval_pass'] and result['source_unchanged_during_run']
    assert_same_bindings(native_binding['selected_backend_MAT_and_MEX_inventory_before'], native_binding['selected_backend_MAT_and_MEX_inventory_after'])
    assert_same_bindings(native_binding['scientific_source_and_configuration_before'], native_binding['scientific_source_and_configuration_after'])
    for key, binding in result['executed_source_hashes'].items():
        if key == 'immutable_configuration':
            assert binding['sha256'] == sha(args.configuration)
        elif not key.startswith('runtime_') and isinstance(binding, dict):
            assert sha(BASE/binding['filename']) == binding['sha256'], binding['filename']
    protocol = result['recording_only_protocol']
    assert items(protocol['state_file_sha256'])[0]['sha256'] == sha(state_path)
    adapter_binding = protocol['adapter_source_binding']
    assert_same_bindings(adapter_binding['adapter_sources_before'], adapter_binding['adapter_sources_after'])
    assert adapter_binding['adapter_source_unchanged_during_run'] and protocol['numerical_outputs_unmodified']
    for binding in items(adapter_binding['adapter_sources_before']):
        path = args.configuration if binding['name'] == args.configuration.name else HERE/binding['name']
        assert sha(path) == binding['sha256']
    raw = read_mat73(state_path, ['recordedCases', 'recordingMetadata'])
    assert raw['recordingMetadata']['adapter_source_unchanged_during_run']
    assert_same_bindings(raw['recordingMetadata']['adapter_sources_before'], adapter_binding['adapter_sources_before'])
    assert_same_bindings(raw['recordingMetadata']['adapter_sources_after'], adapter_binding['adapter_sources_after'])
    cases = items(raw['recordedCases']);entries = items(result['results'])
    assert len(cases) == len(entries) == 1
    case = cases[0];entry = entries[0];assert case['complete_original_return']
    assert config == result['configuration']
    # MATLAB JSON scalar/row-vs-column metadata is not Python list shape proof.
    p = config['reported'];J,U,N,M,K = (int(p[x]) for x in ['J','U','N','M','K'])
    ss = case['scheme_state'];data = data_arrays(ss['data'],J,U,N,M,K)
    settings = ss['settings'];pl = vec(ss['power_limits'],J);il = vec(ss['interference_limits'],K)
    assert int(settings['monte_carlo_realizations']) == 1000 and float(settings['gradient_tolerance']) == 1e-6
    expected_il = p.get('interference_to_noise_ratio',10**(p.get('interference_to_noise_db',0)/10))
    assert np.array_equal(pl,np.full(J,p['power_w'])) and np.array_equal(il,np.full(K,expected_il))
    states = items(ss['scheme_states']);schemes = items(entry['schemes'])
    assert tuple(x['scheme'] for x in states) == tuple(x['scheme'] for x in schemes) == EXPECTED
    trace = ss['actual_call_trace'];original = trace['original_case_input']
    original_data = data_arrays(original['data'],J,U,N,M,K)
    assert all(np.array_equal(data[k],original_data[k]) for k in data)
    assert np.array_equal(pl,vec(original['power_limits'],J)) and np.array_equal(il,vec(original['interference_limits'],K))
    # Regeneration comparison is numerical, never bitwise or recovered author geometry.
    pyconfig = copy.deepcopy(config)
    for field in ['satellite_latitudes_deg','user_latitudes_deg','lu_longitudes_deg','upa_shape']:
        pyconfig['tuned_not_reported'][field] = np.atleast_1d(pyconfig['tuned_not_reported'][field]).tolist()
    regenerated, rpl, ril = oracle.make_scenario(pyconfig)
    regeneration = {key:{'maximum_error':oracle.difference(data[key],regenerated[key]),
        'numeric_comparison_pass':oracle.close(data[key],regenerated[key])} for key in data}
    scheme_records = []
    for state, scheme in zip(states,schemes):
        name = state['scheme'];phi = arr(state['phi'],(U,M))
        if name.startswith('AP'):
            mean,C,Q,f,offset = oracle.moments(data,phi,bool(state['noRIS']))
            rebuilt = oracle.ap_metric(arr(state['AP_W'],(J,N,U)),mean,C,data['gt_second'],offset)
        else:
            power = arr(state['MR_p'],(J,U));assert np.all(power>=0)
            rebuilt = oracle.mr_metric(power,*oracle.coefficients(data,phi,bool(state['tts']),bool(state['noRIS'])))
        reported = metric_vectors(scheme['evaluation'],J,U,K)
        error = {key:oracle.difference(rebuilt[key],reported[key]) for key in rebuilt}
        absolute = max(0.,float(np.max(rebuilt['satellite_power']-pl)),float(np.max(rebuilt['gt_interference']-il)))
        phase_error = float(np.max(abs(abs(phi)-1)))
        status = scheme['status'];stops = items(status['blocks'])
        actual_stops = bool(stops) and all(bool(s['converged']) and np.isfinite(s['final_residual'])
            and s['final_residual']<s['threshold'] and s['stop_rule'] in
            ['signed_relative_objective_increase','Riemannian_gradient_norm'] for s in stops)
        scheme_records.append({'scheme':name,'rebuilt_metrics':plain(rebuilt),'reported_metric_maximum_errors':error,
            'matrix_metric_pass':all(oracle.close(rebuilt[k],reported[k]) for k in rebuilt),
            'unit_modulus_maximum_error':phase_error,'absolute_original_physical_violation':absolute,
            'original_final_physical_gate_pass':absolute<settings['solver_objective_tolerance'] and phase_error<=1e-10,
            'all_recorded_original_stop_residuals_pass':actual_stops,'recorded_stop_count':len(stops)})
    phase_records = []
    for number, stage in enumerate(items(trace['phase'])):
        phi = arr(stage['phi'],(U,M));saved_gradient = arr(stage['gradient'],(U,M));stop = stage['status']
        if stage['phase_kind']=='AP':
            value,gradient = oracle.ap_phase_value_gradient_reference(data,phi,arr(stage['original_AP_W'],(J,N,U)));kind='AP'
        else:
            value,gradient = oracle.mr_phase_value_gradient_reference(data,phi,arr(stage['original_fixed_MR_power'],(J,U)),
                float(stage['smoothing_mu']),il,bool(stage['tts']));kind='MR-TTS' if stage['tts'] else 'MR-S'
        value = np.asarray(value).reshape(-1);saved_value = np.asarray(stage['criterion']).reshape(-1)
        norm = float(np.linalg.norm(gradient));saved_norm = float(np.linalg.norm(saved_gradient))
        history = np.asarray(stage['history']).reshape(-1)
        phase_records.append({'phase_stage':number,'kind':kind,'iterations':int(stop['iterations']),
            'iteration_cap':int(stop['iteration_cap']),'original_threshold':float(stop['threshold']),
            'independent_scalar_coordinate_gradient_norm':norm,'actual_saved_gradient_norm':saved_norm,
            'maximum_gradient_error':oracle.difference(gradient,saved_gradient),
            'maximum_criterion_error':oracle.difference(value,saved_value),
            'reported_residual_error':abs(saved_norm-stop['final_residual']),
            'original_real_stop_and_record_length_pass':bool(stop['converged']) and stop['threshold']==1e-6
                and stop['stop_rule']=='Riemannian_gradient_norm' and saved_norm<1e-6 and len(history)-1==stop['iterations'],
            'independent_gradient_original_threshold_pass':np.isfinite(norm) and norm<1e-6,
            'saved_gradient_and_scalar_oracle_pass':oracle.close(gradient,saved_gradient) and oracle.close(value,saved_value),
            'actual_fixed_phase_stage_context_not_later_final_power_used':True})
    qt_records = []
    for number, qt in enumerate(items(trace['QT'])):
        assert qt['complete_original_return']
        qpl=vec(qt['power_limits'],J);qil=vec(qt['interference_limits'],K)
        assert np.array_equal(qpl,pl) and np.array_equal(qil,il)
        info=qt['actual_solver_info'];gamma=float(info['surrogate_minimum_sinr'])
        if qt['kind']=='ap':
            beforeW=arr(qt['W_before'],(J,N,U));candidate=arr(qt['candidate'],(J,N,U))
            mean=arr(qt['mean'],(J,U,N));C=arr(qt['covariance'],(J,U,N,N))
            GT=arr(qt['GT_second'],(J,K,N,N));offset=vec(qt['offset'],U)
            before=oracle.ap_metric(beforeW,mean,C,GT,offset);after=oracle.ap_metric(candidate,mean,C,GT,offset)
            z=np.array([[np.vdot(mean[j,u],beforeW[j,:,u])/before['denominator'][u] for u in range(U)] for j in range(J)])
            received=np.array([[np.vdot(mean[j,u],candidate[j,:,u]) for u in range(U)] for j in range(J)])
            received0=np.array([[np.vdot(mean[j,u],beforeW[j,:,u]) for u in range(U)] for j in range(J)])
            lower=np.sum(2*np.real(np.conj(z)*received),axis=0)-np.sum(abs(z)**2,axis=0)*after['denominator']
            tight=np.sum(2*np.real(np.conj(z)*received0),axis=0)-np.sum(abs(z)**2,axis=0)*before['denominator']
            user=max(0.,float(np.max((gamma-lower)/np.maximum(1,abs(lower)))));nonnegative=True
        else:
            c=qt['coefficients'];signal=arr(c['signal'],(J,U));cross=arr(c['cross'],(J,U,U))
            power=arr(c['power'],(J,U));leak=arr(c['leak'],(J,U,K));offset=vec(c['offset'],U)
            beforeP=arr(qt['p_before'],(J,U));candidate=arr(qt['candidate'],(J,U))
            before=oracle.mr_metric(beforeP,signal,cross,power,leak,offset);after=oracle.mr_metric(candidate,signal,cross,power,leak,offset)
            y=np.sqrt(np.maximum(beforeP*signal,0))/before['denominator'][None,:]
            lower=np.sum(2*y*np.sqrt(candidate*signal),axis=0)-np.sum(y*y,axis=0)*after['denominator']
            tight=np.sum(2*y*np.sqrt(beforeP*signal),axis=0)-np.sum(y*y,axis=0)*before['denominator']
            scale=qpl[:,None]/np.maximum(power,1e-300)
            for k in range(K):scale=np.minimum(scale,qil[k]/np.maximum(leak[:,:,k],1e-300))
            objective_scale=max(1e-6,float(np.max(np.sum(scale*signal,axis=0)/offset)))
            user=max(0.,float(np.max((gamma-lower)/objective_scale)));nonnegative=bool(np.all(candidate>=0))
        physical=max(0.,float(np.max(after['satellite_power']/pl-1)),float(np.max(after['gt_interference']/il-1)))
        bound=max(0.,float(gamma-np.min(after['sinr'])));increase=float(np.min(after['sinr'])-np.min(before['sinr']))
        reported_before=metric_vectors(info['before'],J,U,K);reported_after=metric_vectors(info['after'],J,U,K)
        qt_records.append({'original_QT_call':number,'kind':qt['kind'],'original_physical_relative_violation':physical,
            'original_conic_user_violation':user,'original_QT_bound_violation':bound,'original_objective_increase':increase,
            'maximum_auxiliary_identity_error':oracle.difference(tight,before['sinr']),
            'original_primal_gate_pass':nonnegative and physical<=1e-5 and user<=1e-5,
            'original_QT_bound_gate_pass':bound<=1e-5,'original_monotonicity_gate_pass':increase>=-settings['solver_objective_tolerance'],
            'recorded_before_after_matrix_metrics_pass':all(oracle.close(actual[k],saved[k]) for actual,saved in
                [(before,reported_before),(after,reported_after)] for k in actual),
            'same_current_auxiliary_identity_pass':oracle.close(tight,before['sinr'])})
    moment=case['actual_moment_draw_record'];assert int(moment['actual_count'])==1000
    draws=arr(moment['actual_effective_channels'],(J,U,N,1000));mcphi=arr(moment['phi'],(U,M))
    assert np.array_equal(mcphi,np.ones((U,M)))
    powers=np.sum(abs(draws)**2,axis=2);empirical2=np.mean(powers,axis=2);empirical4=np.mean(powers*powers,axis=2)
    mean,C,Q,fourth,offset=oracle.moments(data,mcphi);exact2=np.trace(Q,axis1=2,axis2=3).real
    e2=float(np.max(abs(empirical2-exact2)/exact2));e4=float(np.max(abs(empirical4-fourth)/fourth))
    mc=entry['monte_carlo'];analytic_pass=oracle.close(exact2,arr(moment['actual_analytic_second_moments'],(J,U))) and oracle.close(fourth,arr(moment['actual_analytic_fourth_moments'],(J,U)))
    mcpass=oracle.close(e2,mc['second_moment_max_relative_error']) and oracle.close(e4,mc['fourth_moment_max_relative_error'])
    rng_receipt=None;rngpass=False
    if args.native_rng_replay:
        rng_receipt=json.loads(args.native_rng_replay.read_text(encoding='utf-8-sig'))
        assert rng_receipt['actual_native_saved_states_sha256']==sha(state_path) and rng_receipt['actual_native_result_sha256']==sha(args.actual_result)
        assert_same_bindings(rng_receipt['replay_source_and_inputs_before'],rng_receipt['replay_source_and_inputs_after'])
        assert items(rng_receipt['replay_source_and_inputs_before'])[0]['sha256']==sha(HERE/'replay_cooperative_native_v4_moment_draws_work.m')
        rngpass=bool(rng_receipt['all_actual_native_rng_replay_checks_pass']) and all(rng_receipt['checks'].values())
    after_inputs={p.name:sha(p) for p in [args.actual_result,state_path,args.runtime_binding,args.configuration]}
    auditor_after={path.name:sha(path) for path in auditor_paths}
    checks={'actual_original_summary_four_gates_pass':all(result['checks'].values()),
        'actual_input_source_selected_runtime_interval_pass':before_inputs==after_inputs,
        'independent_auditor_and_oracle_source_interval_pass':auditor_before==auditor_after,
        'all_eight_final_matrix_metrics_pass':all(x['matrix_metric_pass'] for x in scheme_records),
        'all_eight_original_final_physical_constraints_pass':all(x['original_final_physical_gate_pass'] for x in scheme_records),
        'all_original_recorded_stop_residuals_pass':all(x['all_recorded_original_stop_residuals_pass'] for x in scheme_records),
        'all_actual_phase_final_gradients_original_threshold_pass':bool(phase_records) and all(x['original_real_stop_and_record_length_pass'] and x['independent_gradient_original_threshold_pass'] and x['saved_gradient_and_scalar_oracle_pass'] for x in phase_records),
        'all_original_QT_candidates_constraints_bound_monotonicity_pass':bool(qt_records) and all(x['original_primal_gate_pass'] and x['original_QT_bound_gate_pass'] and x['original_monotonicity_gate_pass'] and x['recorded_before_after_matrix_metrics_pass'] and x['same_current_auxiliary_identity_pass'] for x in qt_records),
        'all1000_recorded_draw_moment_metrics_rebuilt_pass':int(mc['count'])==1000 and analytic_pass and mcpass,
        'all_original1000_native_draws_and_final_rng_bitwise_replayed':rngpass}
    output={'scope':'ACTUAL_native_recording_v4_one_full_original8_chain_matrix_QT_gradient_and_moment_audit_NOT183_or_historical_figures',
        'actual_inputs_sha256':before_inputs,'full_dimensions':{'J':J,'U':U,'N':N,'M':M,'K':K},
        'independent_auditor_sources_before':auditor_before,'independent_auditor_sources_after':auditor_after,
        'checks':checks,'all_independent_native_implemented_numerical_checks_pass':all(checks.values()),
        'actual_scheme_records':scheme_records,'actual_phase_stage_records':phase_records,'actual_QT_records':qt_records,
        'phase_stage_count':len(phase_records),'QT_candidate_count':len(qt_records),
        'declared_scene_Python_regeneration_numeric_comparison':regeneration,
        'declared_scene_regeneration_bitwise_claimed':False,
        'independent_MC_second_error':e2,'independent_MC_fourth_error':e4,
        'native_RNG_replay_receipt_sha256':sha(args.native_rng_replay) if args.native_rng_replay else None,
        'native_RNG_receipt_present_and_actual':args.native_rng_replay is not None,
        'native_recording_decoder_dependency_versions':dependency_metadata(),
        'audit_source_sha256':sha(Path(__file__)),'decoder_source_sha256':sha(HERE/'mat73_readonly_v2_work.py'),
        'reused_frozen_independent_oracle_sha256':ORACLE_SHA,
        'full_QT_dual_MP80_certification':False,'phase_gradient_MP80_certification':False,
        'optimized_performance1000_MC_claimed':False,'full183_executed':False,
        'original_historical_geometry_or_publisher_conformance_recovered':False,'full_reproduction_pass':False,
        'audit_seconds':time.perf_counter()-start}
    args.output.write_text(json.dumps(plain(output),indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'actual_native_independent_checks_pass':all(checks.values()),'phase_stages':len(phase_records),
        'QT_candidates':len(qt_records),'native_RNG_actual_receipt':rngpass,'full_reproduction_pass':False}),flush=True)
    if not all(checks.values()):raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('actual_result',type=Path);p.add_argument('runtime_binding',type=Path)
    p.add_argument('configuration',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--native-rng-replay',type=Path)
    audit(p.parse_args())

