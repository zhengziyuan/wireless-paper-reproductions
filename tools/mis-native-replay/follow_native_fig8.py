"""Independently check each genuine native Fig8 start as its immutable record closes."""
import argparse
import json
from pathlib import Path
import sys
import time
from audit_native_start import audit_start,digest,KERNEL

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cooperative-stable-replay'))
from follow_native_validation import Producer


def read(p):return json.loads(p.read_bytes())


def follow(records,output,first,pid,creation):
    output.mkdir(parents=True,exist_ok=True);owner=Producer(pid,creation);rows=[];started=time.perf_counter();total=passed=0
    try:
        for scheme in ('MIS','SMS'):
            for start in range(1,6001):
                source=records/scheme/f'start-{start:06d}-record.json'
                while not source.exists():
                    if not owner.live():
                        state=dict(expected_starts=12000,checked_starts=len(rows),records=rows,status='producer_terminated_with_missing_record',missing=[scheme,start],full12000_pass=False)
                        (output/'progress.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');return False
                    time.sleep(5)
                destination=first if scheme=='MIS' and start==1 else output/f'{scheme}-start-{start:06d}.json'
                if destination.exists():
                    report=read(destination);identity=report['actual_source_input_raw_sha256']
                    if identity['record_json']!=digest(source) or identity['oracle']!=digest(KERNEL) or identity['auditor']!=digest(Path(__file__).with_name('audit_native_start.py')):
                        raise ValueError('Old independent audit source/input changed')
                else:
                    try:report=audit_start(records,scheme,start)
                    except Exception as failure:
                        report=dict(scheme=scheme,start=start,all_required_one_start_gates_pass=False,error_type=type(failure).__name__,error=str(failure),record_sha256=digest(source))
                        destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                        raise
                    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                ok=report['all_required_one_start_gates_pass'];count=report['actual_endpoints_checked'];total+=count;passed+=int(ok)
                rows.append(dict(scheme=scheme,start=start,passed=ok,own_mu_endpoints=count,report_sha256=digest(destination)))
                state=dict(expected_starts=12000,expected_own_mu_endpoints=230400,checked_starts=len(rows),passed_starts=passed,checked_own_mu_endpoints=total,
                    records=rows,status='complete' if len(rows)==12000 else 'running',elapsed_seconds=time.perf_counter()-started,
                    full12000_saved_endpoints_and_original_stops_pass=len(rows)==12000 and passed==12000 and total==230400,
                    original_curve_or_unsaved_inner_state_or_full_paper_pass=False)
                tmp=output/'progress.json.partial';tmp.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');tmp.replace(output/'progress.json')
                print(json.dumps(dict(checked=len(rows),passed=passed,endpoints=total,last=[scheme,start],elapsed_seconds=state['elapsed_seconds'])),flush=True)
        return state['full12000_saved_endpoints_and_original_stops_pass']
    finally:owner.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('records','output-dir','reuse-first-report'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--producer-pid',type=int,required=True);p.add_argument('--producer-creation-filetime',type=int,required=True);a=p.parse_args()
    if not follow(a.records,a.output_dir,a.reuse_first_report,a.producer_pid,a.producer_creation_filetime):raise SystemExit(1)
