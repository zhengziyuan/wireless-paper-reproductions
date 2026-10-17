"""An optimizer-independent upper bound on the actual fixed NoRIS inputs.

For one shared GT limit I and numerator n_u, let B_u bound useful-power /
GT-leakage for every satellite serving u. Then sum_u n_u/B_u <= I. Since
den_u >= offset_u, min_u SINR_u <= I / sum_u(offset_u/B_u). We discard all
satellite power limits and all nonnegative intra-system interference, so this
is a relaxation and cannot underestimate the feasible optimum.

AP uses the generalized Cauchy-Schwarz ratio m^H T^-1 m. Statistical MR uses
||m||^4/(m^H T m); TTS MR uses (||m||^2+tr C)^2/tr[T(C+mm^H)]. All T are
checked positive definite; no parameter is estimated from the reference.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import time

import mpmath as mp
import numpy as np
from audit_native_case import sha
from build_power_curve_views import SCOPES, read, require, write
import mp_phase_reference as ref


NAMES = ('AP-NoRIS', 'MR-S-NoRIS', 'MR-TTS-NoRIS')


def bound_group(data, interference):
    J, U, N = data['d_mean'].shape
    require(data['gt_second'].shape == (J, 1, N, N), 'This bound requires exactly one shared GT')
    require(np.all(data['d_var'] >= 0) and np.all(data['geo_d_var'] >= 0), 'Negative physical variance')
    T = [ref.mat_hpart(ref.matrix(data['gt_second'][j, 0])) for j in range(J)]
    for matrix in T:
        mp.cholesky(mp.matrix(matrix))
    offsets = [1 + ref.real(data['geo_d_var'][u]) + abs(ref.scalar(data['geo_d_mean'][u]))**2 for u in range(U)]
    require(all(x > 0 for x in offsets) and interference > 0, 'Positive noise/interference limits required')
    outputs = {}
    for name in NAMES:
        ratios = [[] for _ in range(U)]
        for u in range(U):
            for j in range(J):
                mean = ref.vector(data['d_mean'][j, u]); q = ref.norm2(mean)
                variance = ref.real(data['d_var'][j, u]); gt = T[j]
                if name == 'AP-NoRIS':
                    solved = list(mp.lu_solve(mp.matrix(gt), mp.matrix(mean)))
                    ratio = mp.re(ref.dot(mean, solved))
                else:
                    tts = name == 'MR-TTS-NoRIS'
                    signal = (q + (N*variance if tts else 0))**2
                    leakage = ref.quad(mean, gt) + (variance*ref.tr(gt) if tts else 0)
                    require(leakage > 0, 'Strictly positive actual MR leakage required')
                    ratio = signal/leakage
                require(ratio > 0, 'Strictly positive actual useful/leakage ratio required')
                ratios[u].append(ratio)
        best = [max(row) for row in ratios]
        upper = interference/mp.fsum(x/y for x, y in zip(offsets, best))
        outputs[name] = dict(upper=upper, ratios=ratios, best=best, offsets=offsets)
    return outputs


def audit(directory, reference_directory, output):
    require(not output.exists(), 'Preserve previous bound diagnostic')
    first_index = read(directory/'final-state-index.json')
    scope = first_index.get('case_scope', 'power')
    require(scope in SCOPES, 'Unsupported original sweep')
    _, ordinals, _, figures = SCOPES[scope]
    count = len(ordinals)
    require(first_index.get('expected_case_ordinals', ordinals) == ordinals and
            first_index.get('original_source_figures', figures) == figures,
            'Exact complete original cohort and source figures required')
    paths = [directory/'final-state-index.json', directory/'final-states.npz',
             directory/'python-curve-view.json', directory/'matlab-curve-view.json',
             *[reference_directory/f'original-figure-{figure}-vector-reference.json' for figure in figures],
             Path(__file__), Path(ref.__file__)]
    before = {str(i)+':'+p.name: sha(p) for i, p in enumerate(paths)}
    index = read(paths[0]); require(index['array_bank_sha256'] == sha(paths[1]), 'Actual array bank differs')
    references = {c['label']: c for c in read(paths[4])['curves']}
    views = {language: read(directory/(language+'-curve-view.json')) for language in ('python', 'matlab')}
    for language in views:
        require(sorted(c['ordinal'] for c in index['cases'] if c['language']==language) == ordinals and
                sorted(p['source_case_ordinal'] for p in views[language]['results']) == ordinals,
                'Missing or duplicate original state/curve slot')
    lanes, values = {}, {}; started = time.perf_counter()
    with np.load(paths[1], allow_pickle=False) as arrays:
        for digits in (80, 100):
            groups = {}; numeric = []
            with mp.workdps(digits):
                for key, spec in index['groups'].items():
                    cases = [c for c in index['cases'] if c['input_group'] == key]
                    require(cases, 'Unused input group')
                    data = {k: arrays[v] for k, v in spec['data'].items()}
                    limits = [arrays[c['interference_limit']].reshape(-1) for c in cases]
                    require(all(x.shape == (1,) and x[0]>0 for x in limits), 'Exactly one positive shared GT limit per original case required')
                    if scope!='interference':
                        require(all(np.array_equal(x, limits[0]) for x in limits), 'One identical GT limit required per power group')
                    # The relaxation is exactly linear in I. Reuse only channel
                    # coefficients, and multiply by each actual bound below.
                    I = mp.mpf(1) if scope=='interference' else ref.real(limits[0][0])
                    result = bound_group(data, I)
                    rows = {}
                    for name, r in result.items():
                        rows[name] = dict(upper_bound=mp.nstr(r['upper'], 105),
                            per_user_satellite_useful_to_GT_ratios=[[mp.nstr(v, 105) for v in row] for row in r['ratios']],
                            selected_maximum_ratio_per_user=[mp.nstr(v, 105) for v in r['best']],
                            positive_noise_and_GEO_offsets=[mp.nstr(v, 105) for v in r['offsets']])
                        numeric.extend([r['upper'], *r['best'], *r['offsets'], *(v for row in r['ratios'] for v in row)])
                    groups[key] = dict(language=spec['language'], shared_GT_limit=mp.nstr(I, 105),
                        positive_definite_GT_second_moments_checked=True, source_cases=[c['ordinal'] for c in cases],
                        bounds=rows, unit_interference_coefficient=scope=='interference')
            lanes[str(digits)] = groups; values[digits] = numeric
    with mp.workdps(110):
        gap = max(abs(a-b) for a, b in zip(values[80], values[100])); stable = gap <= mp.mpf('1e-40')
    comparisons = []
    for language in ('python', 'matlab'):
        for point in views[language]['results']:
            ordinal = point['source_case_ordinal']
            if scope=='power':figure=2 if ordinal<11 else 3;offset=ordinal if figure==2 else ordinal-11
            elif scope=='interference':
                require(24<=ordinal<48, 'Exact original interference slots required')
                figure=4 if ordinal<36 else 5;offset=ordinal-24 if figure==4 else ordinal-36
            elif scope=='subsurfaces':
                require(48<=ordinal<66, 'Exact original RIS-size slots required')
                figure=6 if ordinal<57 else 7;offset=ordinal-48 if figure==6 else ordinal-57
            else:
                require(66<=ordinal<111, 'Exact original45 ground-factor slots required')
                figure=8+(ordinal-66)//15;offset=(ordinal-66)%15
            case = next(c for c in index['cases'] if c['language'] == language and c['ordinal'] == ordinal)
            rdoc = read(reference_directory/f'original-figure-{figure}-vector-reference.json')
            refs = {r['label']: r for r in rdoc['curves']}
            for name in NAMES:
                upper = float(lanes['100'][case['input_group']]['bounds'][name]['upper_bound'])
                if scope=='interference':
                    with np.load(paths[1],allow_pickle=False) as arrays:
                        upper*=float(arrays[case['interference_limit']].reshape(-1)[0])
                current = min(point['schemes'][name]['evaluation']['sinr']); original = refs[name]['y'][offset]
                rounding = rdoc['maximum_ordinate_rounding_resolution']
                require(current <= upper+1e-9+1e-10*abs(upper), 'Computed feasible value exceeds the independent relaxation bound')
                comparisons.append(dict(language=language, ordinal=ordinal, figure=figure,
                    source_axis_parameter=point['parameter'], source_axis_value=point['value'],
                    scheme=name, independent_upper_bound=upper, saved_actual_minimum_SINR=current,
                    saved_actual_within_bound=True, author_EPS_ordinate=original,
                    EPS_full_decimal_ordinate_step=rounding, original_minus_bound=original-upper,
                    source_reference_exceeds_this_fixed_input_bound_after_rounding=bool(original-upper > rounding+1e-12*max(1, abs(upper)))))
    after = {str(i)+':'+p.name: sha(p) for i, p in enumerate(paths)}
    report = dict(scope=f'Optimizer-independent NoRIS upper bound for the actual binary input groups and all{count*3} source NoRIS ordinates per language',
        case_scope=scope, source_horizontal_unit_conformance_verified=scope!='interference',
        source_unit_caveat='Source EPS prints W while implementation uses noise-normalized I/N. Source ordinate comparison is conditional on identifying these scalar grids, not proof that the original W input violates the bound.' if scope=='interference' else 'Actual saved noise-normalized GT limits are retained; the complete original source abscissas are paired without fitting.',
        source_input_sha256=before, source_and_inputs_unchanged=before == after, mathematical_bound_assumptions=
        ['one shared GT interference limit', 'positive-definite GT second moments', 'nonnegative MR powers and channel variances',
         'original noncoherent sum-of-powers useful numerator', 'denominator at least positive noise plus GEO interference'],
        relaxation_discards=['all satellite transmit-power constraints', 'all nonnegative intra-system interference'],
        theorem='t <= I / sum_u(offset_u / max_j B_ju)',
        theorem_derivation='n_u <= max_j B_ju * L_u; den_u >= offset_u; t <= n_u/den_u implies L_u >= t*offset_u/max_j B_ju; sum_u L_u <= I.',
        precisions=[80, 100], maximum_MP80_MP100_coefficient_difference=mp.nstr(gap, 105),
        precision_absolute_bound='1e-40', all_bound_evaluations_and_source_bindings_pass=bool(stable and before == after),
        all_actual_NoRIS_values_within_relaxation_bound=True, source_reference_ordinates_per_language=count*3,
        source_reference_exceeds_fixed_input_bound_per_language={l:sum(r['source_reference_exceeds_this_fixed_input_bound_after_rounding'] for r in comparisons if r['language'] == l) for l in ('python', 'matlab')},
        lanes=lanes, comparisons=comparisons,
        conclusion='For the reported above-bound ordinates, no optimizer on these fixed inputs can reproduce the supplied source curve. Source-conforming physical coefficients remain unresolved; this is not a contradiction of the author paper under its unrecovered inputs.',
        cause_identified_as_unique_gain_pattern_or_geometry=False, source_parameters_fitted=False,
        optimizer_or_random_draw_calls=0, original_curve_or_full_paper_pass=False, elapsed_seconds=time.perf_counter()-started)
    write(output, report)
    print({k:v for k,v in report.items() if k in ('all_bound_evaluations_and_source_bindings_pass',
        'source_reference_exceeds_fixed_input_bound_per_language', 'maximum_MP80_MP100_coefficient_difference', 'elapsed_seconds')})
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('directory', 'reference-directory', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    if not audit(a.directory, a.reference_directory, a.output)['all_bound_evaluations_and_source_bindings_pass']:
        raise SystemExit(1)
