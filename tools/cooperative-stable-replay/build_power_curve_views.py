"""Bind two complete saved power or interference sweeps; never run a solver.

All 24 input slots and all eight schemes are required. Raw returns, including
their dispatcher label ``base`` and historical audit flags, remain untouched.
The small public state bank permits independent final-physics replay; full
phase/QT tapes remain bound by their original hashes in the local archive.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.io import loadmat

from audit_native_case import channel_data, sequence, sha
from audit_moment_draws import input_data


NAMES = ('AP-NoRIS', 'AP-AO', 'MR-S-NoRIS', 'MR-S-PA', 'MR-S-TS',
         'MR-TTS-NoRIS', 'MR-TTS-PA', 'MR-TTS-TS')
GATES = ('constraint_pass', 'convergence_pass', 'solver_primal_pass', 'qt_bound_pass')
SCOPES = {
    'power': (('power_kL20', 'power_kL0'), list(range(24)), [11, 13], [2, 3]),
    'interference': (('interference_kL20', 'interference_kL0'), list(range(24, 48)), [12, 12], [4, 5]),
}


def read(path):
    return json.loads(path.read_bytes())


def require(test, message):
    if not test:
        raise ValueError(message)


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def state_array(value, bank):
    if isinstance(value, dict) and 'recorded_array' in value:
        array = bank[value['recorded_array']]
        require(list(array.shape) == value['shape'] and array.dtype.str == value['dtype'],
                'Stored Python shape/dtype differs from the recording descriptor')
        return array.copy()
    return np.asarray(value)


def compact_point(point, identity):
    schemes = point['schemes']
    if isinstance(schemes, list):
        schemes = {s['scheme']: s for s in schemes}
    require(set(schemes) == set(NAMES), 'Exactly eight original schemes required')
    require(point['valid_figure_point'] is True and all(point[k] is True for k in GATES),
            'Failed/capped source slots cannot enter a successful complete curve')
    require(point['monte_carlo']['count'] == 1000, 'Configured 1000 moment draws required')
    scene = identity['full_reported_scene']
    require(scene[identity['parameter']] == identity['value'], 'Source axis differs from its exact configured scene')
    require(point['parameter'] in scene and point['value'] == scene[point['parameter']],
            'Raw dispatcher value differs from its exact configured scene')
    result = {k: copy.deepcopy(v) for k, v in point.items() if k != 'schemes'}
    result['raw_dispatcher_sweep'] = point['sweep']
    result['raw_dispatcher_parameter'] = point['parameter']
    result['raw_dispatcher_value'] = point['value']
    result['sweep'] = identity['sweep']
    result['parameter'] = identity['parameter']
    result['value'] = identity['value']
    result['source_case_ordinal'] = identity['ordinal']
    result['schemes'] = {}
    for name in NAMES:
        status = schemes[name]['status']
        require(status['converged'] is True, 'An original scheme did not converge')
        result['schemes'][name] = dict(evaluation=copy.deepcopy(schemes[name]['evaluation']),
            status={k: copy.deepcopy(status[k]) for k in
                    ('converged', 'termination', 'blocks', 'numerical', 'algorithm_success') if k in status})
    return result


def verify_limits(power, limit, identity):
    """Bind the plotted axis to actual numeric bounds, allowing8 rounding ulps.

    The allowance covers equivalent JSON/MAT exponent evaluation only. It is
    unrelated to solver, feasibility, gradient or physical-field tolerances.
    """
    scene = identity['full_reported_scene']
    power = np.asarray(power).reshape(-1); limit = np.asarray(limit).reshape(-1)
    expected_power = float(scene['power_w'])
    expected_limit = float(scene['interference_to_noise_ratio'] if 'interference_to_noise_ratio' in scene
                           else 10**(scene['interference_to_noise_db']/10))
    require(power.shape == (scene['J'],) and limit.shape == (scene['K'],), 'Stored original constraint dimensions differ')
    require(np.all(np.isfinite(power)) and np.all(np.isfinite(limit)), 'Nonfinite actual constraint bound')
    require(np.all(abs(power-expected_power) <= 8*abs(np.spacing(expected_power))) and
            np.all(abs(limit-expected_limit) <= 8*abs(np.spacing(expected_limit))),
            'Actual stored constraints differ from the source-index scene')
    return dict(source_power_w=expected_power, source_noise_normalized_interference=expected_limit,
                actual_power_and_interference_bounds_match=True, input_serialization_rounding_ulps=8)


def group_identity(data):
    h = hashlib.sha256()
    for name, value in sorted(data.items()):
        a = np.ascontiguousarray(value)
        h.update(name.encode()); h.update(a.dtype.str.encode())
        h.update(json.dumps(list(a.shape)).encode()); h.update(a.tobytes())
    return h.hexdigest()


def build(a):
    require(not a.output_dir.exists(), 'Preserve prior output; select a new directory')
    watched = {}

    def bound(path, expected=None):
        digest = sha(path)
        require(expected is None or digest == expected, 'Saved input/receipt hash differs: ' + path.name)
        watched[path] = digest
        return digest

    bound(a.case_index); bound(Path(__file__))
    scope = getattr(a, 'case_scope', 'power'); sweeps, ordinals, lengths, figures = SCOPES[scope]
    cases = [c for c in read(a.case_index)['cases'] if c['sweep'] in sweeps]
    require([c['ordinal'] for c in cases] == ordinals, 'Complete original two-sweep slots required')
    require([sum(c['sweep'] == s for c in cases) for s in sweeps] == lengths,
            'All original abscissas in both complete source sweeps required')
    followers = [read(p / 'progress.json') for p in (a.phase_dir, a.physics_dir, a.moment_dir)]
    records = [{r['ordinal']: r for r in d['records']} for d in followers]
    arrays, groups, states, provenance, comparisons = {}, {}, [], [], []
    views = {language: dict(paper_id='cooperative-satcom', language=language,
        scope=f'Two complete original-source {scope} sweeps, all24 slots and eight schemes; saved numerical returns',
        original_source_figures=figures,
        source_unchanged_during_run=True, results=[],
        source_case_index_sha256=sha(a.case_index),
        configured1000_draws_are_optimized_performance_MC=False,
        full183_or_original_curve_or_full_paper_pass=False) for language in ('python', 'matlab')}

    def save_group(language, data):
        digest = group_identity(data)
        key = language + '_' + digest
        if key not in groups:
            prefix = f'{language}_group_{sum(g["language"] == language for g in groups.values()):03d}'
            mapping = {}
            for name, value in data.items():
                arrays[prefix + '_' + name] = value.copy()
                mapping[name] = prefix + '_' + name
            groups[key] = dict(language=language, exact_binary_array_signature=digest, data=mapping)
        return key

    def save_state(language, ordinal, data, power, limit, final, evaluations, origin):
        identity = next(c for c in cases if c['ordinal'] == ordinal)
        numeric_binding = verify_limits(power, limit, identity)
        group = save_group(language, data)
        prefix = f'{language}_case_{ordinal:03d}'
        arrays[prefix + '_power_limit'] = np.asarray(power).reshape(-1).copy()
        arrays[prefix + '_interference_limit'] = np.asarray(limit).reshape(-1).copy()
        outputs = []
        for index, state in enumerate(final):
            name = state['scheme']; spec = dict(scheme=name, no_ris=bool(state['no_ris']))
            for key in ('phi', 'W', 'p'):
                if key in state and np.asarray(state[key]).size:
                    entry = f'{prefix}_scheme_{index}_{key}'
                    arrays[entry] = np.asarray(state[key]).copy(); spec[key] = entry
            spec['evaluation'] = copy.deepcopy(evaluations[name]['evaluation'])
            outputs.append(spec)
        require([s['scheme'] for s in outputs] == list(NAMES), 'Final state order differs')
        states.append(dict(language=language, ordinal=ordinal, input_group=group,
            power_limit=prefix + '_power_limit', interference_limit=prefix + '_interference_limit',
            final_states=outputs, original_sha256=origin, input_axis_binding=numeric_binding))

    for identity in cases:
        n = identity['ordinal']; old = a.python_bank / f'case-{n:03d}'
        configuration = old / 'configuration.json'
        bound(configuration, identity['configuration_sha256']); config = read(configuration)
        require(config['reported'] == identity['full_reported_scene'], 'Original reported scene differs')
        receipt_path = old / 'actual-point-receipt.json'; bound(receipt_path); receipt = read(receipt_path)
        require(receipt['case_identity'] == {k: identity[k] for k in ('ordinal', 'sweep', 'parameter', 'value')},
                'Original source case association differs')
        require(receipt['source_interval_pass'] and receipt['actual_complete_result_returned'] and
                receipt['actual_all_original_gates_pass'] and receipt['actual_independent_state_audit_pass'],
                'Historical Python gate was not verified; do not upgrade it')
        for filename, digest in receipt['actual_outputs_sha256'].items():
            bound(old / filename, digest)
        py = read(old / 'actual-result.json'); py_meta = read(old / 'actual-state.json')
        py_audit = read(old / 'actual-independent-audit.json')
        require(py_audit['all_independent_implemented_numerical_checks_pass'] is True,
                'Original independent Python audit failed')
        require(py['source_unchanged_during_run'] is True and py['configuration'] == config,
                'Saved Python sources/configuration changed')
        require(py_meta['actual_saved_array_bank_sha256'] == sha(old / 'actual-state.npz'),
                'Python array recording is not bound')
        native_path = a.native_bank / f'case-{n:03d}-matlab.json'; bound(native_path); native = read(native_path)
        require(native['source_unchanged_during_run'] is True and native['configuration'] == config,
                'Actual native configuration/source differs')
        tape = a.native_bank / native['state_recording']['filename']
        bound(tape, native['state_recording']['sha256'])
        row = [r[n] for r in records]; require(all(x['passed'] is True for x in row), 'Saved native audit failed')
        finite_path = a.finite_dir / f'case-{n:03d}-audit.json'; bound(finite_path, row[0]['finite_audit_sha256'])
        phase_path = Path(row[0]['MP_output']) / 'summary.json'; bound(phase_path, row[0]['MP_summary_sha256'])
        physics_path = a.first_physics if n == 0 else a.physics_dir / f'case-{n:03d}-MP-physics.json'
        bound(physics_path, row[1]['report_sha256']); phase = read(phase_path); physics = read(physics_path)
        require(phase['source_input_sha256']['result'] == sha(native_path) and
                phase['source_input_sha256']['states'] == sha(tape) and
                physics['source_input_sha256']['result'] == sha(native_path) and
                physics['source_input_sha256']['states'] == sha(tape), 'Native MP receipts use another input')
        require(phase['all_MP_fields_original_stop_and_precision_checks_pass'] and
                physics['all_physical_QT_and_precision_checks_pass'], 'Native MP gate failed')
        _, native_data, _, signature = input_data(native_path)
        require(row[2]['input_signature'] == signature and row[2]['result_sha256'] == sha(native_path),
                'Configured native MC group differs')
        group = followers[2]['group_reports'][signature]; moment_path = Path(group['report'])
        bound(moment_path, row[2]['group_audit_sha256']); moment = read(moment_path)
        require(moment['all_independent_checks_pass'] is True and moment['count'] == 1000,
                'Configured moment stream did not pass physical replay')
        require(all(c['passed'] for c in phase['phase_summaries']), 'Native phase endpoint failed')
        pypoint = compact_point(py['results'][0], identity)
        matpoint = compact_point(native['results'][0], identity)
        views['python']['results'].append(pypoint); views['matlab']['results'].append(matpoint)
        recording = loadmat(tape, simplify_cells=True)['recording']
        with np.load(old / 'actual-state.npz', allow_pickle=False) as bank:
            case = py_meta['cases'][0]
            py_data = {k: state_array(v, bank) for k, v in case['data'].items()}
            py_final = []
            for state in case['scheme_final_states']:
                item = dict(scheme=state['scheme'], no_ris=state['noRIS'], phi=state_array(state['phi'], bank))
                for source, dest in (('AP_W', 'W'), ('MR_p', 'p')):
                    if state.get(source) is not None:
                        item[dest] = state_array(state[source], bank)
                py_final.append(item)
            py_origin = {f: sha(old / f) for f in ('configuration.json', 'actual-result.json', 'actual-state.json',
                'actual-state.npz', 'actual-independent-audit.json', 'actual-point-receipt.json')}
            save_state('python', n, py_data, state_array(case['power_limits'], bank),
                       state_array(case['interference_limits'], bank), py_final, pypoint['schemes'], py_origin)
        native_origin = dict(configuration=sha(configuration), result=sha(native_path), states=sha(tape),
            finite=sha(finite_path), phase_MP=sha(phase_path), final_QT_MP=sha(physics_path), moment_MC=sha(moment_path))
        save_state('matlab', n, native_data, recording['input']['power_limit'],
                   recording['input']['interference_limit'], sequence(recording['final_states']),
                   matpoint['schemes'], native_origin)
        input_errors = {}
        require(set(native_data) == set(py_data) and len(py_data) == 11, 'All11 physical input arrays required')
        for key in sorted(py_data):
            x, y = native_data[key], py_data[key]
            require(x.shape == y.shape and np.isfinite(x).all() and np.isfinite(y).all(), 'Input shape/domain mismatch')
            error = x-y; norm = float(np.linalg.norm(y.reshape(-1)))
            input_errors[key] = dict(shape=list(x.shape), maximum_absolute_error=float(np.max(abs(error), initial=0)),
                relative_Frobenius_error=float(np.linalg.norm(error.reshape(-1))/norm) if norm else None,
                bitwise_equal=bool(x.dtype == y.dtype and x.tobytes() == y.tobytes()))
        metric_errors = []
        for name in NAMES:
            x = float(np.min(matpoint['schemes'][name]['evaluation']['sinr']))
            y = float(np.min(pypoint['schemes'][name]['evaluation']['sinr']))
            require(x > 0 and y > 0, 'Finite positive analytical minimum SINR required')
            metric_errors.append(dict(scheme=name, matlab=x, python=y, signed_linear_gap=x-y,
                absolute_linear_gap=abs(x-y), relative_gap_to_python=abs(x-y)/abs(y),
                signed_dB_gap=float(10*np.log10(x/y)),
                same_state_field_tolerance_would_pass=bool(abs(x-y) <= 1e-9 + 1e-10*abs(y))))
        comparisons.append(dict(ordinal=n, sweep=identity['sweep'], value=identity['value'],
            channel_inputs=input_errors, independently_optimized_minimum_SINR=metric_errors))
        provenance.append(dict(identity=identity, python=py_origin, matlab=native_origin,
            native_phase_MP_summary=phase, native_final_QT_MP_summary=dict(
                all_physical_QT_and_precision_checks_pass=True, QT_candidates=physics['QT_candidates'],
                scalar_values_per_precision=physics['scalar_values_per_precision'],
                maximum_MP80_MP100_difference=physics['maximum_MP80_MP100_difference']),
            native_moment_group_signature=signature, native_moment_count=1000,
            historical_Python_full_MP_and_full_paper_flags_unchanged=True))
    a.output_dir.mkdir(parents=True)
    np.savez_compressed(a.output_dir / 'final-states.npz', **arrays)
    write(a.output_dir / 'final-state-index.json', dict(scope='All24 slots x8 actual final states x2 languages; no inner trajectories',
        array_bank_sha256=sha(a.output_dir / 'final-states.npz'), groups=groups, cases=states,
        expected_cases_per_language=24, expected_schemes_per_case=8,
        expected_case_ordinals=ordinals, original_source_figures=figures, case_scope=scope,
        source_case_index_sha256=sha(a.case_index), full_phase_QT_tapes_publicly_included=False))
    write(a.output_dir / 'source-and-audit-bindings.json', dict(source_index_sha256=sha(a.case_index),
        historical_raw_outputs_modified=False, all24_slots_present=True, records=provenance))
    for language, view in views.items():
        write(a.output_dir / f'{language}-curve-view.json', view)
    flat = [x for r in comparisons for x in r['independently_optimized_minimum_SINR']]
    write(a.output_dir / 'dual-language-comparison.json', dict(scope='All24 paired physical inputs and192 independently optimized minimum-SINR pairs',
        same_configuration_all24=True, input_arrays_per_pair=11,
        maximum_absolute_linear_SINR_gap=max(x['absolute_linear_gap'] for x in flat),
        maximum_relative_SINR_gap=max(x['relative_gap_to_python'] for x in flat),
        maximum_absolute_dB_SINR_gap=max(abs(x['signed_dB_gap']) for x in flat),
        number_passing_same_state_field_tolerance=sum(x['same_state_field_tolerance_would_pass'] for x in flat),
        optimized_solution_equality_or_reference_agreement_certified=False,
        note='Same-state evaluation tolerance is reported diagnostically, not relaxed into an independently optimized solution-equivalence claim. MATLAB and Python convex backends and phase paths differ.',
        records=comparisons))
    strict = Path(__file__).resolve().parents[2] / 'strict'; sys.path.insert(0, str(strict))
    from render_satellite_figures import aggregate, render
    renderer = strict / 'render_satellite_figures.py'; bound(renderer)
    for language, view in views.items():
        for figure in figures:
            data = aggregate('cooperative-satcom', figure, [view])
            data.update(language=language, source_case_index_sha256=sha(a.case_index),
                curve_view_sha256=sha(a.output_dir / f'{language}-curve-view.json'), renderer_sha256=sha(renderer),
                configured1000_moment_draws_are_optimized_performance_MC=False)
            render(data, a.output_dir / language)
    for path, digest in watched.items():
        require(sha(path) == digest, 'An original input/source/audit changed while building: ' + path.name)
    write(a.output_dir / 'build-receipt.json', dict(all24_original_slots_and_all_eight_schemes=True,
        case_scope=scope, expected_case_ordinals=ordinals, original_source_figures=figures,
        source_case_index_sha256=sha(a.case_index), saved_input_and_audit_files_unchanged=True,
        builder_sha256=sha(Path(__file__)), solver_or_rng_calls=0,
        raw_saved_183_receipts_modified=False, native_phase_QT_and_configured_MC_receipts_checked=24,
        full183_or_original_curve_or_paper_pass=False,
        output_files_sha256={p.relative_to(a.output_dir).as_posix(): sha(p)
            for p in sorted(a.output_dir.rglob('*')) if p.is_file()}))
    print(json.dumps(dict(cases_per_language=24, schemes=8, original_figures=figures,
        maximum_absolute_linear_SINR_gap=max(x['absolute_linear_gap'] for x in flat),
        output=str(a.output_dir))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('case-index', 'python-bank', 'native-bank', 'phase-dir', 'finite-dir',
                 'physics-dir', 'first-physics', 'moment-dir', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--case-scope', choices=tuple(SCOPES), default='power')
    build(p.parse_args())
