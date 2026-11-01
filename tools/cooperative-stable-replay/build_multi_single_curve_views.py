"""Bind exactly the72 original multi/single source slots after all readers close.

Reuses the unchanged compact-state binder and its complete eight-scheme gates.
The two original scenes have different satellite-power field lengths. Figure11
contains144 original source ordinates per language, while the full state bank
contains1152 endpoints. Source W versus normalized I/N remains unresolved.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

import build_power_curve_views as core
from audit_native_case import sha, sequence
from audit_moment_draws import input_data
from scipy.io import loadmat
from build_power_curve_views import NAMES, compact_point, group_identity, verify_limits
from build_power_curve_views import read, require, write


SCOPES = {'multi-single': (
    ('multi_vs_single_multi_kL0', 'multi_vs_single_single_1.25_kL0',
     'multi_vs_single_single_2.5_kL0', 'multi_vs_single_multi_kL20',
     'multi_vs_single_single_1.25_kL20', 'multi_vs_single_single_2.5_kL20'),
    list(range(111, 183)), [12] * 6, [11])}


def source_scenes(case_index):
    _, ordinals, _, _ = SCOPES['multi-single']
    cases = [c for c in read(case_index)['cases'] if c['ordinal'] in ordinals]
    require([c['ordinal'] for c in cases] == ordinals, 'All72 exact original source slots required')
    sweeps = SCOPES['multi-single'][0]
    for i, sweep in enumerate(sweeps):
        cohort = cases[12 * i:12 * (i + 1)]
        require(all(c['sweep'] == sweep for c in cohort) and
                [c['value'] for c in cohort] == [j / 100 for j in range(1, 13)],
                'Each exact original12-point cohort is required')
        for c in cohort:
            s = c['full_reported_scene']
            expected = (3, 2, 16, 25, 1, 50.) if i in (0, 3) else (1, 2, 48, 25, 1, 150.)
            require(tuple(s[k] for k in ('J', 'U', 'N', 'M', 'K', 'power_w')) == expected,
                    'Only the two exact original satellite/antenna/power scenes are allowed')
    require(sum(c['full_reported_scene']['J'] == 3 for c in cases) == 24,
            'The original24 multi and48 single cases must be retained')
    return cases


def native_configuration_transport(actual, expected, identity):
    """Only the exact MATLAB singleton-latitude scalar/list representation."""
    if actual == expected:
        return dict(raw_configuration_equals_original=True, exact_singleton_mapping_applied=False,
                    every_numeric_value_unchanged=True, original_result_modified=False)
    scene = identity['full_reported_scene']
    require((scene['J'], scene['N']) == (1,48), 'Only an original single-satellite scene may use this transport')
    raw = actual['tuned_not_reported']['satellite_latitudes_deg']
    wanted = expected['tuned_not_reported']['satellite_latitudes_deg']
    require(type(raw) in (int,float) and np.isfinite(raw) and isinstance(wanted,list) and len(wanted)==1 and
            raw==wanted[0], 'Only the identical finite singleton latitude value is admissible')
    canonical = copy.deepcopy(actual)
    canonical['tuned_not_reported']['satellite_latitudes_deg'] = [raw]
    require(canonical==expected, 'Any additional configuration difference remains an error')
    return dict(raw_configuration_equals_original=False, exact_singleton_mapping_applied=True,
        original_field='tuned_not_reported.satellite_latitudes_deg', raw_scalar=raw, expected_singleton=wanted,
        every_numeric_value_unchanged=True, all_other_fields_equal_without_mapping=True,
        original_result_modified=False)


def bind_complete_pairs(a):
    require(not a.output_dir.exists(), 'Preserve prior output; select a new directory')
    watched = {}

    def bound(path, expected=None):
        digest = sha(path)
        require(expected is None or digest == expected, 'Saved input/receipt hash differs: ' + path.name)
        watched[path] = digest
        return digest

    bound(a.case_index); bound(Path(__file__)); bound(Path(core.__file__))
    scope = getattr(a, 'case_scope', 'multi-single'); sweeps, ordinals, lengths, figures = SCOPES[scope]
    count = len(ordinals)
    cases = [c for c in read(a.case_index)['cases'] if c['sweep'] in sweeps]
    require([c['ordinal'] for c in cases] == ordinals, 'Every exact original cohort slot required')
    require([sum(c['sweep'] == s for c in cases) for s in sweeps] == lengths,
            'All original abscissas in every complete source sweep required')
    followers = [read(p / 'progress.json') for p in (a.phase_dir, a.physics_dir, a.moment_dir)]
    records = [{r['ordinal']: r for r in d['records']} for d in followers]
    arrays, groups, states, provenance, comparisons = {}, {}, [], [], []
    views = {language: dict(paper_id='cooperative-satcom', language=language,
        scope=f'{len(sweeps)} complete original-source {scope} sweeps, all{count} slots and eight schemes; saved numerical returns',
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
        from select_python_curve_case import select
        bound(Path(__file__).with_name('select_python_curve_case.py'))
        config, py, py_data, py_final, py_power, py_limit, py_origin, py_selection = select(
            identity, old, getattr(a, 'repaired_python_root', None), bound)
        native_path = a.native_bank / f'case-{n:03d}-matlab.json'; bound(native_path); native = read(native_path)
        configuration_transport = native_configuration_transport(native['configuration'], config, identity)
        require(native['source_unchanged_during_run'] is True,
                'Actual native source differs')
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
        save_state('python', n, py_data, py_power, py_limit, py_final, pypoint['schemes'], py_origin)
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
            native_configuration_transport=configuration_transport,
            Python_saved_epoch_selection=py_selection,
            native_phase_MP_summary=phase, native_final_QT_MP_summary=dict(
                all_physical_QT_and_precision_checks_pass=True, QT_candidates=physics['QT_candidates'],
                scalar_values_per_precision=physics['scalar_values_per_precision'],
                maximum_MP80_MP100_difference=physics['maximum_MP80_MP100_difference']),
            native_moment_group_signature=signature, native_moment_count=1000,
            historical_Python_full_MP_and_full_paper_flags_unchanged=True))
    a.output_dir.mkdir(parents=True)
    np.savez_compressed(a.output_dir / 'final-states.npz', **arrays)
    write(a.output_dir / 'final-state-index.json', dict(scope=f'All{count} slots x8 actual final states x2 languages; no inner trajectories',
        array_bank_sha256=sha(a.output_dir / 'final-states.npz'), groups=groups, cases=states,
        expected_cases_per_language=count, expected_schemes_per_case=8,
        expected_case_ordinals=ordinals, original_source_figures=figures, case_scope=scope,
        source_case_index_sha256=sha(a.case_index), full_phase_QT_tapes_publicly_included=False))
    write(a.output_dir / 'source-and-audit-bindings.json', dict(source_index_sha256=sha(a.case_index),
        historical_raw_outputs_modified=False, all_original_slots_present=True, original_slots=count, records=provenance))
    for language, view in views.items():
        write(a.output_dir / f'{language}-curve-view.json', view)
    flat = [x for r in comparisons for x in r['independently_optimized_minimum_SINR']]
    write(a.output_dir / 'dual-language-comparison.json', dict(scope=f'All{count} paired physical inputs and{count*8} independently optimized minimum-SINR pairs',
        same_configuration_every_original_slot=True, original_slots=count, input_arrays_per_pair=11,
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
    write(a.output_dir / 'build-receipt.json', dict(all24_original_slots_and_all_eight_schemes=count==24,
        all_original_slots_and_all_eight_schemes=True, cases_per_language=count,
        case_scope=scope, expected_case_ordinals=ordinals, original_source_figures=figures,
        source_case_index_sha256=sha(a.case_index), saved_input_and_audit_files_unchanged=True,
        builder_sha256=sha(Path(__file__)), solver_or_rng_calls=0,
        raw_saved_183_receipts_modified=False, native_phase_QT_and_configured_MC_receipts_checked=count,
        explicitly_selected_repaired_Python_case_ordinals=[n for n in ordinals if n in (56,65)],
        full183_or_original_curve_or_paper_pass=False,
        output_files_sha256={p.relative_to(a.output_dir).as_posix(): sha(p)
            for p in sorted(a.output_dir.rglob('*')) if p.is_file()}))
    print(json.dumps(dict(cases_per_language=count, schemes=8, original_figures=figures,
        maximum_absolute_linear_SINR_gap=max(x['absolute_linear_gap'] for x in flat),
        output=str(a.output_dir))))


def build(args):
    require(not args.output_dir.exists(), 'Preserve previous output')
    require(args.case_scope == 'multi-single', 'Only the complete original72 source scope is supported')
    before = {str(p): sha(p) for p in (Path(__file__), args.case_index, Path(core.__file__))}
    cases = source_scenes(args.case_index)
    for root in (args.phase_dir, args.physics_dir, args.moment_dir):
        records = {r['ordinal']: r for r in read(root / 'progress.json')['records']}
        require(all(c['ordinal'] in records and records[c['ordinal']]['passed'] is True for c in cases),
                'Wait for every native phase/physics/configured-moment receipt; partial cases cannot form a figure')
    bind_complete_pairs(args)
    index = read(args.output_dir / 'final-state-index.json')
    total_fields = 0
    with np.load(args.output_dir / 'final-states.npz', allow_pickle=False) as arrays:
        for case in index['cases']:
            group = index['groups'][case['input_group']]['data']
            J, U, N = arrays[group['d_mean']].shape
            M = arrays[group['r_mean']].shape[1]
            require((J, U, N, M) in ((3, 2, 16, 25), (1, 2, 48, 25)), 'Actual binary scene differs')
            power = arrays[case['power_limit']].reshape(-1)
            require(J * N == 48 and float(np.sum(power)) == 150., 'Actual total antenna/power fairness differs')
            total_fields += 8 * (2 * U + J + 1)
    provenance = read(args.output_dir / 'source-and-audit-bindings.json')['records']
    transported = [p['native_configuration_transport'] for p in provenance]
    require(all(p['every_numeric_value_unchanged'] and not p['original_result_modified'] for p in transported),
            'Configuration transport may never alter source values or original files')
    singleton_count = sum(p['exact_singleton_mapping_applied'] for p in transported)
    require(len(index['cases']) == 144 and total_fields == 7680,
            'All1152 final states and both J1/J3 field lengths are required')
    require(all(sha(Path(p)) == h for p, h in before.items()), 'Builder/source identity changed')
    write(args.output_dir / 'multi-single-scene-binding.json', dict(
        exact_original_case_ordinals=list(range(111, 183)), original_source_figures=[11],
        cases_per_language=72, actual_final_states_per_precision=1152,
        physical_scalar_fields_per_precision=7680,
        source_reference_ordinates_per_language=144,
        source_reference_ordinate_count_is_72_times8=False,
        all_actual_scenes_have48_total_antennas_and150W=True,
        exact_singleton_latitude_metadata_transports=singleton_count,
        original_native_JSON_or_recorded_arrays_modified=False,
        exact_allowed_J_U_N_M=[[3, 2, 16, 25], [1, 2, 48, 25]],
        original_six_cohort_12point_grids_preserved=True, source_input_SHA256=before,
        source_W_versus_normalized_I_over_N_conflict_unresolved=True,
        original_reference_or_full183_or_full_paper_pass=False, optimizer_or_RNG_calls=0))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('case-index', 'python-bank', 'native-bank', 'phase-dir', 'finite-dir',
                 'physics-dir', 'first-physics', 'moment-dir', 'output-dir'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--case-scope', choices=tuple(SCOPES), default='multi-single')
    p.add_argument('--repaired-python-root', type=Path)
    build(p.parse_args())
