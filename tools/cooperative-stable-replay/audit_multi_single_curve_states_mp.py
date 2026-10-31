"""Independent MP80/100 physics for exactly72 complete multi/single source pairs.

Consumes the compact real final-state bank, never an optimizer or RNG. Phase
stops and all inner QT candidates retain their separate original audit scope.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time

import mpmath as mp
import numpy as np

from audit_native_case import sha
from audit_native_physics_mp import FIELDS, compare, constraints
from build_power_curve_views import NAMES, read, require, verify_limits, write
from build_multi_single_curve_views import SCOPES, source_scenes
import mp_phase_reference as ref


def restore_native_singleton_design(value, kind, J, U, N, language):
    """Restore only MATLAB's documented J=1 leading-axis squeeze, losslessly."""
    require(kind in ('W', 'p'), 'Known actual design field required')
    expected = (J, N, U) if kind == 'W' else (J, U)
    require(np.issubdtype(value.dtype, np.number) and np.isfinite(value).all(),
            'Finite numeric actual design required')
    if value.shape == expected:
        return value, None
    squeezed = (N, U) if kind == 'W' else (U,)
    require(language == 'matlab' and (J, U, N) == (1, 2, 48) and value.shape == squeezed,
            'Only the exact native single-satellite leading-axis transport may be restored')
    before = value.tobytes(order='C'); dtype = value.dtype.str
    restored = value.reshape(expected, order='C')
    require(restored.dtype.str == dtype and restored.tobytes(order='C') == before,
            'Native singleton restoration must preserve every original dtype and numeric byte')
    return restored, dict(field=kind, original_transport_shape=list(value.shape),
        restored_logical_shape=list(expected), dtype=dtype,
        original_and_restored_C_bytes_SHA256=hashlib.sha256(before).hexdigest(),
        original_numeric_dtype_and_C_bytes_unchanged=True)


def physical(data, phi, p, W, limit, name):
    J, U, N = data['d_mean'].shape
    ctx = ref.FixedContext(data, phi, p, 1., limit, name.startswith('MR-TTS'))
    if name.startswith('AP'):
        w = [[ref.vector(W[j, :, u]) for u in range(U)] for j in range(J)]
        amp = [[ref.dot(ctx.mean[j][u], w[j][u]) for u in range(U)] for j in range(J)]
        den = [ctx.geo_constant[u] + abs(ctx.geo_mean[u])**2 + mp.fsum(
            ref.quad(w[j][i], ctx.C[j][u]) + (abs(ref.dot(ctx.mean[j][u], w[j][i]))**2 if i != u else 0)
            for j in range(J) for i in range(U)) for u in range(U)]
        return dict(sinr=[mp.fsum(abs(amp[j][u])**2 for j in range(J))/den[u] for u in range(U)],
            denominator=den, satellite_power=[mp.fsum(ref.norm2(w[j][i]) for i in range(U)) for j in range(J)],
            gt_interference=[mp.fsum(ref.quad(w[j][i], ctx.gt[j][k]) for j in range(J) for i in range(U))
                             for k in range(data['gt_second'].shape[1])])
    _, _, den, sinr, _, residual, power = ctx.objective(details=True)
    return dict(sinr=sinr, denominator=den,
        satellite_power=[mp.fsum(ref.real(p[j, u])*power[j][u] for u in range(U)) for j in range(J)],
        gt_interference=[a + ref.real(b) for a, b in zip(residual, limit)])


