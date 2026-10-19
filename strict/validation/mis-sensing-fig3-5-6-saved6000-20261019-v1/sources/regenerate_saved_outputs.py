"""Regenerate saved-data displays or deterministic fields; no optimization/RNG.

The package contains one selected state and the already assembled all6000 means.
It cannot reconstruct or independently reselect the undistributed6000 population.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def local_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bound_inputs(package, manifest):
    result = {}
    for row in manifest['files']:
        if row['role'] not in ('runtime_source', 'saved_numeric_input'):
            continue
        relative = Path(row['relative_path'])
        path = (package / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(package):
            raise ValueError('Manifest input escapes this package')
        actual = digest(path)
        if actual != row['SHA256']:
            raise ValueError('A named saved input/runtime source changed: ' + str(relative))
        result[row['relative_path']] = actual
    if not result:
        raise ValueError('No source-bound saved inputs')
    return result


def render_fig3(source, fields_path, destination):
    previous = sys.argv
    try:
        sys.argv = [str(source), str(fields_path), '--output', str(destination)]
        runpy.run_path(str(source), run_name='__main__')
    finally:
        sys.argv = previous


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('curves', 'fields', 'all'), default='all')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    sources = Path(__file__).resolve().parent
    package = sources.parent
    manifest_path = package / 'SOURCE_AND_ARTIFACT_MANIFEST.json'
    manifest_before = digest(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    before = bound_inputs(package, manifest)
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(package):
        raise ValueError('Choose a fresh output directory outside this package')
    summary_path = package / 'data/assembly-summary.json'
    curves_path = package / 'data/fig5-fig6-saved-curves.json'
    selected_path = package / 'data/selected-fixed-final-state.json'
    summary = json.loads(summary_path.read_bytes())
    selected = json.loads(selected_path.read_bytes())
    renderer = local_module(sources / 'render_closed_saved_Fig5_Fig6_v2.py', 'saved_display_v2')
    curves = json.loads(curves_path.read_bytes())
    # Reuse the reviewed pure input validator for every mode, including fields.
    renderer.validate(summary, curves, selected)
    if selected['best']['original_start'] != 3072:
        raise ValueError('This capsule binds the actual selected3072 state')
    output.mkdir(parents=True)
    try:
        if args.mode in ('curves', 'all'):
            plan_path = sources / 'PREPARED_FIG5_FIG6_CLOSED_OUTPUT_ONLY_RENDER_PLAN_V2.json'
            admission_path = output / 'display-input-admission.json'
            put(admission_path, {
                'root_reviewed_saved_fig5_fig6_display_only': True,
                'prepared_plan_SHA256': digest(plan_path),
                'input_SHA256': {'summary': digest(summary_path),
                                 'curves': digest(curves_path),
                                 'selected': digest(selected_path)},
                'scope': 'explicit public CLI request to display three packaged saved inputs',
            })
            result = renderer.main([
                '--summary', str(summary_path), '--curves', str(curves_path),
                '--selected', str(selected_path), '--data-root', str(output),
                '--output', str(output / 'fig5-fig6'), '--admission', str(admission_path),
                '--execute',
            ])
            if result != 0:
                raise RuntimeError('Saved display source/input closure failed')
        if args.mode in ('fields', 'all'):
            sys.path.insert(0, str(sources))
            kernel = local_module(sources / 'saved_Fig3_field_kernel.py', 'saved_field_kernel')
            samples = kernel.evaluate(selected['best'])
            field_path = output / 'fig3-beampattern-saved-selected-state-derived.json'
            put(field_path, {
                'paper_id': 'mis-sensing', 'figure': 'fig3',
                'scope': 'explicit_deterministic_fields_from_one_packaged_saved_state',
                'selected_original_start': 3072,
                'points': [{'configuration': selected['best']['configuration'],
                            'beampattern_samples': samples}],
                'disclosures': {
                    'grid': 'frozen independent1degree grid, not recovered author sampling',
                    'normalization': 'literal_inverseW_raw_per_PRI_gain1',
                    'selected_original_combined_certificate': False,
                    'no_optimization_random_draws_or_reference_fitting': True,
                },
            })
            if args.mode == 'all':
                render_fig3(sources / 'frozen_plot_beampatterns_v5.py', field_path, output / 'fig3')
        after = bound_inputs(package, manifest)
        manifest_after = digest(manifest_path)
        closed = before == after and manifest_before == manifest_after
        put(output / 'regeneration-provenance.json', {
            'scope': 'saved display/deterministic field regeneration only',
            'ended_UTC': dt.datetime.now(dt.timezone.utc).isoformat(),
            'mode': args.mode, 'package_manifest_before_SHA256': manifest_before,
            'package_manifest_after_SHA256': manifest_after,
            'source_and_saved_input_before': before, 'source_and_saved_input_after': after,
            'source_and_input_unchanged': closed,
            'selected_original_start': 3072, 'selected_original_combined_certificate': False,
            'population_mean_source': 'packaged all6000 saved means including720 false',
            'population_bank_recomputed_or_reselected': False,
            'optimizer_RNG_MC_MP_or_reference_fit_called': False,
            'original_reference_gate': False, 'dual_language_gate': False,
            'all6000_original_convergence_pass': False, 'whole_paper_PASS': False,
            'visual_review_of_this_new_output_complete': False,
        })
        return 0 if closed else 1
    except BaseException as error:
        try:
            put(output / 'failed-regeneration.json', {
                'error_type': type(error).__name__, 'error': str(error),
                'outputs_may_be_partial': True, 'new_scientific_PASS': False,
            })
        except Exception:
            pass
        raise


if __name__ == '__main__':
    sys.exit(main())
