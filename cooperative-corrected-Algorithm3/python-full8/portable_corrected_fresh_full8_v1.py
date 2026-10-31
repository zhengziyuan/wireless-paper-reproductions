"""Portable corrected Algorithm3: one explicit fresh full8/MC1000 case.

--execute --full --sweep base are mandatory for the numerical action.
validate-import and inspect-configuration never call the scientific runner.
All source/reference/dual-language acceptance gates remain separate and pending.
"""
import argparse
import ast
import copy
from datetime import datetime
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys

NAMES=('AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS')
BASE_NAMES=('core','models','positive_wick','increments','increments_v2','algorithms','spectral_rmo','core_qt_factored_v3','qt_numerical_guard_v3','termination','scenario','run','receipts','run_cooperative_v3_configured')
FULL_CONTROLS = dict(monte_carlo_realizations=1000, qt_max_iterations=200,
                     ao_max_iterations=200, rmo_max_iterations=100000,
                     relative_tolerance=1e-4, gradient_tolerance=1e-6,
                     solver_objective_tolerance=1e-5,
                     solver_primal_relative_tolerance=1e-5,
                     qt_bound_tolerance=1e-5, smoothing_initial=1,
                     smoothing_final=0.001, smoothing_max_repeats=50,
                     smoothing_progress_tolerance=1e-8)

def need(test,message):
    if not test:raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fresh_json(path,value,default=None):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False,default=default)
        stream.write('\n')

def load_module(path,name):
    need(name not in sys.modules,'Fresh isolated module name required: '+name)
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def check_sources(source_root):
    source_root=Path(source_root).resolve(strict=True)
    expected_path=Path(__file__).with_name('expected_full8_source_pins_v1.json')
    expected=json.loads(expected_path.read_bytes())['source_sha256']
    manifest=source_root/'source-manifest.json'
    need(json.loads(manifest.read_bytes())['source_sha256']==expected,'Exact full8 source manifest required')
    before={}
    for relative,digest in expected.items():
        path=(source_root/relative).resolve(strict=True)
        need(path.is_relative_to(source_root),'Source escaped the explicit root')
        need(sha(path)==digest,'Frozen source differs: '+relative)
        before[str(path)]=digest
    for path in (Path(__file__),expected_path,manifest):before[str(path.resolve())]=sha(path)
    return source_root,before

def read_selected_configuration(path,data_dir):
    path=Path(path).resolve(strict=True);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    return dict(original_path=path,consumed_path=data_dir/'actual-consumed-configuration.json',raw=raw,configuration=None,
        before=dict(original=dict(path=str(path),SHA256=digest),consumed_copy=None))

def materialize_and_validate_configuration(inputs,expected_sha=None):
    raw=inputs['raw'];digest=hashlib.sha256(raw).hexdigest();snapshot=inputs['consumed_path']
    need(expected_sha is None or expected_sha==digest,'Explicit configuration SHA256 differs')
    with snapshot.open('xb') as stream:stream.write(raw)
    consumed=snapshot.read_bytes();need(consumed==raw,'Consumed configuration snapshot must preserve exact bytes')
    inputs['before']['consumed_copy']=dict(path=str(snapshot),SHA256=hashlib.sha256(consumed).hexdigest())
    configuration=json.loads(raw);inputs['configuration']=configuration;settings=configuration['tuned_not_reported']
    need(all(settings.get(k)==v for k,v in FULL_CONTROLS.items()),'Every original full budget/tolerance is required')
    need(settings['solver']=='CLARABEL' and isinstance(settings['solver_options'],dict),'Frozen configured solver/options required')
    need(settings['mr_QT_representation'].startswith('sqrt(scale*v)=sqrt(scale)*sqrt(v), exact positive fixed-coordinate constant'),'Original configured QT representation required')
    need(all(k in configuration for k in ('reported','sweeps','multi_vs_single','source_version','final_publisher_conformance')),'Complete explicit configuration required')
    for key in ('J','U','N','M'):need(type(configuration['reported'][key]) is int and configuration['reported'][key]>0,'Explicit complete dimensions required: '+key)
    return configuration

def input_closure(inputs):
    if inputs is None:return dict(required=False,interval_pass=True)
    after={};errors={}
    for role,path in (('original',inputs['original_path']),('consumed_copy',inputs['consumed_path'])):
        try:after[role]=dict(path=str(path),SHA256=sha(path))
        except BaseException as error:after[role]=None;errors[role]=dict(type=type(error).__name__,message=str(error))
    return dict(required=True,before=inputs['before'],after=after,errors=errors,
        interval_pass=not errors and all(inputs['before'].values()) and after==inputs['before'],one_logical_configuration_two_actual_byte_roles=True)

