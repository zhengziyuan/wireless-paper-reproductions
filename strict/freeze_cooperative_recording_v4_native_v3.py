"""Freeze ACTUAL native-v4 two-fullcase evidence only after independent gates.

Never executes MATLAB or an optimizer. No native/mock/old-Python receipt mixing.
New output directory only; existing published manifests are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT.parent/'work/cooperative-rgd-audit'
sys.path.insert(0,str(WORK))
from mat73_readonly_v2_work import read as read_mat73


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def items(x):return x if isinstance(x,list) else [x]


def strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,dict):
        for v in value.values():yield from strings(v)
    elif isinstance(value,list):
        for v in value:yield from strings(v)


def reject_private_paths(value,label):
    # Binary MAT numeric data are inspected through the read-only decoder first.
    for text in strings(value):
        assert not re.search(r'(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|\\\\[^\\]+\\|/Users/|/home/)',text),f'Private absolute path in {label}'


PORTABLE='''"""Portable actual native-state audit adapter; no numerical body edits.

Requires h5py, the repository's existing Python reproduction dependencies, and
the complete byte-exact recorded MAT state. No MATLAB or optimizer is invoked.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'cooperative-satcom'
SOURCES=HERE/'executed-sources'
sys.path.insert(0,str(BASE));sys.path.insert(0,str(SOURCES))
import audit_cooperative_native_v4_actual_v3_work as native
native.HERE=SOURCES
native.BASE=BASE

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('actual_result',type=Path)
    p.add_argument('runtime_binding',type=Path);p.add_argument('configuration',type=Path)
    p.add_argument('output',type=Path);p.add_argument('--native-rng-replay',type=Path,required=True)
    args=p.parse_args();receipt=Path(str(args.output)+'.portable-binding.json')
    assert not receipt.exists() and not args.output.exists()
    bound=[Path(__file__),SOURCES/'audit_cooperative_native_v4_actual_v3_work.py',
        SOURCES/'mat73_readonly_v2_work.py',SOURCES/'audit_recording_v4_actual_work.py']
    before={p.name:sha(p) for p in bound}
    native.audit(args)
    after={p.name:sha(p) for p in bound};assert before==after
    proof={'scope':'ACTUAL_portable_readonly_native_savedstate_audit_not_reoptimization',
        'adapter_route_only':'Frozen module globals HERE/BASE resolve byte-exact copied sources and current repository science; numerical function bodies unmodified',
        'adapter_and_frozen_auditor_sources_before':before,
        'adapter_and_frozen_auditor_sources_after':after,
        'source_interval_pass':before==after,'actual_independent_audit_sha256':sha(args.output),
        'actual_saved_state_sha256':sha(Path(str(args.actual_result)+'.states.mat')),
        'full183_or_historical_reproduction_pass':False}
    receipt.write_text(json.dumps(proof,indent=2)+'\\n',encoding='utf-8')
