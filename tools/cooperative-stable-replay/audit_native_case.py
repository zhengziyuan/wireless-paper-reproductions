"""Independent complete saved native case: all8 states, phase stops and QT candidates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.io import loadmat


def sequence(x):
    if isinstance(x,dict):return [x]
    if isinstance(x,(list,tuple)):return list(x)
    return list(np.asarray(x,dtype=object).reshape(-1))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def channel_data(raw,J,U,N,M):
    K=np.asarray(raw['gt_second']).size//(J*N*N)
    shapes=dict(d_mean=(J,U,N),d_var=(J,U),G_mean=(J,U,N,M),G_var=(J,U),r_mean=(U,M),r_var=(U,),
        gt_second=(J,K,N,N),geo_d_mean=(U,),geo_d_var=(U,),geo_G_mean=(U,M),geo_G_var=(U,))
    return {key:np.asarray(raw[key]).reshape(shape) for key,shape in shapes.items()}


def close(a,b):
    a,b=np.asarray(a).reshape(-1),np.asarray(b).reshape(-1)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():return False,float('inf')
    err=abs(a-b);return bool(np.all(err<=1e-9+1e-10*abs(b))),float(err.max(initial=0))


def audit(result_path,output,before_recording=None):
    if output.exists():raise FileExistsError('Preserve prior audit')
    result=json.loads(result_path.read_bytes());spec=result['state_recording'];state_path=result_path.parent/spec['filename']
    if sha(state_path)!=spec['sha256']:raise ValueError('Actual state output differs')
    rec=loadmat(state_path,simplify_cells=True)['recording'];p=rec['input']['configuration']['reported']
    J,U,N,M=(int(p[k]) for k in ('J','U','N','M'));data=channel_data(rec['input']['data'],J,U,N,M)
    power=np.asarray(rec['input']['power_limit']).reshape(-1);limit=np.asarray(rec['input']['interference_limit']).reshape(-1)
    strict=Path(__file__).resolve().parents[2]/'strict/cooperative-satcom';sys.path.insert(0,str(strict))
    from positive_wick import moments,evaluate_ap,evaluate_mr
    import core
    point=result['results'][0];schemes=sequence(point['schemes']);states=sequence(rec['final_states'])
    expected=['AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS']
    if [s['scheme'] for s in schemes]!=expected or [s['scheme'] for s in states]!=expected:raise ValueError('All8 original schemes required')
    final=[]
    for state,scheme in zip(states,schemes):
        d={k:v.copy() for k,v in data.items()};phi=np.asarray(state['phi'],complex).reshape(U,M)
        if bool(state['no_ris']):
            for key in ('G_mean','G_var','geo_G_mean','geo_G_var'):d[key]*=0
        if state['scheme'].startswith('AP'):
            terms=moments(d,phi);value=core.ap_evaluate(np.asarray(state['W'],complex).reshape(J,N,U),terms['mean'],terms['C'],d['gt_second'],terms['offset'])
        else:
            pa=np.asarray(state['p']).reshape(J,U);x=evaluate_mr(d,phi,pa,1.,limit,state['scheme'].startswith('MR-TTS'))
            value=dict(sinr=x['sinr'],denominator=x['denominator'],satellite_power=np.sum(pa*x['power'],axis=1),gt_interference=np.einsum('ju,juk->k',pa,x['leakage']))
        comparisons={k:dict(zip(('passed','maximum_error'),close(value[k],scheme['evaluation'][k]))) for k in value}
        physical=bool(np.max(value['satellite_power']-power)<=1e-5 and np.max(value['gt_interference']-limit)<=1e-5)
        domain=bool(np.max(abs(abs(phi)-1))<=1e-10)
        final.append(dict(scheme=state['scheme'],comparisons=comparisons,physical_constraints_pass=physical,phase_domain_pass=domain,
            passed=physical and domain and all(v['passed'] for v in comparisons.values())))
    phases=[]
    for i,state in enumerate(sequence(rec['phase_endpoints'])):
        c=state['context'];d=channel_data(c['data'],J,U,N,M);phi=np.asarray(state['final_phi'],complex).reshape(U,M)
        if bool(state['vector_objective']):value=evaluate_ap(d,phi,np.asarray(c['W'],complex).reshape(J,N,U))
        else:value=evaluate_mr(d,phi,np.asarray(c['p0']).reshape(J,U),float(c['mu']),np.asarray(c['interferenceLimit']).reshape(-1),bool(c['tts']))
        gradient_ok,gradient_error=close(value['gradient'],state['gradient']);criterion_ok,criterion_error=close(value['criterion'],state['value'])
        norm=float(np.linalg.norm(value['gradient']));stop=norm<1e-6
        phases.append(dict(index=i,gradient_error=gradient_error,criterion_error=criterion_error,gradient_norm=norm,strict_original_stop_pass=stop,
            passed=gradient_ok and criterion_ok and stop))
    qt=[]
    for i,state in enumerate(sequence(rec['QT_candidates'])):
        args=sequence(state['input']);candidate=np.asarray(state['candidate']);info=state['info']
        if state['kind']=='ap_qt_update':
            w,mean,cov,gt,off,pl,il=args
            mean=np.asarray(mean).reshape(J,U,N);cov=np.asarray(cov).reshape(J,U,N,N);gt=np.asarray(gt).reshape(J,len(limit),N,N)
            value=core.ap_evaluate(candidate.reshape(J,N,U),mean,cov,gt,np.asarray(off).reshape(-1))
        else:
            p0,s,b,pw,lk,off,pl,il=args
            value=core.mr_evaluate(candidate.reshape(J,U),np.asarray(s).reshape(J,U),np.asarray(b).reshape(J,U,U),np.asarray(pw).reshape(J,U),np.asarray(lk).reshape(J,U,len(limit)),np.asarray(off).reshape(-1))
        comparisons=[close(value[k],info['after'][k])[0] for k in ('sinr','denominator','satellite_power','gt_interference')]
        qt.append(dict(index=i,kind=state['kind'],reported_candidate_physics_consistent=all(comparisons)))
    counts=(len(states)==spec['final_scheme_states'] and len(phases)==spec['phase_endpoints'] and len(qt)==spec['QT_candidates'])
    checks=dict(producer_original_gates_pass=bool(result['source_unchanged_during_run'] and result['overall_implemented_scope_success']),
        complete_saved_populations=counts,all8_independent_physical_states_pass=all(r['passed'] for r in final),
        all_actual_phase_endpoints_and_original_stops_pass=bool(phases) and all(r['passed'] for r in phases),all_saved_QT_candidate_physics_match=bool(qt) and all(r['reported_candidate_physics_consistent'] for r in qt),
        original1000_moment_draw_count=point['monte_carlo']['count']==1000)
    if before_recording is not None:
        before=json.loads(before_recording.read_bytes())
        fields=('schemes','monte_carlo','constraint_pass','convergence_pass','solver_primal_pass','qt_bound_pass')
        checks['original_configuration_and_all_numerical_outputs_unchanged_by_recording']=(before['configuration']==result['configuration'] and all(before['results'][0][k]==point[k] for k in fields))
    report=dict(scope='One complete actual saved native original case; all8 states and all saved phase/QT endpoints',result_sha256=sha(result_path),state_sha256=sha(state_path),
        dimensions=dict(J=J,U=U,N=N,M=M),final_states=final,phase_endpoints=phases,QT_candidates=qt,checks=checks,all_finite_precision_checks_pass=all(checks.values()),
        independent_full_MC_draw_replay_or_MP80_for_new_phase_contexts=False,full183_or_original_reference_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(all_finite_precision_checks_pass=report['all_finite_precision_checks_pass'],checks=checks,schemes=8,phase_endpoints=len(phases),QT_candidates=len(qt))))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--before-recording',type=Path);a=p.parse_args()
    if not audit(a.result,a.output,a.before_recording)['all_finite_precision_checks_pass']:raise SystemExit(1)
