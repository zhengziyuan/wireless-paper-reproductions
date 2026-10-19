"""All900 native saved-state checks, reusing exact-input baseline references.

Wait only on recorded process identities and original closed-prefix progress.
Each native case keeps a distinct physical audit; the actual first-case audit
may be reused after complete content/source checks. No optimizer is launched.
"""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime,timezone
import json
from pathlib import Path
import time

from audit_native_case import audit
from audit_population import write,MISSING
from case_archive import read_member
from source_reader import read,require,sha,source_paths


def alive(pid,birth):
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    h=k.OpenProcess(0x1000,False,pid)
    if not h:
        code=ctypes.get_last_error()
        if code==87:return False
        raise ctypes.WinError(code)
    k.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)];k.GetProcessTimes.restype=wintypes.BOOL
    k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];k.GetExitCodeProcess.restype=wintypes.BOOL
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    try:
        ts=[wintypes.FILETIME() for _ in range(4)];exitcode=wintypes.DWORD()
        if not k.GetProcessTimes(h,*(ctypes.byref(t) for t in ts)) or not k.GetExitCodeProcess(h,ctypes.byref(exitcode)):raise ctypes.WinError(ctypes.get_last_error())
        return ((ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime)==birth and exitcode.value==259
    finally:k.CloseHandle(h)


def follow(a):
    out=a.output_dir.resolve();require(not out.exists(),'Fresh follower directory required')
    bank=a.input_bank.resolve();native=a.native_bank.resolve();python=a.python_math_dir.resolve();repo=a.repo.resolve()
    manifest=read(bank/'manifest.json');rows=sorted(manifest['files'],key=lambda r:(r['case_index'],r['realization']))
    require(len(rows)==manifest['expected_jobs']==900 and len({r['filename'] for r in rows})==900,'All original900 native slots required')
    before_files=source_paths(repo)+[Path(__file__),Path(__file__).with_name('audit_native_case.py'),bank/'run_config.json',bank/'manifest.json']
    before={str(p):sha(p) for p in before_files};out.mkdir(parents=True);records=[];started=time.perf_counter();terminal=None
    write(out/'execution-start.json',dict(scope=__doc__,native_PID=a.native_pid,native_creation_filetime_utc=a.native_birth,
        Python_math_PID=a.python_pid,Python_math_creation_filetime_utc=a.python_birth,source_and_metadata_before=before,
        expected_cases=900,original_scientific_entry_or_parameters_changed=False,all900_success_claimed=False,**MISSING))
    def progress(status,waiting=None):
        return dict(expected_cases=900,checked_cases=len(records),passed_cases=sum(r['passed'] for r in records),failed_or_unverified_cases=sum(not r['passed'] for r in records),
            status=status,waiting_for_case=waiting,elapsed_seconds=time.perf_counter()-started,
            all900_independent_native_saved_math_pass=False,records=records,**MISSING)
    for ordinal,row in enumerate(rows):
        stem=Path(row['filename']).stem;nr=native/(stem+'-matlab.json');pr=python/'receipts'/(stem+'.json')
        while True:
            p=read(native/'execution-progress.json');count=p['attempted']
            require(type(count) is int and 0<=count<=900 and p['expected_jobs']==900,'Actual native complete-prefix metadata differs')
            if count:
                require(p['current_job']==Path(rows[count-1]['filename']).stem,'Native completed prefix order differs from full manifest')
            if count>ordinal and nr.exists() and pr.exists():break
            if count<=ordinal and not alive(a.native_pid,a.native_birth):terminal='native process terminal before the required original slot';break
            if not pr.exists() and not alive(a.python_pid,a.python_birth):terminal='independent Python reference process terminal before the required complete fixed-array cache';break
            write(out/'progress.json',progress('waiting_on_birth_verified_original_workers',stem));time.sleep(5)
        if terminal:break
        try:
            if ordinal==0:
                receipt=read(a.first_native_audit/'receipt.json');archive=a.first_native_audit/'cases'/receipt['archive']['file']
                require(receipt['passed'] and receipt['input_fingerprint']==row['input_fingerprint'] and receipt['original_native_raw_sha256']==sha(nr)
                    and sha(archive)==receipt['archive']['sha256'],'Actual closed native first-case observation differs')
                detail=json.loads(read_member(archive,'actual-native-case-math.json'))
                require(detail['complete_native_case_independent_math_passed'] and detail['source_and_case_inputs_unchanged'],'Closed first native mathematics required')
                for path in source_paths(repo)+[Path(__file__).with_name('audit_native_case.py')]:
                    require(detail['actual_source_and_inputs_before'][str(path)]==sha(path),'Native first-case math source changed')
                record=dict(case=stem,passed=True,reused_actual_closed_native_math=True,actual_receipt=str(a.first_native_audit/'receipt.json'),
                    receipt_sha256=sha(a.first_native_audit/'receipt.json'),archive_sha256=receipt['archive']['sha256'])
            else:
                target=out/'case-audits'/stem
                receipt=audit(nr,pr,python,bank/'jobs'/row['filename'],bank/'run_config.json',target,repo)
                record=dict(case=stem,passed=receipt['passed'],reused_actual_closed_native_math=False,actual_receipt=str(target/'receipt.json'),
                    receipt_sha256=sha(target/'receipt.json'),archive_sha256=receipt['archive']['sha256'])
        except Exception as exc:
            record=dict(case=stem,passed=False,error_type=type(exc).__name__,error=str(exc),original_failure_or_unavailable_reference_retained=True)
            write(out/'retained-failures'/(stem+'.json'),record)
        records.append(record);write(out/'progress.json',progress('running'))
        print(json.dumps(dict(checked_cases=len(records),passed_cases=sum(r['passed'] for r in records),case=stem,passed=record['passed'])),flush=True)
    # A complete native child prefix is separate from the recorder's whole
    # source/input/runtime closure. Observe that real closure before promotion.
    if len(records)==900:
        final_native=native/'owned-native-final-observation.json'
        while not final_native.exists() and alive(a.native_pid,a.native_birth):
            write(out/'progress.json',progress('waiting_for_actual_native_parent_source_closure'));time.sleep(5)
        producer_closed=final_native.exists() and read(final_native).get('record_only_binding_evidence_complete') is True
    else:producer_closed=False
    after={str(p):sha(p) for p in before_files}
    final=progress('complete' if len(records)==900 else 'source_process_terminal_incomplete')
    final.update(source_before=before,source_after=after,source_and_metadata_unchanged=before==after,
        native_full900_source_input_runtime_parent_closure_verified=producer_closed,
        all900_independent_native_saved_math_pass=len(records)==900 and all(r['passed'] for r in records) and producer_closed and before==after,
        terminal_reason=terminal,completed_UTC=datetime.now(timezone.utc).isoformat(),new_MA_or_benchmark_optimizer_or_RNG_calls=0)
    write(out/'summary.json',final)
    return 0 if final['all900_independent_native_saved_math_pass'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input-bank','native-bank','python-math-dir','first-native-audit','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('native-pid','native-birth','python-pid','python-birth'):p.add_argument('--'+name,type=int,required=True)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2]);raise SystemExit(follow(p.parse_args()))
