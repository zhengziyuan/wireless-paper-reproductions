"""ACTUAL metadata comparison/route proof only, no numerical case audit."""
import argparse
import hashlib
import json
from pathlib import Path
from native_configuration_equivalence_v3_work import verify

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]/'wireless-paper-reproductions'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def run(output):
    assert not output.exists()
    original=(HERE/'audit_cooperative_native_v4_actual_v2_work.py').read_text(encoding='utf-8').rstrip()
    changed=(HERE/'audit_cooperative_native_v4_actual_v3_work.py').read_text(encoding='utf-8').rstrip()
    reverse=changed.replace('import audit_recording_v4_actual_work as oracle\nfrom native_configuration_equivalence_v3_work import verify as verify_config_serialization',
        'import audit_recording_v4_actual_work as oracle')
    reverse=reverse.replace("BASE/'models.py',BASE/'scenario.py',BASE/'core.py',HERE/'native_configuration_equivalence_v3_work.py']",
        "BASE/'models.py',BASE/'scenario.py',BASE/'core.py']")
    reverse=reverse.replace("config_serialization = verify_config_serialization(config,result['configuration'])\n    assert config_serialization['all_metadata_conversion_checks_pass']",
        "assert config == result['configuration']")
    reverse=reverse.replace("'actual_configuration_serialization_equivalence':config_serialization,\n        'actual_inputs_sha256':before_inputs,'full_dimensions':",
        "'actual_inputs_sha256':before_inputs,'full_dimensions':")
    assert reverse==original,'Numerical audit body must be unchanged'
    cases=[]
    for label in ['M30','N48']:
        config=REPO/f'strict/validation/cooperative-configured-v3-inputs-v1/{label}-configuration.json'
        result=HERE/f'recording-v4-{label}-actual-matlab-v1.json'
        orig=read(config);actual=read(result);before={p.name:sha(p) for p in [config,result]}
        comparison=verify(orig,actual['configuration'])
        assert actual['executed_source_hashes']['immutable_configuration']['sha256']==sha(config)
        cases.append({'case':label,'actual_source_configuration_byte_sha256':sha(config),
            'actual_native_result_sha256':sha(result),'actual_metadata_comparison':comparison,
            'old_exact_JSON_dictionary_equality_pass':orig==actual['configuration'],
            'input_files_byte_unchanged':before=={p.name:sha(p) for p in [config,result]}})
    assert cases[0]['old_exact_JSON_dictionary_equality_pass'] and not cases[1]['old_exact_JSON_dictionary_equality_pass']
    proof={'scope':'ACTUAL_native_result_configuration_serialization_metadata_and_auditor_source_reverse_proof_NOT_numeric_case_certification',
        'cases':cases,'checks':{'actual_immutable_configuration_files_bound_and_unchanged':all(c['input_files_byte_unchanged'] for c in cases),
            'exact_predeclared_singleton_conversion_and_all_other_fields_unchanged':all(c['actual_metadata_comparison']['all_metadata_conversion_checks_pass'] for c in cases),
            'v3_auditor_numeric_body_reverses_to_v2_without_changes':reverse==original},
        'old_N48_v2_audit_tool_observation':{'session_id':50820,'exit_code':1,
            'failure_stage':'configuration_dictionary_assert_before_matrix_gradient_QT_moment_checks',
            'raw_stderr_file_available':False},
        'v2_auditor_sha256':sha(HERE/'audit_cooperative_native_v4_actual_v2_work.py'),
        'v3_auditor_sha256':sha(HERE/'audit_cooperative_native_v4_actual_v3_work.py'),
        'exact_configuration_metadata_helper_sha256':sha(HERE/'native_configuration_equivalence_v3_work.py'),
        'proof_source_sha256':sha(__file__),'actual_finalstate_audit_pass':False,'full_reproduction_pass':False}
    proof['all_metadata_and_source_proof_checks_pass']=all(proof['checks'].values())
    output.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all_metadata_and_source_proof_checks_pass':proof['all_metadata_and_source_proof_checks_pass'],
        'actual_numeric_audit_pass':False}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('new_output',type=Path);run(p.parse_args().new_output)
