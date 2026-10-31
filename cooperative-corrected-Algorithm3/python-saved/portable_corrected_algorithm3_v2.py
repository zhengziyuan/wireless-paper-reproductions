"""Isolated corrected Algorithm3 installation and explicit saved-input entry.

The validate/inspect-saved actions do not optimize or sample channels. The
saved-two-ts action requires --execute and retains all configured budgets.
Its six unaffected states and MC1000 result are saved reuse, not a full8 rerun.
No action constitutes an independent scientific acceptance or publication.
"""
import argparse
import ast
import copy
from datetime import datetime
import hashlib
import importlib
import importlib.metadata
import importlib.util
import io
import json
from pathlib import Path
import sys
import time

NAMES = ('AP-NoRIS', 'AP-AO', 'MR-S-NoRIS', 'MR-S-PA', 'MR-S-TS',
         'MR-TTS-NoRIS', 'MR-TTS-PA', 'MR-TTS-TS')
AFFECTED = ('MR-S-TS', 'MR-TTS-TS')
BASE_NAMES = ('core', 'models', 'positive_wick', 'increments', 'increments_v2',
              'algorithms', 'spectral_rmo', 'core_qt_factored_v3',
              'qt_numerical_guard_v3', 'termination', 'scenario', 'run',
              'receipts', 'run_cooperative_v3_configured')
FULL_CONTROLS = dict(monte_carlo_realizations=1000, qt_max_iterations=200,
                     ao_max_iterations=200, rmo_max_iterations=100000,
                     relative_tolerance=1e-4, gradient_tolerance=1e-6,
                     solver_objective_tolerance=1e-5,
                     solver_primal_relative_tolerance=1e-5,
                     qt_bound_tolerance=1e-5, smoothing_initial=1,
                     smoothing_final=0.001, smoothing_max_repeats=50,
                     smoothing_progress_tolerance=1e-8)


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fresh_json(path, value, default=None):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, allow_nan=False, default=default)
        handle.write('\n')


