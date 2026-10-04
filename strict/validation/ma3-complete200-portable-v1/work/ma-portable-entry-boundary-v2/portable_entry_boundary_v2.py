"""Prepared outer entry observer: forward the unchanged full200 v1 route, never replace science."""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V1 = ROOT / 'work/ma-full200-portable-archive-v1'
ROUTE_SHA = 'aef5c11e22e3f37cbbec02d57be4dd73dc7437ff3fd470b42127e4154e7a44a3'
DEPENDENCIES = {
    'portable_numeric_route_v1.py': ROUTE_SHA,
    # The remaining source identities are frozen in the approved preparation
    # manifest, checked before importing any of these stdlib-only modules.
}
PREPARATION_SHA = '6b3de8c78f36d4ba4bd2fddfbc8c978a37895f06b2c5dfca8faedeb0adf90612'
ORIGINAL_AUDITOR_SHA = '1058cf5182254533275fb28bed2cbb1c11a0fc759ac8e4be96e593ec6348a0d7'
SUFFIX_SHA = '71eb5fd75e0c188a4b9fe16f881303ca984b2ae6e3424df28e00b401bb5eccbb'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fresh(path, data):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')


def assertions_required():
    if sys.flags.optimize or not __debug__:
        raise RuntimeError('python -O/-OO forbidden: all original assertions must execute')


def v1_source_identity():
    manifest_path = V1 / 'PREPARED-portable-full200-route-freeze-v1.json'
    if sha(manifest_path) != PREPARATION_SHA:
        raise ValueError('Approved v1 source freeze byte identity required')
    manifest = json.loads(manifest_path.read_bytes())
    # Deliberately reject an unexpected manifest schema rather than trust a
    # guessed key or silently accept whichever dependency happens to import.
    expected = manifest['prepared_sources_sha256']
    for name, digest in expected.items():
        if Path(name).name != name or sha(V1 / name) != digest:
            raise ValueError('Approved v1 dependency identity mismatch: ' + name)
    if expected.get('portable_numeric_route_v1.py') != ROUTE_SHA:
        raise ValueError('Pinned route identity missing')
    return {'approved_preparation_sha256': PREPARATION_SHA,
            'approved_v1_sources_sha256': expected}


def load_v1_route():
    v1_source_identity()
    for name in ('full_archive_v1', 'safe_archive_v1', 'size_roundtrip_pilot25_v1'):
        old = sys.modules.get(name)
        if old is not None and Path(old.__file__).resolve().parent != V1:
            raise RuntimeError('Foreign cached v1 dependency: ' + name)
    old_path = list(sys.path)
    sys.path.insert(0, str(V1))
    try:
        spec = importlib.util.spec_from_file_location('unchanged_portable_v1_for_boundary_v2', V1 / 'portable_numeric_route_v1.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old_path
    if sha(module.__file__) != ROUTE_SHA:
        raise ValueError('Loaded route identity mismatch')
    return module


def stage_lines(source, filename):
    """Line observer only; not a source transformation or a replacement entry."""
    module = ast.parse(source)
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'execute')
    matches = {}
    markers = {
        'stdlib_spec_before': 'spec = importlib.util.spec_from_file_location(',
        'stdlib_module_load_before': 'module = importlib.util.module_from_spec(',
        'namespace_copy_before': 'namespace = dict(module.__dict__)',
        'literal_function_definition_before': 'exec(compile(source,',
        'numeric_call_before_trace_disabled': "namespace['execute_portable_numeric'](snapshot, originals, original_hashes, out)",
    }
    lines = source.splitlines()
    for stage, marker in markers.items():
        positions = [i + 1 for i, line in enumerate(lines) if marker in line and function.lineno <= i + 1 <= function.end_lineno]
        if len(positions) != 1:
            raise ValueError('Exactly one original boundary required: ' + stage)
        matches[positions[0]] = stage
    return matches