'''


def freeze(args):
    destination=args.output
    assert not destination.exists(),'New evidence folder required'
    raw_records=[];pending=[]
    source_names=['mat73_readonly_v2_work.py','audit_cooperative_native_v4_actual_v3_work.py',
        'audit_cooperative_native_v4_actual_v2_work.py','native_configuration_equivalence_v3_work.py',
        'verify_native_v4_configuration_v3_work.py',
        'mat73_readonly_work.py','audit_cooperative_native_v4_actual_work.py',
        'verify_native_v4_decoder_v2_work.py',
        'audit_recording_v4_actual_work.py','replay_cooperative_native_v4_moment_draws_work.m',
        'run_strict_cooperative_v4_recording_work.m','strict_satcom_algorithms_v4_recording_work.m',
        'strict_satcom_recording_v4_work.m','run_cooperative_v4_native_checked_work.m']
    for label in ['M30','N48']:
        stem=WORK/f'recording-v4-{label}-actual-matlab-v1'
        result_path=Path(str(stem)+'.json');state=Path(str(result_path)+'.states.mat')
        runtime_path=Path(str(stem)+'-runtime.json');rng_path=Path(str(stem)+'-rng-replay.json')
        audit_path=Path(str(stem)+'-independent-audit-v3.json')
        configuration=ROOT/f'strict/validation/cooperative-configured-v3-inputs-v1/{label}-configuration.json'
        result=read(result_path);runtime=read(runtime_path);rng=read(rng_path);audit=read(audit_path)
        assert len(result['results'])==1 and result['overall_implemented_scope_success'] and all(result['checks'].values())
        assert result['source_unchanged_during_run'] and runtime['source_and_selected_backend_interval_pass']
        assert runtime['actual_full_result_sha256']==sha(result_path) and runtime['actual_recorded_states_sha256']==sha(state)
        assert runtime['selected_backend_MAT_and_MEX_inventory_before']==runtime['selected_backend_MAT_and_MEX_inventory_after']
        assert rng['all_actual_native_rng_replay_checks_pass'] and all(rng['checks'].values())
        assert rng['actual_native_result_sha256']==sha(result_path) and rng['actual_native_saved_states_sha256']==sha(state)
        assert audit['all_independent_native_implemented_numerical_checks_pass'] and all(audit['checks'].values())
        actual_inputs=audit['actual_inputs_sha256']
        for path in [result_path,state,runtime_path,configuration]:assert actual_inputs[path.name]==sha(path),path.name
        assert audit['native_RNG_replay_receipt_sha256']==sha(rng_path) and audit['native_RNG_receipt_present_and_actual']
        assert len(audit['actual_scheme_records'])==8 and audit['phase_stage_count']>0 and audit['QT_candidate_count']>0
        assert audit['audit_source_sha256']==sha(WORK/'audit_cooperative_native_v4_actual_v3_work.py')
        assert audit['decoder_source_sha256']==sha(WORK/'mat73_readonly_v2_work.py')
        for name,digest in audit['independent_auditor_sources_before'].items():
            path=WORK/name if (WORK/name).is_file() else ROOT/'strict/cooperative-satcom'/name
            assert sha(path)==digest,name
        for key,binding in result['executed_source_hashes'].items():
            if key=='immutable_configuration':assert binding['sha256']==sha(configuration)
            elif not key.startswith('runtime_') and isinstance(binding,dict):
                assert sha(ROOT/'strict/cooperative-satcom'/binding['filename'])==binding['sha256']
        decoded=read_mat73(state,['recordedCases','recordingMetadata'])
        reject_private_paths(decoded,label+' complete native MAT state')
        for path in [result_path,runtime_path,rng_path,audit_path,configuration]:reject_private_paths(read(path),path.name)
        assert state.stat().st_size<=90*1024**2,'Per-file public size limit'
        for path in [result_path,state,runtime_path,rng_path,audit_path,configuration]:pending.append((path,path.name))
        raw_records.append({'case':label,'actual_full_dimensions':audit['full_dimensions'],
            'actual_all8_original_gates_pass':all(result['checks'].values()),
            'actual_all_independent_native_state_and_rng_gates_pass':all(audit['checks'].values()),
            'actual_phase_stage_count':audit['phase_stage_count'],'actual_QT_candidate_count':audit['QT_candidate_count'],
            'actual_original_moment_draw_count':rng['actual_draw_count'],
            'actual_result_sha256':sha(result_path),'actual_complete_native_states_sha256':sha(state),
            'actual_native_runtime_binding_sha256':sha(runtime_path),'actual_native_rng_replay_sha256':sha(rng_path),
            'actual_independent_native_state_audit_sha256':sha(audit_path),'actual_configuration_sha256':sha(configuration),
            'selected_backend_scope':'Actual selected callback plus MAT/MEX inventory interval; complete all-dependency inventory NOT claimed'})
    schema_path=WORK/'recording-v4-M30-decoder-v2-actual-schema-only.json'
    schema=read(schema_path);assert schema['all_decoder_and_route_checks_pass'] and all(schema['checks'].values())
    assert schema['decoder_v2_sha256']==sha(WORK/'mat73_readonly_v2_work.py')
    assert schema['auditor_v2_sha256']==sha(WORK/'audit_cooperative_native_v4_actual_v2_work.py')
    assert schema['decoder_v1_sha256']==sha(WORK/'mat73_readonly_work.py')
    assert schema['auditor_v1_sha256']==sha(WORK/'audit_cooperative_native_v4_actual_work.py')
    reject_private_paths(schema,'actual decoder-only failure/source proof')
    pending.append((schema_path,schema_path.name))
    configproof_path=WORK/'native-v4-configuration-v3-actual-metadata-only-proof.json'
    configproof=read(configproof_path);assert configproof['all_metadata_and_source_proof_checks_pass'] and all(configproof['checks'].values())
    assert configproof['v3_auditor_sha256']==sha(WORK/'audit_cooperative_native_v4_actual_v3_work.py')
    assert configproof['exact_configuration_metadata_helper_sha256']==sha(WORK/'native_configuration_equivalence_v3_work.py')
    reject_private_paths(configproof,'actual native JSON configuration serialization proof')
    pending.append((configproof_path,configproof_path.name))
    destination.mkdir(parents=True)
    for path,name in pending:shutil.copyfile(path,destination/name)
    sources=destination/'executed-sources';sources.mkdir()
    for name in source_names:shutil.copyfile(WORK/name,sources/name)
    (destination/'audit_native_recorded_fullcase.py').write_text(PORTABLE,encoding='utf-8')
    (destination/'requirements-state-audit.txt').write_text('h5py==3.16.0\n',encoding='utf-8')
    summary={'scope':'ACTUAL_two_full_original_native_cooperative_v4_cases_all8_final_matrices_phase_QT_and1000_actual_moment_draws',
        'cases':raw_records,'recording_only_scientific_operations_unmodified':True,
        'actual_native_fullcase_independent_certification':True,
        'initial_decoder_v1_failed_before_numeric_audit_preserved':True,
        'initial_N48_v2_config_serialization_assertion_failure_preserved':True,
        'only_exact_J1_singleton_latitude_JSON_serialization_conversion_allowed':True,
        'decoder_v2_only_MATLAB_class_discrimination_and_auditor_route_numeric_body_reverse_proof_pass':True,
        'portable_public_path_actual_reexecution_verified':False,
        'full183_executed':False,'all_QT_duals_or_phase_gradients_MP80_certified':False,
        'optimized_performance1000_realizations_claimed':False,
        'original_historical_geometry_or_publisher_conformance_recovered':False,'full_reproduction_pass':False}
    (destination/'two-actual-native-case-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    readme='''# Two actual native recording-v4 full cases