def source_closure(before):
    after={};errors={}
    for path in before:
        try:after[path]=sha(path)
        except BaseException as error:after[path]=None;errors[path]=dict(type=type(error).__name__,message=str(error))
    return dict(before=before,after=after,errors=errors,interval_pass=not errors and before==after)

def prepare_installation(source_root,data_dir,bindings,inputs):
    """Imports and hooks only. The frozen recorder invokes the installer once."""
    need(sys.dont_write_bytecode and not sys.flags.optimize,'Use python -B with assertions enabled')
    need(not any(name in sys.modules for name in BASE_NAMES),'A fresh process is required')
    base=source_root/'base';sys.path.insert(0,str(base))
    entry=importlib.import_module('run_cooperative_v3_configured')
    alg=importlib.import_module('algorithms')
    ordinary=importlib.import_module('qt_numerical_guard_v3')
    candidate=source_root/'correction/algorithms_final_algorithm3_v2.py'
    provider=load_module(source_root/'correction/final_algorithm3_p7_guard_v1.py','_portable_full8_corrected_preamble_guard_v1')
    recorder=load_module(source_root/'transport/record_python_case_explicit_root_v1.py','_portable_full8_frozen_recorder_v1')
    helpers=load_module(source_root/'transport/passive_original_QT_wrapper_clone_v1.py','_portable_full8_exact_QT_clone_v1')
    recorder._PORTABLE_EXPLICIT_BASE_ROOT=str(base)
    nodes=[node for node in ast.parse(candidate.read_bytes()).body if isinstance(node,ast.FunctionDef) and node.name=='mr_two_stage']
    need(len(nodes)==1,'Exactly one corrected Algorithm3 function required')
    original_installer=entry._install_original_v3_controls
    original_identity=entry.actual_hashes
    original_full_run=entry.original.full_run
    import numpy as np
    from scipy.io import savemat
    def save_fixture(kind, inputs):
        need(kind in ('mr', 'ap'), 'Known original QT fixture block required')
        keys = (('p0', 'signal', 'cross', 'power', 'leak', 'offset',
                 'power_limit', 'interference_limit') if kind == 'mr' else
                ('W0', 'mean', 'covariance', 'gt_second', 'offset',
                 'power_limit', 'interference_limit'))
        need(len(inputs) == len(keys), 'Complete unmodified QT fixture input required')
        digest = hashlib.sha256()
        fixture = {}
        for name, value in zip(keys, inputs):
            x = np.ascontiguousarray(value)
            digest.update(name.encode())
            digest.update(str(x.shape).encode())
            digest.update(x.dtype.str.encode())
            digest.update(x.tobytes())
            fixture[name] = value
        folder = data_dir / 'same-input-numerical-failure-fixtures'
        folder.mkdir(exist_ok=True)
        path = folder / ('v3-' + kind + '-QT-numerical-input-' + digest.hexdigest()[:16] + '.mat')
        sidecar = path.with_suffix('.json')
        if path.exists():
            existing = json.loads(sidecar.read_bytes())
            need(existing['input_sha256'] == digest.hexdigest()
                 and existing['sha256'] == sha(path), 'Preserve existing fixture identity')
        else:
            with path.open('xb') as handle:
                savemat(handle, fixture)
            fresh_json(sidecar, dict(input_sha256=digest.hexdigest(), sha256=sha(path)))
        return dict(filename=str(path.relative_to(data_dir)), sha256=sha(path),
                    input_sha256=digest.hexdigest())
    state=dict(installer_calls=0,full_run_attempts=0,full_run_returns=[],preamble_P7_events=[],tape=None,QT_clone_binding=None,installation_receipt=None)
    def installer():
        need(state['installer_calls']==0,'Exactly one original installer call per fresh full8 process')
        original_installer()
        baseline={name:value for name,value in vars(alg).items() if callable(value)}
        ordinary.save_fixture=save_fixture;provider.save_fixture=save_fixture
        alg._final_algorithm3_P7_update=provider.mr_qt_update
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(candidate),'exec'),alg.__dict__)
        untouched={name:vars(alg).get(name) is value for name,value in baseline.items() if name!='mr_two_stage'}
        need(all(untouched.values()),'Only mr_two_stage may replace an installed scientific callback')
        need(alg.rmo_ascent is entry.rmo_ascent and alg.ap_increment is entry.ap_increment_v2 and alg.mr_increment is entry.mr_increment_v2,'Preserve original spectral RMO and increments')
        need(alg.mr_qt_update is ordinary.mr_qt_update and alg.ap_qt_update is ordinary.ap_qt_update and alg._final_algorithm3_P7_update is provider.mr_qt_update,'Separate unchanged complete-loop and corrected-preamble QT providers required')
        state['installer_calls']+=1
        state['installation_receipt']=dict(original_v3_installer_calls=1,only_corrected_mr_two_stage_AST_injected=True,
            untouched_installed_callbacks=untouched,both_fixture_writers_explicit_data_dir=True,
            candidate_function_AST_SHA256=hashlib.sha256(ast.dump(nodes[0],include_attributes=False).encode()).hexdigest())
    entry._install_original_v3_controls=installer
    def identity(configuration):
        result=original_identity(configuration)
        result.update({'portable_bound_source:'+path:sha(path) for path in bindings})
        if inputs is not None:
            result.update({'portable_actual_configuration:'+role:sha(path) for role,path in (('selected_original',inputs['original_path']),('consumed_exact_copy',inputs['consumed_path']))})
        return result
    entry.actual_hashes=identity
    def last_hook_full_run(*args,**kwargs):
        # execute has already installed all original scenario/8state/phase/QT wrappers.
        need(state['installer_calls']==1 and state['full_run_attempts']==0,'Original recorder/install/full_run order required')
        captured,tape,binding=helpers.clone_frozen_QT_recording_wrapper(alg.mr_qt_update,provider.mr_qt_update)
        state['tape']=tape;state['QT_clone_binding']=binding
        def preamble_with_original_recording(*operands,**options):
            index=len(tape['QT_candidates']);value=captured(*operands,**options)
            need(len(tape['QT_candidates'])==index+1,'One passive original QT capture per preamble P7')
            state['preamble_P7_events'].append(dict(QT_candidate_index_zero_based=index,
                recorded_kind=tape['QT_candidates'][index]['kind'],replaced_only_provider_cell=True,
                arguments_and_return_unchanged=True))
            return value
        alg._final_algorithm3_P7_update=preamble_with_original_recording
        state['full_run_attempts']+=1
        result=original_full_run(*args,**kwargs)
        state['full_run_returns'].append(result)
        return result
    entry.original.full_run=last_hook_full_run
    loaded={name:str(Path(sys.modules[name].__file__).resolve()) for name in BASE_NAMES if name in sys.modules}
    need(all(Path(path)==(base/(name+'.py')).resolve() for name,path in loaded.items()),'Imported science outside explicit source-root')
    return dict(entry=entry,alg=alg,provider=provider,recorder=recorder,state=state,loaded_modules=loaded)

