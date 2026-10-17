"""Actual failed full-size AP QT input: independent MP80 physics and original Python solve."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.io import loadmat
import mpmath as mp


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def evaluate_mp(W,mean,cov,gt,offset):
    J,N,U=W.shape;K=gt.shape[1]
    c=lambda z:mp.mpc(float(np.real(z)),float(np.imag(z)))
    vec=lambda x:mp.matrix([c(v) for v in x])
    mat=lambda x:mp.matrix([[c(v) for v in row] for row in x])
    num=[mp.mpf(0) for _ in range(U)];den=[mp.mpf(float(v)) for v in offset]
    power=[mp.mpf(0) for _ in range(J)];leak=[mp.mpf(0) for _ in range(K)]
    for j in range(J):
        for i in range(U):
            w=vec(W[j,:,i]);power[j]+=(w.H*w)[0].real
            for k in range(K):leak[k]+=(w.H*mat(gt[j,k])*w)[0].real
            for u in range(U):
                m=vec(mean[j,u]);signal=abs((m.H*w)[0])**2
                if u==i:num[u]+=signal
                den[u]+=(w.H*mat(cov[j,u])*w)[0].real+(signal if i!=u else 0)
    return dict(sinr=[a/b for a,b in zip(num,den)],denominator=den,satellite_power=power,gt_interference=leak,numerator=num)


def audit(input_path,native_path,output):
    if output.exists():raise FileExistsError('Preserve prior numerical evidence')
    source=loadmat(input_path,struct_as_record=False,squeeze_me=False)
    args=source['varargin'].reshape(-1)
    if len(args)!=7:raise ValueError('Original complete AP QT input required')
    W0,mean,cov,gt,offset,power,limit=args
    offset,power,limit=(np.asarray(x).reshape(-1) for x in (offset,power,limit))
    if W0.shape!=(3,16,2) or mean.shape!=(3,2,16) or cov.shape!=(3,2,16,16) or gt.shape!=(3,1,16,16):raise ValueError('Original full input dimensions required')
    native=loadmat(native_path,struct_as_record=False,squeeze_me=False);W=native['W'];info=native['info'][0,0]
    strict=Path(__file__).resolve().parents[2]/'strict/cooperative-satcom';sys.path.insert(0,str(strict))
    import core
    python_W,python_info=core.ap_qt_update(W0,mean,cov,gt,offset,power,limit,solver='CLARABEL',solver_options={})
    with mp.workdps(80):
        original=evaluate_mp(W0,mean,cov,gt,offset);actual=evaluate_mp(W,mean,cov,gt,offset);other=evaluate_mp(python_W,mean,cov,gt,offset)
        fields=[]
        for name in ('sinr','denominator','satellite_power','gt_interference'):
            recorded=np.asarray(getattr(info.after[0,0],name)).reshape(-1)
            if len(recorded)!=len(actual[name]):raise ValueError('Physical metric coverage differs')
            for i,(a,b) in enumerate(zip(recorded,actual[name])):
                error=abs(mp.mpf(float(a))-b);allowance=mp.mpf(1e-9)+mp.mpf(1e-10)*abs(b)
                fields.append(dict(field=name,index=i,absolute_error=mp.nstr(error,30),allowance=mp.nstr(allowance,30),passed=bool(error<=allowance)))
        physical=lambda v: all(v['satellite_power'][j]<=mp.mpf(float(power[j]))*(1+mp.mpf(1e-5)) for j in range(3)) and all(v['gt_interference'][k]<=mp.mpf(float(limit[k]))*(1+mp.mpf(1e-5)) for k in range(len(limit)))
        native_gamma=float(info.surrogate_minimum_sinr[0,0]);python_gamma=python_info['surrogate_minimum_sinr']
        qtbound=mp.mpf(native_gamma)-min(actual['sinr'])
        pass_fields=all(r['passed'] for r in fields)
        checks=dict(all_native_metrics_match_independent_MP80=pass_fields,native_original_physical_constraints_pass=physical(actual),
            python_original_physical_constraints_pass=physical(other),native_original_QT_bound_pass=bool(qtbound<=mp.mpf(1e-5)),
            native_original_minimum_sinr_nondecrease=bool(min(actual['sinr'])>=min(original['sinr'])-mp.mpf(1e-5)),
            independent_original_Python_same_QT_optimum_agrees=abs(native_gamma-python_gamma)<=1e-5)
        result=dict(scope='One actual previously failed full-size AP QT input; no reduced system or new nonconvex figure',
            input_sha256=digest(input_path),native_output_sha256=digest(native_path),independent_Python_core_sha256=digest(strict/'core.py'),
            native_AP_provider_sha256=digest(strict/'strict_satcom_ap_qt_scaled.m'),
            dimensions=dict(satellites=3,feeds_per_satellite=16,users=2,ground_terminals=1),MP_digits=80,
            old_native_solver_failure_retained=True,native_solver_status=''.join(info.solver_status.reshape(-1).tolist()),
            native_reported_primal_relative_violation=float(info.solver_diagnostics[0,0].constraint_max_relative_violation[0,0]),
            original_before_minimum_sinr=float(min(original['sinr'])),native_after_minimum_sinr=float(min(actual['sinr'])),
            native_surrogate_minimum_sinr=native_gamma,independent_Python_surrogate_minimum_sinr=python_gamma,
            absolute_independent_optimum_difference=abs(native_gamma-python_gamma),physical_field_comparisons=fields,checks=checks,
            all_checks_pass=all(checks.values()),original_model_or_QT_problem_or_gate_changed=False,complete_nonconvex_case_or_full183_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('native_solver_status','native_after_minimum_sinr','absolute_independent_optimum_difference','checks','all_checks_pass')}))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--native-output',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not audit(a.input,a.native_output,a.output)['all_checks_pass']:raise SystemExit(1)
