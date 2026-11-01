"""Apply common saved-state physical readers to an explicitly Python-only case.

The shared reader filenames retain their native origin. The top-level receipt
binds the actual Python result, tape and source and never calls MATLAB or an
optimizer. Older failed case receipts are retained separately.
"""
import argparse
import json
from pathlib import Path
from audit_native_case import audit as finite,sha
from audit_native_phase_mp import audit as phase_mp
from audit_native_physics_mp import audit as physics_mp


def audit(result_path,output):
    if output.exists():raise FileExistsError('Preserve previous independent output')
    result=json.loads(result_path.read_bytes())
    if result.get('language')!='python':raise ValueError('Explicit original Python execution provenance required')
    original=result_path.parent/'actual-result.json'
    if sha(original)!=result['unchanged_original_result_sha256']:raise ValueError('Original Python numerical return differs')
    output.mkdir(parents=True)
    fp=finite(result_path,output/'python-saved-state-fields.json')
    phases=phase_mp(result_path,output/'python-phase-MP80-MP100')
    physics=physics_mp(result_path,output/'python-all8-QT-MP80-MP100.json')
    checks=dict(original_python_internal_gates_pass=bool(result['source_unchanged_during_run'] and result['overall_implemented_scope_success']),
        complete_saved_state_fields_pass=fp['all_finite_precision_checks_pass'],
        all_actual_phase_fields_and_original_stops_MP80_MP100_pass=phases['all_MP_fields_original_stop_and_precision_checks_pass'],
        all8_actual_physical_states_and_all_QT_MP80_MP100_pass=physics['all_physical_QT_and_precision_checks_pass'])
    report=dict(scope='One actual cold complete original eight-scheme Python case, equivalent positive-Wick evaluation; independent saved states/phase/QT checks',
        actual_execution_language='python',MATLAB_or_new_optimizer_called_by_this_audit=False,
        result_sha256=sha(result_path),unchanged_original_python_result_sha256=sha(original),state_sha256=result['state_recording']['sha256'],
        auditor_sha256=sha(Path(__file__)),shared_reader_scope_origin='native saved-state reader implementations; input provenance remains Python',
        phase_endpoints=phases['stages'],complex_phase_coordinates_per_precision=phases['complex_coordinates_per_lane'],QT_candidates=physics['QT_candidates'],
        checks=checks,all_one_case_checks_pass=all(checks.values()),
        independent_raw_Python_MC_or_full183_or_original_reference_or_paper_pass=False)
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    if not audit(a.result,a.output_dir)['all_one_case_checks_pass']:raise SystemExit(1)
