"""Freeze actual two recorded Python fullcases, portable replay and input proof."""
import hashlib
import json
from pathlib import Path
import shutil

STRICT=Path(__file__).resolve().parent
ROOT=STRICT.parent.parent
WORK=ROOT/'work/cooperative-rgd-audit'
ACTUAL=WORK/'recording-v4-actual-fullcases-20261004-v1'
PUBLIC=STRICT/'validation/cooperative-recording-v4-python-two-fullcases-v1'
INPUTS=STRICT/'validation/cooperative-configured-v3-inputs-v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean_text(path):
    value=path.read_text(encoding='utf-8-sig')
    for prefix in ('C:\\\\','C:/Users/','D:\\\\','template_reference','博士后出站手续'):
        assert prefix not in value,(path.name,prefix)


def main():
    assert PUBLIC.is_dir() and {p.name for p in PUBLIC.iterdir()}=={'audit_recorded_fullcase.py'}
    assert not INPUTS.exists()
    original=(WORK/'audit_recording_v4_actual_work.py').read_text(encoding='utf-8')
    portable=(PUBLIC/'audit_recorded_fullcase.py').read_text(encoding='utf-8')
    old_base="BASE=HERE.parents[1]/'wireless-paper-reproductions/strict/cooperative-satcom'"
    new_base="BASE=HERE.parents[1]/'cooperative-satcom'"
    old_lookup="(HERE/name if (HERE/name).is_file() else BASE/name)"
    new_lookup="(HERE/'executed-sources'/name if (HERE/'executed-sources'/name).is_file() else BASE/name)"
    assert portable.replace(new_base,old_base).replace(new_lookup,old_lookup).rstrip()==original.rstrip()
    proof_path=WORK/'configured-v3-input-boundary-transparency-actual-v4-proof-v1.json'
    proof=json.loads(proof_path.read_text(encoding='utf-8-sig'))
    assert proof['configured_entry_source_sha256']==sha(STRICT/'cooperative-satcom/run_cooperative_v3_configured.py')
    assert proof['frozen_control_install_statements_AST_identical_pass'] and proof['exact_existing_full_run_call_AST_identical_pass']
    assert proof['configured_entry_help_and_full183_refusal_boundary_tests_pass']
    assert not proof['new_configured_entry_direct_heavy_execution_performed']
    INPUTS.mkdir();(PUBLIC/'executed-sources').mkdir()
    for filename in ('recording_v4_work.py','run_cooperative_v4_recording_work.py','audit_recording_v4_actual_work.py'):
        clean_text(WORK/filename);shutil.copyfile(WORK/filename,PUBLIC/'executed-sources'/filename)
    summaries=[];bindings=[]
    configs={'M30':WORK/'prospective-v3-all10-phase-preflight-v1/case-00-configuration.json',
        'N48':WORK/'prospective-v3-N48-INR002-fullcase-configuration.json'}
    for name,configuration in configs.items():
        result_path=ACTUAL/f'{name}-actual-python.json';receipt_path=ACTUAL/f'{name}-actual-state.json'
        bank_path=ACTUAL/f'{name}-actual-state.npz';audit_path=ACTUAL/f'{name}-independent-finalstate-audit-v1.json'
        result=json.loads(result_path.read_text(encoding='utf-8-sig'));audit=json.loads(audit_path.read_text(encoding='utf-8-sig'))
        assert audit['all_independent_implemented_numerical_checks_pass'] and all(audit['checks'].values())
        assert sha(result_path)==audit['actual_result_sha256']
        assert sha(receipt_path)==audit['actual_recording_receipt_sha256'] and sha(bank_path)==audit['actual_array_bank_sha256']
        assert sha(configuration)==audit['actual_configuration_sha256']
        assert audit['auditor_source_sha256']==sha(WORK/'audit_recording_v4_actual_work.py')
        assert all(result['checks'].values()) and result['source_unchanged_during_run']
        assert len(audit['actual_scheme_records'])==8
        assert audit['actual_original_moment_draw_audit']['actual_draw_count']==1000
        assert audit['actual_original_moment_draw_audit']['all_original_draws_bitwise_replayed']
        assert audit['actual_original_moment_draw_audit']['original_rng_after_bitwise_pass']
        for source,digest in audit['actual_scientific_and_adapter_sources'].items():
            path=configuration if source=='actual_immutable_configuration' else (WORK/source if (WORK/source).is_file() else STRICT/'cooperative-satcom'/source)
            assert sha(path)==digest
        assert not audit['native_recording_layer_fullcase_independent_certified']
        assert not audit['all_QT_duals_MP80_certified'] and not audit['full_reproduction_pass']
        for path,target in (
            (result_path,PUBLIC/f'{name}-actual-python.json'),
            (receipt_path,PUBLIC/f'{name}-recorded-state.json'),
            (bank_path,PUBLIC/f'{name}-recorded-state.npz'),
            (audit_path,PUBLIC/f'{name}-independent-finalstate-audit.json'),
            (configuration,INPUTS/f'{name}-configuration.json')):
            assert path.stat().st_size<90*1024*1024
            if path.suffix=='.json':clean_text(path)
            shutil.copyfile(path,target);assert sha(target)==sha(path)
            bindings.append({'original_generated_filename':path.name,'public_filename':target.name,
                'sha256':sha(path),'bytes':path.stat().st_size})
        summaries.append({'case':name,'actual_full_dimensions':audit['full_dimensions'],
            'all_independent_implemented_numerical_checks_pass':True,'actual_phase_stages':audit['phase_stage_count'],
            'actual_QT_candidates':audit['QT_candidate_count'],'actual_moment_draws':1000,
            'all_original_draws_and_final_rng_bitwise_replayed':True,
            'largest_independent_scalar_coordinate_final_gradient_norm':max(s['independent_scalar_coordinate_gradient_norm'] for s in audit['actual_phase_stage_records']),
            'largest_scalar_vector_gradient_component_difference':max(s['gradient_maximum_error'] for s in audit['actual_phase_stage_records']),
            'actual_recorded_source_banks_not_relabeled':True})
    clean_text(proof_path);shutil.copyfile(proof_path,INPUTS/'configured-boundary-transparency-proof.json')
    (PUBLIC/'two-actual-case-summary.json').write_text(json.dumps({'scope':'two_actual_Python_full_original_eight_chain_recorded_cases_AND_independent_savedstate_replay',
        'actual_case_summaries':summaries,'source_model_and_physical_inputs_declared_not_original_historical_recovery':True,
        'native_recording_layer_fullcase_certified':False,'new_full183_bank_certified':False,
        'optimized_performance1000_realizations_claimed':False,'MP80_final_gradients_or_all_QT_duals_claimed':False,'full_reproduction_pass':False},indent=2)+'\n',encoding='utf-8')
    readme='''# Two ACTUAL recorded Python fullcases and independent replay

M30 and N48 were actually executed serially with the frozen cooperative v3
numerical kernel through a recording-only WORK boundary. All eight original
schemes reached their real original stops and passed the original four gates.
An AFTER-run independent audit rebuilds all final matrix metrics/constraints,
uses the retained scalar-coordinate derivative oracle for every phase final
state with its actual fixed W or p/mu context, checks every accepted QT input
and candidate, and bitwise replays all 1000 actual channel draws plus final RNG
state. M30: 48 phases/32 QT candidates; N48: 45/24. No extra optimization,
gradient call, or random draw was inserted into the actual recording run.
The original return snapshot equals the actual caller result exactly.

The NPZ banks and metadata contain the actual final phi/W/p, every phase fixed
context, every original QT input and actual candidate, and all actual sampled
effective channels/RNG state. The files are generated numerical evidence,
not private author manuscripts/artwork. They are copied byte-for-byte from
the actual run, with hashes in the manifest. Original runtime receipts' still
false independent-audit flags are not rewritten; later audit files supply
the separate evidence. Executed WORK sources are archived unchanged under
`executed-sources`; those snapshots are not portable execution entrypoints.

The portable audit below differs from the actually executed auditor only in
two source-path lookups (terminal blank formatting excluded). Its original
numerical body is unchanged and the reversible transformation is recorded.
From the repository root, with the existing Python dependencies installed:

```text
python strict/validation/cooperative-recording-v4-python-two-fullcases-v1/audit_recorded_fullcase.py strict/validation/cooperative-recording-v4-python-two-fullcases-v1/M30-actual-python.json strict/validation/cooperative-recording-v4-python-two-fullcases-v1/M30-recorded-state strict/validation/cooperative-configured-v3-inputs-v1/M30-configuration.json NEW-M30-replay-audit.json
```

Use N48 in the same four input/output positions to replay the second case.
The output must be fresh. Neither audit resolves a QT or optimizes a phase.

Independent gradient checks are double-precision scalar-coordinate checks,
not MP80 gradient certificates; the actual vector/scalar differences are
reported, not hidden. The original 1e-6 stop is unchanged and independently
met. The 1000 draws validate channel moments, not 1000 optimized performance
realizations for every scheme. Native recording-v4, formal183 figure bank,
published-curve agreement, original unreported coordinates/gains, publisher
conformance and all-QT MP80 dual certification remain unconfirmed/false.
In particular N48 uses the disclosed chosen latitude1.25 and UPA6x8; it is not
claimed to recover the author's missing historical geometry.
'''
    (PUBLIC/'README.md').write_text(readme,encoding='utf-8')
    input_readme='''# Actual M30/N48 input bytes + versioned v3 Python boundary

These are unchanged original JSON bytes used in the actual fullcase tests,
not fitted published-curve inputs. The attached boundary certificate verifies
the same frozen control-install AST and exact existing full_run call, actual
recording transparency, all final-state audits, and mocked argument/return
forwarding plus fail-closed refusal of full183. The NEW configured entry was
not itself another heavy run; that distinction is explicit in the proof.

The old frozen v3 entry is unchanged. From the repository root:

```text
python strict/cooperative-satcom/run_cooperative_v3_configured.py --configuration strict/validation/cooperative-configured-v3-inputs-v1/M30-configuration.json --full --sweep base --output NEW-M30-fullcase.json
```

Change M30 to N48 for the second configuration. Native v3 likewise accepts
this configuration path with its base-only guard. New results bind the NEW
entry/source/input bytes before and after execution, never fabricated old
source hashes. Missing/capped/failed original gates remain failures. This
input boundary performs no final-state recording; the separate actual-v4
evidence bank provides the saved-state replay. No full183 bank, native-v4,
1000 optimized-performance MC or historical figure agreement is certified.
'''
    (INPUTS/'README.md').write_text(input_readme,encoding='utf-8')
    transformation={'scope':'portable_audit_two_path_lookups_only_original_numeric_body_unchanged',
        'original_executed_auditor_sha256':sha(WORK/'audit_recording_v4_actual_work.py'),
        'portable_auditor_sha256':sha(PUBLIC/'audit_recorded_fullcase.py'),
        'exact_reverse_path_replacement_numeric_body_pass':True,'terminal_blank_formatting_excluded':True,
        'portable_auditor_direct_reexecution_performed':False}
    manifest={'actual_input_and_generated_state_bindings':bindings,'portable_audit_transformation':transformation,
        'actual_scope_flags':{'Python_recorded_two_cases_independent_pass':True,'native_recording_v4':False,'new_full183':False,'performance1000_MC':False,'MP80_final_gradient':False,'full_reproduction_pass':False},
        'freezer_source_sha256':sha(Path(__file__)),
        'public_files':[{ 'filename':str(p.relative_to(PUBLIC)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(PUBLIC.rglob('*')) if p.is_file()]}
    (PUBLIC/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    inputs_manifest={'unchanged_original_input_bytes':True,'configured_entry_sha256':sha(STRICT/'cooperative-satcom/run_cooperative_v3_configured.py'),
        'boundary_certificate_sha256':sha(proof_path),'new_entry_direct_heavy_execution_performed':False,'full_reproduction_pass':False,
        'public_files':[{ 'filename':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(INPUTS.iterdir()) if p.is_file()]}
    (INPUTS/'manifest.json').write_text(json.dumps(inputs_manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'actual_two_recorded_cases_public_frozen':True,'public_bytes':sum(p.stat().st_size for p in PUBLIC.rglob('*') if p.is_file()),
        'state_manifest_sha256':sha(PUBLIC/'manifest.json'),'input_manifest_sha256':sha(INPUTS/'manifest.json'),
        'new_configured_entry_heavy_execution':False,'full_reproduction_pass':False}))


if __name__=='__main__':main()
