"""All8 actual native final states and every QT candidate with MP80/100 physics.

No optimizer, RNG or production evaluator is called. Native physical channel
coefficients and candidate operands are imported as exact binary numbers.
Phase stops have their separate complete MP audit; this closes received-power,
constraint, QT lower-bound/tightness and same-step nondecrease comparisons.
"""
import argparse
import json
from pathlib import Path
import time
import mpmath as mp
import numpy as np
from scipy.io import loadmat
from audit_native_case import sequence,channel_data,sha
import mp_phase_reference as ref


FIELDS=('sinr','denominator','satellite_power','gt_interference')


def ap(W,mean,cov,gt,offset):
    J,U,N=mean.shape;K=gt.shape[1]
    w=[[ref.vector(W[j,:,u]) for u in range(U)] for j in range(J)]
    m=[[ref.vector(mean[j,u]) for u in range(U)] for j in range(J)]
    C=[[ref.matrix(cov[j,u]) for u in range(U)] for j in range(J)]
    G=[[ref.matrix(gt[j,k]) for k in range(K)] for j in range(J)]
    amplitude=[[ref.dot(m[j][u],w[j][u]) for u in range(U)] for j in range(J)]
    num=[mp.fsum(abs(amplitude[j][u])**2 for j in range(J)) for u in range(U)]
    den=[ref.real(offset[u])+mp.fsum(ref.quad(w[j][i],C[j][u])+(abs(ref.dot(m[j][u],w[j][i]))**2 if i!=u else 0)
         for j in range(J) for i in range(U)) for u in range(U)]
    return dict(sinr=[a/b for a,b in zip(num,den)],denominator=den,
        satellite_power=[mp.fsum(ref.norm2(w[j][i]) for i in range(U)) for j in range(J)],
        gt_interference=[mp.fsum(ref.quad(w[j][i],G[j][k]) for j in range(J) for i in range(U)) for k in range(K)],
        amplitude=amplitude)


def mr(p,signal,cross,power,leak,offset):
    J,U=p.shape;K=leak.shape[2];P=[ref.vector(row) for row in p]
    S=[ref.vector(row) for row in signal]
    num=[mp.fsum(P[j][u]*S[j][u] for j in range(J)) for u in range(U)]
    den=[ref.real(offset[u])+mp.fsum(P[j][i]*ref.real(cross[j,u,i]) for j in range(J) for i in range(U))-num[u] for u in range(U)]
    if any(v<0 for row in P for v in row):raise ValueError('Negative actual MR power; no clipping in independent replay')
    return dict(sinr=[a/b for a,b in zip(num,den)],denominator=den,
        satellite_power=[mp.fsum(P[j][u]*ref.real(power[j,u]) for u in range(U)) for j in range(J)],
        gt_interference=[mp.fsum(P[j][u]*ref.real(leak[j,u,k]) for j in range(J) for u in range(U)) for k in range(K)],
        amplitude=[[mp.sqrt(P[j][u]*S[j][u]) for u in range(U)] for j in range(J)])


def compare(actual,expected):
    rows={}
    for name in FIELDS:
        got=np.asarray(actual[name]).reshape(-1);want=expected[name]
        if len(got)!=len(want):raise ValueError('Missing physical field coordinates')
        errors=[abs(ref.real(x)-y) for x,y in zip(got,want)]
        passed=all(e<=ref.real(1e-9)+ref.real(1e-10)*abs(y) for e,y in zip(errors,want))
        rows[name]=dict(passed=bool(passed),maximum_error=mp.nstr(max(errors,default=mp.mpf(0)),105),
                        reference=[mp.nstr(y,105) for y in want])
    return rows


def constraints(value,power,limit):
    tol=ref.real(1e-5)
    return bool(all(x>0 for x in value['denominator']) and
        all(x-ref.real(y)<=tol for x,y in zip(value['satellite_power'],power)) and
        all(x-ref.real(y)<=tol for x,y in zip(value['gt_interference'],limit)))


