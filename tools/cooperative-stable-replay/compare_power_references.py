"""Unfitted all192-point comparison with the author's two original power EPS.

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


def extract(path, figure):
    text = path.read_text(encoding='latin-1')
    # A gray stroke is exactly equal RGB, not a fitted color conversion. The
    # common parser otherwise rejects this eighth, genuinely gray curve.
    normalized = re.sub(rf'(?m)^({NUMBER}) GC\s*$', lambda m: ' '.join([m[1]]*3) + ' RC', text)
    paths = eps_paths(normalized, [56, 10, 613.1, 421])
    require(len(paths) == 8 and [tuple(p['rgb']) for p in paths] == list(COLORS),
            'All eight original curve paths must match their visually verified legend colors')
    xmax, ymax, exponent = (32, 7.5, 5) if figure == 2 else (64, 3.5, 6)
    expected_x = 2**np.arange(0, exponent+.01, .5)
    curves = []
    for label, p in zip(LABELS, paths):
        xy = np.asarray(p['path_coordinates'])
        require(len(xy) == len(expected_x)+1, 'All original grid points and one exported clipping tail required')
        require(abs(xy[-2, 0]-613) <= 1e-12 and 0 < xy[-1, 0]-613 < .1 and
                abs(xy[-1, 1]-xy[-2, 1]) <= 1e-12, 'Unrecognized tail; no original sample may be discarded')
        x = 1+(xy[:-1, 0]-56)/557*(xmax-1)
        y = (421-xy[:-1, 1])/411*ymax
        resolution = .001*(xmax-1)/557
        require(np.max(abs(x-expected_x)) <= resolution, 'Original EPS abscissas do not match the entire source grid')
        curves.append(dict(label=label, rgb=p['rgb'], x=x.tolist(), y=y.tolist(),
            original_all_path_coordinates=xy.tolist(), clipped_export_tail_is_measurement=False,
            raw_tail_x=1+(xy[-1, 0]-56)/557*(xmax-1)))
    return dict(paper_id='cooperative-satcom', figure=figure,
        source_file=path.name, source_sha256=sha(path),
        source_version='author_thesis_Chapter4_original_EPS_not_verified_final_publisher_version',
        data_kind='original_plot_vector_reference_NOT_simulation', curves=curves,
        axis_calibration=dict(rectangle=[56, 10, 613, 421], x_range=[1, xmax], y_range=[0, ymax],
            scale='linear in displayed coordinates, W and linear SINR', axes_visually_verified=True,
            original_legend_colors_visually_verified=True),
        export_tail_note='Each source polyline has one same-ordinate extension0.066 path units beyond the clipped right axis. All raw coordinates are retained; only the11/13 actual in-axis abscissas are compared.',
        EPS_coordinate_decimal_step=.001, maximum_ordinate_rounding_resolution=ymax/411*.001,
        simulation_reproduction_verified=False)


def run(a):
    require(not a.output_dir.exists(), 'Preserve prior original-reference comparison')
    a.output_dir.mkdir(parents=True)
    reports = []
    for figure, filename in ((2, 'plot_P_T_2.eps'), (3, 'plot_P_T_1.eps')):
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
            require(result['all_curves_and_grids_complete'], 'All192 source points across both figures must be paired')
            result.update(language=language, simulation_sha256=sha(sim_path), reference_packet_sha256=sha(target),
                reference_EPS_sha256=reference['source_sha256'], fitted_parameters_or_interpolated_points=0,
                ordinate_agreement_tolerance_was_prespecified=False,
                maximum_observed_absolute_linear_SINR_gap=max(c['max_abs_error'] for c in result['curves']))
            write(a.output_dir / f'{language}-figure-{figure}-unfitted-comparison.json', result)
            reports.append(dict(language=language, figure=figure, all_curves_and_grids_complete=True,
                points=sum(c['matched_samples'] for c in result['curves']),
                maximum_absolute_linear_SINR_gap=result['maximum_observed_absolute_linear_SINR_gap']))
    summary = dict(scope='Unfitted all24 source power abscissas x8 schemes x2 languages against private-author EPS vectors',
        comparisons=reports, original_points_per_language=192, no_reference_numbers_enter_simulation=True,
        unreported_geometry_gains_and_patterns_not_fitted=True,
        original_curve_agreement_or_full_paper_pass=False, original_private_EPS_redistributed=False,
        source_sha256=dict(extractor=sha(Path(__file__)), eps_parser=sha(STRICT/'figure_reference.py'),
                           comparator=sha(STRICT/'figure_validation.py')))
    write(a.output_dir / 'original-reference-summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--eps-directory', type=Path); g.add_argument('--reference-directory', type=Path)
    p.add_argument('--axes-verified', action='store_true'); p.add_argument('--curve-directory', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True); run(p.parse_args())
