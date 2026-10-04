"""Actual light static/tests/freeze only; never build full archives or execute numeric audit."""
from pathlib import Path
import ast
import contextlib
import io
import json
import sys
import unittest
import safe_archive_v1 as codec
import test_safe_portable_v1 as tests
import portable_numeric_route_v1 as numeric
import full_archive_v1 as full

HERE = Path(__file__).resolve().parent


def main():
    source_paths = sorted([*HERE.glob('*.py'), *HERE.glob('*.md')])
    before = {path.name: codec.sha(path) for path in source_paths}
    for path in HERE.glob('*.py'): ast.parse(path.read_text(encoding='utf-8'))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    proof = numeric.prepare(full.recipe.ACTUAL/'snapshot/sources/isolated/audit_full200_dual_v1.py')
    pilot = HERE/'actual-first25-byte-size-pilot-v1/actual-first25-size-byte-roundtrip-receipt.json'
    observed = json.loads(pilot.read_bytes())
    if not observed['exact_byte_roundtrip_pass'] or not observed['all_entire_original_snapshot_audits_progress_source_bytes_before_after_unchanged']:
        raise ValueError('Actual retained first25 byte evidence required')
    if before != {path.name: codec.sha(path) for path in source_paths}: raise ValueError('Prepared callable sources changed')
    receipt = {'scope': 'Prepared routes and actual light stdlib safety/static tests; NOT full8 archive/full200 re-audit/figure execution',
        'prepared_sources_sha256': before, 'all_prepared_source_bytes_before_after_unchanged': True,
        'actual_stdlib_tests_run': result.testsRun, 'actual_stdlib_tests_all_pass': result.wasSuccessful(),
        'actual_test_output': stream.getvalue(), 'numeric_suffix_literal_text_and_AST_proof': proof,
        'actual_first25_pilot_receipt_sha256': codec.sha(pilot), 'actual_first25_compressed_bytes': observed['part']['compressed_size'],
        'entire_original1044_byte_population_preserved_in_actual_pilot': True,
        'full8_archive_created': False, 'portable_full200_numeric_reaudit_executed': False,
        'portable_full_Fig3_executed': False, 'public_written_commit_push': False,
        'new_optimizer_MATLAB_newMC_or_physics_called': False,
        'numerical_libraries_imported': any(key in sys.modules for key in ('numpy', 'scipy', 'matplotlib', 'cvxpy'))}
    if receipt['numerical_libraries_imported']: raise ValueError('Preparation must stay stdlib-only')
    with (HERE/'PREPARED-portable-full200-route-freeze-v1.json').open('x', encoding='utf-8') as target:
        json.dump(receipt, target, indent=2, allow_nan=False); target.write('\n')
    print(json.dumps({'light_tests_pass': result.wasSuccessful(), 'count': result.testsRun,
                      'full8_and_numeric_not_executed': True, 'freeze_sha256': codec.sha(HERE/'PREPARED-portable-full200-route-freeze-v1.json')}))
    if not result.wasSuccessful(): raise SystemExit(1)


if __name__ == '__main__': main()
