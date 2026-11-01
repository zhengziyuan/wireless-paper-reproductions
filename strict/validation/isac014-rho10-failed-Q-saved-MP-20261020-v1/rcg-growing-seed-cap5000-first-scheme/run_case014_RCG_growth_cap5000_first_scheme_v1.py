"""Cold case014 first scheme: identical growth-seed math, only disclosed RCG/PGA safetycaps500->5000."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
from equivalent_runtime_case014_v1 import load_core
from passive_first_failure_v1 import PassiveFirstFailure
from passive_original_cap_prefix_v1 import PassiveCapBoundaryTrace as PassiveRCGSeedTrace

HERE=Path(__file__).resolve().parent

def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def put(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def run(config,scenario,output):
    if output.exists() or output.parent.exists():raise FileExistsError('Fresh exact task output directory required; never overwrite or repeat.')
    manifest_path=HERE/'SOURCE_MANIFEST_V1.json';manifest_bytes=manifest_path.read_bytes();manifest=json.loads(manifest_bytes)
    config_bytes=config.read_bytes();scenario_bytes=scenario.read_bytes()
    if sha_bytes(config_bytes)!=manifest['inputs']['config']['SHA256'] or sha_bytes(scenario_bytes)!=manifest['inputs']['scenario']['SHA256']:
        raise ValueError('Exact original case014 config/scenario bytes required.')
    config_data=json.loads(config_bytes);scene=json.loads(scenario_bytes)
    if len(config_data)!=28 or not all(scene.get(key)==value for key,value in config_data.items()):
        raise ValueError('All 28 original config members must be embedded unchanged in this saved scenario.')
    if scene['rho']!=10 or scene['noise']!=[0.001,0.001]:raise ValueError('Wrong original case014 physical scenario.')
    paths={relative:HERE/relative for relative in manifest['source_SHA256']}
    before={relative:sha_bytes(path.read_bytes()) for relative,path in paths.items()}
    if before!=manifest['source_SHA256']:raise ValueError('Prepared frozen source changed; require a newly reviewed variant.')
    before.update(manifest=sha_bytes(manifest_bytes),config=sha_bytes(config_bytes),scenario=sha_bytes(scenario_bytes))
    output.parent.mkdir(parents=True,exist_ok=False)
    with (output.parent/'original-config.json').open('xb') as stream:stream.write(config_bytes)
    with (output.parent/'original-scenario.json').open('xb') as stream:stream.write(scenario_bytes)
    observer=PassiveFirstFailure(output.parent);seed_observer=PassiveRCGSeedTrace(HERE/'sources/core_structured_case014_v1.py');started=time.perf_counter();result=None;host_errors=[];after=None;observation=None;execution_error=None
    try:
        core=load_core(observer)
        previous_core=sys.modules.get('core');sys.modules['core']=core
        try:
            specification=importlib.util.spec_from_file_location('exact_original_case014_six_scheme_runner',HERE/'sources/run_selected_first_scheme_case014_v1.py')
            runner=importlib.util.module_from_spec(specification);specification.loader.exec_module(runner)
        finally:
            if previous_core is None:sys.modules.pop('core',None)
            else:sys.modules['core']=previous_core
        # Same cold run_scenario function as case145 framework. No build_scenario,
        # warm start, captured W initialization, RNG or sampling call is made.
        runner.optimize=core.optimize;runner.evaluate=core.evaluate
        sys.settrace(seed_observer.trace)
        result=runner.run_scenario(scene)
    except Exception as error:
        execution_error={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
        host_errors.append({'stage':'uncaught_execution','type':type(error).__name__,'message':str(error)})
    finally:
        sys.settrace(None)
        try:seed_observer.finish(output.parent)
        except Exception as error:host_errors.append({'stage':'seed_observer_report','type':type(error).__name__,'message':str(error)})
        try:observation=observer.finish()
        except Exception as error:host_errors.append({'stage':'observer_report','type':type(error).__name__,'message':str(error)})
        try:
            after={relative:sha_bytes(path.read_bytes()) for relative,path in paths.items()}
            after.update(manifest=sha_bytes(manifest_path.read_bytes()),config=sha_bytes(config.read_bytes()),scenario=sha_bytes(scenario.read_bytes()))
            if before!=after:host_errors.append({'stage':'source_or_input_interval','message':'Before/after source/input identity failed; preserve all outputs.'})
        except Exception as error:host_errors.append({'stage':'source_or_input_interval','type':type(error).__name__,'message':str(error)})
    all_existing_checks=False
    if result is not None:
        checks=result['checks']
        all_existing_checks=list(checks)==['Rot-BS & Rot-RIS'] and len(checks)==1 and all(item.get('status')=='executed' and item.get('full_converged') is True and item.get('power_feasible') is True and item.get('rotation_feasible') is True for item in checks.values())
        result['mode']='only_original_first_RotBS_RotRIS_RCG_growth_cap5000_variant'
        result.update(scope='Cold original case014 first Rot-BS & Rot-RIS; previous explicit I/factored QCQP plus growth seed unchanged; only RCG/PGA unreported safetycaps500->5000, all other controls unchanged.',
            original_all28_config_members_unchanged=False,current_all28_explicit_configuration_members_embedded_exact=True,only_RCG_PGA_reconstruction_safety_caps_extended_from500_to5000=True,RCG_trial_seed_policy="Per RCG block initial1, then2*previous accepted alpha; an unreported line-search control choice, not author parameters",PGA_original_BB_clip_OR_stop_unchanged=True,original_controls={key:scene[key] for key in ('W_solver','RCG_solver','PGA_solver','AO_solver')},
            executed_source_binding=before,input_source_after=after,source_and_input_interval_unchanged=before==after,
            first_failure_observer=observation,host_errors=host_errors,elapsed_seconds=time.perf_counter()-started,
            existing_selected_scheme_checks_all_satisfied=all_existing_checks,
            original_QP_stationarity_record_definition='Original assembled binary64 Q/P diagnostic retained; these matrices do not supply the structured solve. Original source has no absolute residual pass cutoff.',
            independent_physics_dual_language_original_reference_or_full_paper_pass=False,
            variant_scope='Only same finite positive alpha, nonnegative mu, K<=M and padded original W. No jitter, eigenvalue clamp, rank threshold or fallback. RCG growth-seed policy unchanged; only RCG/PGA safetycaps500->5000. All gradients, stops, step rules, W/AO controls unchanged.')
        put(output,result)
    effective_exit=1 if host_errors or result is None else (0 if all_existing_checks else 2)
    closure={'schema':'ACTUAL_CASE014_COLD_FIRST_SCHEME_STRUCTURED_ARITHMETIC_EXECUTION_CLOSURE_V1','source_before':before,'source_after':after,
        'source_and_input_interval_unchanged':before==after,'host_errors':host_errors,'execution_error':execution_error,
        'complete_selected_scheme_result_saved':result is not None,'existing_selected_scheme_checks_all_satisfied':all_existing_checks,
        'effective_entry_exit_code':effective_exit,'independent_physics_dual_language_original_reference_or_full_paper_pass':False,
        'elapsed_seconds':time.perf_counter()-started,'new_scenario_or_MC':False,'original_failed_case014_outcomes_preserved':True}
    put(output.parent/'actual-source-input-and-result-closure.json',closure)
    print(json.dumps({'effective_entry_exit_code':effective_exit,'checks':None if result is None else result['checks'],'source_interval_unchanged':before==after,'host_errors':host_errors}),flush=True)
    return effective_exit

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);parser.add_argument('--scenario',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    arguments=parser.parse_args()
    raise SystemExit(run(arguments.config,arguments.scenario,arguments.output))
