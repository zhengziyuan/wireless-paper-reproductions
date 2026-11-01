"""Fail-closed typed canonical content of every public immutable code field.

This standard-library-only helper does not import or execute scientific code.
It deliberately does not serialize refcounts, intern flags, object identities,
defaults, closure contents, globals, adaptive caches, or arbitrary objects.
Those are NOT certified by a code-content comparison. Raw marshal digests are
available as separate diagnostics and must not be sufficient change gates.
"""
from __future__ import annotations
import hashlib
import json
import marshal
import struct
import types

SCHEMA='TYPED_COMPLETE_IMMUTABLE_CODE_FIELDS_CANONICAL_V1'
CODE_FIELDS=(
    'co_argcount','co_posonlyargcount','co_kwonlyargcount','co_nlocals',
    'co_stacksize','co_flags','co_code','co_consts','co_names','co_varnames',
    'co_filename','co_name','co_qualname','co_firstlineno','co_linetable',
    'co_exceptiontable','co_freevars','co_cellvars')


def canonical_bytes(value):
    """Stable JSON for an already typed payload, never str/repr conversion."""
    return json.dumps(value,sort_keys=True,ensure_ascii=True,
        separators=(',',':'),allow_nan=False).encode('ascii')


def immutable_value(value):
    """Retain type, nested code, sequence order, and exact floating-point bits."""
    kind=type(value)
    if kind is types.CodeType:
        return {'kind':'code','fields':{name:immutable_value(getattr(value,name))
            for name in CODE_FIELDS}}
    if kind is tuple:
        return {'kind':'tuple','values':[immutable_value(item) for item in value]}
    if kind is frozenset:
        values=[immutable_value(item) for item in value]
        return {'kind':'frozenset','values':sorted(values,key=canonical_bytes)}
    if kind is bytes:return {'kind':'bytes','hex':value.hex()}
    if kind is float:return {'kind':'float','binary64_big_endian_hex':struct.pack('>d',value).hex()}
    if kind is complex:return {'kind':'complex',
        'real_binary64_big_endian_hex':struct.pack('>d',value.real).hex(),
        'imag_binary64_big_endian_hex':struct.pack('>d',value.imag).hex()}
    if value is Ellipsis:return {'kind':'ellipsis'}
    if value is None:return {'kind':'none'}
    if kind is bool:return {'kind':'bool','value':value}
    if kind is int:return {'kind':'int','value':value}
    if kind is str:return {'kind':'str','value':value}
    raise TypeError('Unsupported immutable code constant type; fail closed')


def code_content(code):
    if type(code) is not types.CodeType:raise TypeError('Exact CodeType required')
    return {'schema':SCHEMA,'complete_immutable_code':immutable_value(code)}


def code_sha256(code):return hashlib.sha256(canonical_bytes(code_content(code))).hexdigest()


def module_code_profile(module):
    """Same selection as the prior audit: module callables having __code__."""
    return {name:code_sha256(fn.__code__) for name,fn in vars(module).items()
        if callable(fn) and hasattr(fn,'__code__')}


def module_raw_marshal_diagnostics(module):
    """Retained raw hashes only; reference/intern flags are non-content state."""
    return {name:hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest()
        for name,fn in vars(module).items() if callable(fn) and hasattr(fn,'__code__')}
