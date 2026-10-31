"""Only case014 unresolved four cold schemes; reuse closed original fixed NoRIS baseline."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
SCHEMES=[('Rot-BS & Fix-RIS',True,False,True),('Fix-BS & Rot-RIS',False,True,True),
    ('Fix-BS & Fix-RIS',False,False,True),('Rot-BS & No-RIS',True,False,False)]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(path,value):
    with path.open('x',encoding='utf8',newline='\n') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def need(v,m):
    if not v:raise ValueError(m)

def one(ordinal,selection,c,scene,out):
    import numpy as np
    from equivalent_runtime_case014_v1 import load_core
    from passive_first_failure_v1 import PassiveFirstFailure
    from passive_original_cap_prefix_v1 import PassiveCapBoundaryTrace
    from passive_remaining_block_states_v1 import PassiveRemainingBlockStates
    out.mkdir(parents=True,exist_ok=False)
    name,bs,ris,with_ris=selection
    failure=PassiveFirstFailure(out);states=PassiveRemainingBlockStates(out,name,with_ris)
    seeds=PassiveCapBoundaryTrace(HERE/'python-runtime/sources/core_structured_case014_v1.py')
    started=time.perf_counter();result=None;errors=[];observed=None;recording=None
    try:
        core=load_core(failure)
        for method in ('update_w','update_theta','update_rotation'):
            setattr(core,method,states.wrap(method,getattr(core,method)))
        previous=sys.modules.get('core');sys.modules['core']=core
        try:
            spec=importlib.util.spec_from_file_location('actual_only_remaining_case014_scheme',HERE/'python-runtime/sources/run_single_remaining_scheme_case014_v1.py')
            runner=importlib.util.module_from_spec(spec);runner.SELECTED_SINGLE_SCHEME=[selection]
            spec.loader.exec_module(runner)
        finally:
            if previous is None:sys.modules.pop('core',None)
            else:sys.modules['core']=previous
        runner.optimize=core.optimize;runner.evaluate=core.evaluate
        sys.settrace(seeds.trace)
        result=runner.run_scenario(scene)
    except Exception as error:
        errors.append({'stage':'uncaught_host_or_execution','type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
    finally:
        sys.settrace(None)
        for stage,call in [('returned_state_capture',lambda:states.finish(result)),('seed_capture',lambda:seeds.finish(out)),('failure_capture',failure.finish)]:
            try:
                value=call()
                if stage=='returned_state_capture':
                    recording=value
                    if value['capture_errors'] or value['all_completed_outer_blocks_have_applicable_saved_returns'] is False:
                        errors.append({'stage':stage,'message':'Capture incomplete; original result retained.'})
                if stage=='failure_capture':
                    observed=value
                    if value['observer_errors']:errors.append({'stage':stage,'message':'Observer error retained.'})
            except Exception as error:errors.append({'stage':stage,'type':type(error).__name__,'message':str(error)})
    algorithm_pass=False;strict_rcg=None;strict_pga=None
    if result is not None:
        need(list(result['checks'])==[name],'Unexpected first or extra scheme')
        check=result['checks'][name];hist=result['history'].get(name)
        algorithm_pass=bool(check.get('status')=='executed' and check.get('full_converged') is True)
        if hist is not None:
            if with_ris:strict_rcg=all(b['RIS']['final_normalized_gradient_norm']<=c['RCG_solver']['gradient_tolerance'] for b in hist['blocks'])
            strict_pga=all(b['rotation']['final_projected_gradient_norm']<=c['PGA_solver']['gradient_tolerance'] for b in hist['blocks'])
        effective_scene=dict(scene)
        if not with_ris:
            effective_scene['br_gain_re']=[0.]*len(scene['br_gain_re']);effective_scene['br_gain_im']=[0.]*len(scene['br_gain_im'])
        put(out/'effective-scheme-scene.json',effective_scene)
        result.update(mode='only_case014_remaining_single_scheme_current_stable_arithmetic',scheme_ordinal=ordinal,
            executed_scheme_flags={'BS_rotation':bs,'RIS_rotation':ris,'RIS_present':with_ris},
            passive_returned_inner_block_states=recording,passive_first_failure=observed,
            original_controls={k:c[k] for k in ('AO_solver','W_solver','RCG_solver','PGA_solver')},
            original_algorithm_full_stop=algorithm_pass,strict_RCG_returned_blocks_pass=strict_rcg,
            strict_PGA_returned_blocks_pass=strict_pga,RCG_gate_applicable=with_ris,
            independent_physics_feasibility_MP_PASS=None,final_joint_stationarity_PASS=None,
            W_author_absolute_stationarity_gate=None,original_reference_or_full_paper_PASS=False,
            host_errors=errors,elapsed_seconds=time.perf_counter()-started)
        put(out/'full-result.json',result)
    code=1 if errors or result is None else (0 if algorithm_pass else 2)
    receipt={'schema':'actual-one-of-five-case014-cold-stable-scheme-closure-v1','ordinal':ordinal,'scheme':name,
        'algorithm_full_stop':algorithm_pass,'actual_entry_exit':code,'strict_own_RCG':strict_rcg,'strict_own_PGA':strict_pga,
        'host_errors':errors,'result_saved':result is not None,'no_MC_RNG_or_first_scheme_call':True,
        'independent_physics_and_final_joint_pending':True,'no_automatic_retry':True}
    put(out/'actual-scheme-entry-closure.json',receipt)
    return receipt

def run(plan_path,admission_path,out):
    plan=json.loads(plan_path.read_bytes());admit=json.loads(admission_path.read_bytes())
    need(admit.get('root_admitted_only_case014_remaining_five_stable_schemes') is True,'False admission')
    need(admit['plan_SHA256']==sha(plan_path),'Plan admission mismatch')
    need(admit.get('root_admitted_existing_python_FixBS_NoRIS_baseline_reuse') is True,'Old verified baseline reuse must be explicitly admitted')
    need(admit['allowed_scheme_ordinals_by_lane']['python']==[2,3,4,5],'Wrong missing-only Python scope')
    need(str(out.resolve()) in [str(Path(p).resolve()) for p in admit['allowed_output_directories']],'Output not admitted')
    need(out.resolve()==Path(plan['lanes']['python']['fresh_output_directory']).resolve(),'Wrong lane output')
    need(not out.exists(),'Preserve prior/partial output; no automatic retry')
    pins=plan['source_and_input_pins'];before={p:sha(p) for p in pins}
    need(before==pins,'Frozen sources/inputs changed')
    cfg=json.loads((HERE/'original-config.json').read_bytes());scene=json.loads((HERE/'original-scenario.json').read_bytes())
    need(len(cfg)==28 and all(scene.get(k)==v for k,v in cfg.items()),'All28 controls must match scene')
    need(sha(HERE/'original-config.json')==plan['complete_configuration_SHA256'] and sha(HERE/'original-scenario.json')==plan['original_scene_SHA256'],'Wrong case014 inputs')
    sys.path.insert(0,str(HERE/'python-runtime'));sys.path.insert(0,str(HERE))
    out.mkdir(parents=True,exist_ok=False);rows=[];error=None;after=None;source_errors=[]
    try:
        for ordinal,selection in enumerate(SCHEMES,2):
            row=one(ordinal,selection,cfg,scene,out/f'scheme-{ordinal:02d}');rows.append(row)
            put(out/f'closed-scheme-{ordinal:02d}.json',row)
            if row['actual_entry_exit']==1:raise RuntimeError('Host/capture error retained; stop remaining lane')
    except Exception as exc:error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    finally:
        try:after={p:sha(p) for p in pins}
        except Exception as exc:source_errors.append(repr(exc))
        sourceclosed=before==after and not source_errors
        code=1 if error or not sourceclosed else (0 if len(rows)==4 and all(r['actual_entry_exit']==0 for r in rows) else 2)
        put(out/'actual-source-input-five-scheme-closure.json',{'schema':'actual-remaining-five-only-case014-lane-source-closure-v1',
            'source_before':before,'source_after':after,'source_and_input_interval_closed':sourceclosed,
            'source_errors':source_errors,'host_error':error,'rows':rows,'effective_entry_exit_code':code,
            'first_completed_scheme_repeated':False,'new_channel_MC_RNG_calls':0,
            'algorithm_stops_not_independent_physics_or_final_joint_PASS':True,
            'old_python_baseline_reuse':json.loads((HERE/'SOURCE_BOUND_EXISTING_PYTHON_FIXBS_NORIS_BASELINE_REUSE_V1.json').read_bytes())})
    return code

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True)
    a.add_argument('--admission',type=Path,required=True);a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args();raise SystemExit(run(args.plan,args.admission,args.output_dir))