def load_module(path, name):
    need(name not in sys.modules, 'Fresh isolated module name required: ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fingerprint(value):
    import numpy as np
    x = np.ascontiguousarray(value)
    return dict(shape=list(x.shape), dtype=x.dtype.str,
                bytes_sha256=hashlib.sha256(x.tobytes()).hexdigest())


def check_source_root(source_root):
    """Validate the complete staged closure against the adapter's fixed pins."""
    source_root = Path(source_root).resolve(strict=True)
    pins_path = Path(__file__).with_name('expected_source_pins_v1.json')
    expected = json.loads(pins_path.read_bytes())
    declared = json.loads((source_root / 'source-manifest.json').read_bytes())
    need(declared['source_sha256'] == expected['source_sha256'],
         'Source-root declaration must match this versioned adapter closure')
    bindings = {}
    for relative, digest in expected['source_sha256'].items():
        path = (source_root / relative).resolve(strict=True)
        need(path.is_relative_to(source_root), 'Source member escaped source-root')
        need(sha(path) == digest, 'Frozen source differs: ' + relative)
        bindings[str(path)] = digest
    for path in (Path(__file__), pins_path, source_root / 'source-manifest.json',
                 Path(__file__).with_name('saved_input_shapes_v1.py')):
        bindings[str(path.resolve())] = sha(path)
    return source_root, bindings


def install_corrected(source_root, data_dir):
    """Call the original v3 installer, then replace only mr_two_stage AST.

    Exactly one installation per fresh process is supported. This function
    performs imports/installation, never an optimizer, model evaluation or RNG.
    """
    need(sys.dont_write_bytecode and not sys.flags.optimize,
         'Use python -B with assertions enabled')
    source_root, bindings = check_source_root(source_root)
    data_dir = Path(data_dir).resolve()
    need(data_dir.is_dir(), 'Create the explicit exclusive data-dir first')
    need(not data_dir.is_relative_to(source_root), 'Data must be outside source-root')
    need(not data_dir.is_relative_to(Path(__file__).resolve().parent),
         'Data must be outside the adapter source directory')
    need(not any(name in sys.modules for name in BASE_NAMES),
         'Use a fresh process; scientific generic module names are already loaded')
    base = source_root / 'base'
    sys.path.insert(0, str(base))
    entry = importlib.import_module('run_cooperative_v3_configured')
    alg = importlib.import_module('algorithms')
    ordinary = importlib.import_module('qt_numerical_guard_v3')
    entry._install_original_v3_controls()
    baseline = {name: value for name, value in vars(alg).items() if callable(value)}
    guard_path = source_root / 'correction/final_algorithm3_p7_guard_v1.py'
    guard = load_module(guard_path, '_portable_algorithm3_preamble_' + sha(guard_path)[:16])
    import numpy as np
    from scipy.io import savemat

    def save_fixture(kind, inputs):
        need(kind in ('mr', 'ap'), 'Known original QT fixture block required')
        keys = (('p0', 'signal', 'cross', 'power', 'leak', 'offset',
                 'power_limit', 'interference_limit') if kind == 'mr' else
                ('W0', 'mean', 'covariance', 'gt_second', 'offset',
                 'power_limit', 'interference_limit'))
        need(len(inputs) == len(keys), 'Complete unmodified QT fixture input required')
        digest = hashlib.sha256()
        fixture = {}
        for name, value in zip(keys, inputs):
            x = np.ascontiguousarray(value)
            digest.update(name.encode())
            digest.update(str(x.shape).encode())
            digest.update(x.dtype.str.encode())
            digest.update(x.tobytes())
            fixture[name] = value
        folder = data_dir / 'same-input-numerical-failure-fixtures'
        folder.mkdir(exist_ok=True)
        path = folder / ('v3-' + kind + '-QT-numerical-input-' + digest.hexdigest()[:16] + '.mat')
        sidecar = path.with_suffix('.json')
        if path.exists():
            existing = json.loads(sidecar.read_bytes())
            need(existing['input_sha256'] == digest.hexdigest()
                 and existing['sha256'] == sha(path), 'Preserve existing fixture identity')
        else:
            with path.open('xb') as handle:
                savemat(handle, fixture)
            fresh_json(sidecar, dict(input_sha256=digest.hexdigest(), sha256=sha(path)))
        return dict(filename=str(path.relative_to(data_dir)), sha256=sha(path),
                    input_sha256=digest.hexdigest())

    # Only fixture transport is replaced; both numerical solve_guard functions
    # and the original installer's full-loop AP/MR controls stay byte-identical.
    ordinary.save_fixture = save_fixture
    guard.save_fixture = save_fixture
    candidate = source_root / 'correction/algorithms_final_algorithm3_v2.py'
    tree = ast.parse(candidate.read_bytes())
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name == 'mr_two_stage']
    need(len(nodes) == 1, 'Exactly one frozen corrected function required')
    alg._final_algorithm3_P7_update = guard.mr_qt_update
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(candidate), 'exec'), alg.__dict__)
    untouched = {name: vars(alg).get(name) is value for name, value in baseline.items()
                 if name != 'mr_two_stage'}
    need(all(untouched.values()), 'Other installed scientific callback changed')
    need(alg.rmo_ascent is entry.rmo_ascent
         and alg.ap_increment is entry.ap_increment_v2
         and alg.mr_increment is entry.mr_increment_v2,
         'Preserve spectral RMO and v2 exact increment callbacks')
    need(alg.mr_qt_update is ordinary.mr_qt_update
         and alg.ap_qt_update is ordinary.ap_qt_update
         and alg._final_algorithm3_P7_update is guard.mr_qt_update,
         'Preserve separate complete-loop and preamble QT providers')
    loaded = {}
    for name in BASE_NAMES:
        if name in sys.modules:
            path = Path(sys.modules[name].__file__).resolve()
            need(path == (base / (name + '.py')).resolve(), 'Imported another source: ' + name)
            loaded[name] = str(path)
    helper = load_module(Path(__file__).with_name('saved_input_shapes_v1.py'),
                         '_portable_saved_input_shapes_v1')
    receipt = dict(source_root=str(source_root), data_dir=str(data_dir),
                   source_before=bindings, loaded_scientific_modules=loaded,
                   original_v3_installer_called=True, replaced_only_mr_two_stage=True,
                   untouched_installed_callables=untouched,
                   candidate_function_AST_sha256=hashlib.sha256(
                       ast.dump(nodes[0], include_attributes=False).encode()).hexdigest(),
                   both_fixture_writers_explicit_data_dir=True,
                   scientific_optimizer_calls=0, new_MC_draws=0,
                   independent_scientific_PASS=False)
    return dict(entry=entry, alg=alg, guard=guard, ordinary=ordinary, helper=helper,
                source_root=source_root, data_dir=data_dir, receipt=receipt,
                fixture_writer=save_fixture)


