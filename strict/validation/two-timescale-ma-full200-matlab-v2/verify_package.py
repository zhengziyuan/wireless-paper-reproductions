"""Verify this preserved evidence package, without rerunning its simulations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parent
    read = lambda name: json.loads((folder / name).read_text(encoding='utf-8-sig'))
    manifest = read('freeze-manifest.json')
    assert len(manifest['all200_original_input_and_raw_output_bindings']) == 200
    for name, expected in manifest['published_files'].items():
        data = (folder / name).read_bytes()
        assert len(data) == expected['bytes'], name
        assert hashlib.sha256(data).hexdigest() == expected['sha256'], name
    physics = read('full200-matlab-independent-physical-audit-v1.json')
    certificates = read('full200-matlab-independent-coordinate-certificates-v1.json')
    assert physics['all200_independent_gates_passed'] and physics['passed_cases'] == 200 and physics['failed_cases'] == 0
    assert physics['all_sources_inputs_raw_outputs_unchanged_at_end']
    assert certificates['all200_independent_coordinate_certificates_passed'] and certificates['passed'] == 200 and certificates['failed'] == 0
    assert certificates['source_input_raw_unchanged_at_end']
    readiness = read('readiness.json')
    assert readiness['full_execution_verified'] and readiness['complete_jobs'] == 200
    assert not readiness['failed_samples_discarded_for_curve'] and not readiness['original_curve_closeness_verified']
    comparison = read('full200-matlab-original-Fig3-unfitted-vector-comparison-indexing-v2.json')
    assert not comparison['original_curve_closeness_verified']
    summary = read('audit-summary.json')
    assert not summary['same_input_full_Python200_completion_claimed']
    assert not summary['all_paper_figures_completed_claimed']
    identities = read('execution-runtime-source-identity-compact.json')
    assert identities['all_result_identities_pass'] and identities['source_unchanged_during_run']
    assert identities['runtime_dependency_identity_unchanged']
    assert identities['original_execution_identity_sha256'] == manifest['actual_outer_execution_identity_sha256']
    assert readiness['execution_identity_sha256'] == manifest['actual_outer_execution_identity_sha256']
    case_hashes = {item['raw_result_filename']: item['raw_result_sha256'] for item in manifest['all200_original_input_and_raw_output_bindings']}
    ensemble = read('full200-matlab-Fig3-ensemble-protocol-audit-v1.json')
    assert ensemble['all200_actual_raw_sha256'] == case_hashes
    assert all(case_hashes[item['case'] + '-matlab.json'] == item['raw_sha256'] for item in physics['records'])
    print(json.dumps({'all_public_hashes_verified': True, 'public_files': len(manifest['published_files']),
                      'MATLAB_complete_cases': 200, 'physical_audit_passed': True, 'coordinate_certificate_audit_passed': True,
                      'original_curve_closeness_verified': False, 'same_input_Python200_completion_claimed': False,
                      'no_scientific_rerun_performed_by_this_verifier': True}, indent=2))


if __name__ == '__main__':
    main()