def audit(result_path,output):
    if output.exists():raise FileExistsError('Preserve prior physical audit')
    result=json.loads(result_path.read_bytes());tape=result_path.parent/result['state_recording']['filename']
    if sha(tape)!=result['state_recording']['sha256']:raise ValueError('Native sidecar differs')
    rec=loadmat(tape,simplify_cells=True)['recording'];config=rec['input']['configuration']['reported']
    J,U,N,M=(int(config[k]) for k in ('J','U','N','M'));data=channel_data(rec['input']['data'],J,U,N,M);K=data['gt_second'].shape[1]
    pl=np.asarray(rec['input']['power_limit']).reshape(-1);il=np.asarray(rec['input']['interference_limit']).reshape(-1)
    states=sequence(rec['final_states']);schemes=sequence(result['results'][0]['schemes']);qt=sequence(rec['QT_candidates'])
    if len(states)!=8 or len(schemes)!=8 or len(qt)!=result['state_recording']['QT_candidates']:raise ValueError('All original saved states/candidates required')
    before=dict(result=sha(result_path),states=sha(tape),auditor=sha(Path(__file__)),reference=sha(Path(ref.__file__)))
    started=time.perf_counter();lanes={};all_values={}
    for digits in (80,100):
        with mp.workdps(digits):
            final=[];candidates=[];values=[]
            for state,scheme in zip(states,schemes):
                if state['scheme']!=scheme['scheme']:raise ValueError('Wrong scheme order')
                d={k:v.copy() for k,v in data.items()};phi=np.asarray(state['phi'],complex).reshape(U,M)
                if bool(state['no_ris']):
                    for key in ('G_mean','G_var','geo_G_mean','geo_G_var'):d[key]*=0
                p=np.zeros((J,U)) if state['scheme'].startswith('AP') else np.asarray(state['p']).reshape(J,U)
                ctx=ref.FixedContext(d,phi,p,1.,il,state['scheme'].startswith('MR-TTS'))
                if state['scheme'].startswith('AP'):
                    mean=np.asarray(ctx.mean,dtype=object);cov=np.asarray(ctx.C,dtype=object)
                    # ap() takes exact binary inputs; this path must retain MP channel moments.
                    # Use the same contractions below directly on the MP context instead.
                    W=np.asarray(state['W'],complex).reshape(J,N,U)
                    w=[[ref.vector(W[j,:,u]) for u in range(U)] for j in range(J)]
                    amps=[[ref.dot(ctx.mean[j][u],w[j][u]) for u in range(U)] for j in range(J)]
                    den=[ctx.geo_constant[u]+abs(ctx.geo_mean[u])**2+mp.fsum(ref.quad(w[j][i],ctx.C[j][u])+(abs(ref.dot(ctx.mean[j][u],w[j][i]))**2 if i!=u else 0) for j in range(J) for i in range(U)) for u in range(U)]
                    v=dict(sinr=[mp.fsum(abs(amps[j][u])**2 for j in range(J))/den[u] for u in range(U)],denominator=den,
                        satellite_power=[mp.fsum(ref.norm2(w[j][i]) for i in range(U)) for j in range(J)],
                        gt_interference=[mp.fsum(ref.quad(w[j][i],ctx.gt[j][k]) for j in range(J) for i in range(U)) for k in range(K)])
                else:
                    _,num,den,sinr,_,residual,power=ctx.objective(details=True)
                    v=dict(sinr=sinr,denominator=den,satellite_power=[mp.fsum(ref.real(p[j,u])*power[j][u] for u in range(U)) for j in range(J)],
                           gt_interference=[a+ref.real(b) for a,b in zip(residual,il)])
                fields=compare(scheme['evaluation'],v);physical=constraints(v,pl,il)
                domain=max(abs(abs(ref.scalar(z))-1) for z in phi.reshape(-1))<=ref.real(1e-10)
                nonnegative=bool(np.all(p>=0))
                final.append(dict(scheme=state['scheme'],fields=fields,physical_constraints_pass=physical,phase_domain_pass=bool(domain),MR_power_nonnegative=nonnegative,
                    passed=bool(physical and domain and nonnegative and all(x['passed'] for x in fields.values()))))
                values.extend(x for key in FIELDS for x in v[key])
            for index,state in enumerate(qt):
                args=sequence(state['input']);info=state['info'];candidate=np.asarray(state['candidate'])
                if state['kind']=='ap_qt_update':
                    old,mean,cov,gt,off,power,limit=args
                    mean=np.asarray(mean).reshape(J,U,N);cov=np.asarray(cov).reshape(J,U,N,N);gt=np.asarray(gt).reshape(J,K,N,N);off=np.asarray(off).reshape(-1)
                    a=ap(np.asarray(old).reshape(J,N,U),mean,cov,gt,off);b=ap(candidate.reshape(J,N,U),mean,cov,gt,off)
                elif state['kind']=='mr_qt_update':
                    old,signal,cross,pw,leak,off,power,limit=args
                    common=(np.asarray(signal).reshape(J,U),np.asarray(cross).reshape(J,U,U),np.asarray(pw).reshape(J,U),np.asarray(leak).reshape(J,U,K),np.asarray(off).reshape(-1))
                    a=mr(np.asarray(old).reshape(J,U),*common);b=mr(candidate.reshape(J,U),*common)
                else:raise ValueError('Unknown original QT kind')
                y=[[x/a['denominator'][u] for u,x in enumerate(row)] for row in a['amplitude']]
                bound=[2*mp.re(mp.fsum(mp.conj(y[j][u])*b['amplitude'][j][u] for j in range(J)))-mp.fsum(abs(y[j][u])**2 for j in range(J))*b['denominator'][u] for u in range(U)]
                tight=[2*mp.re(mp.fsum(mp.conj(y[j][u])*a['amplitude'][j][u] for j in range(J)))-mp.fsum(abs(y[j][u])**2 for j in range(J))*a['denominator'][u] for u in range(U)]
                old_fields=compare(info['before'],a);new_fields=compare(info['after'],b);tol=ref.real(1e-5)
                checks=dict(all_before_after_reported_fields_pass=all(x['passed'] for x in list(old_fields.values())+list(new_fields.values())),
                    physical_constraints_pass=constraints(b,np.asarray(power).reshape(-1),np.asarray(limit).reshape(-1)),
                    original_surrogate_primal_bound_pass=bool(ref.real(info['surrogate_minimum_sinr'])<=min(bound)+tol),
                    QT_bound_below_actual_SINR=bool(all(x<=z+tol for x,z in zip(bound,b['sinr']))),
                    QT_tight_at_original_state=bool(max(abs(x-z) for x,z in zip(tight,a['sinr']))<=tol),
                    original_minimum_SINR_nondecrease=bool(min(b['sinr'])>=min(a['sinr'])-tol))
                candidates.append(dict(index=index,kind=state['kind'],before_fields=old_fields,after_fields=new_fields,
                    independent_QT_lower_bound=[mp.nstr(x,105) for x in bound],checks=checks,passed=all(checks.values())))
                values.extend(x for v in (a,b) for key in FIELDS for x in v[key]);values.extend(bound)
            lanes[str(digits)]=dict(final_states=final,QT_candidates=candidates,all_pass=all(x['passed'] for x in final+candidates))
            all_values[digits]=values
            print(json.dumps(dict(digits=digits,all8_final_pass=all(x['passed'] for x in final),QT_count=len(qt),all_QT_pass=all(x['passed'] for x in candidates))),flush=True)
    with mp.workdps(110):gap=max(abs(a-b) for a,b in zip(all_values[80],all_values[100]));stable=gap<=mp.mpf('1e-40')
    after=dict(result=sha(result_path),states=sha(tape),auditor=sha(Path(__file__)),reference=sha(Path(ref.__file__)))
    report=dict(scope='All8 actual final states and all saved QT inputs/candidates: independent MP80/100 physical metrics, constraints, QT and nondecrease',
        source_input_sha256=before,source_and_inputs_unchanged=before==after,dimensions=dict(J=J,U=U,N=N,M=M),final_states=8,QT_candidates=len(qt),lanes=lanes,
        scalar_values_per_precision=len(all_values[80]),maximum_MP80_MP100_difference=mp.nstr(gap,105),precision_absolute_bound='1e-40',
        all_physical_QT_and_precision_checks_pass=bool(stable and before==after and all(x['all_pass'] for x in lanes.values())),
        elapsed_seconds=time.perf_counter()-started,phase_stops_MC_original_reference_or_full183_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(all_physical_QT_and_precision_checks_pass=report['all_physical_QT_and_precision_checks_pass'],elapsed_seconds=report['elapsed_seconds'])),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not audit(a.result,a.output)['all_physical_QT_and_precision_checks_pass']:raise SystemExit(1)
