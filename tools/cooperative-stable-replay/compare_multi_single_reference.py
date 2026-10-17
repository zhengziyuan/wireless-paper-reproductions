"""Pair all144 original figure11 ordinates/language without parameter fitting.

Figure11 shows two schemes in six complete configurations. Its printed W axis
has not been reconciled with the supplied implementation's normalized I/N.
Every reported difference therefore retains that conditional interpretation.
"""
import argparse
from pathlib import Path
import sys

import numpy as np

from audit_native_case import sha
from build_power_curve_views import read, require, write

STRICT = Path(__file__).resolve().parents[2] / 'strict'
sys.path.insert(0, str(STRICT))
from figure_validation import compare


def selections():
    out = []
    for beta in (20, 0):
        for scheme in ('AP-AO', 'MR-TTS-TS'):
            tag = 'AP' if scheme == 'AP-AO' else 'MR_TTS_TS'
            out.append((f'M_{tag}_kL{beta}', f'multi_vs_single_multi_kL{beta}', scheme))
        for offset in (1.25, 2.5):
            for scheme in ('AP-AO', 'MR-TTS-TS'):
                tag = 'AP' if scheme == 'AP-AO' else 'MR_TTS_TS'
                out.append((f'S_{tag}_kL{beta}_offset{offset}',
                            f'multi_vs_single_single_{offset}_kL{beta}', scheme))
    return out


def validate_reference(reference):
    require(reference['paper_id'] == 'cooperative-satcom' and reference['figure'] == 11 and
            reference['data_kind'] in ('original_plot_vectors_NOT_simulation',
                                      'original_plot_vector_reference_NOT_simulation') and
            reference['source_sha256'] == '955446f33b71dd5cb6ed55d36b8b4e6dc7bfb1f6f296e644f838bc4b443caaa0',
            'Require the actual visually verified original figure11 source')
    axes = reference['axis_calibration']
    require(axes['rectangle'] == [53, 10, 608, 429] and axes['x_range'] == [.01, .12] and
            axes['y_range'] == [0, 14] and
            axes['axes_all12_legend_colors_and_solid20_dashed0_styles_visually_verified'] is True and
            axes['source_to_simulation_horizontal_unit_conformance_verified'] is False,
            'Preserve the verified axes, legends and unresolved W versus normalized I/N scope')
    require(len(reference['curves']) == 12 and {c['label'] for c in reference['curves']} ==
            {label for label, _, _ in selections()}, 'All12 exact original source labels required')
    x_step = .001 * (.12 - .01) / (608 - 53)
    for curve in reference['curves']:
        xy = np.asarray(curve['original_all_path_coordinates'], dtype=float)
        require(xy.shape == (12, 2) and np.isfinite(xy).all(), 'Every original in-axis EPS point required')
        x = .01 + (xy[:, 0] - 53) / (608 - 53) * (.12 - .01)
        y = (429 - xy[:, 1]) / (429 - 10) * 14
        require(np.allclose(x, curve['x'], rtol=0, atol=1e-14) and
                np.allclose(y, curve['y'], rtol=0, atol=1e-14),
                'Delivered values differ from the original path-coordinate calibration')
        require(curve['line_style'] == ('solid' if 'kL20' in curve['label'] else 'dashed'),
                'Original solid20/dashed0 line identity differs')
        require(np.max(abs(x - np.arange(1, 13) / 100)) <= x_step,
                'The exact original12-point grid must agree within EPS coordinate rounding')
    return x_step


def compare_one(simulation, reference, language):
    require(language in ('python', 'matlab'), 'Exact language identity required')
    x_step = validate_reference(reference)
    if 'panels' in simulation:
        require(len(simulation['panels']) == 1, 'One complete original panel required')
        simulation = dict(simulation, curves=simulation['panels'][0]['curves'])
    require(len(simulation['curves']) == 12 and all(len(c['x']) == len(c['y']) == 12
            for c in simulation['curves']), 'All144 actual computed source-matched points required')
    # The original figure11 preflight uses the plural-vectors schema label.
    # Adapt only that exact known label for the shared comparison reader.
    canonical = dict(reference, data_kind='original_plot_vector_reference_NOT_simulation')
    require(canonical['curves'] == reference['curves'] and
            canonical['axis_calibration'] == reference['axis_calibration'],
            'Schema transport must preserve every source number and axis')
    result = compare(simulation, canonical, max_abs_error=None, x_tolerance=x_step)
    require(result['all_curves_and_grids_complete'] and
            sum(c['matched_samples'] for c in result['curves']) == 144,
            'No original source sample may be omitted or interpolated')
    result.update(language=language, original_reference_ordinates=144,
        original_delivered_reference_data_kind=reference['data_kind'],
        reference_schema_transport_changes_source_numbers=False,
        source_interference_W_versus_normalized_I_over_N_conflict_unresolved=True,
        source_comparison_is_conditional_on_identifying_the_two_horizontal_scalars=True,
        maximum_observed_absolute_linear_SINR_gap=max(c['max_abs_error'] for c in result['curves']),
        fitted_parameters_or_interpolated_points=0,
        ordinate_agreement_tolerance_was_prespecified=False,
        original_reference_or_full183_or_full_paper_pass=False)
    return result


def run(args):
    require(not args.output_dir.exists(), 'Preserve previous original-reference comparison')
    source = args.reference_directory / 'original-figure-11-vector-reference.json'
    reference = read(source)
    validate_reference(reference)
    paths = [source, Path(__file__), STRICT / 'figure_validation.py',
             *[args.curve_directory / language / 'cooperative-satcom-figure-11.json'
               for language in ('python', 'matlab')]]
    before = {str(p): sha(p) for p in paths}
    results = {language: compare_one(read(path), reference, language)
               for language, path in zip(('python', 'matlab'), paths[-2:])}
    require(before == {str(p): sha(p) for p in paths}, 'A bound source or actual curve changed')
    args.output_dir.mkdir(parents=True)
    write(args.output_dir / source.name, reference)
    for language, result in results.items():
        write(args.output_dir / f'{language}-figure-11-unfitted-comparison.json', result)
    summary = dict(scope='Complete original figure11:12 curves x12 ordinates x2 languages',
        case_scope='multi-single', cases_per_language=72, source_points_per_language=144,
        complete_all8_final_states_per_language=576, source_points_are_not72_times8=True,
        source_input_SHA256=before, source_and_curves_unchanged=True,
        source_interference_W_versus_normalized_I_over_N_conflict_unresolved=True,
        comparisons=[dict(language=language, points=144, all_curves_and_grids_complete=True,
            maximum_absolute_linear_SINR_gap=result['maximum_observed_absolute_linear_SINR_gap'])
            for language, result in results.items()],
        source_axis_rectangle=[53, 10, 608, 429], source_y_range=[0, 14],
        all_reference_points_retained_without_fitting=True, original_private_EPS_redistributed=False,
        original_reference_or_full183_or_full_paper_pass=False)
    write(args.output_dir / 'original-reference-summary.json', summary)
    print(summary, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-directory', type=Path, required=True)
    p.add_argument('--curve-directory', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    run(p.parse_args())
