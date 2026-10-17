"""Unfitted complete-grid comparison with original satellite EPS figures.

Only vector ordinates/axis calibration are distributed. Private EPS/manuscript
files are never copied to the public packet or supplied to an optimizer.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

import numpy as np
from audit_native_case import sha
from build_power_curve_views import read, require, write

STRICT = Path(__file__).resolve().parents[2] / 'strict'
sys.path.insert(0, str(STRICT))
from figure_reference import NUMBER, eps_paths
from figure_validation import compare

LABELS = ('AP-NoRIS', 'MR-S-NoRIS', 'MR-TTS-NoRIS', 'AP-AO',
          'MR-S-PA', 'MR-TTS-PA', 'MR-S-TS', 'MR-TTS-TS')
COLORS = ((.376, .447, .455), (.702, .702, .702), (.439, .384, .2), (.443, .114, .69),
          (.761, .071, .573), (1., .655, .196), (.373, .741, 1.), (.937, .251, .251))
SOURCES = {'power': ((2, 'plot_P_T_2.eps'), (3, 'plot_P_T_1.eps')),
           'interference': ((4, 'plot_varsigma_1.eps'), (5, 'plot_varsigma_2.eps')),
           'subsurfaces': ((6, 'plot_MN_1.eps'), (7, 'plot_MN_2.eps'))}


def extract(path, figure):
    text = path.read_text(encoding='latin-1')
    # A gray stroke is exactly equal RGB, not a fitted color conversion. The
    # common parser otherwise rejects this eighth, genuinely gray curve.
    normalized = re.sub(rf'(?m)^({NUMBER}) GC\s*$', lambda m: ' '.join([m[1]]*3) + ' RC', text)
    require(figure in (2, 3, 4, 5, 6, 7), 'Only explicitly calibrated original panels are supported')
    interference = figure in (4, 5)
    subsurfaces = figure in (6, 7)
    left, right, bottom, ymin, ymax = {2:(56,613,421,0,7.5), 3:(56,613,421,0,3.5),
        4:(48,606,431,0,14), 5:(56,606,429,0,4.5),
        6:(50,615,429,2,11), 7:(55,615,429,1,5)}[figure]
    has_tail = not interference and not subsurfaces
    paths = eps_paths(normalized, [left, 10, right+.1 if has_tail else right, bottom])
    require(len(paths) == 8 and [tuple(p['rgb']) for p in paths] == list(COLORS),
            'All eight original curve paths must match their visually verified legend colors')
    xmax = .12 if interference else (45 if subsurfaces else (32 if figure == 2 else 64))
    xmin = .01 if interference else (5 if subsurfaces else 1)
    expected_x = (np.arange(1,13)/100 if interference else (np.arange(5,46,5) if subsurfaces
                  else 2**np.arange(0,(5 if figure==2 else 6)+.01,.5)))
    curves = []
    for label, p in zip(LABELS, paths):
        xy = np.asarray(p['path_coordinates'])
        if not has_tail:
            require(len(xy)==len(expected_x) and abs(xy[0,0]-left)<=1e-12 and abs(xy[-1,0]-right)<=1e-12,
                    'Every original in-axis sample is required; no clipping tail may be removed')
            measured=xy
        else:
            require(len(xy) == len(expected_x)+1, 'All original grid points and one exported clipping tail required')
            require(abs(xy[-2, 0]-right) <= 1e-12 and 0 < xy[-1, 0]-right < .1 and
                    abs(xy[-1, 1]-xy[-2, 1]) <= 1e-12, 'Unrecognized tail; no original sample may be discarded')
            measured=xy[:-1]
        x = xmin+(measured[:, 0]-left)/(right-left)*(xmax-xmin)
        y = ymin+(bottom-measured[:, 1])/(bottom-10)*(ymax-ymin)
        resolution = .001*(xmax-xmin)/(right-left)
        require(np.max(abs(x-expected_x)) <= resolution, 'Original EPS abscissas do not match the entire source grid')
        curves.append(dict(label=label, rgb=p['rgb'], x=x.tolist(), y=y.tolist(),
            original_all_path_coordinates=xy.tolist(), clipped_export_tail_is_measurement=False,
            raw_tail_x=xmin+(xy[-1, 0]-left)/(right-left)*(xmax-xmin) if has_tail else None))
    return dict(paper_id='cooperative-satcom', figure=figure,
        source_file=path.name, source_sha256=sha(path),
        source_version='author_thesis_Chapter4_original_EPS_not_verified_final_publisher_version',
        data_kind='original_plot_vector_reference_NOT_simulation', curves=curves,
        axis_calibration=dict(rectangle=[left, 10, right, bottom], x_range=[xmin, xmax], y_range=[ymin, ymax],
            scale='linear in displayed coordinates and linear SINR', axes_visually_verified=True,
            source_horizontal_unit='RIS subsurface count' if subsurfaces else 'W as printed in original EPS',
            simulation_horizontal_unit='noise-normalized I/N' if interference else ('RIS subsurface count' if subsurfaces else 'W'),
            source_to_simulation_horizontal_unit_conformance_verified=not interference,
            unit_scope_note='Original interference EPS prints W and marks I/N=-12.2dB. The supplied implementation uses noise-normalized I/N; scalar-grid pairing does not resolve this source-unit conflict.' if interference else ('M is the RIS subsurface count.' if subsurfaces else 'Power is expressed in W.'),
            original_legend_colors_visually_verified=True),
        export_tail_note=f'All{len(expected_x)} path points per curve are in-axis and retained; there is no clipping tail.' if not has_tail else 'Each source polyline has one same-ordinate extension0.066 path units beyond the clipped right axis. All raw coordinates are retained; only the11/13 actual in-axis abscissas are compared.',
        EPS_coordinate_decimal_step=.001, maximum_ordinate_rounding_resolution=(ymax-ymin)/(bottom-10)*.001,
        simulation_reproduction_verified=False)


def run(a):
    require(not a.output_dir.exists(), 'Preserve prior original-reference comparison')
    a.output_dir.mkdir(parents=True)
    reports = []
    for figure, filename in SOURCES[a.case_scope]:
        if a.eps_directory:
            require(a.axes_verified, 'Original axes and all eight legend colors must first be visually verified')
            source = a.eps_directory / filename; before = sha(source)
            reference = extract(source, figure)
            require(sha(source) == before, 'Original EPS changed during extraction')
        else:
            reference = read(a.reference_directory / f'original-figure-{figure}-vector-reference.json')
        target = a.output_dir / f'original-figure-{figure}-vector-reference.json'; write(target, reference)
        for language in ('python', 'matlab'):
            sim_path = a.curve_directory / language / f'cooperative-satcom-figure-{figure}.json'
            simulation = read(sim_path)
            require(len(simulation['panels']) == 1, 'One complete original panel required')
            simulation['curves'] = simulation['panels'][0]['curves']
            # Existing generic comparison: exact whole-grid pairing within EPS
            # decimal x rounding. No ordinate threshold is invented here.
            result = compare(simulation, reference, max_abs_error=None)
            require(result['all_curves_and_grids_complete'], 'Every source sample across both figures must be paired')
            result.update(language=language, simulation_sha256=sha(sim_path), reference_packet_sha256=sha(target),
                reference_EPS_sha256=reference['source_sha256'], fitted_parameters_or_interpolated_points=0,
                ordinate_agreement_tolerance_was_prespecified=False,
                maximum_observed_absolute_linear_SINR_gap=max(c['max_abs_error'] for c in result['curves']))
            write(a.output_dir / f'{language}-figure-{figure}-unfitted-comparison.json', result)
            reports.append(dict(language=language, figure=figure, all_curves_and_grids_complete=True,
                points=sum(c['matched_samples'] for c in result['curves']),
                maximum_absolute_linear_SINR_gap=result['maximum_observed_absolute_linear_SINR_gap']))
    count = 18 if a.case_scope == 'subsurfaces' else 24
    summary = dict(scope=f'Unfitted all{count} source {a.case_scope} abscissas x8 schemes x2 languages against private-author EPS vectors',
        case_scope=a.case_scope, horizontal_units_resolved=a.case_scope!='interference',
        comparisons=reports, original_points_per_language=count*8, no_reference_numbers_enter_simulation=True,
        unreported_geometry_gains_and_patterns_not_fitted=True,
        original_curve_agreement_or_full_paper_pass=False, original_private_EPS_redistributed=False,
        source_sha256=dict(extractor=sha(Path(__file__)), eps_parser=sha(STRICT/'figure_reference.py'),
                           comparator=sha(STRICT/'figure_validation.py')))
    write(a.output_dir / 'original-reference-summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-scope', choices=tuple(SOURCES), default='power')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--eps-directory', type=Path); g.add_argument('--reference-directory', type=Path)
    p.add_argument('--axes-verified', action='store_true'); p.add_argument('--curve-directory', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True); run(p.parse_args())
