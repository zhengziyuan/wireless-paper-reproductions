"""Check all183 original native cases as they close; preserve/reuse completed audits."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import time
from audit_native_case import audit as finite_audit
from audit_native_phase_mp import audit as mp_audit
import mp_phase_reference


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())


class Producer:
    """Hold the actual Windows process object, so PID reuse cannot change identity."""
    def __init__(self,pid,creation):
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];self.api.OpenProcess.restype=wintypes.HANDLE
        self.api.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
        self.api.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        self.api.CloseHandle.argtypes=[wintypes.HANDLE]
        self.handle=self.api.OpenProcess(0x1000|0x00100000,False,pid)
        if not self.handle:raise OSError('Declared native process is unavailable')
        values=[wintypes.FILETIME() for _ in range(4)]
        if not self.api.GetProcessTimes(self.handle,*[ctypes.byref(v) for v in values]):raise OSError('Cannot read native creation time')
        actual=(values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
        if actual!=creation:self.close();raise ValueError('Declared native process was replaced')
    def live(self):
        code=wintypes.DWORD()
        if not self.api.GetExitCodeProcess(self.handle,ctypes.byref(code)):raise OSError('Native status unavailable')
        return code.value==259
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None


def follow(bank,output,finite_root,first_report,pid,creation):
    output.mkdir(parents=True,exist_ok=True);finite_root.mkdir(parents=True,exist_ok=True)
    process=Producer(pid,creation);records=[];started=time.perf_counter()
    try:
        for n in range(183):
            result=bank/f'case-{n:03d}-matlab.json'
            while not result.exists() or read(bank/'progress.json')['finished']<=n:
                if not process.live():
                    state=dict(expected=183,finished=len(records),status='producer_terminated_with_missing_case',missing=n,records=records,full183_pass=False)
                    (output/'progress.json').write_text(json.dumps(state,indent=2)+'\n');return False
                time.sleep(5)
            original=read(result)
            if not original['overall_implemented_scope_success']:
                records.append(dict(ordinal=n,status='producer_failed_or_unconverged_retained',passed=False,result_sha256=sha(result)))
            else:
                state_path=bank/original['state_recording']['filename'];state_sha=sha(state_path)
                fp=finite_root/f'case-{n:03d}-audit.json'
                if fp.exists():
                    finite=read(fp)
                    if (finite['result_sha256'],finite['state_sha256'])!=(sha(result),state_sha):raise ValueError('Old finite audit uses different states')
                else:finite=finite_audit(result,fp)
                mp_dir=first_report if n==0 else output/f'case-{n:03d}'
                if (mp_dir/'summary.json').exists():
                    precise=read(mp_dir/'summary.json');identity=precise['source_input_sha256']
                    if identity['result']!=sha(result) or identity['states']!=state_sha or identity['reference']!=sha(Path(mp_phase_reference.__file__)):
                        raise ValueError('Old MP audit uses different actual input or formula')
                else:precise=mp_audit(result,mp_dir)
                records.append(dict(ordinal=n,passed=bool(finite['all_finite_precision_checks_pass'] and precise['all_MP_fields_original_stop_and_precision_checks_pass']),
                    finite_audit_sha256=sha(fp),MP_summary_sha256=sha(mp_dir/'summary.json'),MP_output=str(mp_dir),stages=precise['stages']))
            progress=dict(expected=183,finished=len(records),passed=sum(bool(r['passed']) for r in records),records=records,
                status='running' if len(records)<183 else 'complete',elapsed_seconds=time.perf_counter()-started,
                full183_saved_endpoint_checks_pass=len(records)==183 and all(r['passed'] for r in records),raw_MC_or_original_reference_or_full_paper_pass=False)
            partial=output/'progress.json.partial';partial.write_text(json.dumps(progress,indent=2)+'\n');partial.replace(output/'progress.json')
            print(json.dumps(dict(native_cases_checked=len(records),passed=progress['passed'],last_case=n,elapsed_seconds=progress['elapsed_seconds'])),flush=True)
        return progress['full183_saved_endpoint_checks_pass']
    finally:process.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bank','output-dir','finite-audit-dir','reuse-first-report'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--producer-pid',type=int,required=True);p.add_argument('--producer-creation-filetime',type=int,required=True);a=p.parse_args()
    if not follow(a.bank,a.output_dir,a.finite_audit_dir,a.reuse_first_report,a.producer_pid,a.producer_creation_filetime):raise SystemExit(1)
