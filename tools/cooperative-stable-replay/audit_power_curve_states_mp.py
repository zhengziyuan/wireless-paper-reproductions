"""Independent MP80/100 physics for all24 source slots x8 schemes x2 languages.

Consumes the compact real final-state bank, never an optimizer or RNG. Phase
stops and all inner QT candidates retain their separate original audit scope.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

import mpmath as mp
import numpy as np

from audit_native_case import sha
from audit_native_physics_mp import FIELDS, compare, constraints
from build_power_curve_views import NAMES, SCOPES, read, require, verify_limits, write
import mp_phase_reference as ref


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
             Path(__file__).resolve().parents[2]/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json']
    before = {str(i)+':'+p.name: sha(p) for i, p in enumerate(paths)}
    index = read(paths[0]); require(index['array_bank_sha256'] == sha(paths[1]), 'Real array bank differs')
    scope = index.get('case_scope', 'power'); require(scope in SCOPES, 'Unknown original complete sweep scope')
    _, ordinals, _, figures = SCOPES[scope]
    require(index.get('expected_case_ordinals', ordinals) == ordinals and
            index.get('original_source_figures', figures) == figures, 'Exact original sweep identity differs')
    require(index['source_case_index_sha256'] == sha(paths[-1]), 'Original published case-index snapshot differs')
    source_cases = {c['ordinal']:c for c in read(paths[-1])['cases']}
    cases = index['cases']; require(len(cases) == 48, 'All48 paired language cases required')
    views = {name: read(directory/(name+'-curve-view.json')) for name in ('python', 'matlab')}
    for name in views:
        require(sorted(c['ordinal'] for c in cases if c['language'] == name) == ordinals and
                sorted(p['source_case_ordinal'] for p in views[name]['results']) == ordinals and
                views[name]['source_case_index_sha256'] == sha(paths[-1]),
                'Missing/duplicate original source slots')
    values, lanes = {}, {}; started = time.perf_counter()
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
                    require((J, U, N, M) == (3, 2, 16, 25), 'Complete original source-scene dimensions required')
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
    require(len(values[80]) == len(values[100]) == 3072, 'All original physical field coordinates required')
    with mp.workdps(110):
        gap = max(abs(x-y) for x, y in zip(values[80], values[100])); stable = gap <= mp.mpf('1e-40')
    after = {str(i)+':'+p.name: sha(p) for i, p in enumerate(paths)}
    report = dict(scope=f'All24 original {scope} cases x8 actual final states x2 languages; independent MP80/100 final physics',
        case_scope=scope, exact_original_case_ordinals=ordinals, original_source_figures=figures,
        actual_numeric_input_bounds_match_every_original_source_axis=True,
        source_input_sha256=before, source_and_inputs_unchanged=before == after,
        cases_per_language=24, schemes_per_case=8, actual_final_states_per_precision=384,
        scalar_field_coordinates_per_precision=3072, field_comparison_policy='1e-9+1e-10*abs(reference)',
        original_physical_constraint_absolute_tolerance=1e-5, phase_unit_tolerance=1e-10,
        maximum_MP80_MP100_difference=mp.nstr(gap, 105), precision_absolute_bound='1e-40', lanes=lanes,
        all384_final_states_physics_and_precision_pass=bool(before == after and stable and
            all(c['all_eight_pass'] for lane in lanes.values() for c in lane)),
        independently_optimized_solution_equality_certified=False,
        phase_stops_QT_candidates_MC_reference_or_full_paper_pass=False,
        elapsed_seconds=time.perf_counter()-started, optimizer_or_random_draw_calls=0)
    write(output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('lanes', 'source_input_sha256')}), flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    if not audit(a.directory, a.output)['all384_final_states_physics_and_precision_pass']:
        raise SystemExit(1)
