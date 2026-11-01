"""Read-only MP80/100 final-state/QT follower for the original183 native cases."""
import argparse
import json
from pathlib import Path
import time
from audit_native_case import sha
from audit_native_physics_mp import audit
from follow_native_validation import Producer
import audit_native_physics_mp as auditor
import mp_phase_reference as reference


def read(p):return json.loads(p.read_bytes())


def follow(bank,output,first,pid,creation):
    output.mkdir(parents=True,exist_ok=True);owner=Producer(pid,creation);rows=[];started=time.perf_counter()
    try:
        for n in range(183):
            source=bank/f'case-{n:03d}-matlab.json'
            while not source.exists() or read(bank/'progress.json')['finished']<=n:
                if not owner.live():
                    report=dict(expected=183,finished=len(rows),records=rows,status='producer_terminated_with_missing_case',missing=n,full183_pass=False)
                    (output/'progress.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return False
                time.sleep(5)
            original=read(source)
            if not original['overall_implemented_scope_success']:
                rows.append(dict(ordinal=n,passed=False,status='original_failed_case_retained',result_sha256=sha(source)))
            else:
                target=first if n==0 else output/f'case-{n:03d}-MP-physics.json'
                if target.exists():
                    report=read(target);identity=report['source_input_sha256']
                    expected=dict(result=sha(source),states=sha(source.parent/original['state_recording']['filename']),auditor=sha(Path(auditor.__file__)),reference=sha(Path(reference.__file__)))
                    if identity!=expected:raise ValueError('Reuse requires identical complete source/input hashes')
                else:report=audit(source,target)
                rows.append(dict(ordinal=n,passed=report['all_physical_QT_and_precision_checks_pass'],report_sha256=sha(target),
                    physical_scalar_values_per_precision=report['scalar_values_per_precision'],QT_candidates=report['QT_candidates']))
            state=dict(expected=183,finished=len(rows),passed=sum(bool(x['passed']) for x in rows),records=rows,status='complete' if len(rows)==183 else 'running',
                elapsed_seconds=time.perf_counter()-started,full183_physical_QT_MP_checks_pass=len(rows)==183 and all(x['passed'] for x in rows),
                phase_stops_MC_original_reference_or_full_paper_pass=False)
            tmp=output/'progress.json.partial';tmp.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');tmp.replace(output/'progress.json')
            print(json.dumps(dict(cases=len(rows),passed=state['passed'],last=n,elapsed_seconds=state['elapsed_seconds'])),flush=True)
        return state['full183_physical_QT_MP_checks_pass']
    finally:owner.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bank','output-dir','reuse-first-report'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--producer-pid',type=int,required=True);p.add_argument('--producer-creation-filetime',type=int,required=True);a=p.parse_args()
    if not follow(a.bank,a.output_dir,a.reuse_first_report,a.producer_pid,a.producer_creation_filetime):raise SystemExit(1)