These are actual MATLAB M30 and N48 complete eight-scheme cases, not a mock,
Python simulation relabeled as MATLAB, or a full 183-point bank. Every complete
saved final matrix, phase-stage context, QT input/candidate, and all original
1000 actual **channel-moment** draws are preserved in byte-exact MAT-v7.3 files.
Independent matrix/scalar-gradient/QT checks and a separate native bitwise RNG
replay have actually passed for these cases. Actual source, input and selected
backend intervals and output SHA bindings are preserved.

The `.states.mat` files accompany the original `.json` result stems. Keep their
names together. Source snapshots under `executed-sources` are byte-exact; they
are not newly optimized results or standalone installed production entries.

Install the existing repository reproduction requirements plus
`requirements-state-audit.txt`, then from this folder run:

```text
python audit_native_recorded_fullcase.py recording-v4-M30-actual-matlab-v1.json recording-v4-M30-actual-matlab-v1-runtime.json M30-configuration.json NEW-M30-readonly-audit.json --native-rng-replay recording-v4-M30-actual-matlab-v1-rng-replay.json
```

Replace M30 with N48 for the second case. This adapter only changes module path
resolution to copied frozen sources/current repository science. It does not
change any numerical function body or rerun an optimizer. A public-path replay
is a distinct receipt and is **not** presumed executed by this freeze operation.
The recorded native RNG proof does not claim Python generates MATLAB draws.

Still false: complete formal183 execution, all-QT-dual/final-gradient MP80
certification, 1000 optimized performance samples, recovery of the author's
historical geometry, publisher conformance and original-figure agreement.
Existing v2/v3/Python evidence and all failures remain unchanged.

The initially prepared v1 HDF5 decoder failed before matrix/gradient/QT audit:
it mistook a direct class=cell dataset in a scalar MATLAB struct for a struct
array field. Its original sources and actual failure reproduction are retained.
The new reader adds only that MATLAB-class distinction. The new auditor changes
only reader import/source routing; its full numerical body reverses byte-for-byte
to v1. The real native schema and separate synthetic direct-cell row/column
regression checks passed before the actual numerical v2 audits. A decoder-only
test is not itself a numerical certificate.

The N48 v2 auditor separately failed before numerical checks because MATLAB
serialized the original single-satellite latitude list [1.25] as scalar 1.25.
V3 accepts only that predeclared field conversion when J==1, the source list
has one element, and the scalar is exactly equal. All other configuration
fields must match exactly. Source configuration bytes/SHA and mathematical
array dimensions are unchanged; no generic array flattening or tolerance was
introduced. The metadata-only proof and old v2 source are preserved. Both
actual native cases were independently audited with the same final v3 source.
'''
    (destination/'README.md').write_text(readme,encoding='utf-8')
    files={str(path.relative_to(destination)).replace('\\','/'):sha(path) for path in destination.rglob('*') if path.is_file()}
    manifest={'scope':summary['scope'],'files':files,'files_are_byte_exact_actual_outputs_except_new_summary_README_and_path_adapter':True,
        'private_absolute_paths_checked_and_absent':True,'publication_state':'new_evidence_folder_only_not_external_publish',
        'freezer_source_sha256':sha(Path(__file__)),'complete_cases':raw_records,
        'portable_adapter_numeric_body_unchanged':True,'portable_adapter_actual_execution_verified':False,
        'full_reproduction_pass':False}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frozen_files':len(files)+1,'manifest_sha256':sha(destination/'manifest.json'),
        'actual_native_two_case_state_audit_pass':True,'full_reproduction_pass':False}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,
        default=ROOT/'strict/validation/cooperative-recording-v4-native-two-fullcases-v3')
    freeze(p.parse_args())
