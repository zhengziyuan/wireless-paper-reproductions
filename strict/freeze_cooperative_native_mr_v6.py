"""Freeze actual two-input/four-control native MR components, retaining failures.

Never reruns a solver or upgrades extra strict MP flags. Generated numeric
inputs are public; author manuscripts, raw native stacks and paths are not.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

STRICT = Path(__file__).resolve().parent
ROOT = STRICT.parent.parent
BASE = STRICT / 'cooperative-satcom'
WORK = ROOT / 'work/cooperative-rgd-audit'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def source_path(name, fixture):
    if name == fixture.name:
        return fixture
    if (WORK / name).is_file():
        return WORK / name
    if (BASE / name).is_file():
        return BASE / name
    raise ValueError('Unexpected executed source basename')


def main(args):
    assert not args.output_dir.exists(), 'Do not replace an older frozen public identity'
    components, bindings, generated = [], [], []
    sources = {}
    for tag, fixture in (
        ('N48', BASE / 'outputs/mr-QT-numerical-input-72b59733fcf550ec.mat'),
        ('M30-call20', WORK / 'M30-QT-capture-20261004-v2/same-QT-first-failure-mr-call20.mat')):
        native_path = WORK / f'factored-original-MR-{tag}-backend-controls-ACTUAL-MATLAB-20261004-v6.json'
        proof_path = WORK / f'factored-original-MR-{tag}-ACTUAL-MATLAB80digit-v6.json'
        native, proof = read(native_path), read(proof_path)
        state_path = Path(str(native_path) + '.states.mat')
        assert native['kind'] == 'mr' and native['source_unchanged_during_run']
        assert sha(native_path) == proof['actual_MATLAB_receipt_sha256']
        assert sha(state_path) == native['actual_returned_state_receipt']['sha256'] == proof['actual_MATLAB_states_sha256']
        assert native['all_original_model_auxiliaries_constraints_and_1e5_gates_unchanged']
        attempts, checked = native['actual_attempts'], proof['actual_attempts']
        assert len(attempts) == len(checked) == 4
        assert [(x['actual_cvx_solver'], x['numerical_precision']) for x in attempts] == [
            ('SDPT3', 'high'), ('SDPT3', 'best'), ('SeDuMi', 'high'), ('SeDuMi', 'best')]
        f = loadmat(state_path, simplify_cells=True, mat_dtype=True)
        assert f['kind'] == 'mr'
        inputs = list(f['originalInputs'])
        inputs[0] = np.atleast_2d(inputs[0])
        J, U = inputs[0].shape
        inputs[1] = np.asarray(inputs[1]).reshape(J, U)
        inputs[2] = np.asarray(inputs[2]).reshape(J, U, U)
        inputs[3] = np.asarray(inputs[3]).reshape(J, U)
        inputs[5:] = [np.asarray(x).reshape(-1) for x in inputs[5:]]
        inputs[4] = np.asarray(inputs[4]).reshape(J, U, len(inputs[-1]))
        states = f['states']
        states = [states] if isinstance(states, dict) else list(np.asarray(states, object).reshape(-1))
        assert len(states) == 4
        for item in native['executed_source_hashes']:
            assert sha(source_path(item['filename'], fixture)) == item['sha256']
            sources[item['filename']] = item['sha256']
        generated.append({'input_id': tag, 'generated_original_fixture_sha256': sha(fixture),
            'numeric_scope': 'same_generated_original_MR_QT_coefficients_and_incumbent_NOT_author_manuscript_or_artwork',
            'dimensions': {'J': J, 'U': U, 'K': len(inputs[-1])},
            'fields': {name: np.asarray(value).tolist() for name, value in zip(
                ('p0', 'signal', 'cross', 'power', 'leak', 'offset', 'power_limit', 'interference_limit'), inputs)}})
        for actual, independent, state in zip(attempts, checked, states):
            assert actual['all_original_gates_pass'] and actual['backend_sources_unchanged']
            assert actual['original_primal_relative_violation'] <= 1e-5
            assert actual['original_QT_bound_violation'] <= 1e-5
            assert actual['original_monotonicity_residual'] <= 1e-5
            assert independent['actual_original_precision_gates_pass']
            assert independent['actual_cvx_solver'] == actual['actual_cvx_solver']
            assert independent['numerical_precision'] == actual['numerical_precision']
            assert independent['precision_decimal_digits'] == 80
            assert 0 <= float(independent['true_feasible_primal_dual_gap']) <= 1e-5
            is_sedumi = actual['actual_cvx_solver'] == 'SeDuMi'
            assert independent['complete_precision_pass'] is is_sedumi
            assert independent['all_independent80digit_precision_pass'] is is_sedumi
            assert independent['checks']['actual_raw_primal_dual_gap_original1e5'] is is_sedumi
            if not is_sedumi:
                assert -1e-9 < float(independent['actual_raw_primal_dual_gap']) < 0
            raw_fields = {k: v for k, v in actual.items() if k != 'backend_runtime_MAT_and_MEX_hashes'}
            backend = actual['backend_runtime_MAT_and_MEX_hashes']
            backend_digest = hashlib.sha256(json.dumps(backend, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            evaluation = state['actual_info']
            components.append({'input_id': tag, 'actual_native_attempt': raw_fields,
                'actual_native_before_and_after': {k: {n: np.asarray(v).tolist() for n, v in evaluation[k].items()}
                    for k in ('before', 'after')},
                'actual_native_candidate': np.asarray(state['actual_candidate']).reshape(J, U).tolist(),
                'actual_independent80digit_proof': independent,
                'all_original_precision_gates_pass': True,
                'extra_strict_MP80_pass': is_sedumi,
                'actual_backend_runtime_files_count': len(backend),
                'actual_complete_backend_filename_SHA_bindings_digest': backend_digest,
                'actual_backend_entrypoint_and_MEX_bindings': [x for x in backend
                    if x['filename'].endswith('.mexw64') or x['filename'] in ('sedumi.m', 'sdpt3.m', 'sqlp.m', 'cvx_sdpt3.m', 'cvx_sedumi.m')],
                'whole_scheme_chain_or_figure_certified': False})
        bindings.append({'input_id': tag, 'generated_original_fixture_sha256': sha(fixture),
            'actual_native_receipt_sha256': sha(native_path), 'actual_native_returned_states_sha256': sha(state_path),
            'actual_independent80digit_proof_sha256': sha(proof_path),
            'native_elapsed_seconds': native['elapsed_seconds']})
    assert len(components) == 8 and sum(x['extra_strict_MP80_pass'] for x in components) == 4
    right_path = WORK / 'native-MR-construction-operation-probe-20261004-v1.json'
    left_path = WORK / 'native-MR-construction-operation-probe-20261004-v2-left-dual.json'
    right, left = read(right_path), read(left_path)
    assert right['source_input_unchanged'] and left['source_input_unchanged']
    assert not right['model_was_solved'] and not left['model_was_solved']
    assert right['actual_failure']['identifier'] == 'MATLAB:colon:inputsMustBeNumericCharLogical'
    assert right['actual_failure']['operation'] == 'constraint_and_dual_binding'
    assert not left['actual_failure']
    history = {'scope': 'retained_native_WRAPPER_constructor_metadata_failures_NOT_original_solver_model_failure',
        'right_dual_actual_probe_sha256': sha(right_path), 'left_dual_actual_probe_sha256': sha(left_path),
        'right_dual_actual_executed_operations': right['executed_steps'],
        'right_dual_actual_failure': {k: right['actual_failure'][k] for k in ('operation', 'message', 'identifier')},
        'right_dual_stack_function_and_line_only': [{k: x[k] for k in ('name', 'line')}
            for x in ([right['actual_failure']['stack']] if isinstance(right['actual_failure']['stack'], dict)
                      else right['actual_failure']['stack'])],
        'left_dual_actual_executed_operations': left['executed_steps'],
        'left_dual_constructor_pass_not_solver_or_full_case': True,
        'retained_failures': [], 'full_reproduction_pass': False}
    for folder, category in (
        ('retained-backend-metadata-startup-error-20261004-v1', 'wrapper_backend_metadata_startup_before_numeric_component'),
        ('retained-exact-integer-deserialization-error-20261004-v2', 'generated_fixture_integer_double_deserialization_exception_before_solver'),
        ('retained-native-open-model-exception-20261004-v3', 'constructor_exception_and_CVX_owner_scope_cleanup_before_solver')):
        path = WORK / folder / 'failure.json'
        assert path.is_file()
        history['retained_failures'].append({'failure_classification': category,
            'actual_preserved_failure_receipt_sha256': sha(path), 'actual_preserved_bytes': path.stat().st_size,
            'not_reclassified_as_solver_numerical_failure_or_success': True})
    for version in ('v2', 'v5'):
        path = WORK / f'factored-original-MR-N48-backend-controls-ACTUAL-MATLAB-20261004-{version}.json'
        old = read(path)
        assert not old['any_original_gates_passed']
        history['retained_failures'].append({'failure_classification': 'native_constructor_failure_before_solver',
            'preserved_actual_receipt_sha256': sha(path), 'actual_attempt_count': len(old['actual_attempts']),
            'all_original_success_flags_remain_false': True})
    actual_input_native = WORK / 'production-v2-M30-capture-matlab-20261004-v2.json'
    old_m30 = read(actual_input_native)
    assert old_m30['source_unchanged_during_run'] and all(v is False for v in old_m30['checks'].values())
    history['separate_genuine_old_native_M30_QT_failure'] = {
        'actual_native_full_failure_sha256': sha(actual_input_native),
        'actual_MR_call20_generated_input_sha256': bindings[1]['generated_original_fixture_sha256'],
        'classification': 'genuine_solver_precision_monotonicity_failure_in_original_MR_QT_high_best_NOT_APwarning_or_constructor_error',
        'old_native_complete_case_failure_retained': True}
    args.output_dir.mkdir(parents=True)
    receipt = {'scope': 'actual_nativeMAT_two_fixed_original_MR_QT_inputs_four_numerical_controls_NOT_whole_algorithm_or_figures',
        'actual_fixed_inputs': 2, 'actual_native_attempts': 8,
        'all_original_precision_gates_pass_count': 8, 'extra_strict_MP80_pass_count': 4,
        'extra_strict_MP80_fail_count_retained': 4,
        'extra_strict_failed_controls': 'SDPT3 high/best on bothinputs; actual rawgamma is slightly above truefeasible-dual upper',
        'all_true_feasible_primal_dual_gaps_at_most': max(float(x['actual_independent80digit_proof']['true_feasible_primal_dual_gap']) for x in components),
        'actual_components': components, 'original_precision_threshold_unchanged': 1e-5,
        'exact_numeric_identity': 'sqrt(scale*v)=sqrt(scale)*sqrt(v), scale>0',
        'native_construct_boundary_correction': 'left named dual annotation on identical inequalities; error-only CVX owner workspace cleanup',
        'actual_native_scientific_sources_unchanged': True,
        'native_whole_v3_algorithm_preflight_verified': False, 'new_complete183_bank_verified': False,
        'historical_source_geometry_or_figure_agreement_verified': False, 'full_reproduction_pass': False}
    save(args.output_dir / 'actual-native-eight-MR-components.json', receipt)
    save(args.output_dir / 'generated-original-two-input-bindings.json', {'scope': 'generated_actual_original_MR_subproblem_inputs_NOT_author_privatefiles', 'inputs': generated})
    save(args.output_dir / 'retained-native-failure-classification.json', history)
    (args.output_dir / 'README.md').write_text(
        '# Actual native MATLAB MR-QT components: two inputs, eight attempts\n\n'
        'Both generated original fixed inputs executed SDPT3 high/best and SeDuMi high/best. '
        'All8 attempts passed the unchanged original physical/primal/QT/monotonicity gates. '
        'Only4 SeDuMi attempts passed the additional strict80-digit raw-primal/dual test. '
        'All4 SDPT3 extra strict failures are retained: their raw reported objective exceeds the true feasible '
        'dual witness by roughly1e-11, while their true feasible-primal/dual gaps remain tiny. '
        'No gate is relaxed and no extra strict flag is upgraded.\n\n'
        'The same exact positive coordinate constant is factored outside the original square-root cone. '
        'Native construction required a left named-dual annotation on identical inequalities; '
        'an error-only CVX cleanup occurs in the owning provider workspace. An actual operation probe '
        'separately identifies the old right-dual colon construction exception. Metadata/type/constructor '
        'failures are not original model or solver numerical failures. The older genuine native M30 MR-QT '
        'monotonicity failure also remains unchanged.\n\n'
        'Generated numeric inputs, actual returned-state/result hashes, actual source/runtime bindings, '
        'and independent80-digit results are preserved. Absolute private paths, raw error stacks and author '
        'manuscripts/artwork are excluded. This is NOT an entire eight-scheme native run, a new183-point bank, '
        'or a published-figure reproduction certificate.\n', encoding='utf-8')
    public_files = {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in args.output_dir.iterdir() if p.is_file()}
    manifest = {'scope': receipt['scope'], 'actual_input_result_and_state_bindings': bindings,
        'actual_executed_native_scientific_and_WRAPPER_sources': sources,
        'independent_MP80_checker_sha256': sha(WORK / 'verify_actual_matlab_mr_qt_duals.py'),
        'independent_MP80_math_helper_sha256': sha(WORK / 'try_original_mr_objective_scale.py'),
        'freezer_source_sha256': sha(__file__), 'public_files': public_files,
        'all_original_precision_pass_count': 8, 'additional_strict_MP80_pass_count': 4,
        'additional_strict_MP80_fail_count_retained': 4,
        'native_whole_v3_case_certified': False, 'new_full183_certified': False,
        'full_reproduction_pass': False}
    save(args.output_dir / 'manifest.json', manifest)
    print(json.dumps({'actual_native_attempts': 8, 'original_gates_pass': 8,
        'extra_strict_MP80_pass': 4, 'extra_strict_MP80_fail_retained': 4,
        'public_files': len(public_files)+1, 'full_reproduction_pass': False}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output-dir', type=Path, default=STRICT / 'validation/cooperative-native-mr-components-v6')
    main(p.parse_args())
