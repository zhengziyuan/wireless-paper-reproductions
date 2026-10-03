"""Freeze actual native sample41 cold TS and independent saved-state audit.

This supplement never replaces earlier Python evidence, reruns an optimizer,
publishes author manuscripts, or promotes the old failed full-CDF bank.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

STRICT = Path(__file__).resolve().parent
ROOT = STRICT.parent.parent
BASE = STRICT / 'hotspot-satcom'
WORK = ROOT / 'work/hotspot-sdp-audit'
CVX = ROOT / 'work/external-cvx-2.2.2/cvx'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def history_digest(value):
    values = np.asarray(value, dtype='<f8').reshape(-1)
    return {'float64_values': len(values), 'little_endian_float64_sha256':
            hashlib.sha256(values.tobytes()).hexdigest(),
            'first': float(values[0]), 'last': float(values[-1])}


def main(args):
    assert not args.output_dir.exists(), 'Do not replace an older public frozen identity'
    native_path = WORK / 'cdf41-complete-original-TS-cold-cap100000-matlab-v3.json'
    state_path = Path(str(native_path) + '.states.mat')
    proof_path = WORK / 'cdf41-complete-original-TS-ACTUAL-MATLAB-independent80digit-v3.json'
    boundary_path = WORK / 'cdf41-native-canonical-boundary-receipt-20261004-v3.json'
    native, proof, boundary = read(native_path), read(proof_path), read(boundary_path)
    canonical_path = WORK / 'cdf41-native-canonical-double-20261004-v3.mat'
    original_path = WORK / 'cdf41-complete-original-TS-cold-cap100000-python-v2.mat'
    assert native['sample_index'] == 41 and native['all_complete_TwoStage_original_gates_pass']
    assert len(native['checks']) == 8 and all(v is True for v in native['checks'].values())
    assert native['source_unchanged_during_run']
    assert native['executed_source_hashes'] == native['executed_source_hashes_after']
    assert proof['all_independent_checks_pass'] and len(proof['checks']) == 8
    assert all(v is True for v in proof['checks'].values())
    assert proof['actual_receipt_sha256'] == sha(native_path)
    assert proof['actual_returned_states_sha256'] == sha(state_path)
    saved_hash = native['actual_saved_states_hash']
    saved_hash = saved_hash[0] if isinstance(saved_hash, list) else saved_hash
    assert saved_hash['sha256'] == sha(state_path)
    assert proof['actual_executed_MATLAB_source_hashes'] == native['executed_source_hashes']
    assert boundary['all_physical_numeric_values_exactly_preserved']
    assert boundary['source_unchanged_during_run'] and boundary['native_original_TS_all_checks_pass']
    assert boundary['source_and_selected_backend_sha256_before'] == boundary['source_and_selected_backend_sha256_after']
    assert boundary['actual_native_result_sha256'] == sha(native_path)
    assert boundary['original_fixture_sha256'] == sha(original_path)
    assert boundary['canonical_fixture_sha256'] == sha(canonical_path)
    assert boundary['actual_native_selected_backend'] == native['actual_selected_CVX_solver'] == 'SDPT3'
    assert boundary['converted_integer_fields'] == [{'field': 'power', 'original_type': 'int64', 'actual_shape': [1, 1]}]

    # Recheck current actual executed code/backend bytes, not basename alone.
    runtime_index = {}
    for path in CVX.rglob('*'):
        if path.is_file() and path.suffix in ('.m', '.mexw64'):
            runtime_index.setdefault(path.name, []).append(path)
    sources = {}
    for binding in native['executed_source_hashes'] + boundary['source_and_selected_backend_sha256_before']:
        name, digest = binding['filename'], binding['sha256']
        candidates = [WORK / name, BASE / name] + runtime_index.get(name, [])
        assert any(p.is_file() and sha(p) == digest for p in candidates), 'Actual source/backend SHA not currently matched: ' + name
        key = name + ':' + digest
        sources[key] = {'filename': name, 'sha256': digest}
    for name, digest in proof['WORK_source_hashes'].items():
        assert sha(WORK / name) == digest
    assert proof['independent_Python_evaluator_source_sha256'] == sha(BASE / 'core.py')

    # Audit saved actual states without any phase/QT re-solve.
    state = loadmat(state_path, simplify_cells=True)
    original = loadmat(original_path, simplify_cells=True)
    canonical = loadmat(canonical_path, simplify_cells=True)
    keys = [k for k in original if not k.startswith('__')]
    assert set(keys) == {k for k in canonical if not k.startswith('__')}
    for key in keys:
        assert np.array_equal(np.asarray(original[key]), np.asarray(canonical[key]), equal_nan=True)
    actual_input = state['f']
    assert all(np.array_equal(np.asarray(actual_input[k]), np.asarray(canonical[k]), equal_nan=True) for k in keys)
    assert np.shape(actual_input['cascade']) == (6, 25, 16)
    assert np.shape(actual_input['direct']) == (6, 16) and np.shape(actual_input['nhu']) == (10, 16)
    assert np.shape(actual_input['W0']) == np.shape(state['W']) == (16, 16)
    phi = np.asarray(state['phi']).reshape(-1)
    assert len(phi) == 25 and np.max(np.abs(np.abs(phi)-1)) < 1e-12
    old_history = np.asarray(state['oldHistory']).reshape(-1)
    phase_history = np.asarray(state['phaseHistory']).reshape(-1)
    qt_history = np.asarray(state['QT_history']).reshape(-1)
    assert len(old_history) == 5001 and len(phase_history) == 6820 and len(qt_history) == 4
    assert np.array_equal(phase_history[:5001], old_history)
    assert np.array_equal(old_history, np.asarray(native['old5000_history']).reshape(-1))
    assert np.array_equal(phase_history, np.asarray(native['phase_history']).reshape(-1))
    assert np.array_equal(qt_history, np.asarray(native['QT_history']).reshape(-1))
    phase_stop, qt_stop = native['nativeMAT_phase_stop'], native['nativeMAT_QT_stop']
    assert phase_stop['converged'] and phase_stop['iterations'] == 6819
    assert phase_stop['threshold'] == 1e-6 and phase_stop['iteration_cap'] == 100000
    assert phase_stop['final_residual'] <= phase_stop['threshold']
    assert qt_stop['converged'] and qt_stop['iterations'] == 3 and qt_stop['threshold'] == 1e-4
    residual = float((qt_history[-1]-qt_history[-2])/max(abs(qt_history[-2]), 1e-12))
    assert residual == qt_stop['final_residual'] == proof['independent_QT_relative_residual']
    assert residual < 1e-4
    assert not native['old_nativeMAT_phase_stop']['converged']
    assert native['old_nativeMAT_phase_stop']['iterations'] == 5000
    assert native['original_cap_number5000_not_reported_in_paper']
    assert native['same_original_cold_phi0_and_given_cold_W0']
    assert native['only_changed_numerical_control'] == {'rgd_iteration_cap': {'old': 5000, 'new': 100000}}
    assert native['scheme_status']['algorithm_success'] and native['scheme_status']['converged']
    assert native['physical_constraint_maximum_violation'] <= 1e-5
    assert native['scheme_status']['numerical']['solver_primal_pass']
    assert native['scheme_status']['numerical']['qt_sdr_bound_pass']
    assert proof['independent80digit_actual_final_gradient']['precision_decimal_digits'] == 80
    assert proof['independent80digit_actual_final_gradient']['original1e6_gradient_stop_pass']
    assert float(proof['independent80digit_actual_final_gradient']['riemannian_gradient_norm']) <= 1e-6
    assert proof['metric_SINR_maximum_PyMAT_error'] <= 1e-8
    assert proof['independent_original_physical_violation'] <= 1e-5
    assert proof['no_new_Python_or_MATLAB_optimization_run']
    assert not native['MATLAB_Python_iterates_bitwise_equivalence_claimed']
    assert not native['actual_entire_sample_all_schemes_rerun'] and not native['historical_author_inputs_recovered']

    # Bind the untouched failed original sample and the preexisting Python proof.
    bank = BASE / 'outputs/instantaneous-source-geometry-cdf20-full1000-final/cdf_kS20-e7bbabe7fe22cde6'
    old_path = bank / 'sample-0041.json'
    old = read(old_path)
    python_path = WORK / 'cdf41-complete-original-TS-cold-cap100000-python-v2.json'
    python = read(python_path)
    assert not old['sample']['valid_sample'] and not old['sample']['convergence_pass']
    assert sha(old_path) == python['old_full_sample41_sha256']
    assert python['all_complete_TwoStage_original_gates_pass']
    old_public = STRICT / 'validation/hotspot-cdf-numerical-components-v1'
    old_manifest_path = old_public / 'manifest.json'
    old_manifest = read(old_manifest_path)
    for name, binding in old_manifest['public_files'].items():
        assert sha(old_public / name) == binding['sha256']

    # These are preserved source snapshots and root-observed startup failures,
    # NOT newly invented machine-generated failure receipts.
    snapshot_dir = WORK / 'retained-native-adapter-extension-error-v1'
    metadata_changes = []
    for name in ('run_cdf41_native_double_boundary_work.m', 'run_cdf41_original_TS_cold_chain_work.m'):
        old_source, current = snapshot_dir / name, WORK / name
        before, after = old_source.read_text(encoding='utf-8'), current.read_text(encoding='utf-8')
        assert before.count("sources={mfilename('fullpath')") == 1
        assert before.replace("sources={mfilename('fullpath')", "sources={[mfilename('fullpath'),'.m']") == after
        metadata_changes.append({'filename': name, 'preserved_failed_startup_source_sha256': sha(old_source),
            'actual_v3_source_sha256': sha(current),
            'only_repair': "append the .m extension to own metadata hash filename; numeric body unchanged"})
    failure_history = {
        'scope': 'retained_source_snapshots_and_root_observed_terminal_startup_errors_NOT_machine_failure_receipts',
        'original_failure_terminal_transcripts_preserved': False,
        'machine_generated_failure_receipts_available': False,
        'failure_observations_authority': 'root agent actual terminal observations; no raw transcript saved',
        'retained_source_snapshots_and_verified_metadata_only_repairs': metadata_changes,
        'observed_failures': [
            {'actual_owned_terminal_session': 39579, 'observed_exit_code': 1,
             'failure_classification': 'metadata hashing own filename missing .m extension before canonical fixture save',
             'observed_function_and_line_stack': [{'name': 'run_cdf41_native_double_boundary_work>hash_file', 'line': 41},
                {'name': 'run_cdf41_native_double_boundary_work>hashes', 'line': 38},
                {'name': 'run_cdf41_native_double_boundary_work', 'line': 24}],
             'canonical_fixture_written': False, 'phase_or_QT_started': False,
             'numerical_case_failure_or_success': False},
            {'actual_owned_terminal_session': 25845, 'observed_exit_code': 1,
             'failure_classification': 'inner metadata hashing own filename missing .m extension after canonical fixture save',
             'observed_function_and_line_stack': [{'name': 'run_cdf41_original_TS_cold_chain_work>hashes', 'line': 67},
                {'name': 'run_cdf41_original_TS_cold_chain_work', 'line': 13},
                {'name': 'run_cdf41_native_double_boundary_work', 'line': 26}],
             'canonical_fixture_written': True,
             'preserved_canonical_v2_fixture_sha256': sha(WORK / 'cdf41-native-canonical-double-20261004-v2.mat'),
             'phase_or_QT_started': False, 'numerical_case_failure_or_success': False}],
        'old_actual_5000_phase_cap_failure_remains_false': True,
        'old_full_sample41_failure_sha256': sha(old_path),
        'old_fullCDF_not_promoted': True}

    compact_fields = ('scope', 'sample_index', 'only_changed_numerical_control',
        'original_cap_number5000_not_reported_in_paper', 'same_original_cold_phi0_and_given_cold_W0',
        'old_nativeMAT_phase_stop', 'nativeMAT_phase_stop', 'nativeMAT_QT_stop', 'QT_history', 'QT_diagnostics',
        'checks', 'all_complete_TwoStage_original_gates_pass', 'same_physical_rate_evaluation',
        'physical_constraint_maximum_violation', 'scheme_status', 'final_criterion', 'final_gradient_norm',
        'elapsed_seconds', 'actual_selected_CVX_solver', 'source_unchanged_during_run',
        'oldPython_sample41_failure_not_upgraded', 'MATLAB_Python_iterates_bitwise_equivalence_claimed',
        'actual_entire_sample_all_schemes_rerun', 'historical_author_inputs_recovered', 'full_reproduction_pass')
    compact_native = {k: native[k] for k in compact_fields}
    compact_native.update(actual_full_dimensions={k: native['configuration']['reported'][k] for k in ('N', 'J', 'U', 'K', 'M')},
        physical_reported_parameters=native['configuration']['reported'],
        actual_old5000_history_identity=history_digest(old_history),
        actual_phase_history_identity=history_digest(phase_history),
        native_cold5000_prefix_independently_rechecked_bitwise=True,
        actual_QT_history_identity=history_digest(qt_history),
        complete_native_TwoStage41_executed_and_verified=True,
        all_source_constraints_verified=False, source_historical_geometry_recovered=False,
        complete_CDF_reproduction_pass=False)
    compact_boundary = {k: v for k, v in boundary.items() if not k.startswith('source_and_selected_backend_sha256_')}
    compact_boundary['actual_source_and_selected_backend_filename_SHA_bindings'] = boundary['source_and_selected_backend_sha256_before']
    compact_boundary['current_actual_runtime_and_scientific_bytes_hash_matched'] = True

    args.output_dir.mkdir(parents=True)
    save(args.output_dir / 'actual-native-cold-full-TwoStage41.json', compact_native)
    save(args.output_dir / 'independent-actual-MAT-state80digit-audit.json', proof)
    save(args.output_dir / 'actual-exact-dtype-and-backend-boundary.json', compact_boundary)
    save(args.output_dir / 'retained-metadata-startup-failure-scope.json', failure_history)
    (args.output_dir / 'README.md').write_text(
        '# Native MATLAB sample41: complete cold original Two-Stage supplement\n\n'
        'This is a new supplement to the earlier Python cold-chain and same-SDP component evidence. '
        'It does not overwrite those receipts or upgrade the old failed full-CDF sample. Native MATLAB '
        'executed the full original physical dimensions N=J=16, U=6, K=10, M=25 with the same supplied '
        'cold W0 and phi0. Only the unreported phase safety cap was extended from5000 to100000. '
        'The original RGD direction/retraction/Armijo and gradient threshold1e-6 remain unchanged.\n\n'
        'The actual native phase terminates at6819 steps with gradient norm3.6573737951e-7; '
        'the original QT then terminates in3 steps with relative residual1.8534185034e-6 below1e-4. '
        'The actual old5000 cold prefix is bitwise identical within MATLAB and still fails the gradient '
        'criterion at5000. This is not a claim that MATLAB and Python trajectories are bitwise equal. '
        'Both actual stop rules and all original physical/primal/QT gates pass.\n\n'
        'An independent80-digit evaluator reads the actual saved MATLAB final matrices without solving '
        'the optimization again. All8 checks pass; its final gradient norm is3.6573737947e-7. '
        'Python evaluation of the saved MATLAB final state agrees with the recorded native metrics/SINRs '
        'within1.4210854716e-14. This is state replay parity, not paired-trajectory equivalence. '
        'The actual native chain took208.1032298 seconds.\n\n'
        'The original generated input has an exact int64 power=100 field. The boundary converts this '
        'to binary64 double after an exact-representability check; every input numeric value is unchanged. '
        'Actual begin/end receipts bind the scientific sources, adapter, input, CVX and selected SDPT3 '
        'MAT/MEX runtime bytes. Raw states remain local and their native SHA is retained.\n\n'
        'Two earlier attempts stopped in metadata initialization, before any phase or QT execution. '
        'Their source snapshots are preserved and the only repair appends the .m extension to the own '
        'metadata filename. The root observed those terminal failures, but the raw terminal transcripts '
        'and machine-generated failed-run JSON are unavailable; this limitation is explicitly recorded. '
        'They are not counted as numerical algorithm failures or successes.\n\n'
        'This is one native complete Two-Stage chain, not every scheme of sample41, a full1000-sample '
        'CDF, recovered historical author inputs, or a published-curve reproduction. Those flags remain '
        'false. No private author manuscript/artwork, absolute private path or raw native stack is copied.\n', encoding='utf-8')
    public_files = {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size}
                    for p in args.output_dir.iterdir() if p.is_file()}
    bindings = {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in
                (native_path, state_path, proof_path, boundary_path, original_path, canonical_path,
                 python_path, old_path, old_manifest_path)}
    save(args.output_dir / 'manifest.json', {
        'scope': 'actual_nativeMAT_one_complete_cold_TwoStage41_and_independent_saved_state80digit_NOT_fullCDF',
        'actual_native_input_result_state_and_proof_hashes': bindings,
        'actual_executed_scientific_adapter_CVX_and_selected_backend_hashes': list(sources.values()),
        'independent_Python_state_evaluator_source_sha256': sha(BASE / 'core.py'),
        'independent80digit_WORK_source_hashes': proof['WORK_source_hashes'],
        'freezer_source_sha256': sha(__file__), 'public_files': public_files,
        'native_original_checks_pass_count': 8, 'independent_saved_state_checks_pass_count': 8,
        'previous_python_public_evidence_unmodified': True,
        'native_complete_TwoStage41_verified': True, 'native_entire_sample_all_schemes_verified': False,
        'native_complete1000_CDF_verified': False, 'historical_author_inputs_recovered': False,
        'all_source_constraints_verified': False, 'full_reproduction_pass': False})
    print(json.dumps({'public_files': len(public_files)+1, 'native_complete_TwoStage41_verified': True,
        'native_original_checks_pass': 8, 'independent_actual_state_checks_pass': 8,
        'native_phase_iterations': 6819, 'native_QT_iterations': 3,
        'old_fullCDF_upgraded': False, 'full_reproduction_pass': False}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=STRICT / 'validation/hotspot-cdf41-native-full-TS-v3')
    main(parser.parse_args())
