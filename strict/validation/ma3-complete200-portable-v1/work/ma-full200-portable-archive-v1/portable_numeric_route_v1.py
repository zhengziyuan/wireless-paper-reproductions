"""Prepared all200 portable audit: only path/IO prelude replaced, literal numeric suffix retained."""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import platform
import sys
import full_archive_v1 as archive
import safe_archive_v1 as codec

MARKER = '    # No numeric library/production module was imported before the full freeze.\n'
ORIGINAL_AUDITOR_SHA = '1058cf5182254533275fb28bed2cbb1c11a0fc759ac8e4be96e593ec6348a0d7'
NUMERIC_SUFFIX_SHA = '71eb5fd75e0c188a4b9fe16f881303ca984b2ae6e3424df28e00b401bb5eccbb'


def literal_suffix_source(original):
    if codec.sha(original) != ORIGINAL_AUDITOR_SHA:
        raise ValueError('Actual frozen full200 auditor byte identity required')
    text = Path(original).read_text(encoding='utf-8')
    start = text.index(MARKER, text.index('def execute('))
    end = text.index('\ndef main():', start)
    suffix = text[start:end]
    if hashlib.sha256(suffix.encode()).hexdigest() != NUMERIC_SUFFIX_SHA:
        raise ValueError('Frozen whole numeric suffix identity required')
    source = 'def execute_portable_numeric(snapshot, originals, original_hashes, out):\n' + suffix
    old = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'execute')
    new = ast.parse(source).body[0]
    # Original numeric portion begins at the for-loop after its readiness/copy prelude.
    first = next(i for i, node in enumerate(old.body) if isinstance(node, ast.For))
    if ast.dump(ast.Module(body=old.body[first:], type_ignores=[]), include_attributes=False) != ast.dump(
            ast.Module(body=new.body, type_ignores=[]), include_attributes=False):
        raise ValueError('Literal whole numeric loop/gates/formulas changed')
    return source, {'literal_numeric_suffix_text_sha256': hashlib.sha256(suffix.encode()).hexdigest(),
                    'original_numeric_AST_exactly_equal': True,
                    'new_numeric_oracle_body': False,
                    'changed_scope': 'path/byte-freeze prelude only; original numeric suffix including every gate and summary retained'}


def prepare(source_path):
    _, proof = literal_suffix_source(source_path)
    return proof


def execute(tree, index_path, trusted_sha, out):
    tree, out = Path(tree).resolve(), Path(out).resolve()
    if out.exists() or tree == out or tree in out.parents:
        raise ValueError('Fresh output outside original extracted tree required')
    index = archive.pinned_index(index_path, trusted_sha)
    archive.verify_tree(tree, index)
    snapshot = tree / 'snapshot'
    frozen = json.loads((tree / 'pre-audit-byte-freeze.json').read_bytes())
    originals = {name: snapshot / name for name in frozen['files_sha256']}
    original_hashes = frozen['files_sha256']
    if {name: codec.sha(path) for name, path in originals.items()} != original_hashes:
        raise ValueError('Entire original641-file scientific snapshot required')
    original = snapshot / 'sources/isolated/audit_full200_dual_v1.py'
    source, proof = literal_suffix_source(original)
    out.mkdir(parents=True)
    before = {name: codec.sha(tree / name) for name in index['files']}
    own_paths = [Path(__file__), Path(archive.__file__), Path(codec.__file__), Path(archive.recipe.__file__)]
    own_before = {path.name: codec.sha(path) for path in own_paths}
    def fresh(name, value):
        with (out / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
    fresh('portable-audit-start-identity.json', {
        'scope': 'Fresh portable independent audit, not a re-execution of original optimizer or historical runtime',
        'trusted_whole_archive_index_sha256': trusted_sha, 'all1044_original_evidence_sha256_before': before,
        'portable_wrapper_sources_sha256_before': own_before, 'numeric_body_proof': proof,
        'current_observer_runtime': {'python': sys.version, 'platform': platform.platform()},
        'original_scientific_runtime_identity_retained_not_current_runtime_claim': True,
        'new_MC_optimizer_MATLAB_or_historical_curve_match_claim': False})
    fresh('pre-audit-byte-freeze.json', {'scope': 'portable original641-byte snapshot validated before unchanged numeric audit',
                                       'files_sha256': original_hashes, 'trusted_archive_index_sha256': trusted_sha})
    # Loading this module executes stdlib definitions only. Numeric imports begin inside literal suffix.
    spec = importlib.util.spec_from_file_location('portable_unchanged_full200_auditor', original)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    namespace = dict(module.__dict__)
    exec(compile(source, str(original) + '::literal-portable-numeric-suffix', 'exec'), namespace)
    try:
        namespace['execute_portable_numeric'](snapshot, originals, original_hashes, out)
    finally:
        after = {name: codec.sha(tree / name) for name in index['files']}
        fresh('portable-audit-completion-byte-binding.json', {
            'all1044_original_evidence_bytes_unchanged': before == after,
            'portable_source_bytes_unchanged': own_before == {path.name: codec.sha(path) for path in own_paths},
            'original_641_snapshot_and_old88_untouched': True,
            'actual_numeric_summary_available': (out / 'actual-full200-dual-summary.json').is_file(),
            'original_curve_agreement_claimed': False})
        if before != after: raise ValueError('Original evidence bytes changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only-original-auditor', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--extracted-tree', type=Path)
    parser.add_argument('--index', type=Path)
    parser.add_argument('--index-sha256')
    parser.add_argument('--fresh-output-dir', type=Path)
    args = parser.parse_args()
    if args.execute:
        if args.prepare_only_original_auditor or not all((args.extracted_tree, args.index, args.index_sha256, args.fresh_output_dir)):
            parser.error('Explicit execute requires complete trusted tree/index and fresh output')
        execute(args.extracted_tree, args.index, args.index_sha256, args.fresh_output_dir)
    else:
        if not args.prepare_only_original_auditor: parser.error('Default is prepare-only; no automatic numeric audit')
        print(json.dumps(prepare(args.prepare_only_original_auditor), indent=2))


if __name__ == '__main__': main()