class EntryObserver:
    """Captures entry checkpoints, then turns tracing off before numerical call."""
    def __init__(self, function, lines, directory):
        self.function = function
        self.code = function.__code__
        self.lines = dict(lines)
        self.directory = Path(directory)
        self.records = []
        self.seen = set()
        self.numeric_boundary_reached = False

    def __call__(self, frame, event, arg):
        if frame.f_code is not self.code:
            return None
        if event == 'line' and frame.f_lineno in self.lines:
            name = self.lines[frame.f_lineno]
            if name not in self.seen:
                record = {'entry_stage': name, 'original_execute_line': frame.f_lineno,
                          'original_code_object_identity_preserved': frame.f_code is self.code,
                          'frame_locals_read_or_modified': False,
                          'numerical_function_traced_or_replaced': False}
                fresh(self.directory / ('checkpoint-%02d.json' % len(self.records)), record)
                self.records.append(record)
                self.seen.add(name)
            if name == 'numeric_call_before_trace_disabled':
                self.numeric_boundary_reached = True
                sys.settrace(None)
                return None
        return self


def forward_with_entry_observer(function, arguments, lines, directory):
    """Calls the exact original object once; exceptions remain exceptions."""
    if sys.gettrace() is not None or sys.getprofile() is not None:
        raise RuntimeError('Existing profiler/tracer forbidden for this isolated observer')
    observer = EntryObserver(function, lines, directory)
    original_code = function.__code__
    sys.settrace(observer)
    try:
        value = function(*arguments)
    finally:
        sys.settrace(None)
    if function.__code__ is not original_code:
        raise RuntimeError('Original callable code object changed')
    if not observer.numeric_boundary_reached:
        raise RuntimeError('Original numeric entry boundary was not reached')
    return value, observer


def prepare_only(original):
    assertions_required()
    before = v1_source_identity()
    route = load_v1_route()
    original_code = route.execute.__code__
    source, proof = route.literal_suffix_source(original)
    # Definition compilation alone does not import/call the numerical helpers.
    compile(source, str(original) + '::unchanged-definition-only', 'exec')
    lines = stage_lines(Path(route.__file__).read_text(encoding='utf-8'), route.__file__)
    if route.execute.__code__ is not original_code or v1_source_identity() != before:
        raise ValueError('Original route source/code changed')
    return {'scope': 'Prepared outer entry checkpoints and broad exception recording only',
            'v1_source_identity': before, 'original_auditor_sha256': sha(original),
            'numeric_suffix_sha256': SUFFIX_SHA, 'numeric_suffix_AST_and_text_proof': proof,
            'original_execute_source_not_transformed': True,
            'original_execute_callable_code_object_unchanged': True,
            'observer_line_boundaries': lines, 'numeric_loop_called': False,
            'NumPy_or_physical_or_optimizer_or_MATLAB_called': False,
            'old_empty_stderr_exit1_cause_claimed_recovered': False}


