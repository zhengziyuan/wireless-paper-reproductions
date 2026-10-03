"""Independent recorded-native endpoints, no optimizer imports or state mutation."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat

HERE = Path(__file__).resolve().parent
KERNEL = HERE / 'independent_physical_fig7_v1.py'
PLAN = HERE / 'NATIVE_FIG7_SAVED_ENDPOINT_AUDIT_PLAN_V1.md'
ROUTE = HERE / 'actual-Fig7-oracle-source-route-preflight-v2.json'
SPEC = importlib.util.spec_from_file_location('physical_native_Fig7', KERNEL)
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def scalar(value):
    assert isinstance(value, np.ndarray) and value.shape == (1, 1)
    assert value.dtype.kind in 'biuf' and np.isfinite(value[0, 0])
    return float(value[0, 0])

def structure(value):
    assert isinstance(value, np.ndarray) and value.shape == (1, 1) and value.dtype == object
    item = value[0, 0]
    assert hasattr(item, '_fieldnames')
    return item

def text(value):
    assert isinstance(value, np.ndarray) and value.dtype.kind == 'U' and value.size == 1
    return str(value.item())

def vector(value, n):
    assert isinstance(value, np.ndarray) and value.dtype.kind in 'iuf'
    if n == 0:
        assert value.shape in ((0, 0), (0, 1), (1, 0)) and value.size == 0
        return []
    assert value.shape in ((n, 1), (1, n)) and np.isfinite(value).all()
    return value.reshape(n).tolist()

def state(value, n, u):
    item = structure(value)
    assert set(item._fieldnames) == {'phi', 'theta', 'X'}
    phi, theta = structure(item.phi), structure(item.theta)
    assert set(phi._fieldnames) == {'real', 'imag'} and set(theta._fieldnames) == {'real', 'imag'}
    assert item.X.shape == (4, u) and item.X.dtype.kind in 'iuf' and np.isfinite(item.X).all()
    return {'phi': {'real': vector(phi.real, 2), 'imag': vector(phi.imag, 2)},
            'theta': {'real': vector(theta.real, n), 'imag': vector(theta.imag, n)},
            'X': item.X.tolist()}

def cell(value):
    assert isinstance(value, np.ndarray) and value.dtype == object and value.ndim == 2
    assert value.shape[0] == 1
    return list(value[0])

def named_json_matrix(value, rows, columns):
    # MATLAB jsonencode reduces only a known single-column numeric matrix to
    # a vector. Actual MAT matrix shape is still independently enforced.
    if columns == 1:
        assert isinstance(value, list) and len(value) == rows
        assert all(isinstance(x, (int, float)) for x in value)
        return [[x] for x in value]
    assert isinstance(value, list) and len(value) == rows
    assert all(isinstance(row, list) and len(row) == columns for row in value)
    return value

def exact(a, b):
    """Saved duplicate structural equality; never a general squeeze adapter."""
    if isinstance(a, np.ndarray):
        if not isinstance(b, np.ndarray) or a.shape != b.shape or a.dtype != b.dtype:
            return False
        if a.dtype == object:
            return all(exact(x, y) for x, y in zip(a.flat, b.flat))
        return a.tobytes() == b.tobytes()
    if hasattr(a, '_fieldnames'):
        return (hasattr(b, '_fieldnames') and a._fieldnames == b._fieldnames
                and all(exact(getattr(a, k), getattr(b, k)) for k in a._fieldnames))
    return type(a) is type(b) and a == b

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def audit_start(record_folder, scheme, start):
    require(scheme in ('MIS', 'SMS') and 1 <= start <= 6000, 'Original declared identity required')
    source_route = json.loads(ROUTE.read_text(encoding='utf-8'))
    require(source_route['all_route_and_finite_witness_checks_pass'], 'Prior source route failed')
    require(digest(KERNEL) == source_route['derived_Fig7_oracle_sha256'], 'Oracle changed after actual preflight')
    folder = Path(record_folder) / scheme
    stem = 'start-%06d' % start
    mat_path, initial_path, record_path = [folder / (stem + suffix)
                                          for suffix in ('-full.mat', '-initial.json', '-record.json')]
    sources = {'oracle': KERNEL, 'plan': PLAN, 'route': ROUTE, 'auditor': Path(__file__)}
    files = {**sources, 'full_mat': mat_path, 'initial_json': initial_path, 'record_json': record_path}
    before = {key: digest(path) for key, path in files.items()}
    initial = json.loads(initial_path.read_text(encoding='utf-8'))
    record = json.loads(record_path.read_text(encoding='utf-8'))
    require(before['full_mat'] == record['full_payload_sha256'], 'Saved payload SHA mismatch')
    require(before['initial_json'] == record['initial_file_sha256'], 'Saved initial SHA mismatch')
    require(record['scheme'] == scheme and record['start'] == start, 'Record identity mismatch')
    settings = initial['settings']
    require(settings['number_of_starts'] == 6000 and settings['rcg_max_iterations'] == 4000
            and settings['rcg_gradient_tolerance'] == 1e-6, 'Original full controls changed')
    config, rebuilt_c, indices = ORACLE.geometry(settings, scheme)
    require(initial['model'] == config, 'Actual native Fig7 configuration changed')
    n, u = (1, 2) if scheme == 'MIS' else (0, 1)
    expected_dims = {'M': 2, 'N': n, 'U': u, 'K': 4, 'targets': 4}
    require(initial['actual_model_dimensions'] == expected_dims, 'Native model dimensions wrong')
    p = structure(loadmat(mat_path, struct_as_record=False, squeeze_me=False)['payload'])
    native_initial = structure(p.initial)
    dimensions = structure(native_initial.actual_model_dimensions)
    require({key: scalar(getattr(dimensions, key)) for key in expected_dims} == expected_dims,
            'JSON/MAT dimensions mismatch')
    stored = structure(native_initial.actual_steering_matrix)
    require(stored.real.shape == (4, 2) and stored.imag.shape == (4, 2), 'Actual C shape wrong')
    c = {'real': stored.real.tolist(), 'imag': stored.imag.tolist()}
    require(c == initial['actual_steering_matrix'], 'JSON/MAT actual C mismatch')
    coefficient_error = max(float(np.max(np.abs(np.asarray(c[key]) - np.asarray(rebuilt_c[key]))))
                            for key in ('real', 'imag'))
    require(coefficient_error <= 2e-15, 'Independent geometry vs actual C discrepancy')
    native_indices = native_initial.actual_indices_one_based
    require(native_indices.shape == (u, n), 'Actual indices shape wrong')
    require(native_indices.tolist() == [[i + 1 for i in row] for row in indices], 'Actual indices wrong')
    rng_before, rng_after, expected_initial = ORACLE.initial_input(settings, scheme, start)
    draw_count = 4 * u + 2 + n
    for key, truth in [('random_state_before', rng_before), ('random_state_after', rng_after),
                       ('random_draw_count', draw_count), ('start', start),
                       ('seed_offset', 0 if scheme == 'MIS' else 500000)]:
        require(initial[key] == truth and scalar(getattr(native_initial, key)) == truth, 'Actual RNG/start mismatch: ' + key)
    actual_initial = state(native_initial.state, n, u)
    # MATLAB serializes one scalar phase as a JSON number, not a one-item list;
    # only that named phase vector can be normalized here, with explicit n.
    for phase, length in [('phi', 2), ('theta', n)]:
        for key in ('real', 'imag'):
            raw = initial['state'][phase][key]
            normalized = [raw] if length == 1 and isinstance(raw, (int, float)) else raw
            require(normalized == actual_initial[phase][key], 'Actual initial MAT/JSON phase mismatch')
            require(max([abs(x - y) for x, y in zip(actual_initial[phase][key], expected_initial[phase][key])] or [0.]) <= 2e-15,
                    'Actual original initial phase generation mismatch')
    require(actual_initial['X'] == named_json_matrix(initial['state']['X'], 4, u), 'Actual initial X MAT/JSON mismatch')
    initial_x_error = float(np.max(np.abs(np.asarray(actual_initial['X']) - np.asarray(expected_initial['X']))))
    require(initial_x_error <= 2e-15, 'Actual original initial simplex generation mismatch')
    stages = cell(p.continuation_stages)
    histories = cell(p.full_history)
    mus = ORACLE.prescribed_mu(settings, start)
    require(len(stages) == len(histories) == len(mus) == record['actual_continuation_endpoint_count'], 'Actual stage count wrong')
    require(record['mu_values'] == mus, 'Actual mu sequence mismatch')
    receipts, all_pass = [], True
    for j, (raw_stage, raw_history, mu) in enumerate(zip(stages, histories, mus)):
        stage, history = structure(raw_stage), structure(raw_history)
        require(scalar(stage.stage_index) == j and scalar(stage.mu) == scalar(history.mu) == mu, 'Stage own-mu identity wrong')
        require(exact(stage.inner, history.inner) and exact(stage.stop, history.stop), 'Duplicate original full history mismatch')
        endpoint = state(stage.state, n, u)
        physical = ORACLE.physical(config, c, indices, endpoint, mu)
        stop = structure(stage.stop)
        reason = text(stop.reason)
        actual_norm = scalar(stop.projected_kkt_norm)
        actual_objective = scalar(stop.objective)
        norm_error = abs(physical['projected_kkt_norm'] - actual_norm)
        objective_error = abs(physical['objective'] - actual_objective)
        require(norm_error <= 5e-13, 'Independent own-state gradient discrepancy')
        require(objective_error <= 5e-12 + 5e-14 * abs(actual_objective), 'Independent own-state objective discrepancy')
        require(physical['domain_feasible'], 'Actual saved endpoint outside original domain')
        inner = cell(stage.inner)
        require(1 <= len(inner) <= 4000, 'Original recorded inner cap changed')
        for i, raw_entry in enumerate(inner):
            entry = structure(raw_entry)
            require(scalar(entry.iteration) == i, 'Original iteration numbering mismatch')
            for field in ('objective', 'gradient_norm', 'projected_kkt_norm'):
                scalar(getattr(entry, field))
        stop_truth = physical['unchanged_implemented_1e_minus6_gate_pass'] and reason == 'gradient_tolerance'
        all_pass = all_pass and stop_truth
        require(record['continuation_stops'][j]['reason'] == reason
                and record['continuation_stops'][j]['projected_kkt_norm'] == actual_norm,
                'JSON/MAT original stop mismatch')
        receipts.append({'stage_index': j, 'mu': mu, 'iterations_recorded': len(inner),
                         'actual_reason': reason, 'independent_physical': physical,
                         'saved_norm_abs_error': norm_error, 'saved_objective_abs_error': objective_error,
                         'original_true_gradient_stop': bool(stop_truth)})
    require(exact(stages[-1][0, 0].state, p.final_state), 'Last endpoint is not actual final state')
    last = receipts[-1]['independent_physical']
    metrics = structure(p.metrics)
    for key in ('min_relaxed_snr', 'min_binary_snr'):
        require(abs(last[key] - scalar(getattr(metrics, key))) <= 5e-14, 'Final physical metric mismatch')
        require(scalar(getattr(metrics, key)) == record['final_metrics'][key], 'Final metric MAT/JSON mismatch')
    require(metrics.binary_schedule.shape == (4, u)
            and metrics.binary_schedule.tolist() == last['binary_schedule'] == named_json_matrix(record['final_metrics']['binary_schedule'], 4, u),
            'Original first-argmax binary schedule mismatch')
    status = structure(p.solver_status)
    require(scalar(status.final_inner_tolerance) == 1e-6 and scalar(status.continuation_complete) == 1., 'Final stopping controls changed')
    source_stop = bool(scalar(status.convergence_verified))
    require(source_stop == record['final_solver_status']['convergence_verified'], 'Final status JSON/MAT mismatch')
    after = {key: digest(path) for key, path in files.items()}
    require(before == after, 'Frozen source/input/record mutated during audit')
    return {'scope': 'actual_native_one_full_start_each_own_mu_saved_endpoint_not_every_inner_state',
            'scheme': scheme, 'start': start, 'actual_endpoints_checked': len(stages),
            'actual_original_settings6000_4000_1e_minus6_retained': True,
            'all_independent_physical_consistency_and_domains_checked': True,
            'all_original_independent_true_gradient_stops_pass': bool(all_pass),
            'original_native_source_solver_stop_gate': source_stop,
            'all_required_one_start_gates_pass': bool(all_pass and source_stop),
            'actual_stored_C_used_not_substituted_with_reconstructed_C': True,
            'maximum_independent_geometry_C_abs_error': coefficient_error,
            'actual_original_rng_integer_identities_exact': True,
            'initial_X_abs_difference': initial_x_error,
            'actual_each_endpoint_evidence': receipts, 'before_after_hashes_identical': True,
            'actual_source_input_raw_sha256': before, 'every_inner_state_replayed': False,
            'all12000_population_or_historical_figure_certificate': False}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record-folder', required=True)
    parser.add_argument('--scheme', required=True, choices=['MIS', 'SMS'])
    parser.add_argument('--start', required=True, type=int)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError('Fresh evidence receipt required')
    try:
        result = audit_start(args.record_folder, args.scheme, args.start)
    except Exception as failure:
        result = {'scope': 'actual_native_saved_endpoint_audit_failure_retained', 'scheme': args.scheme,
                  'start': args.start, 'all_required_one_start_gates_pass': False,
                  'actual_exception_class': type(failure).__name__, 'actual_exception_message': str(failure),
                  'auditor_sha256': digest(Path(__file__))}
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        raise
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('actual_each_endpoint_evidence', 'actual_source_input_raw_sha256')}))
    if not result['all_required_one_start_gates_pass']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
