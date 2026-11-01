"""Small real tracing regressions; no MP, model, optimizer or native process."""
from __future__ import annotations

import argparse
import ast
import __future__
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import marshal
import os
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest

from call_only_numeric_source_guard import CallOnlyNumericSourceGuard, SourceBindingError, file_sha256

CTX = {}
FORMULA = '''def leaf(x):
    return (x * x + 0.125) / (x + 1.0)

def nested(x):
    def inner(y):
        return leaf(y) + leaf(y + 1.0)
    return inner(x) + sum(leaf(float(i)) for i in range(3))

def catches(fn):
    try:
        return fn(2.0)
    except ValueError:
        return 99.0
'''


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_legacy_class(path, canonical):
    # Compile only these two original, unchanged AST definitions. No import,
    # manifest constructor, main, formula library or scientific code is run.
    tree = ast.parse(path.read_bytes(), filename=str(path))
    names = {'code_descendants', 'CompleteNumericSourceGuard'}
    selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                and node.name in names]
    if {node.name for node in selected} != names:
        raise RuntimeError('Exact original V10 definitions missing')
    def need(value, message):
        if value is not True:
            raise ValueError(message)
    env = dict(Path=Path, os=os, types=types, marshal=marshal, need=need,
               c=types.SimpleNamespace(sha=file_sha256),
               epoch=types.SimpleNamespace(load_canonical=lambda: canonical, hashlib=hashlib))
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec',
                 dont_inherit=True), env)
    return env['CompleteNumericSourceGuard']


class TracingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fixture-', dir=CTX['work_dir'])
        self.root = Path(self.temp.name)
        self.path = self.root / 'numeric_fixture.py'
        self.path.write_bytes(FORMULA.encode('ascii'))
        self.module = types.ModuleType('full18_bound_frozen_formulas')
        exec(compile(FORMULA, str(self.path), 'exec', dont_inherit=True), self.module.__dict__)
        self.before = {self.path.resolve().as_posix(): file_sha256(self.path)}

    def tearDown(self):
        sys.settrace(None)
        self.temp.cleanup()

    def guard(self, cls=CallOnlyNumericSourceGuard, before=None):
        return cls(self.before if before is None else before, [self.path], CTX['canonical'])

    def test_unselected_callers_do_not_hide_nested_numeric_calls(self):
        helper = types.ModuleType('non_numeric_fixture')
        helper.__dict__['fn'] = self.module.nested
        exec(compile('def outer(x):\n    return relay(x)\ndef relay(x):\n    return fn(x)\n',
                     str(self.root / 'unselected.py'), 'exec'), helper.__dict__)
        guard = self.guard()
        with guard.armed():
            result = helper.outer(2.0)
        self.assertGreater(guard.calls, 5)
        self.assertIn('leaf', {code.co_name for code, _ in guard.code_cache})
        self.assertEqual(result, self.module.nested(2.0))

    def test_v10_same_formula_bits_and_verified_call_sequence(self):
        events_old, events_new = [], []
        Legacy = CTX['legacy']
        class OldProbe(Legacy):
            def trace(self, frame, event, arg):
                if frame.f_globals.get('__name__') == 'full18_bound_frozen_formulas':
                    events_old.append((event, frame.f_code.co_qualname))
                return super().trace(frame, event, arg)
        class NewProbe(CallOnlyNumericSourceGuard):
            def trace(self, frame, event, arg):
                if frame.f_globals.get('__name__') == 'full18_bound_frozen_formulas':
                    events_new.append((event, frame.f_code.co_qualname))
                return super().trace(frame, event, arg)
        old = OldProbe(self.before, [self.path])
        sys.settrace(old.trace)
        try:
            values_old = [self.module.nested(x) for x in (0.0, 2.0, 9.0)]
        finally:
            sys.settrace(None)
        new = self.guard(NewProbe)
        with new.armed():
            values_new = [self.module.nested(x) for x in (0.0, 2.0, 9.0)]
        self.assertEqual([struct.pack('<d', x) for x in values_old],
                         [struct.pack('<d', x) for x in values_new])
        calls_old = [name for event, name in events_old if event == 'call']
        calls_new = [name for event, name in events_new if event == 'call']
        self.assertEqual(calls_old, calls_new)
        self.assertEqual(old.calls, new.calls)
        self.assertEqual(old.verifications, new.verifications)
        self.assertEqual({row['canonical_SHA256'] for row in old.raw_diagnostics},
                         {row['canonical_SHA256'] for row in new.raw_diagnostics})
        self.assertTrue(any(event == 'line' for event, _ in events_old))
        self.assertTrue(any(event == 'return' for event, _ in events_old))
        self.assertEqual({event for event, _ in events_new}, {'call'})
        CTX['equivalence'] = dict(
            scalar_binary64_hex=[struct.pack('<d', x).hex() for x in values_new],
            numeric_call_sequence=calls_new,
            v10_numeric_calls=old.calls, v11_numeric_calls=new.calls,
            v10_event_counts={key: sum(event == key for event, _ in events_old)
                              for key in ('call', 'line', 'return', 'exception')},
            v11_event_counts={key: sum(event == key for event, _ in events_new)
                              for key in ('call', 'line', 'return', 'exception')},
            identical_canonical_verified_code_set=True)

    def compare_actual_importlib_module(self, future_annotations):
        # Actual importlib compilation must not inherit this test module's
        # future flags. This deliberately differs from the old exec fixture.
        prefix = 'from __future__ import annotations\n' if future_annotations else ''
        self.path.write_bytes((prefix + FORMULA).encode('ascii'))
        self.module = load_module(self.path, 'full18_bound_frozen_formulas')
        self.before = {self.path.resolve().as_posix(): file_sha256(self.path)}
        has_future = bool(self.module.leaf.__code__.co_flags & __future__.annotations.compiler_flag)
        self.assertEqual(has_future, future_annotations)
        old = CTX['legacy'](self.before, [self.path])
        sys.settrace(old.trace)
        try:
            old_value = self.module.nested(2.0)
        finally:
            sys.settrace(None)
        new = self.guard()
        with new.armed():
            new_value = self.module.nested(2.0)
        self.assertEqual(struct.pack('<d', old_value), struct.pack('<d', new_value))
        self.assertEqual(old.calls, new.calls)
        self.assertEqual({row['canonical_SHA256'] for row in old.raw_diagnostics},
                         {row['canonical_SHA256'] for row in new.raw_diagnostics})
        CTX.setdefault('actual_importlib_future_regressions', []).append(dict(
            source_declares_future_annotations=future_annotations,
            imported_function_has_future_annotations_flag=has_future,
            v10_numeric_calls=old.calls, v11_numeric_calls=new.calls,
            scalar_binary64_hex=struct.pack('<d', new_value).hex(),
            identical_canonical_verified_code_set=True))

    def test_actual_importlib_module_without_future_annotations(self):
        self.compare_actual_importlib_module(False)

    def test_actual_importlib_module_with_source_future_annotations(self):
        self.compare_actual_importlib_module(True)

    def test_numeric_code_content_drift_rejected_before_body(self):
        fn = self.module.leaf
        constants = tuple(0.25 if type(x) is float and x == 0.125 else x
                          for x in fn.__code__.co_consts)
        fn.__code__ = fn.__code__.replace(co_consts=constants)
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                fn(2.0)

    def test_replaced_code_after_cache_hit_still_rejected(self):
        guard = self.guard()
        with self.assertRaises(SourceBindingError):
            with guard.armed():
                self.module.leaf(2.0)
                code = self.module.leaf.__code__
                self.module.leaf.__code__ = code.replace(co_name='different_name')
                self.module.leaf(2.0)

    def test_dynamic_numeric_filename_rejected(self):
        scope = dict(__name__='mpmath.dynamic_fixture')
        exec(compile('def dynamic(x):\n    return x + 1\n', '<unbound-numeric>', 'exec'), scope)
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                scope['dynamic'](2.0)

    def test_unselected_parent_cannot_hide_dynamic_numeric(self):
        scope = dict(__name__='mpmath.dynamic_fixture')
        exec(compile('def dynamic():\n    return 1\n', '<unbound-numeric>', 'exec'), scope)
        def unselected_parent():
            return scope['dynamic']()
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                unselected_parent()

    def test_unknown_numeric_path_rejected(self):
        other = self.root / 'other.py'
        other.write_text('def unknown():\n    return 1\n', encoding='ascii')
        scope = dict(__name__='full18_bound_frozen_formulas')
        exec(compile(other.read_bytes(), str(other), 'exec'), scope)
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                scope['unknown']()

    def test_whole_source_changed_before_first_binding_rejected(self):
        self.path.write_bytes((FORMULA + '\n# later source change\n').encode('ascii'))
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                self.module.leaf(2.0)

    def test_repeated_code_compiled_once_and_every_call_counted(self):
        guard = self.guard()
        with guard.armed():
            for _ in range(3):
                self.module.leaf(2.0)
        self.assertEqual(guard.calls, 3)
        self.assertEqual(guard.verifications, 1)
        self.assertEqual(len(guard.compiled), 1)

    def test_direct_noncall_hook_returns_none(self):
        guard = self.guard()
        frame = sys._getframe()
        for event in ('line', 'return', 'exception', 'opcode'):
            self.assertIsNone(guard.trace(frame, event, None))

    def test_preexisting_global_trace_is_rejected_and_retained(self):
        def original(frame, event, arg):
            return None
        sys.settrace(original)
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                self.fail('Should not enter')
        self.assertIs(sys.gettrace(), original)

    def test_existing_caller_local_trace_is_rejected_without_mutation(self):
        frame = sys._getframe()
        def original(frame, event, arg):
            return None
        frame.f_trace = original
        try:
            with self.assertRaises(SourceBindingError):
                with self.guard().armed():
                    self.fail('Should not enter')
            self.assertIs(frame.f_trace, original)
            self.assertIsNone(sys.gettrace())
        finally:
            frame.f_trace = None

    def test_caught_trace_failure_cannot_create_successful_scope(self):
        scope = dict(__name__='full18_bound_frozen_formulas')
        exec(compile('def bad(x):\n    return x\n', '<unbound-numeric>', 'exec'), scope)
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                self.assertEqual(self.module.catches(scope['bad']), 99.0)
        self.assertIsNone(sys.gettrace())

    def test_hook_removal_detected_on_scope_exit(self):
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                sys.settrace(None)

    def test_replacement_hook_not_silently_removed(self):
        def replacement(frame, event, arg):
            return None
        with self.assertRaises(SourceBindingError):
            with self.guard().armed():
                sys.settrace(replacement)
        self.assertIs(sys.gettrace(), replacement)

    def test_body_exception_propagates_and_hook_cleaned(self):
        with self.assertRaisesRegex(RuntimeError, 'body failure'):
            with self.guard().armed():
                self.module.leaf(2.0)
                raise RuntimeError('body failure')
        self.assertIsNone(sys.gettrace())

    def test_one_shot_scope_does_not_reuse_previous_success(self):
        guard = self.guard()
        with guard.armed():
            self.module.leaf(2.0)
        with self.assertRaises(SourceBindingError):
            with guard.armed():
                self.fail('Should not rearm')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--v10-entry', required=True, type=Path)
    parser.add_argument('--canonical-helper', required=True, type=Path)
    parser.add_argument('--work-dir', required=True, type=Path)
    parser.add_argument('--result', required=True, type=Path)
    args = parser.parse_args()
    if not sys.dont_write_bytecode or sys.flags.optimize:
        raise RuntimeError('Run with -B and without -O')
    if args.result.exists():
        raise RuntimeError('Fresh result path required; preserve earlier failures')
    args.work_dir.mkdir(parents=True, exist_ok=True)
    before = {str(path): file_sha256(path) for path in (args.v10_entry, args.canonical_helper)}
    canonical = load_module(args.canonical_helper, 'original_pinned_canonical_for_small_tests')
    CTX.update(canonical=canonical, work_dir=args.work_dir,
               legacy=load_legacy_class(args.v10_entry, canonical))
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TracingTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    after = {str(path): file_sha256(path) for path in (args.v10_entry, args.canonical_helper)}
    report = dict(
        schema='ACTUAL_HOTSPOT_V11_SMALL_CALL_BINDING_REGRESSION_V1',
        UTC=datetime.now(timezone.utc).isoformat(),
        actual_tests_run=result.testsRun, actual_failure_count=len(result.failures),
        actual_error_count=len(result.errors),
        failure_details=[dict(test=str(test), traceback=trace) for test, trace in result.failures],
        error_details=[dict(test=str(test), traceback=trace) for test, trace in result.errors],
        all_regressions_pass=result.wasSuccessful(),
        original_v10_and_canonical_small_source_before=before,
        original_v10_and_canonical_small_source_after=after,
        original_small_sources_unchanged=before == after,
        arithmetic_and_trace_comparison=CTX.get('equivalence'),
        actual_importlib_future_regressions=CTX.get('actual_importlib_future_regressions'),
        actual_MP80_MP100_geometry_validation_performed=False,
        actual_original_production_or_optimizer_or_MC_or_native_execution=False,
        scientific_physical_convergence_dual_language_reference_or_paper_PASS=False,
        current_thread_trace_after=None if sys.gettrace() is None else 'nonempty',
    )
    with args.result.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    return 0 if result.wasSuccessful() and before == after else 1


if __name__ == '__main__':
    raise SystemExit(main())
