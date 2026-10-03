"""Freeze separate ACTUAL public-path native-state replay receipts, no rerun."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT.parent/'work/cooperative-rgd-audit'
PUBLIC=ROOT/'strict/validation/cooperative-recording-v4-native-two-fullcases-v3'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def freeze():
    original=read(PUBLIC/'manifest.json')
    for name,digest in original['files'].items():assert sha(PUBLIC/name)==digest,name
    destination=PUBLIC/'portable-replay-actual-v1';assert not destination.exists()
    pending=[];cases=[]
    for label in ['M30','N48']:
        audit_path=WORK/f'{label}-native-v4-public-portable-actual-audit-v3.json'
        binding_path=Path(str(audit_path)+'.portable-binding.json')
        audit=read(audit_path);binding=read(binding_path)
        assert audit['all_independent_native_implemented_numerical_checks_pass'] and all(audit['checks'].values())
        assert binding['source_interval_pass'] and binding['adapter_and_frozen_auditor_sources_before']==binding['adapter_and_frozen_auditor_sources_after']
        assert binding['actual_independent_audit_sha256']==sha(audit_path)
        stem=f'recording-v4-{label}-actual-matlab-v1'
        for name,digest in audit['actual_inputs_sha256'].items():assert original['files'][name]==digest,name
        assert binding['actual_saved_state_sha256']==original['files'][stem+'.json.states.mat']
        assert audit['native_RNG_replay_receipt_sha256']==original['files'][stem+'-rng-replay.json']
        assert audit['audit_source_sha256']==original['files']['executed-sources/audit_cooperative_native_v4_actual_v3_work.py']
        assert binding['adapter_and_frozen_auditor_sources_before']['audit_native_recorded_fullcase.py']==original['files']['audit_native_recorded_fullcase.py']
        cases.append({'case':label,'actual_public_path_readonly_state_audit_pass':True,
            'actual_audit_sha256':sha(audit_path),'actual_portable_route_binding_sha256':sha(binding_path),
            'actual_phase_stage_count':audit['phase_stage_count'],'actual_QT_candidate_count':audit['QT_candidate_count'],
            'original_native1000_bitwise_replay_receipt_verified_not_new_MATLAB_replay':True})
        pending.extend([audit_path,binding_path])
    destination.mkdir()
    for path in pending:shutil.copyfile(path,destination/path.name)
    observer=WORK/'native-v4-public-replay-initial-process-failure-observer-note.md'
    assert observer.is_file();shutil.copyfile(observer,destination/observer.name)
    summary={'scope':'ACTUAL_public_directory_reexecution_of_byte_exact_native_savedstate_matrix_scalar_gradient_QT_moment_audits',
        'cases':cases,'actual_public_path_portable_audit_pass':True,
        'original_frozen_manifest_sha256':sha(PUBLIC/'manifest.json'),
        'original_manifest_and_all_listed_files_unchanged':True,
        'new_MATLAB_rng_replay_or_optimizer_executed':False,
        'original_actual_native_bitwise_RNG_receipt_bound_and_verified':True,
        'initial_unclassified_process_exit_failure_retained_as_observer_note_not_numeric_receipt':True,
        'whole183_or_historical_reproduction_pass':False}
    (destination/'actual-portable-replay-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    readme='''# Actual public-path native-state replay supplement

Both complete saved native M30/N48 cases were actually read and independently
audited again **from the public evidence directory**, one at a time. All final
matrices, stage fixed-context scalar gradients, accepted QT candidates and all
1000 stored channel moment samples passed the unchanged original gates.

This is a new public-path read-only execution, not another optimized simulation
or new MATLAB RNG execution. The original actual native bitwise RNG proof was
verified against its complete saved state/input/helper SHA. The public helper
remains available for an independent MATLAB replay. No native draw was replaced
by a Python draw. Frozen source snapshots were used; the adapter only redirects
path resolution and preserves every numerical function body.

The original manifest still truthfully records portable replay as not yet
executed at initial freeze; it and all its files are unchanged. This supplement
provides the subsequent actual replay receipts and their hashes. Whole183,
optimized performance1000MC, historical-figure/publisher conformance and all
MP80 phase/QT claims remain false.
'''
    (destination/'README.md').write_text(readme,encoding='utf-8')
    manifest={'scope':summary['scope'],'files':{path.name:sha(path) for path in destination.iterdir() if path.is_file()},
        'freezer_source_sha256':sha(__file__),'original_frozen_manifest_sha256':sha(PUBLIC/'manifest.json'),
        'actual_portable_replay_pass':True,'full_reproduction_pass':False}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'actual_public_native_replay_pass':True,'supplement_manifest_sha256':sha(destination/'manifest.json'),
        'original_manifest_unchanged':True,'full_reproduction_pass':False}),flush=True)


if __name__=='__main__':freeze()