def execute(tree, index, trusted_sha, out, boundary):
    assertions_required()
    tree, out, boundary = (Path(value).resolve() for value in (tree, out, boundary))
    if boundary.exists() or out.exists() or boundary == out or tree == boundary or tree in boundary.parents or out in boundary.parents or boundary in out.parents:
        raise ValueError('Fresh sibling boundary and original output directories outside extracted evidence required')
    boundary.mkdir(parents=True)
    own_before = {path.name: sha(path) for path in HERE.glob('*.py')}
    fresh(boundary / 'outer-start.json', {
        'scope': 'Outer entry observer, original v1 route and science unchanged',
        'assertions_enabled': True, 'v1_source_identity_before': v1_source_identity(),
        'outer_sources_sha256_before': own_before,
        'input_paths': {'tree': str(tree), 'index': str(Path(index).resolve()), 'original_out': str(out)},
        'trusted_index_sha256': trusted_sha, 'old_failed_outputs_modified': False,
        'numeric_function_tracing_disabled_before_call': True,
        'known_old_cause_or_science_failure_claim': False})
    failure = None
    status = 'exception_before_or_during_original_call'
    route = None
    try:
        # This try includes the phases missing from the v1 finally boundary.
        route = load_v1_route()
        original_function = route.execute
        original_code = original_function.__code__
        lines = stage_lines(Path(route.__file__).read_text(encoding='utf-8'), route.__file__)
        fresh(boundary / 'route-loaded.json', {'exact_v1_route_source_sha256': ROUTE_SHA,
              'original_execute_AST_unchanged': True, 'observer_lines': lines})
        forward_with_entry_observer(original_function, (tree, index, trusted_sha, out), lines, boundary)
        if route.execute is not original_function or route.execute.__code__ is not original_code:
            raise RuntimeError('Original callable replaced during execution')
        status = 'original_call_returned'
    except BaseException as exc:
        failure = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        fresh(boundary / 'actual-exception.json', failure)
        print(json.dumps(failure), file=sys.stderr, flush=True)
        raise
    finally:
        sys.settrace(None)
        fresh(boundary / 'outer-completion.json', {
            'outer_status': status, 'exception': failure,
            'v1_source_identity_after': v1_source_identity(),
            'outer_sources_unchanged': own_before == {path.name: sha(path) for path in HERE.glob('*.py')},
            'original_v1_finally_receipt_available': (out / 'portable-audit-completion-byte-binding.json').is_file(),
            'original_numeric_summary_available': (out / 'actual-full200-dual-summary.json').is_file(),
            'component_or_full200_numeric_pass_inferred_from_entry_status': False,
            'fatal_process_exit_catchable_by_Python_wrapper': False,
            'old_exit1_cause_recovered_or_old_failure_erased': False})


def capture_child(command, directory, environment):
    """Stdlib subprocess IO only, with a durable parent record even for child hard exit."""
    directory = Path(directory)
    if directory.exists():
        raise FileExistsError('Fresh process capture directory required')
    directory.mkdir(parents=True)
    fresh(directory / 'parent-before-child-start.json', {
        'command': list(command), 'scope': 'Actual subprocess startup/IO, not inferred scientific success',
        'original_assertions_required': True,
        'child_scientific_function_transformed_or_replaced': False})
    code = None
    failure = None
    try:
        with (directory / 'stdout.bin').open('xb') as stdout, (directory / 'stderr.bin').open('xb') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=environment)
            fresh(directory / 'actual-child-started.json', {'actual_child_pid': process.pid})
            code = process.wait()
    except BaseException as exc:
        failure = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        fresh(directory / 'actual-parent-exception.json', failure)
        raise
    finally:
        streams = {name: {'bytes': (directory / name).stat().st_size, 'sha256': sha(directory / name)}
                   for name in ('stdout.bin', 'stderr.bin') if (directory / name).is_file()}
        fresh(directory / 'actual-child-exit-and-streams.json', {
            'actual_child_return_code': code, 'parent_exception': failure,
            'actual_streams': streams, 'child_status_returned': code is not None,
            'child_nonzero_exit_is_not_automatically_a_scientific_failure': True,
            'full200_numeric_pass_inferred_from_exit': False,
            'parent_hard_exit_or_power_failure_caught': False})
    return code


def prepared_boundary_identity(manifest_path, expected_sha):
    manifest_path = Path(manifest_path)
    if sha(manifest_path) != expected_sha:
        raise ValueError('Explicit trusted v2 preparation identity required')
    manifest = json.loads(manifest_path.read_bytes())
    expected_names = {'portable_entry_boundary_v2.py', 'test_entry_boundary_v2.py',
                      'prepare_entry_boundary_v2.py', 'PREDECLARED_ENTRY_BOUNDARY_PLAN_V2.md'}
    expected = manifest['prepared_v2_source_files_sha256']
    if set(expected) != expected_names:
        raise ValueError('Exactly all four prepared v2 sources required')
    if any(sha(HERE / name) != digest for name, digest in expected.items()):
        raise ValueError('Prepared v2 source changed')
    if manifest['frozen_v1_source_identity'] != v1_source_identity():
        raise ValueError('Original v1 source identity changed')
    if manifest['numeric_execution_performed'] is not False or manifest['actual_light_tests_all_pass'] is not True:
        raise ValueError('Prepared-only complete light test manifest required')
    return expected


