"""Bounded, explicit-admission storage of completed independent MP kernels.

No MP import, pickle, model, optimizer, process control or directory discovery.
Caller supplies its original MP context and genuine source-boundary snapshots.
Cross-run admission is external: payload self-description is not provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import uuid


SCHEMA = 'HOTSPOT_EXACT_COMPLETED_KERNEL_PAYLOAD_V1'
RECEIPT_SCHEMA = 'HOTSPOT_COMPLETED_KERNEL_SOURCE_INTERVAL_RECEIPT_V1'
RUN_SCHEMA = 'HOTSPOT_EXPLICIT_KERNEL_PRODUCER_RUN_V1'
KINDS = {'complete_deterministic_geometry', 'one_complete_finite_CN_NHU_projector16'}
HEX64 = re.compile(r'[0-9a-f]{64}\Z')


class KernelCacheError(ValueError):
    pass


def require(condition, message):
    if condition is not True:
        raise KernelCacheError(message)


@dataclass(frozen=True)
class Limits:
    payload_bytes: int = 2 * 1024 * 1024
    metadata_bytes: int = 256 * 1024
    total_new_bytes: int = 256 * 1024 * 1024
    entries: int = 1024
    nodes: int = 50000
    depth: int = 32
    matrix_elements: int = 4096
    integer_bits: int = 8192

    def __post_init__(self):
        require(all(type(value) is int and value > 0 for value in vars(self).values()),
                'Strict positive resource bounds')


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def descriptor_key(descriptor):
    # Same JSON operation and complete preimage as existing keys.digest().
    return sha_bytes(canonical_bytes(descriptor))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON object field rejected')
        result[key] = value
    return result


def _read_json(path, expected_sha, limit):
    require(type(expected_sha) is str and HEX64.fullmatch(expected_sha) is not None,
            'Explicit exact file commitment required')
    with Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'Bounded cache file size exceeded')
    require(sha_bytes(raw) == expected_sha, 'Exact admitted cache file bytes changed')
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          KernelCacheError('Nonfinite JSON constant rejected')))


class ExactMPCodec:
    """Finite original MP tuples, complete matrices and strict typed containers.

    MP values are reconstructed with make_mpf/make_mpc, not rounded decimal
    strings or current-precision arithmetic. The tuple is checked again after
    construction. Matrix cells are full column-major, including explicit zero.
    """

    def __init__(self, mp, limits=Limits()):
        self.mp, self.limits = mp, limits

    def _integer(self, value):
        require(type(value) is int and value.bit_length() <= self.limits.integer_bits,
                'Bounded exact Python integer')
        return str(value)

    def _parse_integer(self, text):
        require(type(text) is str and len(text) <= self.limits.integer_bits // 3 + 3
                and re.fullmatch(r'0|-?[1-9][0-9]*', text) is not None,
                'Canonical bounded integer token')
        value = int(text)
        self._integer(value)
        return value

    def _mp_tuple(self, value):
        require(type(value) is tuple and len(value) == 4
                and all(type(x) is int for x in value), 'Exact pure-Python MP tuple')
        sign, man, exponent, bits = value
        require(sign in (0, 1) and man >= 0 and bits >= 0 and bits == man.bit_length()
                and abs(exponent) <= 2147483647
                and (man % 2 == 1 if man else value == (0, 0, 0, 0)),
                'Canonical finite MP tuple; NaN/Inf and malformed zero rejected')
        return [self._integer(x) for x in value]

    def _parse_mp_tuple(self, value):
        require(type(value) is list and len(value) == 4, 'Complete MP tuple token')
        result = tuple(self._parse_integer(x) for x in value)
        self._mp_tuple(result)
        return result

    def encode(self, value):
        count = [0]
        def visit(item, depth):
            count[0] += 1
            require(count[0] <= self.limits.nodes and depth <= self.limits.depth,
                    'Bounded codec nodes and depth')
            kind = type(item)
            if item is None: return ['none']
            if kind is bool: return ['bool', item]
            if kind is int: return ['int', self._integer(item)]
            if kind is str:
                require(len(item.encode('utf-8')) <= self.limits.metadata_bytes,
                        'Bounded payload string')
                return ['str', item]
            if kind is float:
                require(math.isfinite(item), 'Finite binary64 metadata only')
                return ['binary64', struct.pack('>d', item).hex()]
            if kind is self.mp.mpf:
                return ['mpf', self._mp_tuple(item._mpf_)]
            if kind is self.mp.mpc:
                return ['mpc', self._mp_tuple(item._mpc_[0]), self._mp_tuple(item._mpc_[1])]
            if kind is self.mp.matrix:
                rows, cols = item.rows, item.cols
                require(type(rows) is type(cols) is int and rows >= 0 and cols >= 0
                        and rows * cols <= self.limits.matrix_elements, 'Bounded complete matrix')
                return ['matrix', rows, cols, [visit(item[row, col], depth + 1)
                        for col in range(cols) for row in range(rows)]]
            if kind in (list, tuple):
                return ['list' if kind is list else 'tuple', [visit(x, depth + 1) for x in item]]
            if kind is dict:
                require(all(type(key) is str for key in item), 'String dictionary keys only')
                return ['dict', [[key, visit(val, depth + 1)] for key, val in item.items()]]
            raise KernelCacheError('Unsupported payload type: ' + kind.__name__)
        return visit(value, 0)

    def decode(self, tree):
        count = [0]
        def visit(item, depth):
            count[0] += 1
            require(count[0] <= self.limits.nodes and depth <= self.limits.depth,
                    'Bounded decoded nodes and depth')
            require(type(item) is list and item and type(item[0]) is str, 'Strict tagged payload')
            tag = item[0]
            if tag == 'none' and len(item) == 1: return None
            if tag == 'bool' and len(item) == 2 and type(item[1]) is bool: return item[1]
            if tag == 'int' and len(item) == 2: return self._parse_integer(item[1])
            if tag == 'str' and len(item) == 2 and type(item[1]) is str: return item[1]
            if tag == 'binary64' and len(item) == 2:
                require(type(item[1]) is str and re.fullmatch(r'[0-9a-f]{16}', item[1]) is not None,
                        'Exact binary64 bits')
                value = struct.unpack('>d', bytes.fromhex(item[1]))[0]
                require(math.isfinite(value), 'Finite binary64 metadata only')
                return value
            if tag == 'mpf' and len(item) == 2:
                raw = self._parse_mp_tuple(item[1]); value = self.mp.make_mpf(raw)
                require(value._mpf_ == raw, 'No MP tuple rounding during decode')
                return value
            if tag == 'mpc' and len(item) == 3:
                raw = (self._parse_mp_tuple(item[1]), self._parse_mp_tuple(item[2]))
                value = self.mp.make_mpc(raw)
                require(value._mpc_ == raw, 'No complex MP tuple rounding during decode')
                return value
            if tag == 'matrix' and len(item) == 4:
                rows, cols, cells = item[1:]
                require(type(rows) is type(cols) is int and rows >= 0 and cols >= 0
                        and rows * cols <= self.limits.matrix_elements
                        and type(cells) is list and len(cells) == rows * cols,
                        'Exact bounded matrix shape and all cells')
                value = self.mp.matrix(rows, cols)
                for col in range(cols):
                    for row in range(rows):
                        cell = visit(cells[col * rows + row], depth + 1)
                        require(type(cell) in (self.mp.mpf, self.mp.mpc), 'MP matrix cell only')
                        value[row, col] = cell
                        actual = value[row, col]
                        require(self.encode(actual) == self.encode(cell), 'Matrix assignment preserved MP bits')
                return value
            if tag in ('list', 'tuple') and len(item) == 2 and type(item[1]) is list:
                values = [visit(x, depth + 1) for x in item[1]]
                return values if tag == 'list' else tuple(values)
            if tag == 'dict' and len(item) == 2 and type(item[1]) is list:
                result = {}
                for pair in item[1]:
                    require(type(pair) is list and len(pair) == 2 and type(pair[0]) is str
                            and pair[0] not in result, 'Ordered distinct dictionary fields')
                    result[pair[0]] = visit(pair[1], depth + 1)
                return result
            raise KernelCacheError('Unknown or malformed exact payload tag')
        return visit(tree, 0)


def snapshot_v11_numeric_source_boundary(guard, source_epoch, *, maximum_files=1024,
                                        maximum_file_bytes=4 * 1024 * 1024,
                                        maximum_total_bytes=16 * 1024 * 1024):
    """Optional real boundary supplier: only explicit small .py source files.

    Supply the complete selected numerical Python source epoch, not trace
    chunks, scientific arrays, a project tree, or arbitrary runtime binaries.
    This checks the V11 hook and actual source bytes, not native DLL identity.
    """
    require(type(source_epoch) is dict and 0 < len(source_epoch) <= maximum_files,
            'Explicit bounded numerical source file list')
    require(guard._active is True and sys.gettrace() is guard._callback
            and guard._binding_failed is None, 'Original live V11 binding scope')
    normalized = {Path(name).resolve().as_posix(): expected for name, expected in source_epoch.items()}
    require(len(normalized) == len(source_epoch) and guard.paths <= set(normalized)
            and all(normalized[name] == guard.before.get(name) for name in guard.paths),
            'Boundary must cover every selected numerical source and its original pin')
    actual, total = {}, 0
    for name, expected in source_epoch.items():
        require(type(name) is str and Path(name).suffix == '.py'
                and type(expected) is str and HEX64.fullmatch(expected) is not None,
                'Only pinned Python source file identities')
        with Path(name).open('rb') as stream:
            raw = stream.read(maximum_file_bytes + 1)
        total += len(raw)
        require(len(raw) <= maximum_file_bytes and total <= maximum_total_bytes,
                'Source snapshot resource bound')
        actual[name] = sha_bytes(raw)
        require(actual[name] == expected, 'Kernel source interval drift')
    return dict(source_SHA256=actual, numeric_calls=guard.calls,
                verified_codes=guard.verifications, binding_hook_active=True,
                binding_failure_observed=False)


def geometry_descriptor(keys, config, precision, runtime, formulas, lane):
    require(lane in ('full_physical_MP_pi', 'literal_binary64_constants_point'), 'Constructor lane')
    return dict(scope=keys.scope_key(precision, runtime, formulas, 'complete_deterministic_geometry'),
                config=keys.canonical_literal(config), constructor_lane=lane)


def projector_descriptor(keys, mean, variance, precision, runtime, formulas, row):
    mean.numeric('double'); variance.numeric('double', real=True)
    require(mean.header['size'] == variance.header['size'], 'Same complete NHU row population')
    return dict(scope=keys.scope_key(precision, runtime, formulas, 'one_complete_finite_CN_NHU_projector16'),
                mean=keys.literal_row_bits(mean, row), variance=keys.literal_row_bits(variance, row),
                conjugated_mean_original_model=True, interval_splits=['0', '0.5', '0.9', '0.99', '1'],
                transform='t=s/(1-s)', all16x16_entries=True,
                Hermitian_partners_are_mathematical_not_native_bits=True)


class PersistentExactKernelCache:
    """Fresh single-writer run; only explicit previously admitted receipts hit.

    A boundary supplier is trusted executed host code, not a mathematical
    oracle. It must actually check the complete declared source interval and
    current numerical binding hook at both boundaries. The cache independently
    validates its supplied maps/counters but cannot authenticate an arbitrary
    caller or OS identity. Cross-run `admitted` records must therefore be
    approved outside this module against genuine executed source evidence.
    """

    def __init__(self, root, mp, run_identity, source_epoch, expected_lineage,
                 boundary_supplier, admitted=None, limits=Limits(), allow_synthetic=False):
        self.mp, self.limits = mp, limits
        require(mp.dps in (80, 100), 'Original MP80/100 context only')
        self.codec = ExactMPCodec(mp, limits)
        self.source_epoch = dict(source_epoch)
        require(bool(self.source_epoch) and all(type(k) is str and type(v) is str and HEX64.fullmatch(v)
                for k, v in self.source_epoch.items()), 'Explicit complete source epoch')
        self.epoch_sha = descriptor_key(self.source_epoch)
        self.lineage = json.loads(canonical_bytes(expected_lineage))
        require(type(expected_lineage) is dict and set(expected_lineage) == {'runtime', 'formulas'},
                'Complete expected canonical runtime and formula lineage')
        require(callable(boundary_supplier), 'Executed source-boundary supplier required')
        self.boundary_supplier = boundary_supplier
        self.allow_synthetic = allow_synthetic
        self.run = dict(schema=RUN_SCHEMA, precision_decimal_digits=mp.dps,
                        source_epoch_SHA256=self.epoch_sha, identity=dict(run_identity))
        self._validate_run(self.run)
        self.root = Path(root)
        self.root.mkdir()  # Strict fresh run, not automatic resume of a directory.
        self.run_path = self.root / 'producer-run.json'
        raw = canonical_bytes(self.run)
        require(len(raw) <= limits.metadata_bytes and len(raw) <= limits.total_new_bytes,
                'Bounded producer identity')
        self._atomic(self.run_path, raw)
        self.run_sha = sha_bytes(raw)
        self.admitted = json.loads(canonical_bytes(admitted or {}))
        self.own = {}
        self.hits = self.misses = self.committed = self.failures = 0
        self.new_bytes = len(raw)
        self.last_error_record_failure = None

    def _validate_run(self, run):
        require(type(run) is dict and set(run) == {'schema', 'precision_decimal_digits',
                'source_epoch_SHA256', 'identity'} and run['schema'] == RUN_SCHEMA
                and run['precision_decimal_digits'] == self.mp.dps
                and run['source_epoch_SHA256'] == self.epoch_sha, 'Same exact producer precision/source epoch')
        identity = run['identity']
        require(type(identity) is dict and set(identity) == {'run_id', 'kind', 'admission_SHA256',
                'entry_SHA256', 'process_creation_identity'}, 'Complete declared run identity')
        try: canonical_id = str(uuid.UUID(identity['run_id']))
        except (ValueError, TypeError, AttributeError) as error:
            raise KernelCacheError('Valid declared run UUID required') from error
        require(canonical_id == identity['run_id']
                and type(identity['process_creation_identity']) is str and bool(identity['process_creation_identity'])
                and all(type(identity[k]) is str and HEX64.fullmatch(identity[k])
                        for k in ('admission_SHA256', 'entry_SHA256')),
                'Exact explicit producer identity fields')
        require(identity['kind'] == 'independent-kernel-producer'
                or (self.allow_synthetic and identity['kind'] == 'synthetic-regression'),
                'Synthetic origin is not admitted to production cache use')

    def _atomic(self, path, raw):
        require(not path.exists(), 'Never overwrite existing cache evidence')
        pending = path.with_name(path.name + '.partial-' + uuid.uuid4().hex)
        with pending.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        require(not path.exists(), 'Unexpected concurrent writer; partial retained')
        # Fresh private single-writer root. On Windows rename also refuses an
        # existing destination. No directory fsync/power-loss guarantee claimed.
        os.rename(pending, path)

    def _descriptor(self, key, descriptor):
        require(self.mp.dps == self.run['precision_decimal_digits'], 'Original context precision unchanged')
        require(type(key) is str and HEX64.fullmatch(key) is not None
                and type(descriptor) is dict and descriptor_key(descriptor) == key,
                'Full original key preimage and digest must agree')
        scope = descriptor.get('scope')
        require(type(scope) is dict and set(scope) == {'kernel', 'precision_decimal_digits',
                'runtime', 'formulas', 'key_is_exact_complete_literal_operand_not_case_or_array_index'}
                and scope['kernel'] in KINDS and scope['precision_decimal_digits'] == self.mp.dps
                and scope['key_is_exact_complete_literal_operand_not_case_or_array_index'] is True
                and all(scope[k] == self.lineage[k] for k in ('runtime', 'formulas')),
                'Unreduced original kernel/precision/runtime/formula scope')
        fields = ({'scope', 'config', 'constructor_lane'} if scope['kernel'] == 'complete_deterministic_geometry'
                  else {'scope', 'mean', 'variance', 'conjugated_mean_original_model', 'interval_splits',
                        'transform', 'all16x16_entries', 'Hermitian_partners_are_mathematical_not_native_bits'})
        require(set(descriptor) == fields, 'Strict complete original kernel descriptor schema')
        if scope['kernel'] == 'complete_deterministic_geometry':
            require(descriptor['constructor_lane'] in ('full_physical_MP_pi', 'literal_binary64_constants_point'),
                    'Exact constructor lane')
        else:
            require(descriptor['interval_splits'] == ['0', '0.5', '0.9', '0.99', '1']
                    and descriptor['transform'] == 't=s/(1-s)'
                    and descriptor['conjugated_mean_original_model'] is True
                    and descriptor['all16x16_entries'] is True
                    and descriptor['Hermitian_partners_are_mathematical_not_native_bits'] is True,
                    'Full finite-CN projector contract')

    def _boundary(self):
        require(self.mp.dps == self.run['precision_decimal_digits'], 'Kernel did not change original precision')
        value = self.boundary_supplier()
        require(type(value) is dict and set(value) == {'source_SHA256', 'numeric_calls',
                'verified_codes', 'binding_hook_active', 'binding_failure_observed'}
                and value['source_SHA256'] == self.source_epoch
                and value['binding_hook_active'] is True and value['binding_failure_observed'] is False
                and type(value['numeric_calls']) is type(value['verified_codes']) is int
                and value['numeric_calls'] >= 0 and value['verified_codes'] >= 0,
                'Actual complete source boundary and live code-binding snapshot required')
        return json.loads(canonical_bytes(value))

    def _value_shape(self, descriptor, value):
        if descriptor['scope']['kernel'] == 'one_complete_finite_CN_NHU_projector16':
            require(type(value) is self.mp.matrix and value.rows == value.cols == 16,
                    'Completed full16x16 projector only')
        else:
            names = {'mean_inputs', 'physical_thermal_noise_W', 'normalized_source_noise', 'power',
                     'nhu_target', 'hu_xy_m', 'nhu_xy_m', 'ris_xy_m', 'common_ground_pathloss_distance',
                     'constructor_lane', 'all_deterministic_original_dimensions',
                     'actual_random_channels_or_phi_generated', 'rigorous_forward_or_quadrature_certificate'}
            require(type(value) is dict and set(value) == names
                    and value['constructor_lane'] == descriptor['constructor_lane']
                    and value['actual_random_channels_or_phi_generated'] is False
                    and value['rigorous_forward_or_quadrature_certificate'] is False,
                    'Only complete original deterministic-geometry return')
            dims = value['all_deterministic_original_dimensions']
            require(type(dims) is tuple and len(dims) == 5
                    and all(type(x) is int for x in dims)
                    and dims[0:2] == (16, 16) and dims[4] == 25 and 1 <= dims[2] <= 6
                    and dims[3] == 16 - dims[2], 'Original geometry dimensions')
            def literal_field(node, key):
                require(type(node) is list and len(node) == 2 and node[0] == 'dict'
                        and type(node[1]) is list, 'Complete typed original config dictionary')
                pairs = node[1]
                require(all(type(pair) is list and len(pair) == 2 and type(pair[0]) is str for pair in pairs)
                        and len({pair[0] for pair in pairs}) == len(pairs), 'Distinct typed original config fields')
                values = dict(pairs)
                require(key in values, 'Required original configuration dimension')
                return values[key]
            reported = literal_field(descriptor['config'], 'reported')
            for name, expected in zip(('N', 'J', 'U', 'K', 'M'), dims):
                require(literal_field(reported, name) == ['int', str(expected)],
                        'Complete geometry shape must match the actual keyed original config')
            for name in ('physical_thermal_noise_W', 'normalized_source_noise', 'power',
                         'common_ground_pathloss_distance'):
                require(type(value[name]) is self.mp.mpf, 'Complete MP real geometry scalar')
            require(type(value['nhu_target']) is list and len(value['nhu_target']) == dims[3]
                    and all(type(x) is self.mp.mpf for x in value['nhu_target']), 'All original NHU targets')
            for name, length in (('hu_xy_m', dims[2]), ('nhu_xy_m', dims[3])):
                require(type(value[name]) is list and len(value[name]) == length
                        and all(type(point) is tuple and len(point) == 2
                        and all(type(x) is self.mp.mpf for x in point) for point in value[name]),
                        'All original geometry coordinates')
            require(type(value['ris_xy_m']) is tuple and len(value['ris_xy_m']) == 2
                    and all(type(x) is self.mp.mpf for x in value['ris_xy_m']), 'Complete RIS coordinates')
            require(type(value['mean_inputs']) is dict
                    and set(value['mean_inputs']) == {'direct_mean', 'direct_variance', 'matrix_mean',
                    'matrix_variance', 'ground_mean', 'ground_variance', 'nhu_mean', 'nhu_variance'},
                    'All eight mean/variance fields')
            for name, array in value['mean_inputs'].items():
                shape = ((dims[2], 16) if name.startswith('direct_') else (25, 16)
                         if name.startswith('matrix_') else (dims[2], 25)
                         if name.startswith('ground_') else (dims[3], 16))
                require(type(array) is self.mp.matrix and (array.rows, array.cols) == shape,
                        'Full original geometry field shape')

    def _load(self, key, descriptor, files):
        require(type(files) is dict and set(files) == {'payload_path', 'payload_SHA256',
                'receipt_path', 'receipt_SHA256', 'run_path', 'run_SHA256'}, 'Explicit admitted three-file identities')
        run = _read_json(files['run_path'], files['run_SHA256'], self.limits.metadata_bytes)
        self._validate_run(run)
        receipt = _read_json(files['receipt_path'], files['receipt_SHA256'], self.limits.metadata_bytes)
        require(type(receipt) is dict and set(receipt) == {'schema', 'key', 'run_SHA256', 'payload_SHA256',
                'descriptor_SHA256', 'value_SHA256', 'completed', 'source_before', 'source_after'}
                and receipt['schema'] == RECEIPT_SCHEMA and receipt['key'] == key
                and receipt['run_SHA256'] == files['run_SHA256']
                and receipt['payload_SHA256'] == files['payload_SHA256']
                and receipt['descriptor_SHA256'] == key and receipt['completed'] is True,
                'Completed externally admitted kernel receipt binding')
        for boundary in (receipt['source_before'], receipt['source_after']):
            require(type(boundary) is dict and set(boundary) == {'source_SHA256', 'numeric_calls',
                    'verified_codes', 'binding_hook_active', 'binding_failure_observed'}
                    and boundary['source_SHA256'] == self.source_epoch
                    and boundary['binding_hook_active'] is True and boundary['binding_failure_observed'] is False
                    and type(boundary['numeric_calls']) is type(boundary['verified_codes']) is int
                    and boundary['numeric_calls'] >= 0 and boundary['verified_codes'] >= 0,
                    'Genuine source-closed per-kernel evidence required for admission')
        require(receipt['source_after']['numeric_calls'] > receipt['source_before']['numeric_calls']
                and receipt['source_after']['verified_codes'] >= receipt['source_before']['verified_codes'],
                'Completed kernel numerical-call interval')
        payload = _read_json(files['payload_path'], files['payload_SHA256'], self.limits.payload_bytes)
        require(type(payload) is dict and set(payload) == {'schema', 'key', 'descriptor', 'run_SHA256', 'value'}
                and payload['schema'] == SCHEMA and payload['key'] == key
                and payload['descriptor'] == descriptor and payload['run_SHA256'] == files['run_SHA256']
                and descriptor_key(payload['value']) == receipt['value_SHA256'],
                'Exact key, complete value and executed producer binding')
        value = self.codec.decode(payload['value'])
        require(self.codec.encode(value) == payload['value'], 'Complete lossless typed value roundtrip')
        self._value_shape(descriptor, value)
        return value

    def independent(self, key, compute, *, descriptor):
        self._stage = 'validate_or_read'
        try:
            return self._independent(key, compute, descriptor=descriptor)
        except BaseException as error:
            self.failures += 1
            # Keep the original exception and every partial/orphan. A bounded
            # diagnostic cannot be guaranteed if the disk itself is failing.
            diagnostic = canonical_bytes(dict(schema='KERNEL_CACHE_FAILURE_RETAINED_V1',
                key=key if type(key) is str else None, exception_type=type(error).__name__,
                stage=self._stage, run_SHA256=self.run_sha, precision_decimal_digits=self.mp.dps,
                message=str(error)[:2048], no_retry_performed=True,
                completed_kernel_or_scientific_PASS_inferred=False))
            try:
                require(self.new_bytes + len(diagnostic) <= self.limits.total_new_bytes,
                        'No remaining byte budget for error diagnostic')
                self._atomic(self.root / ('failure-%06d.json' % self.failures), diagnostic)
                self.new_bytes += len(diagnostic)
            except BaseException as diagnostic_error:
                self.last_error_record_failure = type(diagnostic_error).__name__ + ': ' + str(diagnostic_error)[:256]
            raise

    def _independent(self, key, compute, *, descriptor):
        self._descriptor(key, descriptor)
        if key in self.own or key in self.admitted:
            value = self._load(key, descriptor, self.own.get(key) or self.admitted[key])
            self.hits += 1
            return value
        require(callable(compute), 'Original independent kernel callback required')
        require(self.committed < self.limits.entries, 'Cache entry resource bound reached')
        self.misses += 1
        self._stage = 'source_before'
        before = self._boundary()
        self._stage = 'original_kernel_callback'
        value = compute()  # No callback retry on any error.
        self._stage = 'source_after'
        after = self._boundary()
        require(after['numeric_calls'] > before['numeric_calls']
                and after['verified_codes'] >= before['verified_codes'], 'Actual completed numerical call interval')
        self._value_shape(descriptor, value)
        self._stage = 'lossless_encode'
        tree = self.codec.encode(value)
        payload = dict(schema=SCHEMA, key=key, descriptor=descriptor, run_SHA256=self.run_sha, value=tree)
        raw = canonical_bytes(payload)
        receipt = dict(schema=RECEIPT_SCHEMA, key=key, run_SHA256=self.run_sha,
                       payload_SHA256=sha_bytes(raw), descriptor_SHA256=key, value_SHA256=descriptor_key(tree),
                       completed=True, source_before=before, source_after=after)
        receipt_raw = canonical_bytes(receipt)
        require(len(raw) <= self.limits.payload_bytes and len(receipt_raw) <= self.limits.metadata_bytes
                and self.new_bytes + len(raw) + len(receipt_raw) <= self.limits.total_new_bytes,
                'Cache byte resource bound reached; completed computation is not a cache commit')
        payload_path = self.root / (key + '.payload.json')
        receipt_path = self.root / (key + '.completed.json')
        # Reserve conservatively before IO, including an incomplete second
        # write. A failure never resets this reservation or overwrites files.
        self.new_bytes += len(raw) + len(receipt_raw)
        self._stage = 'atomic_payload_write'
        self._atomic(payload_path, raw)
        self._stage = 'atomic_completion_receipt_write'
        self._atomic(receipt_path, receipt_raw)  # Commit marker is published last.
        files = dict(payload_path=str(payload_path), payload_SHA256=sha_bytes(raw),
                     receipt_path=str(receipt_path), receipt_SHA256=sha_bytes(receipt_raw),
                     run_path=str(self.run_path), run_SHA256=self.run_sha)
        self.own[key] = files
        self.committed += 1
        return value

    def committed_files(self):
        """Candidate evidence only; a later root must explicitly admit it."""
        return {key: dict(files) for key, files in self.own.items()}

    def report(self):
        return dict(hits=self.hits, misses=self.misses, uncached_capacity_fallback=0,
                    retained_kernel_count=self.committed, capacity=self.limits.entries,
                    new_committed_bytes=self.new_bytes, run_SHA256=self.run_sha,
                    retained_failure_count=self.failures,
                    last_error_record_failure=self.last_error_record_failure,
                    event_or_component_sampling_or_native_value_replacement=False,
                    native_scientific_speedup_measured_or_forward_certificate=False,
                    external_cross_run_origin_admission_required=True)


class RegisteredLaneKernelCache:
    """Thin optional host wiring; ReferenceLane and all math files stay intact.

    Future host: lane.cache = RegisteredLaneKernelCache(store, original_keys).
    Before each lane.check(routing), call lane.cache.prepare_event(lane,routing).
    This only registers complete original key preimages; lane.check still
    dispatches every original event and compares every original component.
    """

    def __init__(self, store, keys):
        self.store, self.keys, self.descriptors = store, keys, {}

    def prepare_event(self, lane, routing):
        descriptors = []
        if routing['action'] == 'geometry_end':
            for constructor in ('full_physical_MP_pi', 'literal_binary64_constants_point'):
                descriptors.append(geometry_descriptor(self.keys, lane.config, lane.mp.dps,
                                                       lane.runtime, lane.formulas, constructor))
        elif routing['action'] == 'design_context':
            require(type(lane.U) is int and 1 <= lane.U <= 6, 'Original full U1..6 only')
            source = routing['value']['x'].scalar_struct()
            require(source['nhu_mean'].header['size'] == source['nhu_variance'].header['size']
                    == [16 - lane.U, 16], 'Original full NHU population before per-row registration')
            for row in range(16 - lane.U):
                descriptors.append(projector_descriptor(self.keys, source['nhu_mean'], source['nhu_variance'],
                                   lane.mp.dps, lane.runtime, lane.formulas, row))
        self.descriptors = {descriptor_key(value): value for value in descriptors}

    def independent(self, key, compute):
        require(key in self.descriptors, 'No unregistered kernel or missing full key preimage')
        return self.store.independent(key, compute, descriptor=self.descriptors[key])

    def report(self):
        return self.store.report()
