"""Portable Windows native host; preparation is the default, never science PASS.

Exact selected source/input/job bytes close before and after one owned child.
Natural OS exit and stored internal numerical checks are separate requirements.
Post-Popen metadata failures cannot bypass the same child's natural wait.
No timeout, retry, global preference change, installation or network action.
"""
import argparse,copy,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from native_process_identity_v1 import identity,identity_from_process,exited_process_observation

def need(value,message):
    if not value:raise ValueError(message)
def digest(payload):return hashlib.sha256(payload).hexdigest()
def sha(path):return digest(Path(path).read_bytes())
def read(path):return json.loads(Path(path).read_bytes())
def fresh(path,value):
    payload=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode('utf8')
    with Path(path).open('xb') as stream:stream.write(payload)
    return digest(payload)
def pinned_bytes(path,watched,expected=None):
    """The hash is of these exact validated bytes, never a subsequent re-read."""
    path=str(Path(path).resolve());payload=Path(path).read_bytes();actual=digest(payload)
    if expected is not None:need(actual==expected,'Explicit selected input/source digest mismatch: '+path)
    if path in watched:need(watched[path]==actual,'Previously validated bytes changed: '+path)
    watched[path]=actual
    return payload
def pinned_json(path,watched,expected=None):return json.loads(pinned_bytes(path,watched,expected))
def pin(path,expected):return dict(path=str(Path(path).resolve()),sha256=expected)
def within(path,root):return Path(path).resolve().is_relative_to(Path(root).resolve())
def snapshot(watched):
    values={};errors={}
    for path in watched:
        try:values[path]=sha(path)
        except OSError as error:values[path]=None;errors[path]=type(error).__name__+': '+str(error)
    return values,errors

def validate_source_root(source_root):
    root=source_root.resolve();watched={};manifest=root/'NATIVE_SOURCE_MANIFEST_V1.json'
    value=pinned_json(manifest,watched)
    need(value['schema']=='portable-native-exact-scientific-and-transport-source-manifest-v1','Explicit staged native source root')
    for row in value['files']:
        path=(root/row['relative_path']).resolve()
        need(within(path,root) and path.is_file(),'Every relative source stays inside source root')
        pinned_bytes(path,watched,row['sha256'])
    for name in ('portable_native_entry_v1.m',Path(__file__).name,'native_process_identity_v1.py'):
        path=root/'adapter'/name;need(path.is_file(),'Complete adapter entry required');pinned_bytes(path,watched)
    return root,watched

def validate_controls(configuration,watched=None):
    cfg=pinned_json(configuration,{} if watched is None else watched);settings=cfg['tuned_not_reported']
    original=dict(qt_max_iterations=200,ao_max_iterations=200,rmo_max_iterations=100000,monte_carlo_realizations=1000,relative_tolerance=1e-4,gradient_tolerance=1e-6,solver_objective_tolerance=1e-5,solver_primal_relative_tolerance=1e-5,qt_bound_tolerance=1e-5,smoothing_initial=1,smoothing_final=.001,smoothing_max_repeats=50)
    need(all(settings[k]==value for k,value in original.items()),'Retain all original configured budgets/stops; no reduced defaults')
    return cfg

def resolve_pins(value,base,watched):
    if isinstance(value,list):return [resolve_pins(item,base,watched) for item in value]
    if not isinstance(value,dict):return value
    out={key:resolve_pins(item,base,watched) for key,item in value.items()}
    if 'path' in out and ('sha256' in out or 'SHA256' in out):
        raw=Path(out['path']);path=(base/raw).resolve() if not raw.is_absolute() else raw.resolve()
        pinned_bytes(path,watched,out.get('sha256',out.get('SHA256')));out['path']=str(path)
    return out

