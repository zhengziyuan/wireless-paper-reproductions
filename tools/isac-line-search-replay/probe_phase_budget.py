"""Probe the unreported RCG safety cap at the actual frozen full-size state.

This is a NEW fixed-W phase solve warm-started at the captured failed point,
with the original RCG initialization of its PR history. It is not continuation
of the original PR history or a full six-scheme case. Only the explicitly
unreported safety cap changes; physical inputs and all stopping/Armijo rules
are retained. Any failure is recorded with all actually tried vectors.
"""
import argparse
import copy
import json
from pathlib import Path
import sys
import time
import numpy as np
from equivalent_runtime import binding,load_core
from audit_failure import sha


def run(capture,output,cap):
    if output.exists():raise FileExistsError('Preserve prior budget diagnostics')
    before=binding();own_sha=sha(Path(__file__));model=load_core()
    meta=json.loads((capture/'actual-failure.json').read_bytes());original=json.loads((capture/'original-scenario.json').read_bytes())
    assert sha(capture/'actual-failure-arrays.npz')==meta['array_sha256']
    assert isinstance(cap,int) and cap>original['RCG_solver']['maximum_iterations']
    c=copy.deepcopy(original);c['RCG_solver']['maximum_iterations']=cap
    with np.load(capture/'actual-failure-arrays.npz',allow_pickle=False) as data:w,theta,r=data['w'].copy(),data['theta'].copy(),data['r'].copy()
    output.mkdir(parents=True);(output/'explicit-probe-configuration.json').write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8')
    trials=[];iteration=None;failure={};arrays={};code=model.update_theta.__code__
    lines=(Path(__file__).resolve().parents[2]/'strict/rotatable-isac/core.py').read_text().splitlines()
    armijo=next(n for n,line in enumerate(lines,1) if 'if value>=metric["utility"]+spec["armijo"]*alpha*slope:' in line)
    def trace(frame,event,arg):
        nonlocal iteration,trials,failure
        if frame.f_code is not code:return None
        values=frame.f_locals
        if event=='line' and frame.f_lineno==armijo:
            if iteration!=values['iteration']:iteration=values['iteration'];trials=[]
            trials.append(dict(alpha=float(values['alpha']),value=float(values['value']),trial=np.array(values['trial'],copy=True)))
        elif event=='exception' and isinstance(arg[1],RuntimeError):
            for key in ('w','theta','r','g','ambient','direction','oldg','oldd'):
                if values.get(key) is not None:arrays[key]=np.array(values[key],copy=True)
            for n,item in enumerate(trials):arrays[f'trial_{n:03d}']=item.pop('trial')
            failure=dict(error=str(arg[1]),iteration=int(values['iteration']),normalized_gradient=float(values['checked_gradient']),
                slope=float(values.get('slope',0.0)),utility=float(values['metric']['utility']),iota=float(values['iota']),actual_trials=trials)
        return trace
    started=time.perf_counter();history=None
    try:
        sys.settrace(trace);theta,history=model.update_theta(w,theta,r,c,meta['iota'])
    except RuntimeError as error:
        if not failure:failure=dict(error=str(error))
    finally:sys.settrace(None)
    if history is not None:
        metric,(_,ambient,_)=model.evaluate(w,theta,r,c,meta['iota'],True)
        arrays.update(w=w,theta=theta,r=r,ambient=ambient)
        (output/'actual-phase-history.json').write_text(json.dumps(history,indent=2)+'\n',encoding='utf-8')
    np.savez(output/'actual-probe-arrays.npz',**arrays)
    assert before==binding() and own_sha==sha(Path(__file__))
    report=dict(scope='New full M4/N36/K2/A66 fixed-W phase solve warm-started at actual failed point, PR history starts empty as in original solver',
        source_binding=before,probe_source_sha256=own_sha,captured_array_sha256=meta['array_sha256'],
        original_unreported_safety_cap=original['RCG_solver']['maximum_iterations'],selected_unreported_safety_cap=cap,
        original_stopping_tolerance=c['RCG_solver']['gradient_tolerance'],all_other_input_and_Armijo_controls_unchanged=True,
        previous_original_PR_history_continued=False,failure=failure or None,
        original_phase_stop_reached=bool(history and history['converged']),
        final_normalized_gradient=history['final_normalized_gradient_norm'] if history else failure.get('normalized_gradient'),
        iterations=history['iterations'] if history else failure.get('iteration'),elapsed_seconds=time.perf_counter()-started,
        independent_MP_or_full_cold_case_or_original_reference_or_paper_pass=False)
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--safety-cap',type=int,required=True);a=p.parse_args();run(a.capture,a.output_dir,a.safety_cap)
