"""Audit every stored full-size RCG trial with independent MP80 and MP100 physics.

No solver or RNG is called. Stored complex radii, W, rotations, iota, directions,
and all eighty actually tested trial vectors are retained without projection.
The full physical model and exactly promoted binary64 channel fields are
reported separately, isolating path rounding from metric cancellation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import mpmath as mp
import numpy as np
from mp_physical_reference import exact, field_parts
from stable_metrics import evaluate as stable_evaluate


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)):return [clean(v) for v in value]
    if isinstance(value, (mp.mpf, mp.mpc)):return mp.nstr(value, 105)
    if isinstance(value, np.ndarray):return clean(value.tolist())
    if isinstance(value, np.generic):return value.item()
    return value


def mpmatrix(a):
    return mp.matrix([[exact(complex(v)) for v in row] for row in a])


class FixedObjective:
    def __init__(self, w, c, iota, parts):
        h,g,b = parts
        self.n, self.k = len(c['ris_coordinates']), len(c['noise'])
        self.links, self.streams = h.cols, w.cols
        self.noise = [exact(x) for x in c['noise']]
        self.pd, self.rho, self.iota = [exact(x) for x in c['desired_pattern']], exact(c['rho']), exact(iota)
        self.den = self.iota**2*mp.fsum(x*x for x in self.pd)
        self.direct = [[mp.fsum(mp.conj(h[m,l])*w[m,s] for m in range(w.rows))
                        for s in range(w.cols)] for l in range(h.cols)]
        bw = [[mp.fsum(mp.conj(b[m,n])*w[m,s] for m in range(w.rows))
               for s in range(w.cols)] for n in range(self.n)]
        self.coupling = [[[mp.conj(g[n,l])*bw[n][s] for n in range(self.n)]
                          for s in range(w.cols)] for l in range(h.cols)]

    def evaluate(self, theta, gradient=False):
        y = [[self.direct[l][s]+mp.fsum(mp.conj(theta[n])*self.coupling[l][s][n]
                                      for n in range(self.n))
              for s in range(self.streams)] for l in range(self.links)]
        powers = [[abs(v)**2 for v in row] for row in y]
        interference = [self.noise[u]+mp.fsum(p for s,p in enumerate(powers[u]) if s!=u)
                        for u in range(self.k)]
        signal = [powers[u][u] for u in range(self.k)]
        total = [s+i for s,i in zip(signal, interference)]
        rate = mp.fsum(mp.log1p(s/i) for s,i in zip(signal, interference))/mp.log(2)
        residual = [mp.fsum(row)-self.iota*d for row,d in zip(powers[self.k:],self.pd)]
        nmse = mp.fsum(x*x for x in residual)/self.den
        result = dict(utility=rate-self.rho*nmse, rate=rate, nmse=nmse,
                      signal=signal, interference=interference, total=total)
        if gradient:
            weights = [[(1/total[u] if s==u else -signal[u]/(total[u]*interference[u]))/mp.log(2)
                        for s in range(self.streams)] for u in range(self.k)]
            weights += [[-2*self.rho*r/self.den]*self.streams for r in residual]
            ambient = [2*mp.fsum(weights[l][s]*mp.conj(y[l][s])*self.coupling[l][s][n]
                                for l in range(self.links) for s in range(self.streams))
                       for n in range(self.n)]
            result['ambient'] = ambient
        return result


def run(capture, output):
    if output.exists():raise FileExistsError('Preserve previous audit evidence')
    output.mkdir(parents=True)
    started=time.perf_counter()
    package=Path(__file__).resolve().parents[2]/'strict/rotatable-isac'
    sys.path.insert(0,str(package))
    import core
    from isac_metadata import implementation_fingerprint
    before=implementation_fingerprint()
    meta=json.loads((capture/'actual-failure.json').read_bytes())
    c=json.loads((capture/'original-scenario.json').read_bytes())
    assert before==meta['implementation_fingerprint'] and meta['source_unchanged']
    assert sha(capture/'actual-failure-arrays.npz')==meta['array_sha256']
    assert sha(capture/'original-scenario.json')==meta['scenario_sha256']
    with np.load(capture/'actual-failure-arrays.npz',allow_pickle=False) as archive:
        a={k:archive[k].copy() for k in archive.files}
    w,theta,r,iota=a['w'],a['theta'],a['r'],meta['iota']
    trials=[a[f'trial_{n:03d}'] for n in range(len(meta['actual_trials']))]
    assert len(trials)==80 and w.shape==(4,6) and theta.shape==(36,)
    bundle=core.channels(theta,r,c)
    h,g,dh,dg,b,db=core.channel_base(r,c)
    np.savez(output/'frozen-original-channel-fields.npz',h=h,g=g,b=b)
    old,(ogw,ogt,ogr)=core.evaluate(w,theta,r,c,iota,True)
    stable,(sgw,sgt,sgr)=stable_evaluate(w,*bundle,c,iota,True)
    assert old['utility']==meta['utility'] and np.array_equal(ogt,a['ambient'])
    stable_trials=[stable_evaluate(w,*core.channels(t,r,c),c,iota)['utility'] for t in trials]
    y=bundle[0][:,:len(c['noise'])].conj().T@w
    ps=abs(y)**2;tot=ps.sum(axis=1)+c['noise'];sig=ps[np.arange(len(c['noise'])),np.arange(len(c['noise']))]
    explicit=np.array([c['noise'][u]+sum(ps[u,s] for s in range(w.shape[1]) if s!=u) for u in range(len(c['noise']))])
    subtraction=tot-sig
    sources={p.name:sha(p) for p in (Path(__file__),Path(__file__).with_name('stable_metrics.py'),Path(__file__).with_name('mp_physical_reference.py'))}
    lanes=[];numeric={}
    for digits in (80,100):
        with mp.workdps(digits):
            mw=mpmatrix(w); mt=[exact(complex(x)) for x in theta]
            direction=[exact(complex(x)) for x in a['direction']]
            for model in ('full_original_physics','frozen_original_binary64_fields'):
                parts=field_parts(r.tolist(),c) if model=='full_original_physics' else tuple(mpmatrix(x) for x in (h,g,b))
                objective=FixedObjective(mw,c,iota,parts)
                base=objective.evaluate(mt,True)
                ambient=base.pop('ambient')
                tangent=[v-mp.re(v*mp.conj(t))*t for t,v in zip(mt,ambient)]
                norm=mp.sqrt(mp.fsum(abs(x)**2 for x in tangent)/len(mt))
                slope=mp.fsum(mp.re(mp.conj(v)*d) for v,d in zip(ambient,direction))
                values=[];rows=[]
                for index,(trial,record) in enumerate(zip(trials,meta['actual_trials'])):
                    metric=objective.evaluate([exact(complex(x)) for x in trial])
                    delta=metric['utility']-base['utility']
                    required=exact(c['RCG_solver']['armijo'])*exact(record['alpha'])*exact(meta['slope'])
                    values.append(metric['utility'])
                    rows.append(dict(index=index,alpha=record['alpha'],utility=metric['utility'],delta=delta,
                        original_recorded_slope_required_increment=required,MP_accepts_same_stored_trial_with_original_slope=bool(delta>=required),
                        printed_double_delta=record['value']-meta['utility'],stable_double_delta=stable_trials[index]-stable['utility'],
                        printed_value_error=exact(record['value'])-metric['utility'],stable_value_error=exact(stable_trials[index])-metric['utility']))
                row=dict(digits=digits,model=model,base=base,normalized_gradient=norm,passes_original_gradient_stop=bool(norm<=exact(c['RCG_solver']['gradient_tolerance'])),
                         analytic_slope_along_stored_direction=slope,
                         printed_ambient_maxerror=max(abs(exact(complex(x))-y) for x,y in zip(a['ambient'],ambient)),
                         stable_ambient_maxerror=max(abs(exact(complex(x))-y) for x,y in zip(sgt,ambient)),
                         ambient_gradient=[[mp.re(x),mp.im(x)] for x in ambient],trials=rows)
                numeric[(digits,model)]=[base['utility'],norm,slope]+ambient+values
                lanes.append(clean(row))
                (output/f'{model}-MP{digits}.json').write_text(json.dumps(clean(row),indent=2,allow_nan=False)+'\n',encoding='utf-8')
                print(json.dumps(dict(digits=digits,model=model,normalized_gradient=float(norm),MP_accepted=sum(x['MP_accepts_same_stored_trial_with_original_slope'] for x in rows))),flush=True)
    with mp.workdps(110):
        cross={model:max(abs(x-y) for x,y in zip(numeric[(80,model)],numeric[(100,model)]))
               for model in ('full_original_physics','frozen_original_binary64_fields')}
        precision_pass=all(x<mp.mpf('1e-40') for x in cross.values())
    after=implementation_fingerprint()
    assert after==before
    summary=dict(scope='Actual one failed full-size RCG iteration and all80 original trial vectors only',
        source_unchanged=True,implementation_fingerprint=before,capture_manifest_sha256=sha(capture/'actual-failure.json'),
        capture_array_sha256=meta['array_sha256'],scenario_sha256=meta['scenario_sha256'],auditor_sources=sources,
        frozen_channel_sha256=sha(output/'frozen-original-channel-fields.npz'),source_shape=dict(M=4,N=36,K=2,A=66,streams=6),
        all_stored_radii_preserved=True,original_Armijo_slope_and_controls_used=True,
        binary64=dict(printed_base=old['utility'],stable_base=stable['utility'],signal=sig,noise=c['noise'],
                      subtracted_interference=subtraction,explicit_self_excluded_interference=explicit,
                      relative_interference_subtraction_error=(subtraction-explicit)/explicit,
                      printed_diagonal_coeff=(1/tot-1/subtraction)+1/subtraction,stable_diagonal_coeff=1/(sig+explicit),
                      stable_original_slope_accepts=[n for n,(v,tr) in enumerate(zip(stable_trials,meta['actual_trials']))
                          if v>=stable['utility']+c['RCG_solver']['armijo']*tr['alpha']*meta['slope']]),
        crossprecision_max_abs_difference=clean(cross),crossprecision_absolute_bound='1e-40',crossprecision_pass=precision_pass,
        lanes=[{k:v for k,v in row.items() if k not in ('ambient_gradient','trials')} for row in lanes],
        elapsed_seconds=time.perf_counter()-started,full_solver_or_six_scheme_or_paper_pass=False)
    (output/'summary.json').write_text(json.dumps(clean(summary),indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(crossprecision_pass=precision_pass,source_unchanged=True,elapsed_seconds=summary['elapsed_seconds'])),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    if not run(args.capture,args.output_dir)['crossprecision_pass']:raise SystemExit(1)
