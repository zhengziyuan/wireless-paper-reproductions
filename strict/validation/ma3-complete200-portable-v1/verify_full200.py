"""PREPARED one-command complete saved-dual audit and display, NOT optimizer."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
if sys.flags.optimize or not __debug__ or not sys.flags.dont_write_bytecode:
    raise RuntimeError('Use python -B, never -O/-OO, before loading any local source')
from publication_contract import (INDEX_SHA, sha, verify_ready_bundle,
    verify_relative_pins, read_actual_complete_audit, actual_supervision_gate)

HERE = Path(__file__).resolve().parent


def fresh(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def load_exact(name, path, trusted):
    path = Path(path).resolve()
    if sha(path) != trusted:
        raise ValueError('Only exact staged immutable entry source permitted')
    cached = sys.modules.get(name)
    if cached is not None:
        raise ValueError('No foreign/already loaded portable module cache')
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def execute(output):
    # Required BEFORE every original assertion/source import; no bytecode writes
    # into the immutable extracted evidence or staged dependency directories.
    if sys.flags.optimize or not __debug__ or not sys.dont_write_bytecode:
        raise RuntimeError('Use python -B, never -O/-OO; no new PYC and all original assertions required')
    if sys.gettrace() is not None or sys.getprofile() is not None:
        raise RuntimeError('No numerical profiling/tracing in this immutable route')
    manifest = verify_ready_bundle(HERE)
    manifest_before = sha(HERE / 'bundle-manifest.json')
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    output = Path(output).resolve()
    if output.exists() or output.is_relative_to(HERE):
        raise ValueError('A completely NEW output outside the immutable bundle required')
    index = HERE / 'archives/full200-archive-index.json'
    inventory = json.loads(index.read_bytes())
    uncompressed = sum(item['size'] for item in inventory['files'].values())
    if shutil.disk_usage(output.parent).free < max(8 * 1024**3, 2 * uncompressed):
        raise ValueError('Insufficient observed free space before fresh extraction/audit; no deletion/reduction')
    output.mkdir()
    pins = manifest['public_file_sha256']
    fresh(output / 'actual-single-command-start.json', dict(
        trusted_full_index_sha256=INDEX_SHA, staged_source_and_evidence_before=pins,
        public_manifest_sha256=manifest_before,
        actual_geometry_jobs=200, source_parameter_cases=2,
        required_geometries_per_parameter_case=100, original_draws_per_geometry=1000,
        fresh_native_MATLAB_optimizer_or_new_random_ensemble=False,
        original_author_historical_curve_agreement=False))
    failure, stage = None, 'archive_verification_and_fresh_unpack'
    try:
        v1 = HERE / 'work/ma-full200-portable-archive-v1'
        sys.path.insert(0, str(v1))
        archive = load_exact('published_full_archive_exact', v1 / 'full_archive_v1.py',
            pins['work/ma-full200-portable-archive-v1/full_archive_v1.py'])
        archive.pinned_index(index, INDEX_SHA)
        tree, audit, boundary, figures = (output / name for name in ('fresh-extracted1044', 'fresh-full200-audit', 'fresh-entry-boundary', 'figures'))
        archive.unpack(HERE / 'archives', inventory, tree)
        stage = 'fresh_all200_unchanged_math_saved_dual_independent_audit'
        entry_dir = HERE / 'work/ma-portable-entry-boundary-v2'
        entry = load_exact('published_full200_entry_exact', entry_dir / 'portable_entry_boundary_v2.py',
            pins['work/ma-portable-entry-boundary-v2/portable_entry_boundary_v2.py'])
        manifest_path = entry_dir / 'PREPARED-entry-boundary-freeze-v2.json'
        code = entry.supervise(tree, index, INDEX_SHA, audit, boundary, manifest_path,
            pins['work/ma-portable-entry-boundary-v2/PREPARED-entry-boundary-freeze-v2.json'])
        if code != 0:
            raise RuntimeError('Original full200 independent child failed; all partial outputs retained')
        read_actual_complete_audit(audit)
        # BEGIN V2 fresh supervisor/source interval gate BEFORE display
        actual_supervision_gate(boundary)
        verify_relative_pins(HERE, pins)
        if sha(HERE / 'bundle-manifest.json') != manifest_before:
            raise ValueError('Public immutable manifest changed before display')
        # END V2 fresh supervisor/source interval gate BEFORE display
        stage = 'both_language_Fig3_display_after_ALL200_gate'
        renderer = load_exact('published_Fig3_renderer_exact', v1 / 'render_portable_Fig3_v1.py',
            pins['work/ma-full200-portable-archive-v1/render_portable_Fig3_v1.py'])
        renderer.render(tree, index, INDEX_SHA, audit, figures)
        archive.verify_tree(tree, inventory)
        verify_relative_pins(HERE, pins)
        if sha(HERE / 'bundle-manifest.json') != manifest_before:
            raise ValueError('Public immutable manifest changed during the actual run')
    except BaseException as error:
        failure = dict(stage=stage, type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        raise
    finally:
        fresh(output / 'actual-single-command-completion.json', dict(
            exception=failure, last_stage=stage,
            fresh_complete_all200_saved_dual_audit_and_two_figures_passed=failure is None,
            all_partial_and_failed_outputs_retained=True,
            fresh_native_MATLAB_optimizer_full_sweep_or_new_MC=False,
            historical_curve_closeness_or_global_nonconvex_optimum=False,
            no_existing_file_deleted_overwritten_or_relabelled=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new-output', type=Path)
    parser.add_argument('--verify-unpack-audit-render', action='store_true')
    args = parser.parse_args()
    if not args.verify_unpack_audit_render:
        print(json.dumps(dict(prepared_only=True, no_unpack_arrays_numeric_audit_renderer_or_optimizer=True,
            actual_publication_full200_gate_and_staging_required_before_execution=True,
            expected_trusted_whole_index_sha256=INDEX_SHA)))
        return
    if args.new_output is None:
        parser.error('Completely NEW output outside the bundle required')
    execute(args.new_output)


if __name__ == '__main__':
    main()
