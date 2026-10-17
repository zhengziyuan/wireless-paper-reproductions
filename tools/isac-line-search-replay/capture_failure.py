"""Capture the first actual RCG failure in an original full-size input, without edits."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np


class CapturedBoundary(BaseException):pass


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def capture(config_path,scenario_path,output):
    if output.exists():raise FileExistsError('Preserve prior evidence')
    package=Path(__file__).resolve().parents[2]/'strict/rotatable-isac';sys.path.insert(0,str(package))
    import core
    from isac_metadata import implementation_fingerprint,fingerprint
    source=package/'core.py';lines=source.read_text().splitlines()
    armijo=[n for n,line in enumerate(lines,1) if 'if value>=metric["utility"]+spec["armijo"]*alpha*slope:' in line]
    if len(armijo)!=1:raise ValueError('Review actual original Armijo source before tracing')
    before=implementation_fingerprint();scene=json.loads(scenario_path.read_bytes());code=core.update_theta.__code__
    phases=0;trials=[];current_iteration=None;saved={};arrays={};started=time.perf_counter()

    def trace(frame,event,arg):
        nonlocal phases,current_iteration,trials,saved
        if frame.f_code is not code:return None
        if event=='call':phases+=1;current_iteration=None;trials=[]
        elif event=='line' and frame.f_lineno==armijo[0]:
            v=frame.f_locals;iteration=v['iteration']
            if current_iteration!=iteration:current_iteration=iteration;trials=[]
            trials.append(dict(alpha=float(v['alpha']),value=float(v['value']),recorded_threshold=float(v['metric']['utility']+v['spec']['armijo']*v['alpha']*v['slope']),trial=np.array(v['trial'],copy=True)))
        elif event=='exception' and isinstance(arg[1],RuntimeError) and ('RCG Armijo' in str(arg[1]) or 'PR direction is not ascent' in str(arg[1])):
            v=frame.f_locals
            for key in ('w','theta','r','g','ambient','direction','oldg','oldd'):
                if v.get(key) is not None:arrays[key]=np.array(v[key],copy=True)
            for n,row in enumerate(trials):arrays[f'trial_{n:03d}']=row.pop('trial')
            saved=dict(scope='Actual first failing original full-size RCG block; no reduced scene or changed solver',
                source_exception=str(arg[1]),phase_call=phases,iteration=int(v['iteration']),iota=float(v['iota']),
                beta=float(v['beta']),slope=float(v['slope']),utility=float(v['metric']['utility']),
                checked_normalized_gradient=float(v['checked_gradient']),RCG_solver=v['spec'],actual_trials=trials,
                original_normalization_divisor=int(len(v['theta'])),initialization_or_model_or_budget_changed=False,
                full_six_scheme_execution_claimed=False,intercepted_before_any_substitute_update=True)
            raise CapturedBoundary()
        return trace

    widths=np.r_[np.ones(3)*scene.get('rotation_bs_half_width',scene.get('rotation_half_width',np.pi/2)),
                 np.ones(3)*scene.get('rotation_ris_half_width',scene.get('rotation_half_width',np.pi/2))]
    output.mkdir(parents=True)
    try:
        sys.settrace(trace)
        core.optimize(scene,-widths,widths,True)
    except CapturedBoundary:pass
    finally:sys.settrace(None)
    if not saved:raise RuntimeError('Original first scheme did not reach the declared failure; no failure certificate generated')
    after=implementation_fingerprint()
    if before!=after:raise RuntimeError('Active original numerical source changed')
    np.savez(output/'actual-failure-arrays.npz',**arrays)
    saved.update(input_fingerprint=fingerprint(config_path.read_bytes(),scenario_path.read_bytes()),
        implementation_fingerprint=before,source_unchanged=True,capture_source_sha256=sha(Path(__file__)),
        scenario_sha256=sha(scenario_path),config_sha256=sha(config_path),array_sha256=sha(output/'actual-failure-arrays.npz'),
        elapsed_seconds=time.perf_counter()-started,full_reproduction_pass=False)
    (output/'original-scenario.json').write_bytes(scenario_path.read_bytes())
    (output/'actual-failure.json').write_text(json.dumps(saved,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:saved[k] for k in ('phase_call','iteration','source_exception','beta','slope','checked_normalized_gradient','elapsed_seconds')}))
    return saved


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--scenario',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    capture(a.config,a.scenario,a.output_dir)