def check_source_interval(installation):
    before = installation['receipt']['source_before']
    after = {path: sha(path) for path in before}
    need(before == after, 'Adapter/scientific source bytes changed during action')
    return after


def read_saved_input(installation, result_path, expected_result_sha256):
    """Read one actual saved case; no coefficient/model/optimizer/RNG calls."""
    import numpy as np
    from scipy.io import loadmat
    result_path = Path(result_path).resolve(strict=True)
    raw = result_path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected_result_sha256,
         'Saved container must match explicitly supplied source receipt hash')
    result = json.loads(raw)
    spec = result['state_recording']
    matrix = (result_path.parent / spec['filename']).resolve(strict=True)
    need(matrix.is_relative_to(result_path.parent), 'Recording path escaped saved case')
    raw_matrix = matrix.read_bytes()
    need(hashlib.sha256(raw_matrix).hexdigest() == spec['sha256'],
         'Saved numerical recording identity differs')
    rec = loadmat(io.BytesIO(raw_matrix), simplify_cells=True)['recording']
    configuration = result['configuration']
    settings = configuration['tuned_not_reported']
    need(all(settings.get(key) == value for key, value in FULL_CONTROLS.items()),
         'Full frozen configured budgets/tolerances are required without reduction')
    need(settings['solver'] == 'CLARABEL' and isinstance(settings['solver_options'], dict),
         'Original configured CLARABEL solver/options required')
    need(settings['mr_QT_representation'].startswith(
        'sqrt(scale*v)=sqrt(scale)*sqrt(v), exact positive fixed-coordinate constant'),
        'Frozen original-QT representation required')
    reported = configuration['reported']
    J, U, N, M = (int(reported[key]) for key in ('J', 'U', 'N', 'M'))
    helper = installation['helper']
    data = helper.channel_data(rec['input']['data'], J, U, N, M)
    power = np.asarray(rec['input']['power_limit']).reshape(J)
    limit = np.asarray(rec['input']['interference_limit']).reshape(-1)
    final = helper.sequence(rec['final_states'])
    need([state['scheme'] for state in final] == list(NAMES), 'All eight saved final states required')
    need(len(result['results']) == 1, 'One explicit saved scenario only')
    old_schemes = helper.sequence(result['results'][0]['schemes'])
    need([state['scheme'] for state in old_schemes] == list(NAMES), 'All eight saved result rows required')
    need(result['results'][0]['monte_carlo']['count'] == 1000, 'Complete saved MC1000 result required')
    final_by_name = {state['scheme']: state for state in final}
    initial_phi = np.exp(1j * np.asarray(settings['initial_phase_radians']) * np.ones((U, M)))
    for prefix in ('MR-S', 'MR-TTS'):
        need(np.array_equal(np.asarray(final_by_name[prefix + '-NoRIS']['phi']).reshape(U, M), initial_phi),
             'Exact saved original initial phase and NoRIS initialization required')
        need(np.asarray(final_by_name[prefix + '-NoRIS']['p']).size == J * U,
             'Complete saved own NoRIS power initialization required')
    summary = dict(actual_saved_container=dict(path=str(result_path), sha256=expected_result_sha256),
                   actual_saved_recording=dict(path=str(matrix), sha256=spec['sha256']),
                   dimensions=dict(J=J, U=U, N=N, M=M),
                   full_controls={key: settings[key] for key in FULL_CONTROLS},
                   all_saved_state_names=list(NAMES),
                   saved_channel_operands={key: fingerprint(value) for key, value in data.items()},
                   power_limit=fingerprint(power), interference_limit=fingerprint(limit),
                   saved_own_NoRIS_powers={prefix: fingerprint(final_by_name[prefix + '-NoRIS']['p'])
                                          for prefix in ('MR-S', 'MR-TTS')},
                   original_MC1000_result_is_saved_reuse=True,
                   copied_saved_values_are_not_new_independent_verification=True,
                   new_optimizer_calls=0, new_MC_draws=0, independent_scientific_PASS=False)
    # Retain the exact two byte streams actually read and verified, not a later
    # re-read presented as an initial observation. These bytes stay in memory.
    return dict(result=result, recording=rec, data=data, power=power, limit=limit,
                settings=settings, dimensions=(J, U, N, M), initial_phi=initial_phi,
                final_by_name=final_by_name, old_schemes=old_schemes, summary=summary,
                input_snapshot={str(result_path): raw, str(matrix): raw_matrix})


