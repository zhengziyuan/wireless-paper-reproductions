"""All900 saved Fig6 cases: full-state math, all1000 draws and five schemes.

The original MA positions are never optimized again. Independent fixed-array
benchmark formulas are freshly evaluated in both batched and scalar forms on
all1000 original draws per case. Those are current verification calculations,
not recovered historical W/QT/KKT transcripts. Failed gates remain failures.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

from case_archive import pack,read_member
from source_reader import load,read,require,sha,source_paths


MISSING=dict(actual_complete_native900_available=False,all900_independent_dual_language_gates_passed=False,
    original_saved_FPA_each_step_W_QT_KKT_available=False,original_saved_coordinate_gradient_RAW_available=False,
    original_saved_intermediate1000_MC_history_available=False,old759_producer_time_RAW_SHA_receipts_recovered=False,
    original_author_random_records_or_MC_counts_recovered=False,original_figure_closeness_verified=False,
    full_paper_strict_reproduction_passed=False,complete_transitive_runtime_binary_provenance=False)
SCHEMES={'MA-MRT','MA-ZF','FPA-MRT','FPA-ZF','FPA-OPT'}
POWERS=[9,12,15,18,21,24,27,30,33]


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();temp=path.with_name(path.name+'.stage')
    for attempt in range(8):
        try:temp.write_bytes(raw);temp.replace(path);return
        except PermissionError:
            if attempt==7:raise
            time.sleep(.05*(attempt+1))


def error(error):return dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),failed_observation_preserved=True)


def runtime():
    result=dict(PID=os.getpid(),parent_PID=os.getppid(),python_version=sys.version,
        sys_executable=str(Path(sys.executable).resolve()),sys_executable_sha256=sha(Path(sys.executable)),
        optimize=sys.flags.optimize,dont_write_bytecode=sys.dont_write_bytecode,
        historical_producer_runtime_identity_claimed=False,complete_transitive_binary_BLAS_provenance=False)
    base=Path(getattr(sys,'_base_executable',sys.executable)).resolve()
    result.update(base_executable=str(base),base_executable_sha256=sha(base))
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        k.GetCurrentProcess.restype=wintypes.HANDLE
        k.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
        k.GetProcessTimes.restype=wintypes.BOOL
        times=[wintypes.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(t) for t in times)):raise ctypes.WinError(ctypes.get_last_error())
        result['actual_process_creation_filetime_utc']=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
        k.GetModuleFileNameW.argtypes=[wintypes.HMODULE,wintypes.LPWSTR,wintypes.DWORD];k.GetModuleFileNameW.restype=wintypes.DWORD
        buffer=ctypes.create_unicode_buffer(32768)
        if not k.GetModuleFileNameW(None,buffer,len(buffer)):raise ctypes.WinError(ctypes.get_last_error())
        actual=Path(buffer.value);result.update(actual_process_image=str(actual),actual_process_image_sha256=sha(actual))
    if 'numpy' in sys.modules:
        import numpy as np
        result.update(numpy_version=np.__version__,numpy_init=str(Path(np.__file__).resolve()),numpy_init_sha256=sha(Path(np.__file__)))
        import numpy._core._multiarray_umath as arithmetic
        result.update(numpy_arithmetic_extension=str(Path(arithmetic.__file__).resolve()),numpy_arithmetic_extension_sha256=sha(Path(arithmetic.__file__)))
    return result


def same_files(files,wanted):
    actual={};errors=[]
    for key,path in files.items():
        try:actual[key]=sha(path)
        except Exception as exc:actual[key]=None;errors.append(dict(path=str(path),type=type(exc).__name__,message=str(exc)))
    return actual,errors,not errors and actual==wanted


def execute(a):
    require(sys.dont_write_bytecode and not sys.flags.optimize,'Use -B without -O')
    repo=a.repo.resolve();out=a.output_dir.resolve();binding=a.binding_index.resolve()
    require(not out.exists() or a.resume,'Fresh output or explicit resume required')
    selected=read(binding);rows=selected['rows']
    require(len(rows)==900 and len({r['filename'] for r in rows})==900 and not selected['failures'],'Complete original900 selected inputs/results required')
    require(Counter(r['origin'] for r in rows)==Counter(fig6_old139_reused=139,fig6_old759_recovery=759,fig6_new_original_slot_retry=2),'Exact139+759+2 provenance')
    bank=Path(rows[0]['files']['config']['path']).parent
    require(out!=bank and not out.is_relative_to(bank),'Numerical bank is read-only')
    files={str(p):p for p in source_paths(repo)};files[str(binding)]=binding
    expected={str(p):sha(p) for p in files.values()}
    for path,spec in selected['files'].items():
        p=Path(path);require(p.is_file() and p.stat().st_size==spec['bytes'],'Selected original file unavailable/size differs')
        actual=sha(p);require(actual==spec['sha256'],'Original input/result/classification bytes differ')
        files[str(p)]=p;expected[str(p)]=actual
    for name in ('manifest.json','plan.json','run_config.json'):
        p=bank/name;files[str(p)]=p;expected[str(p)]=sha(p)
    before=expected.copy();source_signature={str(p):before[str(p)] for p in source_paths(repo)}
    cfgbytes=(bank/'run_config.json').read_bytes();cfg=json.loads(cfgbytes);manifest=read(bank/'manifest.json');plan=read(bank/'plan.json')
    require(sha(bank/'run_config.json')=='72bd6211cd90e238bfa34a25d4f8e56d29454b01c51aca32aa483488475a0d80','Original full configured controls required')
    c,original,independent,certificates,extension,terminal,proof,_=load(repo)
    c.config_contract(cfg,manifest,plan);c.population(rows)
    runtime_before=runtime();out.mkdir(parents=True,exist_ok=a.resume)
    epoch=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+str(os.getpid())
    write(out/('execution-start-'+epoch+'.json'),dict(scope=__doc__,actual_verifier_runtime=runtime_before,source_and_input_before=before,
        full900_inputs_bound_before_scientific_evaluation=True,source_scope_proofs=proof,all_original_MA_positions_reused=True,
        new_MA_position_optimizer_or_RNG_calls=0,independent_fixed_benchmark_recalculations_are_new=True,**MISSING))
    all_records=[];failed=[];started=time.perf_counter();fatal=None;deferred=None;cached=0;new=0
    try:
        for ordinal,row in enumerate(sorted(rows,key=lambda r:(r['case_index'],r['realization']))):
            stem=Path(row['filename']).stem;receipt_path=out/'receipts'/(stem+'.json')
            jp=Path(row['files']['job']['path']);rp=Path(row['files']['selected_raw']['path'])
            require(sha(jp)==row['files']['job']['sha256'] and sha(rp)==row['files']['selected_raw']['sha256'],'Current case input/RAW changed')
            if receipt_path.exists():
                require(a.resume,'Prior case receipt needs explicit resume')
                receipt=read(receipt_path);archive=out/'cases'/receipt['archive']['file']
                require(receipt['source_signature']==source_signature and receipt['input_fingerprint']==row['input_fingerprint'] and
                    receipt['original_RAW_sha256']==sha(rp) and receipt['original_input_sha256']==sha(jp) and sha(archive)==receipt['archive']['sha256'],
                    'Prior actual mathematical case cannot be reused under different source/input bytes')
                prior=json.loads(read_member(archive,'actual-case-math.json'))
                require(prior['case']==stem and prior['source_and_case_inputs_unchanged'] is True and receipt['passed']==prior['complete_saved_case_independent_math_passed'],
                    'Cached archive does not bind the actual case observation')
                cached+=1;record=dict(case=stem,passed=receipt['passed'],actual_new_math_in_this_epoch=False,receipt_sha256=sha(receipt_path),archive_sha256=receipt['archive']['sha256'])
                all_records.append(record)
                if not record['passed']:failed.append(dict(case=stem,retained_cached_failure=True))
                continue
            if shutil.disk_usage(out).free<16*1024**3:
                deferred='Target volume below16GiB before next complete case';break
            casepath=out/'active-cases'/stem
            require(not casepath.exists(),'Unclosed prior case retained; do not overwrite or silently rerun it')
            casepath.mkdir(parents=True)
            gates={};stages={};case_failures=[];case_before={str(jp):sha(jp),str(rp):sha(rp),**source_signature}
            write(out/'active-case.json',dict(case=stem,ordinal=ordinal,original_population=900,verifier_PID=os.getpid(),stage='raw-input-contract'))
            try:
                jobbytes=jp.read_bytes();job=json.loads(jobbytes);raw=read(rp)
                fingerprint=hashlib.sha256(b'strict-v1\0'+cfgbytes+b'\0'+jobbytes).hexdigest()
                require(fingerprint==row['input_fingerprint']==raw['input_fingerprint'],'Exact original input fingerprint')
                if row['origin']=='fig6_new_original_slot_retry':
                    done=read(Path(row['files']['origin_closed_receipt']['path']))
                    rr=next(r for r in done['records'] if r['figure']==6 and r['slot']==stem)
                    wanted=rr['current_implementation_fingerprint']
                else:wanted='b3b8134f4c9be5213dee91930e240792be509003a1b840848131e1f2621ee5ef'
                require(raw['implementation_fingerprint']==wanted,'Actual historical raw fingerprint differs')
                require((job['figure'],job['N'],job['M'],job['kappa'],job['A'])==(6,6,5,6,2) and job['power']==10**((POWERS[row['case_index']]-30)/10),'Exact original Fig6 full dimensions/power')
                require(job['point']==POWERS[row['case_index']] and type(job['realization']) is int and job['realization']==row['realization'],'Exact source labels')
                require(raw['job_metadata']=={key:job[key] for key in ('N','M','kappa','power','A','figure','point','realization')},'Entire raw scenario identity differs')
                require(set(raw['metrics']['schemes'])==SCHEMES and raw['checks']['nlos_samples']==1000 and raw['checks']['full_N']==6 and raw['checks']['full_M']==5,'Complete five-scheme/full1000 schema')
                require(all('instantaneous_MC_mean' not in raw['history'][mode] for mode in ('mrt','zf')),'No fabricated optional historical MC history')
                require(all(type(raw['metrics']['schemes'][name]['nonconverged_samples']) is int and raw['metrics']['schemes'][name]['nonconverged_samples']==0
                    for name in ('FPA-MRT','FPA-ZF','FPA-OPT')),'Stored original baseline convergence flags are incomplete')
                initial,_,_,_,noise,channel,_=independent.geometry_functions(job,cfg)
                tasks=[('complete_saved_state_extension',lambda:extension.complete_saved_state_audit(raw,job,cfg,independent,certificates,casepath/'full-state-observations')),
                    ('whole_original_history_math',lambda:original.history_audit(raw,job,cfg,independent)[0]),
                    ('whole_original_terminal1000_math',lambda:terminal(raw,job,cfg,independent,initial,noise,channel,'python',{},scalar_oracle=True)),
                    ('whole_original_coordinate_certificate_math',lambda:certificates.check_case(raw,job,cfg))]
                for name,task in tasks:
                    write(out/'active-case.json',dict(case=stem,ordinal=ordinal,original_population=900,verifier_PID=os.getpid(),stage=name))
                    try:
                        result=task()
                        if name=='whole_original_terminal1000_math':
                            schemes,values,scalar=result
                            stages[name]=dict(original_reader_reports=schemes,independent_all1000_values={k:v.tolist() for k,v in values.items()},
                                all1000_scalar_vs_batched_oracles_each_original_baseline=scalar,
                                independent_baseline_iterations_are_current_new_calculations=True,
                                recovered_historical_FPA_weights_or_internal_stops=False)
                            good=True
                        else:
                            stages[name]=result;good=result.get('complete_saved_state_extension_gates_passed',True)
                        gates[name]=bool(good)
                        if not good:case_failures.append(dict(stage=name,explicit_failed_gate=True))
                    except Exception as exc:
                        item=dict(stage=name,**error(exc));case_failures.append(item);stages[name]=dict(available=False,passed=False,failure=item);gates[name]=False
            except Exception as exc:case_failures.append(dict(stage='raw_input_contract',**error(exc)))
            case_after,identity_errors,unchanged=same_files({p:Path(p) for p in case_before},case_before)
            good=len(gates)==4 and all(gates.values()) and not case_failures and unchanged
            report=dict(case=stem,figure=6,case_index=row['case_index'],realization=row['realization'],origin=row['origin'],
                input_fingerprint=row['input_fingerprint'],original_input_sha256=row['files']['job']['sha256'],original_RAW_sha256=row['files']['selected_raw']['sha256'],
                old_RAW_SHA_observation_semantics=row['raw_SHA_observation_semantics'],source_signature=source_signature,
                gates=gates,stages=stages,failures=case_failures,source_and_case_inputs_unchanged=unchanged,
                actual_case_files_before=case_before,actual_case_files_after=case_after,identity_observation_errors=identity_errors,
                complete_saved_case_independent_math_passed=good,original_positions_reoptimized=False,**MISSING)
            c.fresh_json(casepath/'actual-case-math.json',report)
            for name,p in (('original-input.json',jp),('original-python-raw.json',rp),('original-run-config.json',bank/'run_config.json')):
                target=casepath/name;target.write_bytes(p.read_bytes());require(sha(target)==sha(p),'Exact evidence copy differs')
            archive=pack(casepath,out/'cases'/(stem+'.tar.gz'),out)
            receipt=dict(case=stem,passed=good,input_fingerprint=row['input_fingerprint'],original_input_sha256=sha(jp),original_RAW_sha256=sha(rp),
                source_signature=source_signature,actual_verifier_runtime=runtime_before,archive=archive,
                old_producer_records_or_source_modified=False,failure_count=len(case_failures),source_and_case_inputs_unchanged=unchanged)
            write(receipt_path,receipt);new+=1
            record=dict(case=stem,passed=good,actual_new_math_in_this_epoch=True,receipt_sha256=sha(receipt_path),archive_sha256=archive['sha256'])
            all_records.append(record)
            if not good:failed.append(dict(case=stem,failures=case_failures,identity_errors=identity_errors))
            progress=dict(expected_cases=900,closed_cases=len(all_records),passed_cases=sum(r['passed'] for r in all_records),failed_cases=len(failed),
                actual_new_cases_this_epoch=new,reused_closed_math_cases=cached,last_closed_case=stem,source_signature=source_signature,
                elapsed_seconds=time.perf_counter()-started,all900_mathematical_checks_passed=False,**MISSING)
            write(out/'progress.json',progress);print(json.dumps({k:v for k,v in progress.items() if k!='source_signature'}),flush=True)
    except BaseException as exc:fatal=error(exc);raise
    finally:
        after,identity_errors,unchanged=same_files(files,before)
        try:runtime_after=runtime();runtime_equal=runtime_before==runtime_after
        except Exception as exc:runtime_after=None;runtime_equal=False;identity_errors.append(error(exc))
        passed=len(all_records)==900 and all(r['passed'] for r in all_records) and unchanged and runtime_equal and fatal is None and deferred is None
        final=dict(scope=__doc__,expected_cases=900,closed_cases=len(all_records),passed_cases=sum(r['passed'] for r in all_records),failed_cases=len(failed),
            actual_new_cases_this_epoch=new,reused_closed_math_cases=cached,records=all_records,failures=failed,fatal_exception=fatal,deferred_reason=deferred,
            all900_mathematical_checks_passed=passed,all900_observations_complete=len(all_records)==900,
            source_and_input_before=before,source_and_input_after=after,source_input_runtime_interval_unchanged=unchanged and runtime_equal,
            actual_runtime_before=runtime_before,actual_runtime_after=runtime_after,identity_observation_errors=identity_errors,
            original_MA_position_optimizer_and_RNG_calls=0,independent_fixed_benchmark_recalculations_are_new=True,
            elapsed_seconds=time.perf_counter()-started,completed_UTC=datetime.now(timezone.utc).isoformat(),**MISSING)
        write(out/('completion-'+epoch+'.json'),final);write(out/'latest-completion.json',final)
    return 0 if final['all900_mathematical_checks_passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--binding-index',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--resume',action='store_true')
    raise SystemExit(execute(p.parse_args()))
