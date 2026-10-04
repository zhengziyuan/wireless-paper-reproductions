"""Actual light preparation and source proof only. Never starts a numerical child."""
from pathlib import Path
import io
import json
import sys
import unittest
import portable_entry_boundary_v2 as boundary
import test_entry_boundary_v2 as tests

HERE = Path(__file__).resolve().parent


def main():
    target = HERE / 'PREPARED-entry-boundary-freeze-v2.json'
    if target.exists():
        raise FileExistsError('Prepared source freeze immutable; choose a new version')
    sources = ['portable_entry_boundary_v2.py', 'test_entry_boundary_v2.py', 'prepare_entry_boundary_v2.py',
               'PREDECLARED_ENTRY_BOUNDARY_PLAN_V2.md']
    before = {name: boundary.sha(HERE / name) for name in sources}
    v1_before = boundary.v1_source_identity()
    failed = boundary.ROOT / 'work/ma-full200-portable-archive-execution-v1/ACTUAL-fresh-portable-complete200-audit-v1'
    if {path.name for path in failed.iterdir()} != {'portable-audit-start-identity.json', 'pre-audit-byte-freeze.json'}:
        raise ValueError('Retained old incomplete entry failure exact two-file shape required')
    old_before = {path.name: boundary.sha(path) for path in failed.iterdir()}
    proof = boundary.prepare_only(tests.ORIGINAL)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    if not result.wasSuccessful():
        print(output.getvalue())
        raise RuntimeError('Preparation light tests failed; no ready freeze')
    after = {name: boundary.sha(HERE / name) for name in sources}
    old_after = {path.name: boundary.sha(path) for path in failed.iterdir()}
    if before != after or old_before != old_after or v1_before != boundary.v1_source_identity():
        raise ValueError('Original sources/evidence changed during light preparation')
    forbidden = [name for name in sys.modules if name.split('.')[0] in ('numpy', 'scipy', 'mpmath', 'cvxpy')]
    if forbidden:
        raise RuntimeError('Unexpected numerical libraries in preparation')
    boundary.fresh(target, {
        'scope': 'Prepared only outer process/entry observer; unchanged original v1 scientific audit body',
        'prepared_v2_source_files_sha256': before, 'frozen_v1_source_identity': v1_before,
        'old_failed_two_files_sha256_before_after': old_before, 'old_failed_tree_and_v1_source_bytes_unchanged': True,
        'unchanged_numeric_suffix_text_and_AST_proof': proof,
        'actual_light_tests_count': result.testsRun, 'actual_light_tests_all_pass': True,
        'actual_light_test_output': output.getvalue(),
        'actual_stdlib_only_synthetic_subprocesses_tested': True,
        'numerical_libraries_imported': forbidden, 'numeric_execution_performed': False,
        'optimizer_MC_MATLAB_physics_or_renderer_run': False,
        'old_nonzero_empty_output_cause_recovered': False,
        'old_failure_reclassified_as_scientific_failure': False,
        'prepared_v2_scientific_function_replaced_transformed_or_recompiled': False})
    print(json.dumps({'actual_light_tests': result.testsRun, 'all_pass': True,
                      'prepared_freeze_sha256': boundary.sha(target), 'numeric_execution': False}))


if __name__ == '__main__':
    main()
