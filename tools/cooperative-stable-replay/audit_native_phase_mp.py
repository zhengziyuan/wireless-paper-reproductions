"""All saved full-case native phase endpoints at80/100 digits, no optimization."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import mpmath as mp
import numpy as np
from scipy.io import loadmat
from audit_native_case import sequence,channel_data
import mp_phase_reference as reference


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def ap_reference(data,phi,W):
    J,U,N=data['d_mean'].shape;M=phi.shape[1]
    ctx=reference.FixedContext(data,phi,np.zeros((J,U)),1.,np.zeros(data['gt_second'].shape[1]),False)
    w=[[reference.vector(W[j,:,u]) for u in range(U)] for j in range(J)]
    num=[mp.mpf(0) for _ in range(U)];den=[ctx.geo_constant[u]+abs(ctx.geo_mean[u])**2 for u in range(U)]
    for u in range(U):
        for j in range(J):
            for i in range(U):
                signal=abs(reference.dot(ctx.mean[j][u],w[j][i]))**2
                if i==u:num[u]+=signal
                den[u]+=reference.quad(w[j][i],ctx.C[j][u])+(signal if i!=u else 0)
    gradient=[]
    for u in range(U):
        row=[]
        for m in range(M):
            dn=mp.mpf(0);dd=2*mp.re(mp.conj(ctx.geo_mean[u])*1j*ctx.phi[u][m]*ctx.geo_G[u][m]*ctx.r[u][m])
            for j in range(J):
                d=[1j*ctx.phi[u][m]*ctx.G[j][u][n][m]*ctx.r[u][m] for n in range(N)]
                for i in range(U):
                    increment=2*mp.re(mp.conj(reference.dot(ctx.mean[j][u],w[j][i]))*reference.dot(d,w[j][i]))
                    if i==u:dn+=increment
                    else:dd+=increment
            row.append(1j*ctx.phi[u][m]*(dn*den[u]-num[u]*dd)/den[u]**2)
        gradient.append(row)
    return dict(criterion=[a/b for a,b in zip(num,den)],complex_gradient=gradient,norm=mp.sqrt(mp.fsum(abs(z)**2 for row in gradient for z in row)))


def audit(result_path,output):
    if output.exists():raise FileExistsError('Preserve prior high-precision evidence')
    result=json.loads(result_path.read_bytes());state_path=result_path.parent/result['state_recording']['filename']
    if sha(state_path)!=result['state_recording']['sha256']:raise ValueError('Native recording changed')
    recording=loadmat(state_path,simplify_cells=True)['recording'];p=recording['input']['configuration']['reported']
    J,U,N,M=(int(p[k]) for k in ('J','U','N','M'));stages=sequence(recording['phase_endpoints'])
    if len(stages)!=result['state_recording']['phase_endpoints']:raise ValueError('Complete actual phase population required')
    before=dict(result=sha(result_path),states=sha(state_path),reference=sha(Path(reference.__file__)),auditor=sha(Path(__file__)))
    output.mkdir(parents=True);rows=[];started=time.perf_counter()
    for i,state in enumerate(stages):
        c=state['context'];data=channel_data(c['data'],J,U,N,M);phi=np.asarray(state['final_phi'],complex).reshape(U,M)
        native=np.asarray(state['gradient'],complex).reshape(U,M);criteria=np.asarray(state['value']).reshape(-1)
        lane={};reference_values={}
        for digits in (80,100):
            with mp.workdps(digits):
                if bool(state['vector_objective']):v=ap_reference(data,phi,np.asarray(c['W'],complex).reshape(J,N,U))
                else:
                    ctx=reference.FixedContext(data,phi,np.asarray(c['p0']).reshape(J,U),float(c['mu']),np.asarray(c['interferenceLimit']).reshape(-1),bool(c['tts']))
                    v=ctx.gradient(finite_difference=False)
                criterion=v['criterion'] if isinstance(v['criterion'],list) else [v['criterion']]
                if len(criterion)!=len(criteria):raise ValueError('Complete criterion coverage required')
                gradients=[z for row in v['complex_gradient'] for z in row];errors=[];passed=True
                for actual,ref in zip(native.reshape(-1),gradients):
                    error=abs(reference.scalar(actual)-ref);allowance=reference.real(1e-9)+reference.real(1e-10)*abs(ref)
                    errors.append(error);passed=passed and error<=allowance
                criterion_pass=all(abs(reference.real(actual)-ref)<=reference.real(1e-9)+reference.real(1e-10)*abs(ref) for actual,ref in zip(criteria,criterion))
                strict_stop=v['norm']<reference.real(1e-6)
                lane[str(digits)]=dict(gradient_norm=mp.nstr(v['norm'],digits),max_native_gradient_error=mp.nstr(max(errors),digits),
                    all_native_fields_pass=bool(passed and criterion_pass),strict_original_norm_stop_pass=bool(strict_stop),
                    criterion=[mp.nstr(x,digits) for x in criterion],gradient=[dict(real=mp.nstr(z.real,digits),imag=mp.nstr(z.imag,digits)) for z in gradients])
                reference_values[digits]=(gradients,criterion)
        with mp.workdps(110):
            gaps=[abs(a-b) for a,b in zip(reference_values[80][0]+reference_values[80][1],reference_values[100][0]+reference_values[100][1])]
            gap=max(gaps);stable=gap<=mp.mpf('1e-40')
        passed=all(v['all_native_fields_pass'] and v['strict_original_norm_stop_pass'] for v in lane.values()) and stable
        row=dict(index=i,mode='AP' if bool(state['vector_objective']) else ('MR-TTS' if bool(c['tts']) else 'MR-S'),lanes=lane,
            maximum_crossprecision_difference=mp.nstr(gap,100),crossprecision_absolute1e40_pass=bool(stable),passed=bool(passed))
        (output/f'phase-{i:03d}.json').write_text(json.dumps(row,indent=2,allow_nan=False)+'\n',encoding='utf-8');rows.append(row)
        progress=dict(expected=len(stages),finished=i+1,all_finished_pass=all(r['passed'] for r in rows),elapsed_seconds=time.perf_counter()-started)
        (output/'progress.json').write_text(json.dumps(progress)+'\n',encoding='utf-8')
        print(json.dumps(dict(phase=i,expected=len(stages),passed=row['passed'],MP100_norm=lane['100']['gradient_norm'],elapsed_seconds=time.perf_counter()-started)),flush=True)
    after=dict(result=sha(result_path),states=sha(state_path),reference=sha(Path(reference.__file__)),auditor=sha(Path(__file__)))
    report=dict(scope='All actual saved full-case phase criteria, complex gradients and strict original norm stops atMP80/100; no optimizer',
        dimensions=dict(J=J,U=U,N=N,M=M),stages=len(rows),complex_coordinates_per_lane=len(rows)*U*M,precisions=[80,100],source_and_input_unchanged=before==after,
        source_input_sha256=before,all_MP_fields_original_stop_and_precision_checks_pass=all(r['passed'] for r in rows) and before==after,
        phase_summaries=[dict(index=r['index'],mode=r['mode'],passed=r['passed'],MP100_norm=r['lanes']['100']['gradient_norm'],maximum_crossprecision_difference=r['maximum_crossprecision_difference']) for r in rows],
        elapsed_seconds=time.perf_counter()-started,new_optimization_or_MC=False,interval_enclosure_or_full183_or_original_reference_pass=False)
    (output/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    if not audit(a.result,a.output_dir)['all_MP_fields_original_stop_and_precision_checks_pass']:raise SystemExit(1)
