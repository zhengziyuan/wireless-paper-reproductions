"""Independently reconstruct every native1000-draw moment sample from r,G,d."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import mpmath as mp
import numpy as np
from scipy.io import loadmat
from audit_native_case import channel_data
import mp_phase_reference as reference


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())


def input_data(result_path):
    result=read(result_path);state=result_path.parent/result['state_recording']['filename']
    if sha(state)!=result['state_recording']['sha256']:raise ValueError('Actual native states differ')
    rec=loadmat(state,simplify_cells=True)['recording']['input'];p=rec['configuration']['reported']
    J,U,N,M=(int(p[k]) for k in ('J','U','N','M'));data=channel_data(rec['data'],J,U,N,M)
    t=rec['configuration']['tuned_not_reported'];h=hashlib.sha256()
    for name,a in sorted(data.items()):h.update(name.encode());h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes(order='C'))
    source=result['executed_source_hashes']['run_strict_cooperative_v3_m']['sha256']
    h.update(json.dumps(dict(seed=int(t['seed']),count=int(t['monte_carlo_realizations']),source=source,phase='allones'),sort_keys=True).encode())
    return result,data,(J,U,N,M),h.hexdigest()


def within(a,b):return np.isfinite(a).all() and np.isfinite(b).all() and np.all(abs(a-b)<=1e-9+1e-10*abs(b))


def audit(result_path,replayed,output,bank=None):
    if output.exists():raise FileExistsError('Preserve prior independent replay')
    result,data,(J,U,N,M),signature=input_data(result_path);meta=read(replayed/'index.json');payload=replayed/meta['payload'];count=meta['count']
    if count!=1000 or [meta[k] for k in ('J','U','N','M')]!=[J,U,N,M]:raise ValueError('Full original dimensions and1000 draws required')
    if meta['source_result_sha256']!=sha(result_path) or meta['state_sha256']!=result['state_recording']['sha256']:raise ValueError('Replay uses different actual inputs')
    if sha(payload)!=meta['payload_sha256']:raise ValueError('Raw draw payload differs')
    raw=np.memmap(payload,dtype='<f8',mode='r');expected=count*U*(2*M+J*(2*N*M+2*N+2))
    if raw.size!=expected:raise ValueError('Missing/extra draw operands')
    cursor=0
    def complex_array(shape):
        nonlocal cursor
        n=int(np.prod(shape));z=np.asarray(raw[cursor:cursor+n])+1j*np.asarray(raw[cursor+n:cursor+2*n]);cursor+=2*n
        return z.reshape(shape,order='F')
    second=np.zeros((count,J,U));fourth=np.zeros_like(second);native2=np.zeros_like(second);native4=np.zeros_like(second)
    all_samples=True;max2=max4=0.
    for draw in range(count):
        for u in range(U):
            r=complex_array((M,))
            for j in range(J):
                G=complex_array((N,M));d=complex_array((N,));p,p4=map(float,raw[cursor:cursor+2]);cursor+=2
                h=d+G@r;q=float(np.sum(abs(h)**2));q4=q*q
                second[draw,j,u]=q;fourth[draw,j,u]=q4;native2[draw,j,u]=p;native4[draw,j,u]=p4
                all_samples=all_samples and bool(within(np.asarray(q),np.asarray(p))) and bool(within(np.asarray(q4),np.asarray(p4)))
                max2=max(max2,abs(q-p));max4=max(max4,abs(q4-p4))
    strict=Path(__file__).resolve().parents[2]/'strict/cooperative-satcom';sys.path.insert(0,str(strict));from positive_wick import moments
    theory=moments(data,np.ones((U,M),complex));expected2=np.trace(theory['Q'],axis1=2,axis2=3).real;expected4=theory['fourth']
    mp_theory={}
    for digits in (80,100):
        with mp.workdps(digits):
            ctx=reference.FixedContext(data,np.ones((U,M),complex),np.zeros((J,U)),1.,np.zeros(data['gt_second'].shape[1]),True)
            e2=[[reference.norm2(ctx.mean[j][u])+reference.tr(ctx.C[j][u]) for u in range(U)] for j in range(J)]
            e4=[[ctx.fourth(j,u,ctx.mean[j][u]) for u in range(U)] for j in range(J)]
            mp_theory[str(digits)]=dict(second=[[mp.nstr(x,digits) for x in row] for row in e2],fourth=[[mp.nstr(x,digits) for x in row] for row in e4])
    with mp.workdps(110):
        gap=max(abs(mp.mpf(a)-mp.mpf(b)) for key in ('second','fourth') for row1,row2 in zip(mp_theory['80'][key],mp_theory['100'][key]) for a,b in zip(row1,row2))
    mp_pass=within(expected2,np.asarray(mp_theory['100']['second'],float)) and within(expected4,np.asarray(mp_theory['100']['fourth'],float)) and gap<=mp.mpf('1e-40')
    mean2=second.mean(axis=0);mean4=fourth.mean(axis=0)
    e2=float(np.max(abs(mean2-expected2)/expected2));e4=float(np.max(abs(mean4-expected4)/expected4));original=result['results'][0]['monte_carlo']
    checks=dict(all12000_reported_sample_moments_match_physical_received_signal=all_samples,all_raw_operands_consumed=cursor==expected,
        empirical_second_and_fourth_moments_match_native=bool(within(mean2,np.asarray(meta['native_empirical_second_moment'])) and within(mean4,np.asarray(meta['native_empirical_fourth_moment']))),
        independent_finite_Rician_expected_moments_MP80_MP100_pass=bool(mp_pass),original_reported_MC_error_metrics_reproduced=bool(abs(e2-original['second_moment_max_relative_error'])<=1e-9 and abs(e4-original['fourth_moment_max_relative_error'])<=1e-9))
    same=[];different=[]
    if bank is not None:
        for path in sorted(bank.glob('case-*-matlab.json')):
            other,_,_,key=input_data(path)
            if key!=signature:different.append(path.name);continue
            mc=other['results'][0].get('monte_carlo',{})
            passed=(mc.get('count')==1000 and abs(e2-mc.get('second_moment_max_relative_error',float('inf')))<=1e-9 and abs(e4-mc.get('fourth_moment_max_relative_error',float('inf')))<=1e-9)
            same.append(dict(case=path.name,unchanged_exact_input_and_seed=True,reported_MC_metrics_pass=passed,result_sha256=sha(path)))
    output.mkdir(parents=True)
    np.savez_compressed(output/'all1000_native_sample_moments.npz',second=native2,fourth=native4,independent_second=second,independent_fourth=fourth)
    report=dict(scope='Exact configured1000-draw native channel-moment stream; no optimized-design performance MC',count=1000,links_per_draw=J*U,sample_moment_values=2*count*J*U,
        dimensions=dict(J=J,U=U,N=N,M=M),input_signature=signature,checks=checks,all_independent_checks_pass=all(checks.values()) and all(r['reported_MC_metrics_pass'] for r in same),
        maximum_sample_second_error=max2,maximum_sample_fourth_error=max4,second_moment_max_relative_error=e2,fourth_moment_max_relative_error=e4,MP_expected_moments=mp_theory,
        maximum_MP80_MP100_expected_moment_difference=mp.nstr(gap,100),same_exact_input_cases=same,different_inputs_not_replayed=different,
        source_result_sha256=sha(result_path),raw_primitive_payload_sha256=sha(payload),native_replay_index_sha256=sha(replayed/'index.json'),independent_reference_sha256=sha(Path(reference.__file__)),
        original_historical_callback_buffers_recovered=False,new_optimization_or_changed_MC_count=False,full183_or_original_reference_pass=False)
    (output/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('count','sample_moment_values','all_independent_checks_pass','maximum_sample_second_error','maximum_sample_fourth_error','second_moment_max_relative_error','fourth_moment_max_relative_error')}));print('Same exact-input cases covered:',len(same));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,required=True);p.add_argument('--replayed-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--bank',type=Path);a=p.parse_args()
    if not audit(a.result,a.replayed_dir,a.output_dir,a.bank)['all_independent_checks_pass']:raise SystemExit(1)
