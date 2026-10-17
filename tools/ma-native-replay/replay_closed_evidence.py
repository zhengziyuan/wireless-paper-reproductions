"""Verify real closed900 receipts and all4500 public aggregate-table rows.

This public command rechecks the delivered aggregate tables. The full4.5million
sample comparison was performed by audit_closed_population.py on preserved
external RAW files; those samples are not rederived by this compact replay.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path


def replay(packet,output):
    if output.exists():
        raise FileExistsError('Preserve previous closed900 aggregate replay')
    manifest=json.loads((packet/'manifest.json').read_bytes())
    for name,spec in manifest['files'].items():
        if Path(name).name!=name or ':' in name or '\\' in name:
            raise ValueError('Unsafe aggregate-evidence member')
        raw=(packet/name).read_bytes()
        if len(raw)!=spec['bytes'] or hashlib.sha256(raw).hexdigest()!=spec['sha256']:
            raise ValueError('Actual closed900 evidence differs: '+name)
    parent_raw=gzip.decompress((packet/'actual-native-execution-parent.json.gz').read_bytes())
    report_raw=gzip.decompress((packet/'actual-closed900-return-and-aggregation-audit.json.gz').read_bytes())
    if (hashlib.sha256(parent_raw).hexdigest()!=manifest['original_native_parent_uncompressed_sha256'] or
        hashlib.sha256(report_raw).hexdigest()!=manifest['original_full_return_audit_uncompressed_sha256']):
        raise ValueError('Original complete receipt changed through compression')
    parent,report=json.loads(parent_raw),json.loads(report_raw)
    if not (parent['record_only_binding_evidence_complete'] and parent['actual_saved_schema_gate_count']==900 and
        report['all900_complete_return_and_aggregation_checks_pass'] and report['actual_complete_pairs']==900 and
        report['paired_terminal_rate_samples_compared']==4500000 and not report['failures']):
        raise ValueError('Original complete producer/return comparison did not close')
    with gzip.open(packet/'all4500-paired-scheme-aggregates.csv.gz','rt',newline='') as stream:
        rows=list(csv.DictReader(stream))
    names=('MA_MRT','MA_ZF','FPA_MRT','FPA_ZF','FPA_OPT')
    expected={(i,j,n) for i in range(9) for j in range(100) for n in names}
    keys=[(int(r['case_index']),int(r['realization']),r['scheme']) for r in rows]
    if len(rows)!=4500 or set(keys)!=expected or len(set(keys))!=4500:
        raise ValueError('A complete original geometry or scheme disappeared')
    points=json.loads((packet/'all45-complete-curve-points.json').read_bytes())
    if len(points)!=45 or {(p['point_dBm'],p['scheme']) for p in points}!={(9+3*i,n) for i in range(9) for n in names}:
        raise ValueError('All45 complete original grid/scheme aggregates are required')
    maximum_error=0.
    for point in points:
        selected=[r for r in rows if float(r['point_dBm'])==point['point_dBm'] and r['scheme']==point['scheme']]
        if len(selected)!=100:
            raise ValueError('No surviving-subset averaging is admitted')
        for language in ('Python','MATLAB'):
            actual=math.fsum(float(r[language+'_sample_mean_recomputed']) for r in selected)/100
            error=abs(actual-point[language+'_mean_sum_rate'])
            maximum_error=max(maximum_error,error)
            if error>1e-12+1e-12*abs(actual):
                raise ValueError('A complete public curve aggregate differs')
    output.parent.mkdir(parents=True,exist_ok=True)
    result=dict(actual_public_payload_files_verified=len(manifest['files']),actual_closed_native_cases=900,
        public_complete_geometry_scheme_rows_replayed=4500,complete_curve_points_recomputed=45,
        maximum_public_curve_aggregation_error=maximum_error,
        full4500000_sample_comparison_repeated_by_this_compact_reader=False,
        actual900_RAW_rehashed_by_this_compact_reader=False,
        original_full_RAW_auditor_retains_4500000_actual_compared_samples=True,
        full900_independent_signal_coordinate_FPA_KKT_or_original_reference_or_paper_pass=False,
        optimizer_or_random_draw_calls=0)
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    replay(a.packet,a.output)
