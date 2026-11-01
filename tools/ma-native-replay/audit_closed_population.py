"""Inspect the actual closed native900 and paired saved Python returns.

Rehashes the completed inputs/RAW, verifies every retained slot and recomputes
reported sample means. It compares all4.5million paired terminal-rate returns.
It does not recompute received signals, rerun an optimizer or replace the full
independent state/coordinate audit. All per-slot exceptions remain failures.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import time


NAMES=('MA_MRT','MA_ZF','FPA_MRT','FPA_ZF','FPA_OPT')
PYTHON_NAMES={name:name.replace('_','-') for name in NAMES}


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def read(path):
    return json.loads(path.read_bytes())


def require(test,message):
    if not test:
        raise ValueError(message)


def audit(native_bank,binding_index,output):
    require(not output.exists(),'Preserve previous actual closed-population audit')
    output.mkdir(parents=True)
    started=time.perf_counter()
    receipt_path=native_bank/'owned-native-final-observation.json'
    parent=read(receipt_path); bound=read(binding_index)
    watched={str(p):sha(p) for p in (receipt_path,binding_index,Path(__file__),
        native_bank/'full_summary.json',native_bank/'execution-start-identity.json')}
    require(parent['record_only_binding_evidence_complete'] and parent['scientific_entry_call_count']==1 and
        not parent['exception'] and not parent['evidence_exceptions'] and
        parent['actual_expected_jobs']==parent['actual_raw_slots_observed']==parent['actual_saved_schema_gate_count']==900,
        'Actual complete original native parent closure is required')
    for name in ('selected_source','own_recording_sources','original_bank_metadata','input','own_runtime'):
        require(parent[name+'_before']==parent[name+'_after'],'Parent interval changed: '+name)
    require(parent['actual_native_full_summary_sha256']==sha(native_bank/'full_summary.json') and
        parent['actual_native_start_identity_sha256']==sha(native_bank/'execution-start-identity.json'),
        'Actual native returned summary/start identity differs')
    require(parent['all900_actual_saved_schema_and_declared_gate_observations_passed'] and
        not bound['failures'] and bound['source_inputs_before']==bound['source_inputs_after'],
        'Original native gates or retained saved-source binding failed')
    rows=bound['rows']; observations=parent['raw_observations']
    expected=[(i,j) for i in range(9) for j in range(100)]
    require([(r['case_index'],r['realization']) for r in rows]==expected and
        [(r['case_index'],r['realization']) for r in observations]==expected,'Every exact original slot is required')
    repo=Path(__file__).resolve().parents[2]
    for row in parent['selected_source_before']:
        path=repo/row['key']
        require(sha(path)==row['sha256'],'Executed original native numerical source changed')
        watched[str(path)]=row['sha256']
    checked_files={}; case_rows=[]; metric_rows=[]; failures=[]
    mean_error=0.; max_sample_gap=0.; total_samples=0
    def consume(spec):
        p=Path(spec['path'])
        if p in checked_files:
            require(checked_files[p]['sha256']==spec['sha256'],'Inconsistent byte binding')
            return None
        raw=p.read_bytes()
        require(sha_bytes(raw)==spec['sha256'] and ('bytes' not in spec or len(raw)==spec['bytes']),
            'Selected unchanged input/result/classification hash differs: '+p.name)
        checked_files[p]=dict(bytes=len(raw),sha256=spec['sha256'])
        return raw
    for n,(selection,observed) in enumerate(zip(rows,observations)):
        identity=f"case-{selection['case_index']:03d}-mc-{selection['realization']:03d}"
        try:
            require(observed['filename']==selection['filename'] and
                observed['input_fingerprint']==selection['input_fingerprint'] and
                observed['saved_schema_and_declared_gates_passed'] and not observed['exception'],
                'Native source slot/fingerprint differs')
            for spec in selection['files'].values():
                # The RAW is read below exactly once so its exact consumed
                # bytes, numerical samples and producer binding are joined.
                if spec is not selection['files']['selected_raw']:
                    consume(spec)
            py_spec=selection['files']['selected_raw']
            py_bytes=Path(py_spec['path']).read_bytes()
            require(sha_bytes(py_bytes)==py_spec['sha256'] and len(py_bytes)==py_spec['bytes'],
                'Exact selected Python RAW changed')
            checked_files[Path(py_spec['path'])]=dict(bytes=len(py_bytes),sha256=py_spec['sha256'])
            native_path=native_bank/(identity+'-matlab.json')
            native_bytes=native_path.read_bytes()
            require(sha_bytes(native_bytes)==observed['raw_sha256'],'Actual closed native RAW changed')
            checked_files[native_path]=dict(bytes=len(native_bytes),sha256=observed['raw_sha256'])
            py,native=json.loads(py_bytes),json.loads(native_bytes)
            require(py['input_fingerprint']==native['input_fingerprint']==selection['input_fingerprint'],
                'Actual complete-language returns use different original inputs')
            meta=native['job_metadata']
            require((meta['figure'],meta['N'],meta['M'],meta['kappa'],meta['A'],meta['realization'])==
                (6,6,5,6,2,selection['realization']) and meta['point']==9+3*selection['case_index'],
                'Actual full source scene/axis differs')
            require(set(py['metrics']['schemes'])==set(PYTHON_NAMES.values()) and
                set(native['metrics']['schemes'])==set(NAMES),
                'Exactly five schemes are required in each actual return')
            local=[]
            for name in NAMES:
                left,right=py['metrics']['schemes'][PYTHON_NAMES[name]],native['metrics']['schemes'][name]
                x,y=left['sample_sum_rates'],right['sample_sum_rates']
                require(len(x)==len(y)==1000 and all(math.isfinite(v) for v in x+y),
                    'Every configured physical-rate return must be retained')
                a,b=math.fsum(x)/1000,math.fsum(y)/1000
                err=max(abs(a-left['mean_sum_rate']),abs(b-right['mean_sum_rate']),
                    abs(b-observed['saved_schema']['families'][name]['saved_mean_sum_rate']))
                require(err<=1e-12+1e-12*max(abs(a),abs(b)),'Stored complete sample mean differs')
                gap=max(abs(u-v) for u,v in zip(x,y))
                local.append(dict(case_index=selection['case_index'],realization=selection['realization'],
                    point_dBm=meta['point'],scheme=name,selected_Python_origin=selection['origin'],
                    Python_mean_reported=left['mean_sum_rate'],MATLAB_mean_reported=right['mean_sum_rate'],
                    Python_sample_mean_recomputed=a,MATLAB_sample_mean_recomputed=b,
                    absolute_language_mean_gap=abs(a-b),maximum_paired_sample_gap=gap,
                    paired_sample_RMSE=math.sqrt(math.fsum((u-v)**2 for u,v in zip(x,y))/1000)))
                mean_error=max(mean_error,err);max_sample_gap=max(max_sample_gap,gap);total_samples+=1000
            metric_rows.extend(local)
            case_rows.append(dict(case=identity,original_input_fingerprint=selection['input_fingerprint'],
                original_input_sha256=selection['files']['job']['sha256'],Python_RAW_sha256=py_spec['sha256'],
                MATLAB_RAW_sha256=observed['raw_sha256'],selected_Python_origin=selection['origin'],
                original_producer_time_RAW_SHA=selection['original_producer_time_RAW_SHA'],
                Python_RAW_SHA_observation_semantics=selection['raw_SHA_observation_semantics'],
                both_complete_actual_returns_and_sample_aggregates_checked=True))
        except Exception as error:
            failures.append(dict(case=identity,error_type=type(error).__name__,error=str(error)))
        if (n+1)%100==0:
            print(json.dumps(dict(actual_original_slots_inspected=n+1,successful_complete_pairs=len(case_rows),
                retained_failure_count=len(failures),paired_terminal_rate_samples_compared=total_samples)),flush=True)
    aggregate=[]
    if not failures:
        for i in range(9):
            for name in NAMES:
                selected=[r for r in metric_rows if r['case_index']==i and r['scheme']==name]
                require(len(selected)==100,'No failed geometry may disappear from an aggregate')
                left=math.fsum(r['Python_sample_mean_recomputed'] for r in selected)/100
                right=math.fsum(r['MATLAB_sample_mean_recomputed'] for r in selected)/100
                aggregate.append(dict(point_dBm=9+3*i,scheme=name,configured_geometry_cases=100,
                    configured_NLoS_samples_per_geometry=1000,Python_mean_sum_rate=left,
                    MATLAB_mean_sum_rate=right,absolute_language_curve_gap=abs(left-right)))
    data=io.StringIO(newline='')
    if metric_rows:
        writer=csv.DictWriter(data,fieldnames=list(metric_rows[0]));writer.writeheader();writer.writerows(metric_rows)
    (output/'all4500-paired-scheme-aggregates.csv.gz').write_bytes(gzip.compress(data.getvalue().encode(),mtime=0))
    (output/'all45-complete-curve-points.json').write_text(json.dumps(aggregate,indent=2)+'\n',encoding='utf-8')
    after={str(p):sha(Path(p)) for p in watched}
    report=dict(scope='Actual closed original native900 and selected complete Python900: all4500 scheme returns/all4.5million rate samples; no signal/coordinate rederivation',
        original_cases=900,actual_complete_pairs=len(case_rows),scheme_returns=len(metric_rows),
        paired_terminal_rate_samples_compared=total_samples,full_native_parent_closed=True,
        original_native_entry_call_count=1,original_native_stored_gates_passed=900,
        source_input_sha256=watched,source_interval_unchanged=watched==after,
        exact_unambiguous_original_Python_to_native_scheme_name_map=PYTHON_NAMES,
        actual_current_input_RAW_and_receipt_files_rehashed=len(checked_files),
        actual_current_bytes_rehashed=sum(v['bytes'] for v in checked_files.values()),
        maximum_stored_mean_recalculation_error=mean_error,maximum_paired_rate_sample_difference=max_sample_gap,
        maximum_per_geometry_scheme_mean_difference=max((r['absolute_language_mean_gap'] for r in metric_rows),default=None),
        maximum_complete_curve_mean_difference=max((r['absolute_language_curve_gap'] for r in aggregate),default=None),
        failures=failures,failed_or_missing_cases_discarded=False,original_900_case_bindings=case_rows,
        all900_complete_return_and_aggregation_checks_pass=len(case_rows)==900 and not failures and watched==after,
        historical_missing_producer_time_RAW_hashes_recovered=False,
        independent_received_signal_or_coordinate_gradient_or_FPA_step_W_KKT_or_original_reference_pass=False,
        original_author_MC_counts_seeds_geometry_or_caps_recovered=False,
        all_full900_independent_dual_language_physics_or_full_paper_pass=False,
        new_optimizer_or_random_draw_calls=0,elapsed_seconds=time.perf_counter()-started)
    (output/'actual-closed900-return-and-aggregation-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    printed={k:v for k,v in report.items() if k not in ('source_input_sha256','original_900_case_bindings','failures')}
    printed.update(retained_failure_count=len(failures),first_retained_failures=failures[:3])
    print(json.dumps(printed),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native-bank','binding-index','output-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if not audit(a.native_bank,a.binding_index,a.output_dir)['all900_complete_return_and_aggregation_checks_pass']:
        raise SystemExit(1)
