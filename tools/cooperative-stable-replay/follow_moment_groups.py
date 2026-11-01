"""Verify every closed native case's configured moment stream, reusing exact inputs.

Only a new exact coefficient/seed/count/source signature regenerates operands.
No optimization or performance-MC run is duplicated. MATLAB exports the original
declared moment stream; Python independently reconstructs all received samples.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from audit_moment_draws import input_data,audit
from audit_native_case import sha
from follow_native_validation import Producer


def read(p):
    for attempt in range(10):
        try:return json.loads(p.read_bytes())
        except (json.JSONDecodeError,PermissionError):
            if attempt==9:raise
            time.sleep(.2)


def quote(p):return "'"+str(p).replace('\\','/').replace("'","''")+"'"


def follow(bank,output,first,matlab,pid,creation):
    output.mkdir(parents=True,exist_ok=True);owner=Producer(pid,creation);rows=[];started=time.perf_counter()
    repo=Path(__file__).resolve().parents[2];helper=Path(__file__).resolve().parent
    previous=read(first)
    if not previous['all_independent_checks_pass']:raise ValueError('The reusable original stream has not passed')
    groups={previous['input_signature']:dict(report=first,summary=previous)}
    try:
        for n in range(183):
            result=bank/f'case-{n:03d}-matlab.json'
            while not result.exists() or read(bank/'progress.json')['finished']<=n:
                if not owner.live():
                    state=dict(expected=183,finished=len(rows),status='producer_terminated_with_missing_case',missing=n,records=rows,full183_pass=False)
                    (output/'progress.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');return False
                time.sleep(5)
            original=read(result)
            if not original['overall_implemented_scope_success']:
                rows.append(dict(ordinal=n,passed=False,status='original_failed_case_retained',result_sha256=sha(result)))
            else:
                _,_,dims,signature=input_data(result)
                if signature not in groups:
                    folder=output/f'group-{len(groups):03d}';summary_path=folder/'independent/summary.json'
                    if summary_path.exists():
                        checked=read(summary_path)
                        if checked['input_signature']!=signature:raise ValueError('Saved group has different exact coefficients')
                    else:
                        J,U,N,M=dims;required=1000*U*(2*M+J*(2*N*M+2*N+2))*8
                        folder.mkdir(parents=True,exist_ok=True)
                        if shutil.disk_usage(folder).free<required+2*1024**3:raise OSError('Insufficient E data space for this full original moment stream')
                        prefs=folder/'matlab-preferences';prefs.mkdir(exist_ok=True)
                        expression='restoredefaultpath;addpath('+quote(helper)+');export_saved_moment_draws('+quote(repo)+','+quote(result)+','+quote(folder/'raw')+');'
                        args=[str(matlab),*(['-wait'] if os.name=='nt' else []),'-batch',expression]
                        env=dict(os.environ,MATLAB_PREFDIR=str(prefs));flags=dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name=='nt' else {}
                        with (folder/'native-export.log').open('ab') as log:
                            subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,env=env,check=True,**flags)
                        checked=audit(result,folder/'raw',folder/'independent')
                    groups[signature]=dict(report=summary_path,summary=checked)
                group=groups[signature];checked=group['summary'];mc=original['results'][0]['monte_carlo']
                match=mc['count']==1000 and abs(mc['second_moment_max_relative_error']-checked['second_moment_max_relative_error'])<=1e-9 and abs(mc['fourth_moment_max_relative_error']-checked['fourth_moment_max_relative_error'])<=1e-9
                rows.append(dict(ordinal=n,passed=bool(match and checked['all_independent_checks_pass']),input_signature=signature,
                    group_audit_sha256=sha(group['report']),result_sha256=sha(result),count=1000))
            state=dict(expected=183,finished=len(rows),passed=sum(bool(x['passed']) for x in rows),unique_exact_input_groups=len(groups),records=rows,
                group_reports={key:dict(report=str(value['report']),sha256=sha(value['report'])) for key,value in groups.items()},
                status='complete' if len(rows)==183 else 'running',elapsed_seconds=time.perf_counter()-started,
                all183_configured_moment_stream_physical_checks_pass=len(rows)==183 and all(x['passed'] for x in rows),
                configured1000_count_is_source_reported_optimized_performance_MC=False,original_reference_or_full_paper_pass=False)
            tmp=output/'progress.json.partial';tmp.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');tmp.replace(output/'progress.json')
            print(json.dumps(dict(checked=len(rows),passed=state['passed'],unique_exact_groups=len(groups),last=n,elapsed_seconds=state['elapsed_seconds'])),flush=True)
        return state['all183_configured_moment_stream_physical_checks_pass']
    finally:owner.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bank','output-dir','reuse-first-report','matlab'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--producer-pid',type=int,required=True);p.add_argument('--producer-creation-filetime',type=int,required=True);a=p.parse_args()
    if not follow(a.bank,a.output_dir,a.reuse_first_report,a.matlab,a.producer_pid,a.producer_creation_filetime):raise SystemExit(1)