def prepare(args):
    need(sys.dont_write_bytecode and not sys.flags.optimize,'Use -B and enabled assertions')
    root,watched=validate_source_root(args.source_root);data=args.data_dir.resolve()
    need(not data.exists() and len(data.parts)>1 and not within(data,root) and not within(root,data),'Exclusive data directory disjoint from all source files')
    configuration=None;saved=None
    if args.mode=='full8':
        need(args.configuration is not None,'Explicit full configuration required');configuration=args.configuration.resolve();cfg=validate_controls(configuration,watched)
        need(all(key in cfg for key in ('reported','sweeps','multi_vs_single','source_version','final_publisher_conformance')),'Complete original single-case config schema')
    elif args.mode in ('saved-two-TS','reuse-A088'):
        need(args.saved_input_spec is not None,'Explicit saved input/proof specification required');specfile=args.saved_input_spec.resolve()
        saved=resolve_pins(pinned_json(specfile,watched),specfile.parent,watched)
        required=('ordinal','disposition','original_configuration','old_container','old_states','old_physics_reference','old_phase_reference','old_MC1000_proof','expected_reported_scene')
        need(all(key in saved for key in required),'Complete source-bound original saved-case schema')
        need(type(saved['ordinal']) is int and 0<=saved['ordinal']<183,'Original ordinal retained')
        if args.mode=='reuse-A088':
            need(saved['ordinal']==88 and saved['disposition']=='reuse-existing-corrected-native-A-exact-inputs' and 'existing_corrected_A_reuse' in saved,'Explicit exact A088 source reuse only')
            proof=saved['existing_corrected_A_reuse']['corrected_A_ownstate_mathematics_proof']
            original_A=pinned_json(proof['path'],watched,proof.get('sha256',proof.get('SHA256')))
            need(original_A['native_real_host_terminal_exit_code']==1 and original_A['native_host_natural0_or_full_pipeline_pass'] is False,'Original A host1 cannot become natural0')
        else:need(saved['ordinal']!=88 and saved['disposition']=='new-two-TS-required','A088 uses pure reuse, never a new optimizer')
        configuration=Path(saved['original_configuration']['path']);validate_controls(configuration,watched)
    cvx_root=args.cvx_root.resolve() if args.cvx_root else None
    prefs=args.cvx_preferences.resolve() if args.cvx_preferences else None;prefs_payload=None
    if args.mode in ('full8','saved-two-TS'):
        need(cvx_root is not None and (cvx_root/'cvx_startup.m').is_file() and prefs is not None and prefs.is_file(),'Provide already-installed CVX root and explicit configured prefs; never install/configure global CVX')
        pinned_bytes(cvx_root/'cvx_startup.m',watched)
    if prefs is not None:prefs_payload=pinned_bytes(prefs,watched)
    exe=args.matlab_executable.resolve() if args.matlab_executable else None
    if args.execute:need(exe is not None and exe.is_file(),'Explicit installed MATLAB executable required')
    data.mkdir(parents=True);(data/'prefs').mkdir();(data/'temp').mkdir()
    if prefs_payload is not None:
        localprefs=data/'prefs/cvx_prefs.mat'
        with localprefs.open('xb') as stream:stream.write(prefs_payload)
        watched[str(localprefs)]=digest(prefs_payload)
    job=dict(schema='portable-corrected-native-single-case-job-v1',mode=args.mode,source_root=str(root),data_dir=str(data),configuration=str(configuration) if configuration else None,cvx_root=str(cvx_root) if cvx_root else None,new_entry_does_not_upgrade_old_checkpoints=True,original_A_host1_preserved=True,dryrun_is_scientific_PASS=False)
    if saved is not None:
        keep=('schema','ordinal','disposition','original_configuration','old_container','old_states','old_physics_reference','old_phase_reference','old_MC1000_proof','expected_reported_scene','existing_corrected_A_reuse')
        native={key:copy.deepcopy(saved[key]) for key in keep if key in saved}
        native.update(schema='native-original183-saved-input-two-TS-job-v1',output_directory=str(data),source_pins=[pin(path,value) for path,value in watched.items()],prepared_mode='reuse-A088' if args.mode=='reuse-A088' else 'execute',portable_source_contract_distinct_from_original_host=True)
        nativepath=data/'native-saved-job.json';watched[str(nativepath)]=fresh(nativepath,native);job['native_saved_job_path']=str(nativepath)
    job['source_pins']=[pin(path,value) for path,value in watched.items()]
    jobpath=data/'portable-native-job.json';watched[str(jobpath)]=fresh(jobpath,job)
    quote=lambda value:str(value).replace('\\','/').replace("'","''")
    expression="addpath('"+quote(root/'adapter')+"','-begin');portable_native_entry_v1('"+quote(jobpath)+"')"
    command=[str(exe),'-batch',expression] if exe else None
    descriptor=dict(schema='portable-native-prepared-single-case-command-v2',prepared_only=not args.execute,mode=args.mode,source_root=str(root),data_dir=str(data),job=pin(jobpath,watched[str(jobpath)]),command=command,windows_host_scope=True,configuration_is_immutable_and_not_silently_reduced=True,validated_bytes_not_later_rehashes_are_watch_roots=True,only_explicit_selected_inputs_not_bank_scan=True,global_preferences_or_CVX_installation_modified=False,configured_CVX_prefs_contents_not_printed=True,actual_optimizer_MATLAB_MC_RNG_calls=0,scientific_or_paper_PASS=False)
    fresh(data/'PREPARED_PORTABLE_NATIVE_COMMAND_V2.json',descriptor)
    return root,data,command,watched