def audit(directory, output):
    require(not output.exists(), 'Preserve previous independent report')
    paths = [directory/'final-state-index.json', directory/'final-states.npz',
             directory/'python-curve-view.json', directory/'matlab-curve-view.json',
             Path(__file__), Path(ref.__file__),
             Path(__file__).with_name('audit_native_physics_mp.py'),
             Path(__file__).with_name('build_power_curve_views.py'),
             Path(__file__).with_name('build_multi_single_curve_views.py'),
             Path(__file__).resolve().parents[2]/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json']
    before = {str(i)+':'+p.name: sha(p) for i, p in enumerate(paths)}
    index = read(paths[0]); require(index['array_bank_sha256'] == sha(paths[1]), 'Real array bank differs')
    scope = index.get('case_scope', 'power'); require(scope in SCOPES, 'Unknown original complete sweep scope')
    _, ordinals, _, figures = SCOPES[scope]
    count = len(ordinals)
    require(index.get('expected_case_ordinals', ordinals) == ordinals and
            index.get('original_source_figures', figures) == figures, 'Exact original sweep identity differs')
    require(index['source_case_index_sha256'] == sha(paths[-1]), 'Original published case-index snapshot differs')
    source_cases = {c['ordinal']:c for c in source_scenes(paths[-1])}
    cases = index['cases']; require(len(cases) == 2*count, 'Every paired language case is required')
    views = {name: read(directory/(name+'-curve-view.json')) for name in ('python', 'matlab')}
    for name in views:
        require(sorted(c['ordinal'] for c in cases if c['language'] == name) == ordinals and
                sorted(p['source_case_ordinal'] for p in views[name]['results']) == ordinals and
                views[name]['source_case_index_sha256'] == sha(paths[-1]),
                'Missing/duplicate original source slots')
    values, lanes, design_transports = {}, {}, {}; started = time.perf_counter()
    with np.load(paths[1], allow_pickle=False) as arrays:
        for digits in (80, 100):
            lane = []; scalar_values = []
            with mp.workdps(digits):
                for case in cases:
                    spec = index['groups'][case['input_group']]
                    require(spec['language'] == case['language'], 'Wrong source input group')
                    data = {name: arrays[key].copy() for name, key in spec['data'].items()}
                    require(len(data) == 11 and all(np.isfinite(x).all() for x in data.values()),
                            'All11 finite physical arrays required')
                    J, U, N = data['d_mean'].shape; M = data['r_mean'].shape[1]
                    scene = source_cases[case['ordinal']]['full_reported_scene']
                    require((J, U, N, M) == tuple(scene[k] for k in ('J', 'U', 'N', 'M')) and
                            (J, U, N, M) in ((3, 2, 16, 25), (1, 2, 48, 25)), 'Exact complete original source-scene dimensions required')
                    power = arrays[case['power_limit']].reshape(-1); limit = arrays[case['interference_limit']].reshape(-1)
                    require(power.shape == (J,) and limit.shape == (1,), 'Missing original bounds')
                    selected = [p for p in views[case['language']]['results'] if p['source_case_ordinal'] == case['ordinal']]
                    require(len(selected) == 1, 'Curve view source slot differs')
                    point = selected[0]; final = []
                    identity = source_cases[case['ordinal']]
                    require(all(point[key] == identity[key] for key in ('sweep', 'parameter', 'value')),
                            'Plotted abscissa does not match its exact original source slot')
                    verify_limits(power, limit, identity)
                    require([s['scheme'] for s in case['final_states']] == list(NAMES), 'Eight actual final states required')
                    for state in case['final_states']:
                        name = state['scheme']; require(state['evaluation'] == point['schemes'][name]['evaluation'],
                                                        'Final-state evaluation differs from the plotted return')
                        d = {key: value.copy() for key, value in data.items()}
                        if state['no_ris']:
                            for key in ('G_mean', 'G_var', 'geo_G_mean', 'geo_G_var'):
                                d[key] *= 0
                        phi = arrays[state['phi']]; require(phi.shape == (U, M), 'Actual phase shape differs')
                        p = np.zeros((J, U)) if name.startswith('AP') else arrays[state['p']]
                        W = arrays[state['W']] if name.startswith('AP') else None
                        kind = 'W' if W is not None else 'p'
                        restored, transport = restore_native_singleton_design(
                            W if W is not None else p, kind, J, U, N, case['language'])
                        if W is not None:
                            W = restored
                        else:
                            p = restored
                        if transport is not None:
                            key = (case['language'], case['ordinal'], name, kind)
                            transport.update(language=case['language'], ordinal=case['ordinal'], scheme=name)
                            require(key not in design_transports or design_transports[key] == transport,
                                    'A native singleton transport changed between precision lanes')
                            design_transports[key] = transport
                        require(p.shape == (J, U) and (W is None or W.shape == (J, N, U)), 'Actual design shape differs')
                        actual = physical(d, phi, p, W, limit, name)
                        fields = compare(state['evaluation'], actual)
                        domain = max(abs(abs(ref.scalar(z))-1) for z in phi.reshape(-1)) <= ref.real(1e-10)
                        checks = dict(all_reported_physical_fields_pass=all(f['passed'] for f in fields.values()),
                            original_physical_constraints_pass=constraints(actual, power, limit),
                            original_phase_domain_pass=bool(domain), MR_powers_nonnegative=bool(np.all(p >= 0)))
                        final.append(dict(scheme=name, fields=fields, checks=checks, passed=all(checks.values())))
                        scalar_values.extend(v for key in FIELDS for v in actual[key])
                    lane.append(dict(language=case['language'], ordinal=case['ordinal'], final_states=final,
                                     all_eight_pass=all(s['passed'] for s in final)))
                    if len(lane) % 8 == 0:
                        print(json.dumps(dict(digits=digits, cases_checked=len(lane), all_pass=all(c['all_eight_pass'] for c in lane))), flush=True)
            lanes[str(digits)] = lane; values[digits] = scalar_values
    scalar_count = 2*8*sum(2*source_cases[n]['full_reported_scene']['U'] +
        source_cases[n]['full_reported_scene']['J'] + source_cases[n]['full_reported_scene']['K'] for n in ordinals)
    require(scalar_count == 7680, 'J1/J3 field lengths must be counted separately')
    require(len(values[80]) == len(values[100]) == scalar_count, 'All original physical field coordinates required')
    with mp.workdps(110):
        gap = max(abs(x-y) for x, y in zip(values[80], values[100])); stable = gap <= mp.mpf('1e-40')
    after = {str(i)+':'+p.name: sha(p) for i, p in enumerate(paths)}
    passed = bool(before == after and stable and all(c['all_eight_pass'] for lane in lanes.values() for c in lane))
    report = dict(scope=f'All{count} original {scope} cases x8 actual final states x2 languages; independent MP80/100 final physics',
        case_scope=scope, exact_original_case_ordinals=ordinals, original_source_figures=figures,
        actual_numeric_input_bounds_match_every_original_source_axis=True,
        source_input_sha256=before, source_and_inputs_unchanged=before == after,
        cases_per_language=count, schemes_per_case=8, actual_final_states_per_precision=count*16,
        scalar_field_coordinates_per_precision=scalar_count, field_comparison_policy='1e-9+1e-10*abs(reference)',
        original_physical_constraint_absolute_tolerance=1e-5, phase_unit_tolerance=1e-10,
        maximum_MP80_MP100_difference=mp.nstr(gap, 105), precision_absolute_bound='1e-40', lanes=lanes,
        actual_native_singleton_design_arrays_losslessly_restored=len(design_transports),
        native_singleton_design_transports=list(design_transports.values()),
        native_singleton_transport_changes_numeric_values=False,
        all_final_states_physics_and_precision_pass=passed,
        independently_optimized_solution_equality_certified=False,
        phase_stops_QT_candidates_MC_reference_or_full_paper_pass=False,
        elapsed_seconds=time.perf_counter()-started, optimizer_or_random_draw_calls=0)
    report['all1152_final_states_physics_and_precision_pass'] = passed
    report['source_figure11_reference_ordinates_per_language'] = 144
    report['source_W_versus_normalized_I_over_N_conflict_unresolved'] = True
    write(output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('lanes', 'source_input_sha256', 'native_singleton_design_transports')}), flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    if not audit(a.directory, a.output)['all_final_states_physics_and_precision_pass']:
        raise SystemExit(1)
