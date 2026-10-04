"""Light stdlib-only synthetic/negative tests. No scientific function or helper is called."""
from pathlib import Path
import ast
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
import portable_entry_boundary_v2 as boundary

ORIGINAL = boundary.ROOT / 'work/ma-full200-portable-archive-execution-v1/ACTUAL-all8-lossless-roundtrip-20261004-v1/byte-roundtrip-full200/snapshot/sources/isolated/audit_full200_dual_v1.py'


def synthetic_function():
    source = '''def synthetic_execute(sentinel, consumer):
    marker = "stdlib-definition-only"
    namespace = {"sentinel": sentinel}
    return consumer(sentinel)
'''
    namespace = {}
    exec(compile(source, '<stdlib-synthetic-entry>', 'exec'), namespace)
    return namespace['synthetic_execute'], {2: 'stdlib_module_load_before', 4: 'numeric_call_before_trace_disabled'}


class BoundaryTests(unittest.TestCase):
    def test_original_source_whole_AST_and_suffix_unchanged_without_call(self):
        identity = boundary.v1_source_identity()
        report = boundary.prepare_only(ORIGINAL)
        self.assertTrue(report['numeric_suffix_AST_and_text_proof']['original_numeric_AST_exactly_equal'])
        self.assertEqual(report['numeric_suffix_sha256'], boundary.SUFFIX_SHA)
        self.assertFalse(report['numeric_loop_called'])
        self.assertEqual(identity, boundary.v1_source_identity())

    def test_original_execute_object_is_not_wrapped_or_recompiled(self):
        route = boundary.load_v1_route()
        original = route.execute
        code = original.__code__
        parsed = ast.parse(inspect.getsource(original))
        self.assertEqual(parsed.body[0].name, 'execute')
        self.assertIs(original, route.execute)
        self.assertIs(code, route.execute.__code__)
        source = inspect.getsource(boundary.forward_with_entry_observer)
        self.assertIn('function(*arguments)', source)
        self.assertNotIn('exec(', source)
        self.assertNotIn('compile(', source)

    def test_exact_single_forward_and_trace_disabled_before_synthetic_consumer(self):
        function, lines = synthetic_function()
        sentinel = object()
        calls = []
        def consumer(actual):
            self.assertIs(actual, sentinel)
            self.assertIsNone(sys.gettrace())
            calls.append(actual)
            return sentinel
        with tempfile.TemporaryDirectory() as temporary:
            value, observer = boundary.forward_with_entry_observer(function, (sentinel, consumer), lines, temporary)
            self.assertIs(value, sentinel)
            self.assertEqual(calls, [sentinel])
            self.assertTrue(observer.numeric_boundary_reached)
            self.assertEqual(len(observer.records), 2)
            self.assertEqual(len(list(Path(temporary).glob('checkpoint-*.json'))), 2)
        self.assertIsNone(sys.gettrace())

    def test_pretry_exception_propagates_trace_is_cleaned(self):
        namespace = {}
        exec(compile('def synthetic_execute():\n    marker = 1\n    raise LookupError("fixed-synthetic-pretry")\n', '<stdlib-only>', 'exec'), namespace)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(LookupError, 'fixed-synthetic-pretry'):
                boundary.forward_with_entry_observer(namespace['synthetic_execute'], (), {2: 'stdlib_module_load_before'}, temporary)
            self.assertEqual(len(list(Path(temporary).glob('checkpoint-*.json'))), 1)
        self.assertIsNone(sys.gettrace())

    def test_checkpoint_IO_failure_cannot_reach_consumer(self):
        function, lines = synthetic_function()
        called = []
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / 'checkpoint-00.json').write_text('existing synthetic negative', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                boundary.forward_with_entry_observer(function, (object(), lambda value: called.append(value)), lines, temporary)
        self.assertEqual(called, [])
        self.assertIsNone(sys.gettrace())

    def test_existing_trace_hook_rejected(self):
        function, lines = synthetic_function()
        with tempfile.TemporaryDirectory() as temporary:
            sys.settrace(lambda *args: None)
            try:
                with self.assertRaisesRegex(RuntimeError, 'Existing profiler/tracer'):
                    boundary.forward_with_entry_observer(function, (None, lambda value: None), lines, temporary)
            finally:
                sys.settrace(None)

    def test_missing_or_duplicated_numeric_boundary_rejected(self):
        source = (boundary.V1 / 'portable_numeric_route_v1.py').read_text(encoding='utf-8')
        marker = "namespace['execute_portable_numeric'](snapshot, originals, original_hashes, out)"
        with self.assertRaises(ValueError):
            boundary.stage_lines(source.replace(marker, 'pass'), '<missing>')
        with self.assertRaises(ValueError):
            boundary.stage_lines(source.replace(marker, marker + '\n        ' + marker), '<duplicate>')

    def test_stdlib_child_nonzero_stdout_stderr_and_return_code_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'fresh-capture'
            command = [sys.executable, '-B', '-c', 'import sys;sys.stdout.write("fixed-out");sys.stderr.write("fixed-err");sys.exit(17)']
            code = boundary.capture_child(command, path, dict(os.environ))
            self.assertEqual(code, 17)
            self.assertEqual((path / 'stdout.bin').read_bytes(), b'fixed-out')
            self.assertEqual((path / 'stderr.bin').read_bytes(), b'fixed-err')
            receipt = json.loads((path / 'actual-child-exit-and-streams.json').read_bytes())
            self.assertEqual(receipt['actual_child_return_code'], 17)
            self.assertFalse(receipt['full200_numeric_pass_inferred_from_exit'])
            with self.assertRaises(FileExistsError):
                boundary.capture_child(command, path, dict(os.environ))

    def test_stdlib_child_hard_exit_remains_non_science_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'hard-exit'
            code = boundary.capture_child([sys.executable, '-B', '-c', 'import os;os._exit(23)'], path, dict(os.environ))
            self.assertEqual(code, 23)
            self.assertEqual((path / 'stdout.bin').stat().st_size, 0)
            self.assertTrue(json.loads((path / 'actual-child-exit-and-streams.json').read_bytes())['child_nonzero_exit_is_not_automatically_a_scientific_failure'])

    def test_nonexistent_child_full_parent_exception_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'missing-child'
            with self.assertRaises(OSError):
                boundary.capture_child([str(path / 'does-not-exist.exe')], path, dict(os.environ))
            self.assertTrue((path / 'actual-parent-exception.json').is_file())
            self.assertIsNone(json.loads((path / 'actual-child-exit-and-streams.json').read_bytes())['actual_child_return_code'])

    def test_optimize_flags_fail_before_route_import(self):
        for flag in ('-O', '-OO'):
            result = subprocess.run([sys.executable, '-B', flag, str(Path(boundary.__file__)), '--prepare-only-original-auditor', str(ORIGINAL)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'python -O/-OO forbidden', result.stderr)

    def test_default_and_missing_execution_contract_rejected(self):
        for args in ([], ['--execute'], ['--worker']):
            result = subprocess.run([sys.executable, '-B', str(Path(boundary.__file__)), *args], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'error:', result.stderr)

    def test_untrusted_v2_freeze_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'untrusted.json'
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'trusted v2'):
                boundary.prepared_boundary_identity(path, '0' * 64)

    def test_no_numerical_libraries_imported(self):
        self.assertFalse(any(name.split('.')[0] in ('numpy', 'scipy', 'mpmath', 'cvxpy') for name in sys.modules))


if __name__ == '__main__':
    unittest.main(verbosity=2)