def check_input_interval(saved):
    """Close only the two actual selected-case input streams; never scan a bank.

    Return failed observations instead of raising so CLI failure artifacts and
    action-summary are retained before the final nonzero exit.
    """
    if saved is None:
        return dict(applicable=False, checked_files=0, input_before={}, input_after={},
                    exact_input_bytes_unchanged=None, interval_pass=True)
    snapshot = saved['input_snapshot']
    need(len(snapshot) == 2, 'Exactly container plus actual recording required')
    before, after = {}, {}
    for filename, raw in snapshot.items():
        before[filename] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        try:
            observed = Path(filename).read_bytes()
            after[filename] = dict(sha256=hashlib.sha256(observed).hexdigest(),
                                   bytes=len(observed), exact_read_bytes_equal=(observed == raw))
        except Exception as error:
            after[filename] = dict(exact_read_bytes_equal=False,
                                   error_type=type(error).__name__, error=str(error))
    passed = all(row['exact_read_bytes_equal'] for row in after.values())
    return dict(applicable=True, checked_files=2, input_before=before, input_after=after,
                exact_input_bytes_unchanged=passed, interval_pass=passed)


def fixture_IO_selfcheck(installation):
    """Synthetic MAT transport only; never invoke either solve_guard."""
    import numpy as np
    from scipy.io import loadmat
    a = np.array([[-0.0, 1.25]], dtype=np.float64)
    b = np.array([[complex(1.0, -0.0), complex(-2.0, 3.0)]], dtype=np.complex128)
    outputs = []
    for module, kind, values in ((installation['ordinary'], 'ap', (b,) + (a,) * 6),
                                (installation['ordinary'], 'mr', (a,) * 8),
                                (installation['guard'], 'mr', (a,) * 8)):
        meta = module.save_fixture(kind, values)
        path = installation['data_dir'] / meta['filename']
        readback = loadmat(path)
        fields = (('W0', 'mean', 'covariance', 'gt_second', 'offset', 'power_limit', 'interference_limit')
                  if kind == 'ap' else ('p0', 'signal', 'cross', 'power', 'leak', 'offset', 'power_limit', 'interference_limit'))
        exact = all(fingerprint(readback[key]) == fingerprint(value) for key, value in zip(fields, values))
        need(exact and sha(path) == meta['sha256'], 'Fixture IEEE bytes/dtype/shape readback failed')
        outputs.append(dict(kind=kind, provider=module.__name__, metadata=meta,
                            raw_value_dtype_shape_and_signed_zero_exact=exact))
    return dict(pure_IO_only=True, fixtures=outputs, actual_solver_calls=0,
                independent_scientific_PASS=False)