def preserve_outer_failure(installation,numerical_dir):
    """Save already returned values only; no numerical method is called here."""
    state=installation['state'];recorder=installation['recorder'];original=installation['entry'].original
    retained=[]
    tape=state['tape']
    if tape is not None and tape['input'] and not any((numerical_dir/name).exists() for name in ('actual-python-recording.mat','partial-actual-recording.mat')):
        numerical_dir.mkdir(exist_ok=True,parents=True)
        path=numerical_dir/'outer-preserved-incomplete-actual-recording.mat'
        recording={**tape,'final_states':recorder.cells(tape['final_states']),'phase_endpoints':recorder.cells(tape['phase_endpoints']),'QT_candidates':recorder.cells(tape['QT_candidates'])}
        recorder.savemat(path,dict(recording=recording),do_compression=True,long_field_names=True);retained.append(str(path))
    if state['full_run_returns'] and not (numerical_dir/'actual-result.json').exists():
        numerical_dir.mkdir(exist_ok=True,parents=True)
        path=numerical_dir/'outer-observed-unaltered-full-run-return.json'
        fresh_json(path,state['full_run_returns'][-1],default=original.numerical_json);retained.append(str(path))
    return retained

def package_versions():
    result={}
    for name in ('numpy','scipy','cvxpy','clarabel'):
        if name not in sys.modules:continue
        try:result[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:result[name]=dict(unavailable_reason=str(error))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('validate-import','inspect-configuration','full8-single-configuration'))
    parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--configuration',type=Path);parser.add_argument('--configuration-sha256')
    parser.add_argument('--execute',action='store_true');parser.add_argument('--full',action='store_true');parser.add_argument('--sweep',choices=('base',))
    args=parser.parse_args();is_run=args.action=='full8-single-configuration'
    need(args.execute==is_run,'--execute is required exclusively for the explicit full8 numerical action')
    need(not is_run or (args.full and args.sweep=='base'),'Explicit --full --sweep base required')
    need(args.action=='validate-import' or args.configuration is not None,'One explicit complete configuration is required')
    need(args.configuration_sha256 is None or args.configuration is not None,'SHA256 requires a selected configuration')
    source_root,before=check_sources(args.source_root)
    output=args.data_dir.resolve()
    need(not output.is_relative_to(source_root) and not output.is_relative_to(Path(__file__).resolve().parent),'Data must be outside source and adapter code roots')
    output.mkdir(parents=True,exist_ok=False)
    inputs=None;installation=None;failure=None;result=None;retained=[];internal=None;internal_pass=None;structure=None
    try:
        if args.configuration is not None:
            inputs=read_selected_configuration(args.configuration,output)
            materialize_and_validate_configuration(inputs,args.configuration_sha256)
            fresh_json(output/'actual-configuration-input-identity.json',dict(**inputs['before'],full_controls=FULL_CONTROLS,
                unmodified_configuration_semantics=inputs['configuration'],actual_new_MC_draws=0,optimizer_calls=0))
        if args.action!='inspect-configuration':
            installation=prepare_installation(source_root,output,before,inputs)
            if args.action=='validate-import':installation['entry']._install_original_v3_controls()
            else:
                # Frozen execute retains original.full_run(config,'base',None).
                result=installation['recorder'].execute(inputs['consumed_path'],output/'numerical-full8')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),code=getattr(error,'code',None),receipt=getattr(error,'receipt',None))
    if installation is not None:
        try:retained=preserve_outer_failure(installation,output/'numerical-full8')
        except BaseException as error:
            retained.append(dict(supplement_export_failure=dict(type=type(error).__name__,message=str(error))))
            if failure is None:failure=dict(type=type(error).__name__,message=str(error))
        state=installation['state'];tape=state['tape']
        if state['full_run_returns']:
            raw=state['full_run_returns'][-1];internal=raw.get('checks')
            internal_pass=bool(isinstance(internal,dict) and set(internal)=={'constraint_pass','convergence_pass','solver_primal_pass','qt_bound_pass'} and all(bool(v) for v in internal.values()) and raw.get('overall_implemented_scope_success'))
            structure=dict(one_original_full_run=state['full_run_attempts']==1,original_installer_calls_one=state['installer_calls']==1,
                all8_recorded_names=tape is not None and [x['scheme'] for x in tape['final_states']]==list(NAMES),
                two_additional_preamble_P7_captures=len(state['preamble_P7_events'])==2,
                scenario_configuration_equals_consumed_input=tape is not None and tape['input'].get('configuration')==inputs['configuration'],
                one_base_result_with_actual1000_moments=len(raw.get('results',[]))==1 and raw['results'][0].get('monte_carlo',{}).get('count')==1000)
    source=source_closure(before);actual_input=input_closure(inputs)
    exit_code=(2 if not source['interval_pass'] or not actual_input['interval_pass'] else
        1 if is_run and (failure is not None or not internal_pass or not structure or not all(structure.values())) else
        2 if failure is not None else 0)
    state=installation['state'] if installation is not None else None
    summary=dict(action=args.action,source_interval=source,actual_input_interval=actual_input,
        internal_checks=internal,all_internal_checks_pass=internal_pass,passive_structure_checks=structure,
        original_installer_receipt=state['installation_receipt'] if state is not None else None,
        loaded_scientific_modules=installation['loaded_modules'] if installation is not None else {},
        preamble_P7_capture_events=state['preamble_P7_events'] if state is not None else [],
        original_QT_wrapper_clone_binding=state['QT_clone_binding'] if state is not None else None,
        actual_new_full_run_attempts=state['full_run_attempts'] if state is not None else 0,
        original_recorder_summary=result,retained_failure_supplements=retained,failure_retained=failure,CLI_exit_code=exit_code,
        independent_physics_convergence_QT_phase_domain_MC_or_dual_reference_PASS=False,
        first_true_numerical_use_independent_review_pending=True,full183_Fig12_Fig13_or_allpapers_PASS=False,
        observed_local=datetime.now().astimezone().isoformat(),process_PID=os.getpid(),python_executable=sys.executable,
        package_versions=package_versions())
    if not is_run:summary.update(actual_optimizer_calls=0,actual_new_MC_draws=0,control_only_not_scientific_acceptance=True)
    default=installation['entry'].original.numerical_json if installation is not None else None
    fresh_json(output/'action-summary.json',summary,default=default)
    print(json.dumps(dict(action=args.action,CLI_exit_code=exit_code,source_interval_pass=source['interval_pass'],input_interval_pass=actual_input['interval_pass'],internal_checks_pass=internal_pass,independent_scientific_PASS=False)),flush=True)
    return exit_code

if __name__=='__main__':raise SystemExit(main())