def run_owned_process(command,cwd,env,data,watched,role,lifecycle_observation=None):
    """After Popen returns, metadata cannot bypass the same handle's natural wait."""
    need(os.name=='nt','This lifecycle host is explicitly Windows-only; no cross-platform birth claim')
    need(command and all(isinstance(item,str) for item in command),'Concrete reviewed child command')
    before,before_errors=snapshot(watched)
    if before!=watched:
        fresh(data/'actual-prelaunch-input-source-job-refusal.json',dict(role=role,expected_validated_bytes=watched,actual_before=before,read_errors=before_errors,child_started=False,public_exit_code=1,scientific_or_paper_PASS=False))
        return 1
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    owner=identity(os.getpid());errors=[];start=None;end=None;code=None
    observation={} if lifecycle_observation is None else lifecycle_observation
    observation.update(role=role,owner=owner,metadata_errors=errors,child_started=False,natural_wait_completed=False,initial_birth_observed=False,no_kill_signal_timeout_retry_or_replacement=True)
    def retain_error(stage,error):
        errors.append(dict(stage=stage,error_type=type(error).__name__,message=str(error)))
    def receipt_without_abandoning_child(path,value,stage):
        try:fresh(path,value);return True
        except BaseException as error:retain_error(stage,error);return False
    # Opening streams/owner identity may fail before Popen; no child then exists.
    log=(data/'actual-owned-child-console.log').open('xb')
    try:
        child=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,startupinfo=startup)
        try:
            # Ownership starts immediately after this one Popen returns. Both
            # initial identity and start-receipt failures are metadata failures.
            observation.update(child_started=True,actual_child_PID=child.pid)
            try:
                start=identity_from_process(child);observation['initial_birth_observed']=True
            except BaseException as error:retain_error('post_Popen_initial_identity',error)
            observation['actual_child']=start
            receipt_without_abandoning_child(data/'actual-owned-child-start.json',dict(role=role,owner=owner,child=start,initial_birth_observed=start is not None,command=command,cwd=str(cwd),valid_OS_stdin_DEVNULL_stdout_file_stderr_STDOUT=True,source_and_selected_input_and_job_before=before,metadata_errors=errors),'post_Popen_start_receipt_write')
        except BaseException as error:
            retain_error('post_Popen_metadata_outer',error)
        finally:
            # Receipt failures and interruptions are never allowed to leave
            # this scope until this exact child naturally exits. No new Popen,
            # timeout, kill, terminate or signal is used in this loop.
            interruptions=0
            while True:
                try:
                    code=child.wait()
                    observation['natural_wait_completed']=True
                    observation['natural_wait_return_monotonic_ns']=time.monotonic_ns()
                    break
                except BaseException as error:
                    interruptions+=1
                    try:
                        retain_error('owned_wait_interruption',error)
                        name='actual-host-wait-interruption-retained.json' if interruptions==1 else 'actual-host-wait-interruption-retained-'+str(interruptions)+'.json'
                        receipt_without_abandoning_child(data/name,dict(error_type=type(error).__name__,error=str(error),interruption_index=interruptions,no_signal_timeout_restart_or_replacement_sent=True,same_original_Popen_handle_will_be_waited_again=True),'wait_interruption_receipt_write')
                    except BaseException as nested:
                        # Even an error while retaining a report cannot unwind
                        # ownership. Continue waiting the same original handle.
                        try:retain_error('wait_interruption_report_outer',nested)
                        except BaseException:pass
                    continue
            observation['wait_interruption_count']=interruptions
        # All remaining observations happen AFTER the natural wait. Failures
        # are retained and force nonzero; absent initial birth stays absent.
        try:end=exited_process_observation(child)
        except BaseException as error:retain_error('original_handle_terminal_observation',error)
        observation.update(actual_child_terminal=end,actual_natural_exit_code=code)
    finally:
        try:log.close()
        except BaseException as error:retain_error('owned_console_close_after_wait',error)
    after,after_errors=snapshot(watched)
    birth_available=start is not None and end is not None
    birth_match=birth_available and all(start[key]==end[key] for key in ('PID','creation_FILETIME'))
    valid=birth_match and end['actual_OS_exit_code']==code
    receipt=dict(role=role,owner=owner,actual_child=start,actual_child_terminal=end,actual_natural_exit_code=code,initial_birth_observed=start is not None,birth_comparison_available=birth_available,exact_original_handle_birth_and_exit_match=bool(valid),natural_wait_completed=observation['natural_wait_completed'],natural_wait_return_monotonic_ns=observation['natural_wait_return_monotonic_ns'],wait_interruption_count=observation['wait_interruption_count'],metadata_errors=errors,source_before=before,source_after=after,post_read_errors=after_errors,source_interval_pass=before==after,validated_source_selected_input_and_job_interval_pass=before==watched and after==watched,all_failed_and_partial_outputs_retained=True,original_A_host1_not_upgraded=True,lifecycle_or_IO_is_not_scientific_acceptance=True,scientific_or_paper_PASS=False)
    observation['terminal_receipt_in_memory']=receipt
    terminal_written=receipt_without_abandoning_child(data/'actual-owned-child-terminal.json',receipt,'post_wait_terminal_receipt_write')
    effective=code if valid and before==after and not errors and terminal_written else (code if code else 1)
    observation.update(terminal_receipt_written=terminal_written,effective_exit_code=effective)
    return effective