def supervise(tree, index, trusted_sha, out, boundary, manifest_path, expected_sha):
    assertions_required()
    before = prepared_boundary_identity(manifest_path, expected_sha)
    tree, out, boundary = (Path(value).resolve() for value in (tree, out, boundary))
    if boundary.exists() or out.exists() or boundary == out or tree == boundary or tree in boundary.parents or out in boundary.parents or boundary in out.parents:
        raise ValueError('Fresh sibling process capture and audit directories outside extracted evidence required')
    command = [sys.executable, '-B', '-u', str(Path(__file__).resolve()), '--worker',
               '--extracted-tree', str(tree), '--index', str(Path(index).resolve()),
               '--index-sha256', trusted_sha, '--fresh-output-dir', str(out),
               '--fresh-boundary-dir', str(boundary / 'worker-entry'),
               '--expected-worker-sha256', before['portable_entry_boundary_v2.py']]
    environment = dict(os.environ)
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        environment[name] = '1'
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    code = capture_child(command, boundary, environment)
    after = prepared_boundary_identity(manifest_path, expected_sha)
    fresh(boundary / 'parent-v2-source-binding-after.json', {
        'trusted_v2_preparation_sha256': expected_sha,
        'v2_sources_sha256_before': before, 'v2_sources_sha256_after': after,
        'v2_and_v1_sources_unchanged': before == after,
        'actual_child_return_code': code,
        'worker_entry_completion_present': (boundary / 'worker-entry/outer-completion.json').is_file(),
        'original_v1_finally_receipt_available': (out / 'portable-audit-completion-byte-binding.json').is_file(),
        'actual_numeric_summary_available': (out / 'actual-full200-dual-summary.json').is_file(),
        'scientific_pass_inferred_from_metadata_or_exit': False,
        'old_failed_folder_reused_or_changed': False})
    return 0 if code == 0 else 1


def main():
    assertions_required()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only-original-auditor', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--extracted-tree', type=Path)
    parser.add_argument('--index', type=Path)
    parser.add_argument('--index-sha256')
    parser.add_argument('--fresh-output-dir', type=Path)
    parser.add_argument('--fresh-boundary-dir', type=Path)
    parser.add_argument('--prepared-source-freeze', type=Path)
    parser.add_argument('--prepared-source-freeze-sha256')
    parser.add_argument('--expected-worker-sha256', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.execute or args.prepare_only_original_auditor or not all((args.extracted_tree, args.index, args.index_sha256, args.fresh_output_dir, args.fresh_boundary_dir, args.expected_worker_sha256)):
            parser.error('Internal explicit worker requires complete original arguments and trusted worker identity')
        if sha(__file__) != args.expected_worker_sha256:
            raise ValueError('Worker source differs from parent preparation identity')
        execute(args.extracted_tree, args.index, args.index_sha256, args.fresh_output_dir, args.fresh_boundary_dir)
        return 0
    elif args.execute:
        if args.prepare_only_original_auditor or not all((args.extracted_tree, args.index, args.index_sha256, args.fresh_output_dir, args.fresh_boundary_dir)):
            parser.error('Explicit execution requires original complete trusted archive and two fresh output directories')
        if not all((args.prepared_source_freeze, args.prepared_source_freeze_sha256)):
            parser.error('Explicit trusted prepared v2 source manifest also required')
        return supervise(args.extracted_tree, args.index, args.index_sha256, args.fresh_output_dir,
                         args.fresh_boundary_dir, args.prepared_source_freeze, args.prepared_source_freeze_sha256)
    else:
        if not args.prepare_only_original_auditor:
            parser.error('Default is prepare-only; no automatic numerical execution')
        print(json.dumps(prepare_only(args.prepare_only_original_auditor), indent=2))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
