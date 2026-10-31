"""Call-only replacement for the Hotspot V10 numerical source binder.

This module does not import a numerical library or execute a scientific model.
The caller must bind its complete source epoch and check that epoch afterward.
Only immutable Python code content is checked here, as in V10: defaults,
closure contents, globals, native DLLs and scientific acceptance are not proved.
"""
from __future__ import annotations

import hashlib
import marshal
import os
from pathlib import Path
import sys
import threading
import types


# This is the V10 selector, including its exact module names.
NUMERIC_MODULE_NAMES = frozenset((
    'full18_bound_frozen_formulas',
    'independent_full_event_math_sourceonly_v4',
    'independent_geometry_kernels_sourceonly_v1',
    'literal_typed_MP_adapter_sourceonly_v1',
    'independent_conic_prefix_sourceonly_v3',
    'full_coordinate_comparison_sourceonly_v4',
    'exact_sparse_logical_vector_sourceonly_v2',
    'exact_CVX_SDPT3_terminal_contract_stdlib_v3',
    'exact_original_full_causal_contract_stdlib_v4',
    'exact_selected_MP_runtime_contract_stdlib_v4',
))


class SourceBindingError(ValueError):
    """The selected numerical code is outside its declared immutable epoch."""


def need(value, message):
    if value is not True:
        raise SourceBindingError(message)


def code_descendants(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            yield from code_descendants(value)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


class CallOnlyNumericSourceGuard:
    """Preserve V10 call binding without installing any local line tracer.

    `canonical` is the caller's pinned original canonical_code_fields module;
    no substitute code digest or raw-marshal equality gate is introduced.
    Every selected call is validated, even below an unselected caller. A global
    sys.settrace callback still receives nested call events when it returns
    None for the caller. Returning None only declines that frame's local
    line/return/exception events.

    Use `with guard.armed(): ...` in a fresh, untraced current thread. Existing
    caller-local trace functions are rejected too; they are never overwritten.
    This is not a security boundary against arbitrary code disabling tracing.
    It does detect loss/replacement of its hook and caught binding errors at
    normal scope exit. Other threads are not bound by this current-thread API.
    """

    def __init__(self, before, selected_numeric_paths, canonical):
        self.before = dict(before)
        self.paths = {Path(p).resolve().as_posix() for p in selected_numeric_paths}
        self.canonical = canonical
        need(callable(getattr(canonical, 'code_sha256', None)),
             'Caller supplies the pinned original typed canonical helper')
        self.file_cache = {}
        self.code_cache = set()
        self.compiled = {}
        self.calls = 0
        self.verifications = 0
        self.raw_diagnostics = []
        self._active = False
        self._used = False
        self._callback = None
        self._thread = None
        self._binding_failed = None

    def trace(self, frame, event, arg):
        # Every non-error branch returns None: no per-frame local tracer.
        if event != 'call':
            return None
        try:
            filename = frame.f_code.co_filename
            name = frame.f_globals.get('__name__', '')
            numeric = name.startswith('mpmath') or name in NUMERIC_MODULE_NAMES
            if not numeric:
                return None
            self.calls += 1
            need(not filename.startswith('<'),
                 'Unbound dynamically generated numerical frame: ' + filename)
            absolute = os.path.isabs(filename)
            path = self.file_cache.get(filename) if absolute else None
            if path is None:
                path = Path(filename).resolve(strict=True).as_posix()
                need(path in self.paths and path in self.before,
                     'Every actual selected numeric frame source path pinned')
                if absolute:
                    self.file_cache[filename] = path
            token = (frame.f_code, filename)
            if absolute and token in self.code_cache:
                return None
            binding = (path, filename)
            if binding not in self.compiled:
                need(file_sha256(path) == self.before[path],
                     'Actual current whole numerical source before first callable binding')
                self.compiled[binding] = {
                    self.canonical.code_sha256(code):
                    hashlib.sha256(marshal.dumps(code)).hexdigest()
                    for code in code_descendants(compile(Path(path).read_bytes(), filename, 'exec',
                                                         dont_inherit=True))
                }
            canonical = self.canonical.code_sha256(frame.f_code)
            need(canonical in self.compiled[binding],
                 'Every immutable typed code field equals whole pinned compiled source')
            self.raw_diagnostics.append(dict(
                path=path, filename=filename, canonical_SHA256=canonical,
                compiled_raw_marshal_SHA256=self.compiled[binding][canonical],
                actual_raw_marshal_SHA256=hashlib.sha256(marshal.dumps(frame.f_code)).hexdigest(),
                raw_marshal_digest_is_diagnostic_not_gate=True,
                defaults_closure_globals_or_all_loaded_DLL_certified=False,
            ))
            self.verifications += 1
            if absolute:
                self.code_cache.add(token)
            return None
        except BaseException as failure:
            # CPython unsets a trace function which raises. Retain that fact
            # even if user code later catches the propagated binding error.
            self._binding_failed = failure
            raise

    def armed(self):
        return self

    def __enter__(self):
        need(not self._active and not self._used, 'One fresh binding scope per guard')
        need(sys.gettrace() is None, 'Fresh current thread; existing global tracer rejected')
        caller = sys._getframe(1)
        try:
            while caller is not None:
                need(caller.f_trace is None, 'Existing caller-local tracer rejected')
                caller = caller.f_back
        finally:
            del caller
        self._thread = threading.get_ident()
        self._callback = self.trace
        self._used = True
        self._active = True
        sys.settrace(self._callback)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        need(threading.get_ident() == self._thread, 'Binding scope exits in original thread')
        current = sys.gettrace()
        hook_intact = current is self._callback
        if hook_intact:
            sys.settrace(None)
        # Do not silently remove another party's replacement tracing function.
        self._active = False
        if exc_type is None:
            need(self._binding_failed is None, 'Numerical binding failure was caught inside scope')
            need(hook_intact, 'Call-only trace hook was removed or replaced inside scope')
        return False

    def report(self):
        return dict(
            schema='HOTSPOT_CALL_ONLY_NUMERIC_SOURCE_BINDING_V11',
            calls=self.calls, verified_codes=self.verifications,
            compiled_source_bindings=len(self.compiled),
            full_raw_marshal_diagnostics=self.raw_diagnostics,
            original_v10_numeric_selector_preserved=True,
            local_line_return_or_exception_tracer_installed=False,
            binding_failure_observed=self._binding_failed is not None,
            source_interval_checked_by_this_helper=False,
            scientific_or_paper_acceptance_certified=False,
            current_thread_only=True,
        )