def one(value):
    if isinstance(value,list):need(len(value)==1,'Exactly one explicit base case');return value[0]
    need(isinstance(value,dict),'Expected recorded case object');return value

def inspect_recorded_result(mode,data,outputs):
    """Recorded internal gates only; no numerical replay or science certification."""
    names=('AP-NoRIS','AP-AO','MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS')
    filename='actual-native-IO-only-result.json' if mode=='io-only' else ('actual-native-complete-timed-result.json' if mode=='full8' else 'case-matlab-corrected-two-TS-recorded.json')
    path=data/filename;value=pinned_json(path,outputs)
    raw=Path(str(path)+'.full-result-before-JSON.mat');pinned_bytes(raw,outputs)
    need(raw.stat().st_size>0,'Retain nonempty raw MAT before JSON output')
    gates={};errors=[]
    def gate(label,condition):
        gates[label]=condition is True
        if not gates[label]:errors.append(label)
    if mode=='io-only':
        gate('explicit_non_scientific_IO_scope',value.get('scope')=='PURE_NATIVE_CODEC_AND_EXPLICIT_PATH_IO_ONLY')
        gate('no_scientific_algorithms_or_MC',value.get('actual_scientific_algorithms_executed')==0 and value.get('actual_new_MC_draws')==0 and value.get('scientific_PASS') is False)
        return gates,errors
    scopes=dict(full8='author_model_all_eight_algorithm_chains_full_dimensions_tuned_sweeps',**{'saved-two-TS':'Corrected two complete TS chains plus six explicit saved chains and old configured1000 moments','reuse-A088':'All eight states are saved-data reuse: six original native088 and two corrected nativeA with exact actual inputs and initialization'})
    gate('expected_recorded_scope',value.get('scope')==scopes[mode])
    gate('source_unchanged_during_run',value.get('source_unchanged_during_run') is True)
    gate('overall_implemented_scope_success',value.get('overall_implemented_scope_success') is True)
    checks=('constraint_pass','convergence_pass','solver_primal_pass','qt_bound_pass')
    for key in checks:gate('recorded_'+key,value.get('checks',{}).get(key) is True)
    point=one(value.get('results'));schemes=point.get('schemes')
    gate('exact_all8_recorded_scheme_order',isinstance(schemes,list) and [item.get('scheme') for item in schemes]==list(names))
    for key in checks:gate('single_case_'+key,point.get(key) is True)
    gate('single_case_valid_figure_point',point.get('valid_figure_point') is True)
    if isinstance(schemes,list):
        for index,scheme in enumerate(schemes):
            status=scheme.get('status',{});numeric=status.get('numerical',{})
            gate('scheme_'+str(index)+'_converged',status.get('converged') is True and status.get('phase_source_converged',True) is True)
            gate('scheme_'+str(index)+'_primal_and_QT_bound',numeric.get('solver_primal_pass') is True and numeric.get('qt_bound_pass') is True)
    state=value['state_recording'];statepath=(data/state['filename']).resolve()
    need(within(statepath,data),'Recorded state MAT must stay in owned data directory')
    pinned_bytes(statepath,outputs,state['sha256']);gate('all8_raw_final_states_recorded',state.get('final_scheme_states')==8)
    if mode=='full8':
        gate('full_configured_MC1000',value.get('configuration',{}).get('tuned_not_reported',{}).get('monte_carlo_realizations')==1000 and value.get('measured_pipeline_clocks',{}).get('configured_moment_draws')==1000)
    else:
        reuse=value.get('exact_reuse_provenance',{})
        gate('original_MC1000_explicit_reuse_without_draws',reuse.get('configured1000_moment_result_copied_without_new_draws') is True and value.get('actual_new_MC_draws')==0)
        if mode=='saved-two-TS':gate('only2_new_TS_and_no_unaffected_optimizer',value.get('actual_completed_TS_entries')==2 and value.get('actual_unaffected_optimizer_calls')==0)
        else:
            gate('A088_no_new_optimizer',value.get('actual_new_TS_optimizer_calls')==0)
            gate('A088_original_host1_retained',value.get('original_corrected_A_host_exit_code')==1 and value.get('original_corrected_A_host_terminal0_claimed') is False)
    return gates,errors

