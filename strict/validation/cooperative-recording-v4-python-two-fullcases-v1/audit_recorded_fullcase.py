"""Independent saved-state audit; never resolves a QT or optimizes a phase.

Matrix metrics/moments are rebuilt below; final gradients use the retained
independent scalar-coordinate oracle, not the executed vector contraction.
All original random draws are replayed only AFTER the actual run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'cooperative-satcom'
sys.path.insert(0,str(BASE))
from models import (sample_effective,ap_phase_value_gradient_reference,
    mr_phase_value_gradient_reference)
from scenario import make_scenario


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decode(node,bank):
    if isinstance(node,dict):
        if 'recorded_array' in node:
            a=bank[node['recorded_array']]
            assert list(a.shape)==node['shape'] and a.dtype.str==node['dtype']
            return a
        if 'recorded_complex_scalar' in node:
            c=node['recorded_complex_scalar'];return complex(decode(c['real'],bank),decode(c['imag'],bank))
        if 'recorded_nonfinite_scalar' in node:return float(node['recorded_nonfinite_scalar'])
        return {k:decode(v,bank) for k,v in node.items()}
    if isinstance(node,list):return [decode(v,bank) for v in node]
    return node


def difference(a,b):
    a,b=np.asarray(a),np.asarray(b)
    assert a.shape==b.shape
    return float(np.max(abs(a-b),initial=0))


def close(a,b):
    return bool(np.allclose(a,b,rtol=1e-10,atol=1e-9,equal_nan=False))


def same_tree(a,b):
    """Exact stored original return vs the result actually given to caller."""
    if isinstance(a,np.ndarray):return bool(np.array_equal(a,np.asarray(b)))
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(same_tree(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,(list,tuple)) and len(a)==len(b) and all(same_tree(x,y) for x,y in zip(a,b))
    return a==b


def moment(d,dvar,G,Gvar,r,rvar,phi):
    """Conditional-Gaussian law for d+G diag(phi)r, with exact fourth moment."""
    N,M=G.shape;A=G*phi[None,:];mean=d+A@r
    Cb=rvar*A@A.conj().T;er2=np.vdot(r,r).real+M*rvar
    eb2=np.vdot(mean,mean).real+np.trace(Cb).real
    C=Cb+(dvar+Gvar*er2)*np.eye(N)
    Q=C+np.outer(mean,mean.conj())
    eb4=eb2**2+np.trace(Cb@Cb).real+2*np.vdot(mean,Cb@mean).real
    er4=er2**2+M*rvar**2+2*rvar*np.vdot(r,r).real
    er2b2=er2*eb2+rvar**2*np.sum(abs(A)**2)+2*rvar*np.real(np.vdot(r,A.conj().T@mean))
    evb2=dvar*eb2+Gvar*er2b2
    ev2=dvar**2+2*dvar*Gvar*er2+Gvar**2*er4
    fourth=eb4+2*(N+1)*evb2+N*(N+1)*ev2
    return mean,C,Q,float(fourth)


def moments(data,phi,no_ris=False):
    J,U,N=data['d_mean'].shape
    mean=np.zeros((J,U,N),complex);C=np.zeros((J,U,N,N),complex)
    Q=np.zeros_like(C);fourth=np.zeros((J,U));offset=np.ones(U)
    multiplier=0 if no_ris else 1
    for u in range(U):
        for j in range(J):
            mean[j,u],C[j,u],Q[j,u],fourth[j,u]=moment(
                data['d_mean'][j,u],data['d_var'][j,u],data['G_mean'][j,u]*multiplier,
                data['G_var'][j,u]*multiplier,data['r_mean'][u],data['r_var'][u],phi[u])
        _,_,gQ,_=moment(np.array([data['geo_d_mean'][u]]),data['geo_d_var'][u],
            data['geo_G_mean'][u][None,:]*multiplier,data['geo_G_var'][u]*multiplier,
            data['r_mean'][u],data['r_var'][u],phi[u])
        offset[u]+=gQ[0,0].real
    return mean,C,Q,fourth,offset


def ap_metric(W,mean,C,GT,offset):
    J,N,U=W.shape;desired=np.zeros(U);den=np.array(offset,copy=True)
    leakage=np.zeros(GT.shape[1])
    for u in range(U):
        for j in range(J):
            desired[u]+=abs(mean[j,u].conj()@W[j,:,u])**2
            for i in range(U):
                A=C[j,u] if u==i else C[j,u]+np.outer(mean[j,u],mean[j,u].conj())
                den[u]+=np.real(W[j,:,i].conj()@A@W[j,:,i])
    for k in range(GT.shape[1]):
        for j in range(J):
            for i in range(U):leakage[k]+=np.real(W[j,:,i].conj()@GT[j,k]@W[j,:,i])
    return {'sinr':desired/den,'denominator':den,'satellite_power':np.sum(abs(W)**2,axis=(1,2)),'gt_interference':leakage}


def coefficients(data,phi,tts,no_ris):
    mean,C,Q,fourth,offset=moments(data,phi,no_ris);J,U,N=mean.shape;K=data['gt_second'].shape[1]
    s=np.zeros((J,U));b=np.zeros((J,U,U));power=np.zeros((J,U));leak=np.zeros((J,U,K))
    for j in range(J):
        for u in range(U):
            power[j,u]=np.trace(Q[j,u]).real if tts else np.vdot(mean[j,u],mean[j,u]).real
            s[j,u]=power[j,u]**2
            for i in range(U):
                b[j,u,i]=(fourth[j,u] if u==i else np.trace(Q[j,u]@Q[j,i]).real) if tts else np.vdot(mean[j,i],Q[j,u]@mean[j,i]).real
            for k in range(K):
                leak[j,u,k]=np.trace(data['gt_second'][j,k]@Q[j,u]).real if tts else np.vdot(mean[j,u],data['gt_second'][j,k]@mean[j,u]).real
    return s,b,power,leak,offset


def mr_metric(p,s,b,power,leak,offset):
    numerator=np.sum(p*s,axis=0);den=np.array(offset,copy=True)
    for u in range(p.shape[1]):den[u]+=np.sum(p*b[:,u,:])-numerator[u]
    return {'sinr':numerator/den,'denominator':den,'satellite_power':np.sum(p*power,axis=1),'gt_interference':np.einsum('ju,juk->k',p,leak)}


def audit(args):
    began=time.perf_counter();assert not args.output.exists()
    result=json.loads(args.actual_result.read_text(encoding='utf-8-sig'))
    receipt_path=Path(str(args.recording_prefix)+'.json');array_path=Path(str(args.recording_prefix)+'.npz')
    receipt=json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    assert sha(array_path)==receipt['actual_saved_array_bank_sha256']
    protocol=result['recording_only_protocol']
    assert sha(receipt_path)==protocol['actual_state_receipt_sha256']
    assert sha(array_path)==protocol['actual_state_array_bank_sha256']
    assert protocol['adapter_and_numerical_sources_before']==protocol['adapter_and_numerical_sources_after']
    assert result['source_unchanged_during_run']
    source_bindings=protocol['adapter_and_numerical_sources_before']
    for name,digest in source_bindings.items():
        path=args.configuration if name=='actual_immutable_configuration' else (HERE/'executed-sources'/name if (HERE/'executed-sources'/name).is_file() else BASE/name)
        assert sha(path)==digest,name
    config=json.loads(args.configuration.read_text(encoding='utf-8-sig'))
    assert config==result['configuration']
    expected=('AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS')
    bank=np.load(array_path,allow_pickle=False)
    cases=decode(receipt['cases'],bank);assert len(cases)==len(result['results'])==1
    case=cases[0];entry=result['results'][0];assert case['complete_original_return']
    assert tuple(entry['schemes'])==expected
    original_return_same=same_tree(case['original_numeric_result'],entry['schemes'])
    assert original_return_same
    states={s['scheme']:s for s in case['scheme_final_states']};assert tuple(states)==expected
    data=case['data'];pl=case['power_limits'];il=case['interference_limits'];settings=case['settings']
    actual_data,actual_pl,actual_il=make_scenario(config)
    data_same=set(actual_data)==set(data) and all(np.array_equal(actual_data[k],data[k]) for k in data)
    assert data_same and np.array_equal(pl,actual_pl) and np.array_equal(il,actual_il)
    assert settings==config['tuned_not_reported'] and settings['monte_carlo_realizations']==1000
    J,U,N=data['d_mean'].shape;M=data['r_mean'].shape[1]
    scheme_records=[]
    for name in expected:
        state=states[name];phi=state['phi'];reported=entry['schemes'][name]['evaluation']
        if name.startswith('AP'):
            mean,C,Q,f,off=moments(data,phi,state['noRIS'])
            rebuilt=ap_metric(state['AP_W'],mean,C,data['gt_second'],off)
        else:
            p=state['MR_p'];rebuilt=mr_metric(p,*coefficients(data,phi,state['tts'],state['noRIS']))
            assert np.all(p>=0)
        errors={k:difference(rebuilt[k],reported[k]) for k in rebuilt}
        metric_pass=all(close(rebuilt[k],reported[k]) for k in rebuilt)
        absolute=max(0,float(np.max(rebuilt['satellite_power']-pl)),float(np.max(rebuilt['gt_interference']-il)))
        relative=max(0,float(np.max(rebuilt['satellite_power']/pl-1)),float(np.max(rebuilt['gt_interference']/il-1)))
        phase_error=float(np.max(abs(abs(phi)-1)))
        scheme_records.append({'scheme':name,'rebuilt_metrics':{k:v.tolist() for k,v in rebuilt.items()},
            'reported_metric_maximum_errors':errors,'matrix_metric_pass':metric_pass,
            'unit_modulus_max_error':phase_error,'absolute_original_physical_violation':absolute,
            'relative_physical_violation':relative,'original_physical_gate_pass':absolute<settings['solver_objective_tolerance'],
            'unit_modulus_pass':phase_error<=1e-10})
    phase_records=[]
    for number,stage in enumerate(case['phase_stages']):
        assert stage['complete_original_return'] and stage['same_final_phi_as_existing_FG_call']
        phi=stage['original_final_phi'];last=stage['original_final_fg_call'];context=stage['original_FG_closure_context']
        assert np.array_equal(phi,last['phi']) and all(np.array_equal(data[k],context['data'][k]) for k in data)
        if 'W' in context:
            value,gradient=ap_phase_value_gradient_reference(data,phi,context['W']);kind='AP'
        else:
            value,gradient=mr_phase_value_gradient_reference(data,phi,context['p0'],context['mu'],context['interference_limit'],context['tts']);kind='MR-TTS' if context['tts'] else 'MR-S'
            assert np.array_equal(context['interference_limit'],il)
        saved_gradient=last['original_gradient'];stop=stage['original_phase_status']
        rebuilt_norm=float(np.linalg.norm(gradient));saved_norm=float(np.linalg.norm(saved_gradient))
        error=difference(gradient,saved_gradient);value_error=difference(value,last['original_value'])
        phase_records.append({'phase_stage':number,'phase_kind':kind,'iterations':stop['iterations'],
            'original_iteration_cap':stop['iteration_cap'],'original_threshold':stop['threshold'],
            'actual_saved_gradient_norm':saved_norm,'independent_scalar_coordinate_gradient_norm':rebuilt_norm,
            'gradient_maximum_error':error,'criterion_maximum_error':value_error,
            'reported_stop_residual_error':abs(saved_norm-stop['final_residual']),
            'fixed_phase_context_used_not_final_power':True,
            'independent_gradient_original_threshold_pass':np.isfinite(rebuilt_norm) and rebuilt_norm<stop['threshold'],
            'saved_gradient_and_scalar_coordinate_oracle_pass':close(gradient,saved_gradient) and close(value,last['original_value']),
            'original_real_stop_record_pass':stop['converged'] and stop['threshold']==1e-6 and stop['stop_rule']=='Riemannian_gradient_norm' and saved_norm<1e-6})
    qt_records=[]
    qt_calls=[c for c in case['boundary_calls'] if c['function'] in ('ap_qt_update','mr_qt_update')]
    for number,c in enumerate(qt_calls):
        inputs=c['original_inputs'];candidate,info=c['original_return']
        if c['function']=='ap_qt_update':
            W0,mean,C,GT,off,qpl,qil=inputs[:7];before=ap_metric(W0,mean,C,GT,off);after=ap_metric(candidate,mean,C,GT,off)
            z=np.array([[np.vdot(mean[j,u],W0[j,:,u])/before['denominator'][u] for u in range(U)] for j in range(J)])
            received=np.array([[np.vdot(mean[j,u],candidate[j,:,u]) for u in range(U)] for j in range(J)])
            lower=np.sum(2*np.real(np.conj(z)*received),axis=0)-np.sum(abs(z)**2,axis=0)*after['denominator']
            original_received=np.array([[np.vdot(mean[j,u],W0[j,:,u]) for u in range(U)] for j in range(J)])
            tight=np.sum(2*np.real(np.conj(z)*original_received),axis=0)-np.sum(abs(z)**2,axis=0)*before['denominator']
            scale=1.;nonnegative=True;kind='AP'
        else:
            p0,s,b,power,leak,off,qpl,qil=inputs[:8];before=mr_metric(p0,s,b,power,leak,off);after=mr_metric(candidate,s,b,power,leak,off)
            y=np.sqrt(np.maximum(p0*s,0))/before['denominator'][None,:]
            lower=np.sum(2*y*np.sqrt(candidate*s),axis=0)-np.sum(y*y,axis=0)*after['denominator']
            tight=np.sum(2*y*np.sqrt(p0*s),axis=0)-np.sum(y*y,axis=0)*before['denominator']
            coordinate_scale=qpl[:,None]/np.maximum(power,1e-300)
            for k in range(leak.shape[2]):coordinate_scale=np.minimum(coordinate_scale,qil[k]/np.maximum(leak[:,:,k],1e-300))
            scale=max(1e-6,float(np.max(np.sum(coordinate_scale*s,axis=0)/off)))
            nonnegative=bool(np.all(candidate>=0));kind='MR'
        assert np.array_equal(qpl,pl) and np.array_equal(qil,il)
        gamma=info['surrogate_minimum_sinr'];physical=max(0,float(np.max(after['satellite_power']/pl-1)),float(np.max(after['gt_interference']/il-1)))
        user=max(0,float(np.max((gamma-lower)/scale/np.maximum(1,np.maximum(abs(gamma/scale),abs(lower/scale))))))
        original_bound=max(0,float(gamma-np.min(after['sinr'])))
        monotonic=float(np.min(after['sinr'])-np.min(before['sinr']))
        reported_error=max(difference(actual[k],info[label][k]) for label,actual in (('before',before),('after',after)) for k in actual)
        qt_records.append({'original_QT_call':number,'kind':kind,'physical_relative_violation':physical,
            'original_conic_user_relative_violation':user,'qt_bound_max_violation':original_bound,
            'original_monotonic_objective_change':monotonic,'before_after_matrix_metric_maximum_error':reported_error,
            'same_current_auxiliary_tightness_error':difference(tight,before['sinr']),
            'saved_surrogate_objective':gamma,'minimum_actual_candidate_lower_surrogate':float(np.min(lower)),
            'original_primal_constraints_pass':nonnegative and physical<=1e-5 and user<=1e-5,
            'original_QT_bound_pass':original_bound<=1e-5,
            'original_monotonicity_pass':monotonic>=-settings['solver_objective_tolerance'],
            'reported_and_rebuilt_before_after_pass':all(close(actual[k],info[label][k]) for label,actual in (('before',before),('after',after)) for k in actual),
            'original_auxiliary_identity_pass':close(tight,before['sinr'])})
    # Exactly the ACTUAL original sampler sequence, replayed only after run.
    draws=case['effective_channel_draws'];assert len(draws)==entry['monte_carlo']['count']==1000
    before=case['actual_MC_rng_state_before'];bitgen=getattr(np.random,before['bit_generator'])();bitgen.state=before
    rng=np.random.Generator(bitgen);draw_errors=[];bitwise=[]
    for number,saved in enumerate(draws):
        replay=sample_effective(data,case['actual_MC_phi'],rng)
        bitwise.append(bool(np.array_equal(saved,replay)));draw_errors.append(difference(saved,replay))
    rng_equal=rng.bit_generator.state==case['actual_MC_rng_state_after']
    all_draws=np.stack(draws);powers=np.sum(abs(all_draws)**2,axis=-1)
    empirical2=np.mean(powers,axis=0);empirical4=np.mean(powers*powers,axis=0)
    mean,C,Q,fourth,off=moments(data,case['actual_MC_phi']);exact2=np.trace(Q,axis1=2,axis2=3).real
    mc2=float(np.max(abs(empirical2-exact2)/exact2));mc4=float(np.max(abs(empirical4-fourth)/fourth))
    mc={'actual_draw_count':len(draws),'all_original_draws_bitwise_replayed':all(bitwise),
        'maximum_effective_channel_replay_error':max(draw_errors),'original_rng_after_bitwise_pass':rng_equal,
        'same_original_count_no_repeated_randomization':len(draws)==1000,
        'independent_second_moment_relative_error':mc2,'independent_fourth_moment_relative_error':mc4,
        'reported_second_error_difference':abs(mc2-entry['monte_carlo']['second_moment_max_relative_error']),
        'reported_fourth_error_difference':abs(mc4-entry['monte_carlo']['fourth_moment_max_relative_error']),
        'reported_original_moment_metrics_rebuilt_pass':close(mc2,entry['monte_carlo']['second_moment_max_relative_error']) and close(mc4,entry['monte_carlo']['fourth_moment_max_relative_error']),
        'optimized_performance1000_realizations_claimed':False}
    checks={'actual_original_summary_gates_pass':all(result['checks'].values()),
        'saved_original_return_exactly_matches_actual_caller_output':original_return_same,
        'actual_input_and_runtime_source_interval_pass':True,'declared_scene_regeneration_bitwise_pass':data_same,
        'all_eight_final_matrix_metrics_pass':all(s['matrix_metric_pass'] for s in scheme_records),
        'all_eight_original_final_physical_constraints_pass':all(s['original_physical_gate_pass'] and s['unit_modulus_pass'] for s in scheme_records),
        'all_actual_phase_final_gradients_original_threshold_pass':bool(phase_records) and all(s['independent_gradient_original_threshold_pass'] and s['saved_gradient_and_scalar_coordinate_oracle_pass'] and s['original_real_stop_record_pass'] for s in phase_records),
        'all_original_QT_candidate_primal_bound_and_monotonicity_pass':bool(qt_records) and all(s['original_primal_constraints_pass'] and s['original_QT_bound_pass'] and s['original_monotonicity_pass'] and s['reported_and_rebuilt_before_after_pass'] and s['original_auxiliary_identity_pass'] for s in qt_records),
        'all_original1000_actual_draws_and_rng_bitwise_replay_pass':mc['all_original_draws_bitwise_replayed'] and mc['original_rng_after_bitwise_pass'],
        'original_saved_moment_metrics_pass':mc['reported_original_moment_metrics_rebuilt_pass']}
    output={'scope':'ACTUAL_full_one_cooperative_v4_recorded_Python_original8_chains_finalstate_and_all1000_moment_draw_audit_NOT183_or_historical_figures',
        'actual_result_sha256':sha(args.actual_result),'actual_recording_receipt_sha256':sha(receipt_path),'actual_array_bank_sha256':sha(array_path),
        'actual_configuration_sha256':sha(args.configuration),'actual_scientific_and_adapter_sources':source_bindings,
        'full_dimensions':{'J':J,'U':U,'N':N,'M':M,'K':data['gt_second'].shape[1]},
        'checks':checks,'all_independent_implemented_numerical_checks_pass':all(checks.values()),
        'actual_scheme_records':scheme_records,'actual_phase_stage_records':phase_records,'actual_QT_records':qt_records,
        'actual_original_moment_draw_audit':mc,'phase_stage_count':len(phase_records),'QT_candidate_count':len(qt_records),
        'auditor_source_sha256':sha(Path(__file__)),'audit_seconds':time.perf_counter()-began,
        'native_recording_layer_fullcase_independent_certified':False,'all_QT_duals_MP80_certified':False,
        'new_formal183_bank_executed':False,'publisher_or_original_historical_geometry_recovered':False,
        'full_reproduction_pass':False}
    bank.close();args.output.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'all_independent_checks_pass':all(checks.values()),'phase_stages':len(phase_records),'QT_candidates':len(qt_records),'all1000_bitwise':all(bitwise),'full_reproduction_pass':False}),flush=True)
    if not all(checks.values()):raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('actual_result',type=Path);parser.add_argument('recording_prefix',type=Path)
    parser.add_argument('configuration',type=Path);parser.add_argument('output',type=Path)
    audit(parser.parse_args())
