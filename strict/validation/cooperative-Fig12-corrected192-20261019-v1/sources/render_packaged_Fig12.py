"""Display the192 saved ordinates and96 published vector values; no solver."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def check_inputs(package, manifest):
    identities = {}
    for row in manifest['files']:
        if row['role'] not in ('runtime_source', 'saved_numeric_input'):
            continue
        relative = Path(row['relative_path'])
        path = (package / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(package):
            raise ValueError('Manifest path escapes this package')
        digest = sha(path)
        if digest != row['SHA256']:
            raise ValueError('Named input/source bytes differ: ' + str(relative))
        identities[row['relative_path']] = digest
    if len(identities) != 5:
        raise ValueError('Expected two runtime sources and three saved numeric inputs')
    return identities


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if sys.flags.optimize != 0:
        raise ValueError('Run without Python optimization flags')
    package = Path(__file__).resolve().parent.parent
    manifest_path = package / 'SOURCE_AND_ARTIFACT_MANIFEST.json'
    manifest_before = sha(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    before = check_inputs(package, manifest)
    data = package / 'data'
    row_name = 'all192-dual-language-source-bound-sumrates-and-unfitted-source-gaps.json'
    reference_name = 'published-Fig12-all8-curves-all96-original-vector-reference-values-v1.json'
    points = json.loads((data / row_name).read_bytes())
    reference = json.loads((data / reference_name).read_bytes())
    rows = points['all192_derived_points']
    identities = {(r['language'], r['original_full_bank_case_ordinal'], r['method']) for r in rows}
    if len(rows) != 192 or len(identities) != 192 or points['available_ordinates'] != 192:
        raise ValueError('Refuse partial, duplicate or missing derived slots')
    if reference['actual_all_original_reference_markers'] != 96 or len(reference['curves']) != 8:
        raise ValueError('The original eight vector curves are incomplete')
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(package):
        raise ValueError('Choose a fresh output directory outside this package')
    output.mkdir(parents=True)
    try:
        # The unchanged renderer reads these two files beside its outputs.
        # Byte copies route its existing I/O; no point is reconstructed/changed.
        for name in ('summary.json', row_name):
            with (output / name).open('xb') as stream:
                stream.write((data / name).read_bytes())
        source = package / 'sources/render_cooperative_final_Fig12_all192_unfitted_diagnostic_v1.py'
        spec = importlib.util.spec_from_file_location('frozen_Fig12_renderer', source)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        renderer.P = data
        renderer.O = output
        renderer.main()
        after = check_inputs(package, manifest)
        manifest_after = sha(manifest_path)
        closed = before == after and manifest_before == manifest_after
        put(output / 'portable-render-provenance.json', {
            'scope': 'display_only192_saved_points_and96_original_vectors',
            'ended_UTC': dt.datetime.now(dt.timezone.utc).isoformat(),
            'source_and_input_before': before, 'source_and_input_after': after,
            'manifest_before_SHA256': manifest_before, 'manifest_after_SHA256': manifest_after,
            'source_and_input_unchanged': closed,
            'actual_saved_language_points': 192, 'original_vector_points': 96,
            'renderer_source_modified': False,
            'relative_path_host_changes': 'in-memory P/O input/output directories only',
            'optimizer_scientific_RNG_MC_MP_or_rate_recomputation_called': False,
            'unit_conversion_or_reference_fitting_applied': False,
            'original_reference_gate': False,
            'independently_optimized_dual_language_equal_gate': False,
            'whole_paper_PASS': False,
            'visual_review_of_this_new_display_complete': False,
        })
        return 0 if closed else 1
    except BaseException as error:
        try:
            put(output / 'failed-portable-display.json', {
                'error_type': type(error).__name__, 'error': str(error),
                'outputs_may_be_partial': True, 'new_scientific_PASS': False,
            })
        except Exception:
            pass
        raise


if __name__ == '__main__':
    sys.exit(main())