def finalize_public_host(mode,data,watched,child_effective_exit,host_error=None,lifecycle_observation=None):
    """Always retain terminal/result/summary; child OS0 alone never yields green."""
    failures=[];outputs={};terminal=None;gates={}
    try:terminal=pinned_json(data/'actual-owned-child-terminal.json',outputs)
    except (OSError,ValueError,TypeError,KeyError) as error:failures.append('actual_terminal_unavailable: '+type(error).__name__+': '+str(error))
    if lifecycle_observation is not None and lifecycle_observation.get('metadata_errors'):failures.append('owned_child_metadata_or_wait_errors_retained')
    if lifecycle_observation is not None and lifecycle_observation.get('child_started') and not lifecycle_observation.get('natural_wait_completed'):failures.append('same_child_natural_wait_not_completed')
    if child_effective_exit!=0:failures.append('owned_child_effective_exit_nonzero')
    if terminal is not None:
        for key in ('exact_original_handle_birth_and_exit_match','validated_source_selected_input_and_job_interval_pass'):
            if terminal.get(key) is not True:failures.append(key)
        if terminal.get('actual_natural_exit_code')!=0:failures.append('actual_natural_OS_exit_nonzero')
    try:
        gates,recorded_failures=inspect_recorded_result(mode,data,outputs);failures+=recorded_failures
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as error:failures.append('recorded_internal_gate_readback_error: '+type(error).__name__+': '+str(error))
    source_after,source_errors=snapshot(watched);output_after,output_errors=snapshot(outputs)
    if source_after!=watched:failures.append('validated_inputs_sources_and_jobs_changed_before_public_summary')
    if output_after!=outputs:failures.append('recorded_output_bytes_changed_during_readback')
    if host_error is not None:failures.append('host_exception_retained')
    public_exit=0 if not failures else (child_effective_exit if child_effective_exit else 1)
    if public_exit==0 and terminal is None:public_exit=1
    receipt=dict(schema='portable-native-public-host-natural-exit-and-recorded-internal-gate-summary-v3',mode=mode,actual_natural_OS_exit_code=(lifecycle_observation or {}).get('actual_natural_exit_code') if terminal is None else terminal.get('actual_natural_exit_code'),owned_child_effective_exit=child_effective_exit,public_host_exit_code=public_exit,public_host_internal_recorded_gate_pass=not failures,recorded_internal_checks=gates,failures=failures,host_error=host_error,in_memory_owned_child_lifecycle=lifecycle_observation,validated_inputs_source_and_jobs=watched,selected_input_source_job_bytes_closed_through_summary=source_after==watched,source_after=source_after,source_read_errors=source_errors,actual_output_bytes_read=outputs,output_after=output_after,output_read_errors=output_errors,all_raw_partial_failed_and_terminal_outputs_retained=True,original_A_host1_not_upgraded=True,recorded_internal_flags_are_not_independent_scientific_acceptance=True,scientific_physical_dual_reference_and_paper_PASS=False)
    fresh(data/'ACTUAL_PORTABLE_PUBLIC_HOST_SUMMARY_V3.json',receipt)
    return public_exit

