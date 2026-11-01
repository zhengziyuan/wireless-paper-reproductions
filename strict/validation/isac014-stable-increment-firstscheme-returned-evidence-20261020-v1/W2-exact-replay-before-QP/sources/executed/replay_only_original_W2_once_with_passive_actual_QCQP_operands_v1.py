"""PREPARED: one original W2 call, actual passive QP coefficients; no campaign.
Requires a new explicit true root admission. No preparation-time import or science.
"""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,os,struct,sys,traceback
import numpy as np
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exact_array(a,b):
    return a.dtype==b.dtype and a.shape==b.shape and np.iscomplexobj(a)==np.iscomplexobj(b) and np.asarray(a.real).tobytes(order='F')==np.asarray(b.real).tobytes(order='F') and (not np.iscomplexobj(a) or np.asarray(a.imag).tobytes(order='F')==np.asarray(b.imag).tobytes(order='F'))
def exact_tree(a,b):
    if isinstance(b,dict):return isinstance(a,dict) and a.keys()==b.keys() and all(exact_tree(a[k],b[k]) for k in b)
    if isinstance(b,list):return isinstance(a,(list,tuple)) and len(a)==len(b) and all(exact_tree(x,y) for x,y in zip(a,b))
    if isinstance(b,bool):return isinstance(a,(bool,np.bool_)) and bool(a)==b
    if isinstance(b,int):return isinstance(a,(int,np.integer)) and not isinstance(a,(bool,np.bool_)) and int(a)==b
    if isinstance(b,float):return isinstance(a,(float,np.floating)) and struct.pack('>d',float(a))==struct.pack('>d',b)
    return type(a) is type(b) and a==b

