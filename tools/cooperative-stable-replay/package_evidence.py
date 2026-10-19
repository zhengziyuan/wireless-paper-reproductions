"""Package actual91 endpoints and summarize retained183 checks without relabelling flags."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def package(bank,mpbank,fixture,references,native,python_audit,native_audit,output):
    if output.exists():raise FileExistsError('Fresh evidence packet required')
    py,mat=read(python_audit),read(native_audit)
    if not(py['all_endpoint_checks_pass'] and mat['all_endpoint_checks_pass']):raise ValueError('Both full91 lanes required')
    if (py['fixture_sha256'],py['references_sha256'])!=(sha(fixture),sha(references)) or (mat['fixture_sha256'],mat['references_sha256'])!=(sha(fixture),sha(references)):
        raise ValueError('Independent lanes use different inputs')
    plan=read(bank/'execution-plan.json')
    if plan['required_points']!=183 or [c['ordinal'] for c in plan['cases']]!=list(range(183)):raise ValueError('Original complete183 schedule required')
    rows=[]
    for n in range(183):
        case=bank/f'case-{n:03d}'; receipt=read(case/'actual-point-receipt.json'); audit=read(case/'actual-independent-audit.json')
        mp_path=mpbank/f'case-{n:03d}/external-case-summary.json'; mp=read(mp_path)
        nonphase={k:v for k,v in audit['checks'].items() if k!='all_actual_phase_final_gradients_original_threshold_pass'}
        rows.append(dict(ordinal=n,sweep=plan['cases'][n]['sweep'],parameter=plan['cases'][n]['parameter'],value=plan['cases'][n]['value'],
            original_complete_case_returned=receipt['actual_complete_result_returned'],original_internal_gates_pass=receipt['actual_all_original_gates_pass'],
            original_source_interval_pass=receipt['source_interval_pass'],all_retained_nonphase_independent_checks_pass=all(nonphase.values()),
            original_float_auditor_all_checks_pass=audit['all_independent_implemented_numerical_checks_pass'],
            original_MP_whole_case_flag=mp['whole_case_recheck_pass'],original_MP_component_comparisons_pass=mp['all_four_new_MP80_components_close_pass'],
            MP80_reported_false_stop_stages=mp['MP80_false_original_stop_stages'],all_phase_coordinates_covered=mp['allphase_allcoordinate_coverage_pass'],
            phase_stages=mp['every_original_phase_context_count'],QT_candidates=mp['every_original_QT_candidate_count'],moment_draws=mp['all_original_moment_draw_count'],
            positive_formula_replay_for_this_case=(n in (56,65)),point_receipt_sha256=sha(case/'actual-point-receipt.json'),
            original_independent_audit_sha256=sha(case/'actual-independent-audit.json'),MP_summary_sha256=sha(mp_path)))
    inventory=dict(scope='Retained183-point evidence inventory plus new91-endpoint positive-formula replay; no original flags rewritten',
        points=183,schemes_per_point=8,phase_stages=sum(r['phase_stages'] for r in rows),QT_candidates=sum(r['QT_candidates'] for r in rows),
        moment_draws=sum(r['moment_draws'] for r in rows),original_float_auditor_pass_points=sum(r['original_float_auditor_all_checks_pass'] for r in rows),
        original_float_failed_case_ordinals=[r['ordinal'] for r in rows if not r['original_float_auditor_all_checks_pass']],
        all_original_internal_gates_pass=all(r['original_internal_gates_pass'] for r in rows),
        all_retained_nonphase_independent_checks_pass=all(r['all_retained_nonphase_independent_checks_pass'] for r in rows),
        all_MP80_reported_false_stop_lists_empty=all(not r['MP80_reported_false_stop_stages'] for r in rows),
        original_MP_whole_case_pass_points=sum(r['original_MP_whole_case_flag'] for r in rows),
        new91_endpoint_both_language_comparisons_pass=True,original_raw_float_consistency_failures_overwritten=False,
        all_original_whole_case_flags_upgraded=False,full_historical_inner_trajectory_replay=False,
        original_reference_agreement=False,full_reproduction_pass=False,records=rows)
    output.mkdir(parents=True)
    write(output/'retained183-inventory.json',inventory)
    for source,name in ((python_audit,'actual-python91-audit.json'),(native_audit,'actual-native91-audit.json'),(native/'summary.json','actual-native91-summary.json')):
        raw=source.read_bytes()
        if name in ('actual-python91-audit.json','actual-native91-audit.json'):
            detailed=read(source); detailed.pop('records')
            compressed=gzip.compress(raw,mtime=0); (output/(name+'.gz')).write_bytes(compressed)
            detailed['detailed_report']=dict(file=name+'.gz',gzip_sha256=hashlib.sha256(compressed).hexdigest(),uncompressed_sha256=hashlib.sha256(raw).hexdigest(),uncompressed_bytes=len(raw),stage_records=91)
            write(output/name,detailed)
        else:(output/name).write_bytes(raw)
    files={'inputs/original-all91-inputs.mat':fixture,'inputs/references.json':references,
        'native/native-all91-original-components.mat':native/'native-all91-original-components.mat','native/summary.json':native/'summary.json'}
    manifest=dict(scope='Actual complete91 original endpoint inputs, retained MP80 values and actual native outputs',
        files={name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in files.items()},stage_count=91,complex_gradient_coordinates=8190)
    archive=output/'native91-positive-wick.tar.gz'
    with archive.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as compressed,tarfile.open(fileobj=compressed,mode='w') as tar:
        for name,data in sorted([(name,p.read_bytes()) for name,p in files.items()]+[('manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())]):
            item=tarfile.TarInfo(name);item.size=len(data);item.mtime=0;item.mode=0o644;tar.addfile(item,io.BytesIO(data))
    write(output/'archive.json',dict(file=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,**manifest))
    print(json.dumps(dict(points=183,old_float_pass=inventory['original_float_auditor_pass_points'],old_float_failed=inventory['original_float_failed_case_ordinals'],
        all_retained_nonphase_pass=inventory['all_retained_nonphase_independent_checks_pass'],phase_stages=inventory['phase_stages'],moment_draws=inventory['moment_draws'],
        new_native_and_python91_pass=True,archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),full_reproduction_pass=False)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bank','mpbank','fixture','references','native','python-audit','native-audit','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();package(a.bank,a.mpbank,a.fixture,a.references,a.native,a.python_audit,a.native_audit,a.output_dir)
