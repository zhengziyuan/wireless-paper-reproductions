"""Prepared saved-only MP reader for new Python ordinals2..5; never1 or6."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
import types

HERE=Path(__file__).resolve().parent

def need(value,message):
    if not value:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def put(path,value):
    with path.open('x',encoding='utf8',newline='\n')as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def same(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(same(a[k],b[k])for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(same(x,y)for x,y in zip(a,b))
    if isinstance(a,float):return a.hex()==b.hex()
    return a==b
def module(name,path):
    raw=Path(path).read_bytes();mod=types.ModuleType(name);mod.__file__=str(path)
    exec(compile(raw,str(path),'exec'),mod.__dict__);return mod

def gate_closed(plan,admission):
    """Only small truly closed metadata; no MP/NumPy import before this gate."""
    R=HERE.parent
    sys.path.insert(0,str(R/'ISAC-original439-closed-return-observer-v2-prepared-20261019'))
    from root_shared_controller_snapshot_v1 import read_snapshot
    snap=read_snapshot(plan['producer_journal']);j=snap['parsed_JSON']
    need(snap['SHA256']==admission['actual_closed_producer_journal_SHA256'],'Actual closed journal not admitted')
    need(j['natural_wait_completed'] is True and j['exact_original_handle_birth_and_exit_match'] is True,'Original held wait/identity not closed')
    need(j['all_watched_source_and_job_bytes_unchanged'] is True and not j['host_errors'],'Producer source/host interval not closed')
    need(type(j['actual_child_terminal_exit_code']) is int,'Unknown actual producer exit')
    identity=plan['producer_initial_identity']
    for role in ['owner','child']:
        need(j[role]['PID']==identity[role+'_PID'] and j[role]['creation_FILETIME']==identity[role+'_creation_FILETIME'],'Initial held identity changed')
    job=read(plan['production_job']);need(job['lane']=='python' and job['allowed_scheme_ordinals']==[2,3,4,5],'Wrong actual producer job')
    need(j['source_before']==j['source_after'],'Producer before/after mismatch')
    need(all(j['source_before'].get(p)==h for p,h in job['source_guard_pins'].items()),'Journal does not cover actual job sources')
    A=Path(plan['producer_output']);cp=A/'actual-source-input-five-scheme-closure.json'
    need(sha(cp)==admission['actual_closed_lane_source_receipt_SHA256'],'Closed lane receipt not admitted')
    closure=read(cp)
    need(closure['source_and_input_interval_closed'] is True and closure['source_before']==closure['source_after'],'Inner producer interval not closed')
    need(not closure['host_error'] and not closure['source_errors'],'Inner producer host/source failure')
    need(closure['first_completed_scheme_repeated'] is False and closure['new_channel_MC_RNG_calls']==0,'Wrong producer scope')
    original=read(plan['production_plan'])
    need(closure['source_before']==original['source_and_input_pins'],'Inner source pins mismatch')
    need([row['ordinal']for row in closure['rows']]==[2,3,4,5],'Missing or extra actual scheme closures')
    files=[Path(plan['producer_journal']),cp]
    cases=[]
    required={'full-result.json','actual-returned-inner-block-states.json','actual-returned-inner-block-states.npz',
        'effective-scheme-scene.json','actual-scheme-entry-closure.json'}
    for ordinal in [2,3,4,5]:
        folder=A/f'scheme-{ordinal:02d}';spec=admission['closed_new_scheme_inputs'][str(ordinal)]
        need(isinstance(spec,dict) and set(spec)==required,'Root must admit exactly the actual new scheme files')
        for name,digest in spec.items():
            need(isinstance(digest,str) and len(digest)==64 and sha(folder/name)==digest,'New actual input digest mismatch: '+name)
            files.append(folder/name)
        marker=A/f'closed-scheme-{ordinal:02d}.json';row=read(marker);entry=read(folder/'actual-scheme-entry-closure.json')
        need(same(row,entry) and same(row,closure['rows'][ordinal-2]),'Scheme closure lineage mismatch')
        need(row['ordinal']==ordinal and row['scheme']==plan['schemes'][str(ordinal)]['name'],'Wrong scheme identity')
        need(row['actual_entry_exit'] in (0,2) and not row['host_errors'] and row['result_saved'] is True,'Incomplete host/capture scheme closure')
        files.append(marker);cases.append((ordinal,folder,row))
    return j,closure,cases,files

def prepare_actual_states(plan,ordinal,folder,original):
    import numpy as np
    D=Path(plan['production_plan']).parent;cfg=read(D/'original-config.json');base=read(D/'original-scenario.json')
    need(sha(D/'original-config.json')==plan['actual_input_configuration_SHA256'] and sha(D/'original-scenario.json')==plan['actual_input_scene_SHA256'],'Wrong base28cfg/scene')
    need(len(cfg)==28 and all(same(base.get(k),v)for k,v in cfg.items()),'Original28 members not embedded')
    spec=plan['schemes'][str(ordinal)];name=spec['name'];bs,ris,with_ris=spec['flags']
    scene=read(folder/'effective-scheme-scene.json');expected=dict(base)
    if not with_ris:
        expected['br_gain_re']=[0.]*len(base['br_gain_re']);expected['br_gain_im']=[0.]*len(base['br_gain_im'])
    need(same(scene,expected),'Effective NoRIS/current physical scene changed')
    result=read(folder/'full-result.json');sm=read(folder/'actual-returned-inner-block-states.json')
    need(result['scheme_ordinal']==ordinal and list(result['checks'])==[name] and list(result['metrics'])==[name],'Extra or wrong result scheme')
    need(result['executed_scheme_flags']==dict(BS_rotation=bs,RIS_rotation=ris,RIS_present=with_ris),'Result flag mismatch')
    need(same(result['original_controls'],{k:cfg[k]for k in ('AO_solver','W_solver','RCG_solver','PGA_solver')}),'Control mismatch')
    need(not result['host_errors'] and sm['scheme']==name and sm['with_RIS'] is with_ris and not sm['capture_errors'],'Bad actual recording')
    ap=folder/'actual-returned-inner-block-states.npz';need(sha(ap)==sm['arrays_SHA256'],'Actual state NPZ binding failed')
    sequence=('update_w','update_theta','update_rotation') if with_ris else ('update_w','update_rotation')
    hist=result['history'].get(name);blocks=[] if hist is None else hist['blocks']
    if hist is not None:
        need(sm['all_completed_outer_blocks_have_applicable_saved_returns'] is True,'Incomplete saved returned scheme')
        need(len(sm['rows'])==len(blocks)*len(sequence),'Actual returned-state count mismatch')
    else:need(result['metrics'][name]['status']=='failed','Missing history without genuine stored failure')
    with np.load(ap,allow_pickle=False)as z:arrays={k:z[k].copy()for k in z.files}
    need(all(v.dtype.kind in 'fc' and np.all(np.isfinite(v))for v in arrays.values()),'Nonfinite or unsupported actual stored state')
    sys.path.insert(0,str(D/'python-runtime'))
    from equivalent_runtime_case014_v1 import load_core
    model=load_core(None);prepared=[];counts={};actual_iotas={}
    for i,row in enumerate(sm['rows']):
        need(row['scheme']==name and row['method']==sequence[i%len(sequence)] and row['call']==i//len(sequence)+1,'Actual source returned-order mismatch')
        need(row['original_result_tuple_object_preserved'] is True,'Observer did not preserve original tuple')
        call=row['call'];fixed=row['fixed_iota']
        if call in actual_iotas:need(float(fixed).hex()==float(actual_iotas[call]).hex(),'Actual AO fixediota changed between returns')
        actual_iotas[call]=fixed
        if hist is not None:need(float(fixed).hex()==float(blocks[call-1]['iota']).hex(),'Block iota mismatch')
        w,theta,r=[arrays[row['arrays'][k]]for k in ('W','theta','r')]
        need(w.shape==(4,6) and theta.shape==(36,) and r.shape==(6,),'Actual full saved state shape mismatch')
        need(w.dtype.kind=='c' and theta.dtype.kind=='c' and r.dtype.kind=='f','Actual complex/real state classes required')
        metric,gradient=model.evaluate(w,theta,r,scene,fixed,True)
        state=original.clean(dict(metric,w_re=w.real,w_im=w.imag,theta_re=theta.real,theta_im=theta.imag,rotation=r))
        prepared.append(dict(method=row['method'],call=call,state=state,w=w,theta=theta,r=r,
            fixed_iota=fixed,gradient=gradient[{'update_w':0,'update_theta':1,'update_rotation':2}[row['method']]],flags=row['actual_returned_flags']))
        counts[row['method']]=counts.get(row['method'],0)+1
    need(counts==sm['counts'],'Actual per-method counts mismatch')
    final_available=hist is not None
    if final_available:
        need(prepared and prepared[-1]['method']=='update_rotation','No actual final returned PGA state')
        last=prepared[-1];final=result['metrics'][name]
        for part,actual in [('w_re',last['w'].real),('w_im',last['w'].imag),('theta_re',last['theta'].real),('theta_im',last['theta'].imag),('rotation',last['r'])]:
            saved=np.asarray(final[part],dtype=np.float64)
            need(saved.shape==actual.shape and saved.tobytes()==np.asarray(actual,dtype=np.float64).tobytes(),'Final JSON/actual returned state IEEE64 mismatch: '+part)
        # Use actual complex NPZ arrays, never re+1j*im recombination.
        _,fg=model.evaluate(last['w'],last['theta'],last['r'],scene,float(final['iota']),True)
        prepared.append(dict(method='final_ownstate',call=1,state=final,w=last['w'],theta=last['theta'],r=last['r'],all_gradients=fg,flags=result['checks'][name]))
    width=np.r_[np.ones(3)*base.get('rotation_bs_half_width',base.get('rotation_half_width',np.pi/2))*bs,
        np.ones(3)*base.get('rotation_ris_half_width',base.get('rotation_half_width',np.pi/2))*ris]
    return prepared,scene,width,with_ris,result,final_available

def run(plan_path,admission_path,out):
    plan=read(plan_path);admission=read(admission_path)
    need(admission.get('root_admitted_only_closed_new_Python_ord2_5_saved_MP') is True,'False root admission')
    need(admission['plan_SHA256']==sha(plan_path),'Wrong admitted reader plan')
    need(out.resolve()==Path(plan['fresh_output_directory']).resolve()==Path(admission['output_directory']).resolve(),'Wrong fresh saved-MP output')
    need(not out.exists(),'Preserve existing/partial scientific output; no automatic retry')
    need(plan['allowed_new_ordinals']==[2,3,4,5] and plan['hard_forbidden_ordinals']==[1,6],'Forbidden old-result scope')
    need(all(sha(p)==h for p,h in plan['source_and_input_pins'].items()),'Reader/source immutable input mismatch')
    j,closure,cases,inputfiles=gate_closed(plan,admission)
    files=[Path(p)for p in plan['source_and_input_pins']]+[plan_path,admission_path]+inputfiles
    before={str(p):sha(p)for p in files}
    # The genuine closure/admission gate above precedes any MP/model import.
    old=module('frozen_original80fe_numerical_definitions_only',HERE/'original_executed_80fe_reader.py.source')
    engine=module('same_existing80fe_MP_loop',HERE/'existing_80fe_MP_loop_applicable_saved_states_v1.py')
    out.mkdir(parents=True,exist_ok=False);rows=[];hosterror=None;after=None;sourceerrors=[];started=time.perf_counter()
    try:
        for ordinal,folder,entry in cases:
            target=out/f'scheme-{ordinal:02d}';target.mkdir(exist_ok=False)
            prepared,scene,width,with_ris,result,hasfinal=prepare_actual_states(plan,ordinal,folder,old)
            old.put(target/'actual-new-only-binary64-fixed-input-evaluations.json',{'states':[{'method':x['method'],'call':x['call'],'state':x['state'],'actual_returned_flags':x['flags']}for x in prepared],
                'new_common_Python64_evaluation_at_actual_new_saved_inputs':True,'no_optimizer_MC_RNG_or_old_result_calls':True})
            if prepared:
                lanes,gap,cross=engine.check_saved_states(prepared,scene,width,with_ris,old)
                science=all(r['physical_pass'] and r['gradient_formula_check_pass']for lane in lanes.values()for r in lane)and cross
                pga=[r['call']for r in lanes['100']if r['method']=='update_rotation'and not r['block_gradient']['strict_gradient_pass']]
                rcg=[r['call']for r in lanes['100']if r['method']=='update_theta'and not r['block_gradient']['strict_gradient_pass']]
                final=lanes['100'][-1]['block_gradient'] if hasfinal else None
            else:lanes={};gap=None;cross=None;science=False;pga=[];rcg=[];final=None
            report={'schema':'actual-only-new-Python-scheme-applicable-returned-states-existing-MP80-MP100-v1',
                'ordinal':ordinal,'scheme':plan['schemes'][str(ordinal)]['name'],'actual_producer_scheme_entry':entry,
                'actual_returned_state_count':sum(x['method']!='final_ownstate'for x in prepared),'final_ownstate_available_and_checked':hasfinal,
                'existing_physics_feasibility_and_gradient_formula_scope_PASS':science,
                'precision_lanes':lanes,'MP80_MP100_maximum_absolute_difference':gap,'MP80_MP100_bound':'1e-35','crossprecision_pass':cross,
                'strict_own_PGA_failed_calls':pga,'strict_own_RCG_failed_calls':rcg if with_ris else None,
                'RCG_applicable':with_ris,'NoRIS_RCG_PASS_not_assigned':not with_ris,
                'final_joint_diagnostics':final,'W_author_absolute_stationarity_gate':None,
                'original_algorithm_full_stop':result['original_algorithm_full_stop'],
                'new_saved_scope_complete':hasfinal and science,'original_reference_dual_trajectory_or_fullpaper_PASS':False,
                'partial_actual_states_not_final_fabrication':not hasfinal,'no_automatic_retry':True}
            put(target/'ACTUAL_ONLY_NEW_APPLICABLE_SCHEME_SAVED_MP80_MP100_V1.json',report)
            rows.append({'ordinal':ordinal,'scheme':report['scheme'],'report':str(target/'ACTUAL_ONLY_NEW_APPLICABLE_SCHEME_SAVED_MP80_MP100_V1.json'),
                'report_SHA256':sha(target/'ACTUAL_ONLY_NEW_APPLICABLE_SCHEME_SAVED_MP80_MP100_V1.json'),
                'saved_scope_complete':report['new_saved_scope_complete'],'original_algorithm_full_stop':report['original_algorithm_full_stop'],
                'strict_own_RCG_failed_calls':report['strict_own_RCG_failed_calls'],'strict_own_PGA_failed_calls':pga})
    except BaseException as error:
        hosterror={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
    finally:
        try:after={str(p):sha(p)for p in files}
        except Exception as error:sourceerrors.append(repr(error))
        closed=before==after and not sourceerrors
        code=1 if hosterror or not closed else (0 if len(rows)==4 and all(r['saved_scope_complete']for r in rows) else 2)
        put(out/'ACTUAL_ONLY_NEW_PYTHON_ORD2_5_SAVED_MP_SOURCE_AND_GATE_SUMMARY_V1.json',{
            'schema':'actual-new-only-python-four-saved-MP-closed-source-scope-v1','rows':rows,'actual_entry_exit_code':code,
            'source_before':before,'source_after':after,'source_input_interval_closed':closed,'source_errors':sourceerrors,'host_error':hosterror,
            'producer_actual_terminal_exit':j['actual_child_terminal_exit_code'],'producer_natural_exactheld_sourceclosed':True,
            'forbidden_old_first_and_old_ordinal6_not_read_or_reaudited':True,'independent_scope_not_producer_host0':True,
            'elapsed_seconds':time.perf_counter()-started,'optimizer_MC_RNG_or_new_trial_calls':0,
            'full_six_dual_trajectory_original_reference_or_fullpaper_PASS':False})
    return code

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True)
    a.add_argument('--admission',type=Path,required=True);a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args();raise SystemExit(run(args.plan,args.admission,args.output_dir))