def main():
    q=argparse.ArgumentParser();q.add_argument('--admission',type=Path,required=True);q.add_argument('--expected-admission-sha',required=True);q.add_argument('--output-dir',type=Path,required=True);a=q.parse_args()
    assert sha(a.admission)==a.expected_admission_sha
    admission=json.loads(a.admission.read_bytes());assert admission.get('root_admitted_once_original_W2_source_replay') is True
    manifest=HERE/'SOURCE_MANIFEST_EXACT_ACTUAL_PROVIDER_AND_INPUTS_V1.json';assert sha(manifest)==admission['source_manifest_SHA256']
    assert sha(Path(__file__))==admission['entry_SHA256'] and str(a.output_dir.resolve())==admission['unique_output_directory']
    assert not a.output_dir.exists();assert sys.gettrace() is None
    pins=json.loads(manifest.read_bytes())['files_SHA256'];paths={str(HERE/n):s for n,s in pins.items()};paths[str(manifest)]=sha(manifest);paths[str(a.admission.resolve())]=a.expected_admission_sha
    assert all(sha(Path(p))==s for p,s in paths.items());a.output_dir.mkdir()
    c=json.loads((HERE/'original-scenario.json').read_bytes());cfg=json.loads((HERE/'original-config.json').read_bytes());assert len(cfg)==28 and all(c[k]==x for k,x in cfg.items())
    assert c['W_solver']==dict(maximum_iterations=10000,relative_tolerance=1e-6,bisection_tolerance=1e-12)
    m=json.loads((HERE/'EXACT_ACTUAL_W2_SAVED_INPUT_MAPPING_AND_STOP_SCALARS_V1.json').read_bytes())['mapping'];expected=json.loads((HERE/'expected-original-W2-returned-status.json').read_bytes())
    with np.load(HERE/'actual-returned-inner-block-states.npz',allow_pickle=False) as z:
        old=z[m['old_W']].copy();theta=z[m['theta']].copy();r=z[m['r']].copy();wanted=z[m['expected_new_W']].copy();ptheta=z[m['previous_theta']].copy();pr=z[m['previous_r']].copy()
    assert exact_array(theta,ptheta) and exact_array(r,pr),'Source-proven unchanged theta/r across W2 must match actual saved bits'
    assert old.shape==(4,6) and old.dtype==np.complex128 and theta.shape==(36,) and theta.dtype==np.complex128 and r.shape==(6,) and r.dtype==np.float64 and m['fixed_iota']==60348785663.072914
    sys.path.insert(0,str(HERE/'runtime'))
    for name in ('equivalent_runtime_case014_v1','stable_metrics','structured_original_qcqp_candidate_v1','stable_rotation_increment_v1'):assert name not in sys.modules
    from equivalent_runtime_case014_v1 import load_core
    model=load_core(None);original=model.update_w;original_solver=model._structured_solve;original_evaluate=model.evaluate
    solver_code=original_solver.__globals__['solve_fixed_original_qcqp'].__code__;transmit_codes={x for x in solver_code.co_consts if isinstance(x,type(solver_code)) and x.co_name=='transmit'}
    # Runtime guards exclude any other algorithm or new initialization.
    def forbidden(*args,**kwargs):raise RuntimeError('Unexpected other algorithm/initialization; no permitted full trajectory')
    for name in ('initialize','update_theta','update_rotation','optimize'):setattr(model,name,forbidden)
    core=HERE/'runtime/sources/core_structured_case014_v1.py';tree=ast.parse(core.read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='update_w')
    solve_node=next(n for n in ast.walk(node) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='_structured_solve');capture_line=solve_node.end_lineno+1
    assert 'nu=structured_info' in core.read_text().splitlines()[capture_line-1]
    arrays={'actual_input__W':old.copy(),'actual_input__theta':theta.copy(),'actual_input__r':r.copy(),'actual_input__iota':np.array(m['fixed_iota'])};nulls={};snapshots=[];calls=[];error=None;returned=None;observer_errors=[];evaluate_calls=[];transmit_calls=[]
    def capture(prefix,value):
        if isinstance(value,dict):
            for k,x in value.items():capture(prefix+'__'+k,x)
        elif value is None:nulls[prefix]=None
        else:
            x=np.array(value,copy=True)
            if x.dtype.kind not in 'biufc':raise TypeError('Unexpected passive value '+prefix)
            arrays[prefix]=x
    def safe_capture(prefix,value):
        try:capture(prefix,value)
        except BaseException as exc:observer_errors.append(dict(stage='passive_copy',field=prefix,type=type(exc).__name__,message=str(exc)))
    def wrapped_evaluate(*args,**kwargs):
        value=original_evaluate(*args,**kwargs);index=len(evaluate_calls);evaluate_calls.append(index)
        if isinstance(value,dict):
            for key in ('utility','rate','nmse','sinr','pattern','iota'):
                if key in value:safe_capture('EVALUATE%05d__'%index+key,value[key])
        return value
    def wrapped_solver(*args,**kwargs):
        calls.append(len(calls));index=len(calls)-1
        for key,x in zip(('W_old','fc','mu','eta','lip','Ga','den','rho','power','bisection_tolerance'),args):safe_capture('QP%05d__arg__'%index+key,x)
        returned_solver=original_solver(*args,**kwargs)
        safe_capture('QP%05d__solution'%index,returned_solver[0]);safe_capture('QP%05d__info'%index,returned_solver[1])
        return returned_solver
    def tracer(frame,event,arg):
        if frame.f_code is solver_code:
            if event=='return' and arg is not None:
                for key in ('row','diagonal','projected_w','projected_ga','sigma2'):
                    if key in frame.f_locals:safe_capture('SOLVERACTUAL__'+key,frame.f_locals[key])
            return tracer
        if frame.f_code in transmit_codes:
            if event=='return':
                index=len(transmit_calls);transmit_calls.append(index);safe_capture('TRANSMIT%05d__nu'%index,frame.f_locals.get('nu'));safe_capture('TRANSMIT%05d__actual_return'%index,arg)
            return tracer
        if frame.f_code is not original.__code__:return None
        if event=='line' and frame.f_lineno==capture_line:
            try:
                local=frame.f_locals;index=int(local['_']);snapshots.append(index)
                for key in ('w','f','fc','fs','pd','norms','lip','den','y','signal','interference','total','mu','eta','q','p','z','pattern','ga','new'):
                    safe_capture('WITER%05d__'%index+key,local[key])
            except BaseException as exc:observer_errors.append(dict(stage='passive_locals',type=type(exc).__name__,message=str(exc)))
        return tracer
    model._structured_solve=wrapped_solver;model.evaluate=wrapped_evaluate
    try:
        sys.settrace(tracer);returned=original(old,theta,r,c,m['fixed_iota'])
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    finally:
        sys.settrace(None);model._structured_solve=original_solver;model.evaluate=original_evaluate
    if returned is not None:arrays['actual_return__W']=returned[0].copy()
    # Passive raw values first; no object arrays/pickle or extra model calls.
    np.savez_compressed(a.output_dir/'actual-original-W2-replay-and-passive-QCQP-operands.npz',**arrays)
    after={p:sha(Path(p)) for p in paths};closed=after==paths
    same_W=returned is not None and exact_array(returned[0],wanted);same_history=returned is not None and exact_tree(returned[1],expected)
    same_path=error is None and not observer_errors and closed and len(calls)==1 and snapshots==[0] and len(evaluate_calls)==2 and same_W and same_history
    report=dict(schema='actual-one-original-W2-source-replay-and-passive-coefficients-v1',source_before=paths,source_after=after,source_and_input_interval_closed=closed,actual_update_w_calls=1,actual_structured_QP_calls=len(calls),actual_original_evaluate_calls=len(evaluate_calls),actual_original_transmit_call_count=len(transmit_calls),actual_QP_snapshots=snapshots,complete_returned_W_IEEE_bits_match_history=same_W,complete_returned_status_and_all_numeric_IEEE_bits_match_history=same_history,same_original_W2_path_pass=same_path,original_error=error,observer_errors=observer_errors,observer_error_never_replaces_original_numeric_exception_or_return=True,passive_None_values=nulls,raw_operands_SHA256=sha(a.output_dir/'actual-original-W2-replay-and-passive-QCQP-operands.npz'),absolute_norm_W_delta_not_newly_evaluated=True,no_initialize_other_scheme_AO_RCG_PGA_MC_RNG_or_new_MP_calls=True,after_W2_MP_not_recomputed=True,independent_before_or_QP_MP_not_yet_executed=True,original_reference_or_joint_stationarity_or_full_paper_PASS=False)
    with (a.output_dir/'ACTUAL_ORIGINAL_W2_ONE_UPDATE_SOURCE_REPLAY_AND_PASSIVE_QCQP_CLOSURE_V1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
    return 0 if same_path else (1 if observer_errors or not closed else 2)
if __name__=='__main__':raise SystemExit(main())
