"""Actual full-state stable W/RIS/rotation gradients versus independent MP80/100."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import mpmath as mp
import numpy as np
from audit_failure import FixedObjective,clean,mpmatrix,sha
from equivalent_runtime import binding,load_core
from mp_physical_reference import exact,field_parts


def reference(w,theta,r,c,iota):
    h,g,b=field_parts(r,c);mw=mpmatrix(w);mt=[exact(complex(x)) for x in theta]
    obj=FixedObjective(mw,c,iota,(h,g,b));metric=obj.evaluate(mt,True)
    f=h+b*mp.diag(mt)*g;y=f.conjugate().transpose()*mw
    k=len(c['noise']);den=exact(iota)**2*mp.fsum(exact(x)**2 for x in c['desired_pattern'])
    weights=[]
    for u in range(k):
        I=exact(c['noise'][u])+mp.fsum(abs(y[u,s])**2 for s in range(mw.cols) if s!=u)
        S=abs(y[u,u])**2;T=I+S
        weights.append([(1/T if s==u else -S/(T*I))/mp.log(2) for s in range(mw.cols)])
    for l,d in enumerate(c['desired_pattern'],k):
        residual=mp.fsum(abs(y[l,s])**2 for s in range(mw.cols))-exact(iota)*exact(d)
        weights.append([-2*exact(c['rho'])*residual/den]*mw.cols)
    gw=[[2*mp.fsum(f[m,l]*weights[l][s]*y[l,s] for l in range(f.cols))
         for s in range(mw.cols)] for m in range(mw.rows)]
    eps=mp.mpf('1e-20');gr=[]
    for d in range(6):
        plus=[exact(float(x)) for x in r];minus=list(plus);plus[d]+=eps;minus[d]-=eps
        p=FixedObjective(mw,c,iota,field_parts(plus,c)).evaluate(mt)['utility']
        q=FixedObjective(mw,c,iota,field_parts(minus,c)).evaluate(mt)['utility']
        gr.append((p-q)/(2*eps))
    return gw,metric['ambient'],gr


def run(capture,output):
    if output.exists():raise FileExistsError('Preserve previous audit')
    before=binding();model=load_core();meta=json.loads((capture/'actual-failure.json').read_bytes())
    c=json.loads((capture/'original-scenario.json').read_bytes())
    assert sha(capture/'actual-failure-arrays.npz')==meta['array_sha256']
    with np.load(capture/'actual-failure-arrays.npz',allow_pickle=False) as a:
        w,theta,r=a['w'].copy(),a['theta'].copy(),a['r'].copy()
    _,actual=model.evaluate(w,theta,r,c,meta['iota'],True)
    started=time.perf_counter();lanes={};values={}
    for digits in (80,100):
        with mp.workdps(digits):
            ref=reference(w,theta,r.tolist(),c,meta['iota']);rows={}
            for name,got,expected in zip(('W','RIS','rotation'),actual,ref):
                flat=list(np.asarray(expected,dtype=object).reshape(-1));numeric=list(np.asarray(got).reshape(-1))
                errors=[abs(exact(complex(x)) - y) for x,y in zip(numeric,flat)]
                rows[name]=dict(components=len(flat),maximum_error=mp.nstr(max(errors),digits),
                    original_component_absolute_1e_minus5_pass=bool(max(errors)<exact(1e-5)),
                    expected=[dict(real=mp.nstr(mp.re(y),digits),imag=mp.nstr(mp.im(y),digits)) for y in flat])
            values[digits]=[x for block in ref for x in np.asarray(block,dtype=object).reshape(-1)]
            lanes[str(digits)]=rows
            print(json.dumps(dict(digits=digits,maximum_errors={k:v['maximum_error'] for k,v in rows.items()})),flush=True)
    with mp.workdps(110):gap=max(abs(a-b) for a,b in zip(values[80],values[100]));stable=gap<=mp.mpf('1e-35')
    assert before==binding()
    report=dict(scope='Actual M4/N36/K2/A66 fixed failure state; all original W/RIS/rotation gradient components',
        source_binding=before,auditor_sha256=sha(Path(__file__)),reference_sha256=sha(Path(__file__).with_name('mp_physical_reference.py')),
        capture_array_sha256=meta['array_sha256'],source_unchanged=True,lanes=lanes,
        rotation_reference='MP central difference at1e-20; W and RIS use independent analytic derivatives',
        original_component_absolute_error_bound=1e-5,maximum_MP80_MP100_difference=mp.nstr(gap,105),crossprecision_absolute_bound='1e-35',
        all_gradient_checks_pass=bool(stable and all(row['original_component_absolute_1e_minus5_pass'] for lane in lanes.values() for row in lane.values())),
        elapsed_seconds=time.perf_counter()-started,full_convergence_or_paper_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(all_gradient_checks_pass=report['all_gradient_checks_pass'],elapsed_seconds=report['elapsed_seconds'])),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not run(a.capture,a.output)['all_gradient_checks_pass']:raise SystemExit(1)