def main(args):
    root,data,command,watched=prepare(args)
    if not args.execute:
        print(json.dumps(dict(prepared_only=True,job=str(data/'portable-native-job.json'),actual_MATLAB_optimizer_MC_RNG_calls=0,scientific_PASS=False)));return
    env=os.environ.copy();env.update(MATLAB_PREFDIR=str(data/'prefs'),TEMP=str(data/'temp'),TMP=str(data/'temp'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    host_error=None;lifecycle_observation={}
    try:effective=run_owned_process(command,root,env,data,watched,'actual-explicit-portable-native-'+args.mode,lifecycle_observation)
    except BaseException as error:
        effective=1;host_error=dict(type=type(error).__name__,message=str(error))
        try:fresh(data/'actual-public-host-exception-retained.json',dict(error=host_error,partial_outputs_retained=True,no_signal_timeout_restart_or_replacement_sent=True))
        except BaseException as report_error:host_error['exception_receipt_write_failure']=dict(type=type(report_error).__name__,message=str(report_error))
    raise SystemExit(finalize_public_host(args.mode,data,watched,effective,host_error,lifecycle_observation))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--mode',choices=('io-only','full8','saved-two-TS','reuse-A088'),required=True);parser.add_argument('--configuration',type=Path);parser.add_argument('--saved-input-spec',type=Path);parser.add_argument('--cvx-root',type=Path);parser.add_argument('--cvx-preferences',type=Path);parser.add_argument('--matlab-executable',type=Path);parser.add_argument('--execute',action='store_true');main(parser.parse_args())