def run_saved_two_ts(installation, saved):
    """Explicit full two-TS call, with original saved-input recording semantics.

    This function is prepared but must not be confused with an audited run.
    Independent own-state/QT/phase/MC provenance checks remain downstream.
    """
    import numpy as np
    from scipy.io import savemat
    alg, entry = installation['alg'], installation['entry']
    data, power, limit, settings = (saved[key] for key in ('data', 'power', 'limit', 'settings'))
    J, U, N, M = saved['dimensions']
    initial_phi = saved['initial_phi']
    final_by_name = copy.deepcopy(saved['final_by_name'])
    schemes = {row['scheme']: {key: copy.deepcopy(value) for key, value in row.items() if key != 'scheme'}
               for row in saved['old_schemes']}
    tape = dict(input=copy.deepcopy(saved['recording']['input']), final_states=[], phase_endpoints=[], QT_candidates=[])
    preamble_indices = []

    def cells(values):
        x = np.empty((1, len(values)), dtype=object)
        for k, value in enumerate(values):
            x[0, k] = value
        return x

    def record_qt(function, is_preamble):
        def call(*args, **kwargs):
            candidate, info = function(*args, **kwargs)
            if is_preamble:
                preamble_indices.append(len(tape['QT_candidates']))
            keep = {key: info[key] for key in ('before', 'after', 'surrogate_minimum_sinr', 'solver_status', 'qt_bound_max_violation', 'qt_tightness_error')}
            tape['QT_candidates'].append(copy.deepcopy(dict(kind='mr_qt_update', input=cells(args[:8]), candidate=candidate, info=keep)))
            return candidate, info
        return call

    alg.mr_qt_update = record_qt(alg.mr_qt_update, False)
    alg._final_algorithm3_P7_update = record_qt(installation['guard'].mr_qt_update, True)
    runtime_call_observer = dict(full_TS_entries=0, final_mr_power_by_TS={}, forbidden_attempts={})
    active_TS = None

    def forbidden(name):
        def call(*args, **kwargs):
            counts = runtime_call_observer['forbidden_attempts']
            counts[name] = counts.get(name, 0) + 1
            raise RuntimeError('Unrelated computation forbidden in saved two-TS entry: ' + name)
        return call

    alg.ap_no_ris = forbidden('AP-NoRIS')
    alg.ap_ao = forbidden('AP-AO')
    alg.mr_initial = forbidden('new_NoRIS_power_initialization')
    entry.original.full_run = forbidden('new_full8_runner')
    entry.original.make_scenario = forbidden('scenario_generation')
    entry.original.sample_effective = forbidden('new_effective_channel_draw')
    import scenario as scenario_module
    import models as models_module
    scenario_module.make_scenario = forbidden('scenario_generation_direct')
    models_module.sample_effective = forbidden('new_effective_channel_draw_direct')
    original_final_power = alg.mr_power

    def observed_final_power(*args, **kwargs):
        need(active_TS in AFFECTED, 'No NoRIS/PA power optimizer entry')
        counts = runtime_call_observer['final_mr_power_by_TS']
        counts[active_TS] = counts.get(active_TS, 0) + 1
        need(counts[active_TS] == 1, 'Exactly one complete final power call per TS')
        return original_final_power(*args, **kwargs)

    alg.mr_power = observed_final_power
    original_rmo = alg.rmo_ascent

    def rmo(phi, value_gradient, max_iterations, gradient_tolerance, vector_objective=False, status=None, increment=None):
        answer = original_rmo(phi, value_gradient, max_iterations, gradient_tolerance, vector_objective, status, increment)
        closure = {key: value.cell_contents for key, value in zip(value_gradient.__code__.co_freevars, value_gradient.__closure__ or ())}
        need(not vector_objective, 'No AP phase optimizer is rerun')
        context = dict(data=closure['data'], p0=closure['p0'], mu=closure['mu'], interferenceLimit=closure['interference_limit'], tts=closure['tts'])
        value, gradient = value_gradient(answer[0])
        tape['phase_endpoints'].append(copy.deepcopy(dict(context=context, final_phi=answer[0], gradient=gradient, value=value, vector_objective=False, original_stop=status or {})))
        return answer

    alg.rmo_ascent = rmo
    output = installation['data_dir']
    fresh_json(output / 'execution-start.json', dict(
        observed_local=datetime.now().astimezone().isoformat(), source_before=installation['receipt']['source_before'],
        actual_saved_inputs=saved['summary'], actual_only_these_two_chains_executed=list(AFFECTED),
        unaffected_six_and_MC1000_are_explicit_saved_reuse=True, independent_scientific_PASS=False))
    started = time.perf_counter()
    completed = []
    error = None
    try:
        for tts,prefix in ((False,'MR-S'),(True,'MR-TTS')):
            p0=np.asarray(final_by_name[prefix+'-NoRIS']['p']).reshape(J,U).copy()
            active_TS=prefix+'-TS';runtime_call_observer['full_TS_entries']+=1
            status={};phi,p,history=alg.mr_two_stage(data,initial_phi,p0,power,limit,settings,tts,status)
            active_TS=None
            coef=alg.mr_components(data,phi,tts)
            schemes[prefix+'-TS']=dict(evaluation=alg.mr_evaluate(p,*coef[:5]),history=history,status=status)
            final_by_name[prefix+'-TS']=dict(scheme=prefix+'-TS',p=p.copy(),phi=phi.copy(),no_ris=False)
            completed.append(prefix+'-TS')
    except BaseException as exc:
        error = exc
    finally:
        tape['final_states'] = [copy.deepcopy(final_by_name[name]) for name in NAMES]
        recording = {**tape, 'final_states': cells(tape['final_states']),
                     'phase_endpoints': cells(tape['phase_endpoints']), 'QT_candidates': cells(tape['QT_candidates'])}
        actual_matrix = output / ('partial-actual-two-TS-recording.mat' if error else 'actual-two-TS-recording.mat')
        with actual_matrix.open('xb') as handle:
            savemat(handle, dict(recording=recording), do_compression=True, long_field_names=True)
        try:
            source_after = check_source_interval(installation)
        except BaseException as interval_error:
            if error is None:
                error = interval_error
            source_after = None
        if error is not None:
            fresh_json(output / 'execution-error.json', dict(
                error_type=type(error).__name__, message=str(error), failure_receipt=getattr(error, 'receipt', None),
                completed_new_chains=completed, actual_runtime_call_observer=runtime_call_observer,
                partial_states_sha256=sha(actual_matrix), source_after=source_after,
                failed_outcomes_retained=True, independent_scientific_PASS=False), default=entry.original.numerical_json)
    if error is not None:
        raise error
    need(len(completed) == 2 and len(preamble_indices) == 2, 'Both full corrected TS chains required')
    need(runtime_call_observer == dict(full_TS_entries=2, final_mr_power_by_TS={name: 1 for name in AFFECTED}, forbidden_attempts={}),
         'Exact two final powers and no unrelated computation required')
    violations = []
    for item in schemes.values():
        value = item['evaluation']
        violations.extend(np.asarray(value['satellite_power']) - power)
        violations.extend(np.asarray(value['gt_interference']) - limit)
    point = copy.deepcopy(saved['result']['results'][0])
    point.update(schemes=[dict(scheme=name, **schemes[name]) for name in NAMES],
                 constraint_pass=bool(max(violations) < settings['solver_objective_tolerance']),
                 convergence_pass=all(s['status']['converged'] and s['status'].get('phase_source_converged', True) for s in schemes.values()),
                 solver_primal_pass=all(s['status']['numerical']['solver_primal_pass'] for s in schemes.values()),
                 qt_bound_pass=all(s['status']['numerical']['qt_bound_pass'] for s in schemes.values()))
    checks = {key: point[key] for key in ('constraint_pass', 'convergence_pass', 'solver_primal_pass', 'qt_bound_pass')}
    point.update(valid_figure_point=all(checks.values()), status='executed_corrected_two_TS_with_six_unchanged_chains_reused')
    composite = dict(scope='Two full corrected TS chains plus six explicit saved states and MC1000; no full8 rerun',
                     language='python', configuration=copy.deepcopy(saved['result']['configuration']), results=[point],
                     checks=checks, overall_implemented_scope_success=all(checks.values()), source_unchanged_during_run=True,
                     state_recording=dict(filename=actual_matrix.name, sha256=sha(actual_matrix), final_scheme_states=8,
                                          phase_endpoints=len(tape['phase_endpoints']), QT_candidates=len(tape['QT_candidates'])),
                     exact_reuse_provenance=dict(original_result_container=saved['summary']['actual_saved_container']['path'],
                         original_result_SHA256=saved['summary']['actual_saved_container']['sha256'],
                         unaffected_schemes=[name for name in NAMES if name not in AFFECTED],
                         configured1000_moment_result_copied_without_new_draws=True,
                         original_saved_recording=saved['summary']['actual_saved_recording']),
                     actual_new_Algorithm3_preamble_QT_indices=preamble_indices, actual_runtime_call_observer=runtime_call_observer,
                     source_before=installation['receipt']['source_before'], source_after=source_after,
                     source_corrected_chain_independent_review_pending=True, independent_scientific_PASS=False,
                     full183_or_reference_or_paper_PASS=False)
    target = output / 'case-python-corrected-two-TS-recorded.json'
    fresh_json(target, composite, default=entry.original.numerical_json)
    fresh_json(output / 'execution-summary.json', dict(result_sha256=sha(target), states_sha256=sha(actual_matrix),
               elapsed_seconds=time.perf_counter() - started, internal_checks=checks,
               independent_scientific_PASS=False, actual_new_MC_draws=0))
    return composite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'inspect-saved', 'saved-two-ts'))
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--saved-result', type=Path)
    parser.add_argument('--saved-result-sha256')
    parser.add_argument('--fixture-io-check', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    need((args.action == 'saved-two-ts') == args.execute,
         '--execute belongs exclusively to explicit saved-two-ts action')
    need((args.saved_result is None) == (args.saved_result_sha256 is None), 'Supply both saved input path and expected receipt SHA256')
    need(args.action == 'validate' or args.saved_result is not None, 'An explicit saved result identity is required')
    source_root, _ = check_source_root(args.source_root)
    output = args.data_dir.resolve()
    need(not output.is_relative_to(source_root) and not output.is_relative_to(Path(__file__).resolve().parent),
         'Explicit data-dir must be outside code roots')
    output.mkdir(parents=True, exist_ok=False)
    installation = None
    saved = None
    failure = None
    result = None
    internal_checks = None
    internal_pass = None
    try:
        installation = install_corrected(source_root, output)
        fresh_json(output / 'installation-source-receipt.json', installation['receipt'])
        if args.saved_result is not None:
            saved = read_saved_input(installation, args.saved_result, args.saved_result_sha256)
            fresh_json(output / 'saved-input-readonly-inspection.json', saved['summary'])
        if args.fixture_io_check:
            need(args.action != 'saved-two-ts', 'Synthetic fixture IO check is a separate control-only action')
            fresh_json(output / 'pure-IO-fixture-readback.json', fixture_IO_selfcheck(installation))
        if args.action == 'saved-two-ts':
            result = run_saved_two_ts(installation, saved)
            internal_checks = result['checks']
            need(set(internal_checks) == {'constraint_pass', 'convergence_pass', 'solver_primal_pass', 'qt_bound_pass'},
                 'All four original internal checks must be present')
            internal_pass = all(bool(value) for value in internal_checks.values())
    except BaseException as error:
        failure = dict(error_type=type(error).__name__, message=str(error),
                       failure_receipt=getattr(error, 'receipt', None))
    # Result/partial MAT and failure files from the numerical function are never
    # replaced. Close the two real inputs after all work and export completes.
    input_interval = check_input_interval(saved)
    source_after = None
    source_pass = False
    try:
        if installation is not None:
            source_after = check_source_interval(installation)
            source_pass = True
    except BaseException as error:
        if failure is None:
            failure = dict(error_type=type(error).__name__, message=str(error))
    exit_code = (2 if failure is not None or not source_pass or not input_interval['interval_pass']
                 else 1 if internal_pass is False else 0)
    artifacts = {}
    for name in ('case-python-corrected-two-TS-recorded.json', 'actual-two-TS-recording.mat',
                 'partial-actual-two-TS-recording.mat', 'execution-start.json',
                 'execution-error.json', 'execution-summary.json'):
        path = output / name
        if path.is_file():
            artifacts[name] = dict(sha256=sha(path), bytes=path.stat().st_size)
    summary = dict(action=args.action, internal_checks=internal_checks,
                   all_internal_checks_pass=internal_pass, source_after=source_after,
                   source_interval_pass=source_pass, actual_input_interval=input_interval,
                   retained_execution_artifacts=artifacts, failure_retained=failure,
                   CLI_exit_code=exit_code, independent_scientific_PASS=False,
                   observed_local=datetime.now().astimezone().isoformat())
    if args.action != 'saved-two-ts':
        summary.update(actual_optimizer_calls=0, new_MC_draws=0,
                       imports_installation_and_saved_IO_only=True)
    default = installation['entry'].original.numerical_json if installation is not None else None
    fresh_json(output / 'action-summary.json', summary, default=default)
    print(json.dumps(dict(action=args.action, source_interval_pass=source_pass,
                          input_interval_pass=input_interval['interval_pass'],
                          internal_checks_pass=internal_pass, CLI_exit_code=exit_code,
                          independent_scientific_PASS=False)), flush=True)
    if exit_code:
        raise SystemExit(exit_code)
    return summary


if __name__ == '__main__':
    main()
