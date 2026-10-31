"""Disabled case13 saved-matrix PSD check. No optimizer or channel generation.

Only an independently reviewed, storage-guarded single-task admission may enable
real input. The pure arithmetic functions can be exercised with toy matrices.
"""
import base64
import json
import math
import os
import struct
import time
from fractions import Fraction as F
from pathlib import Path

REAL_CHECK_ENABLED = False
N = 16
MAX_BITS = 8192
MAX_SECONDS = 480
MAX_OUTPUT = 512 * 1024
MAX_LINE = 16384
TERMINAL_RESERVE = 4096
ORDINALS = (1327666, 1327713, 1327755, 1327778,
            1327876, 1327926, 1327964, 1328004)
ZERO = F(0)


class ResourceLimit(Exception):
    pass


def checked(x, deadline, max_bits):
    if time.monotonic() >= deadline:
        raise ResourceLimit('internal time bound')
    if x.numerator.bit_length() > max_bits or x.denominator.bit_length() > max_bits:
        raise ResourceLimit('rational bit bound')
    return x


def add(a, b):
    return a[0] + b[0], a[1] + b[1]


def sub(a, b):
    return a[0] - b[0], a[1] - b[1]


def conj(a):
    return a[0], -a[1]


def mul(a, b):
    return a[0]*b[0] - a[1]*b[1], a[0]*b[1] + a[1]*b[0]


def bounded_pair(x, deadline, max_bits):
    return checked(x[0], deadline, max_bits), checked(x[1], deadline, max_bits)


def ratio(x):
    return {'numerator': str(x.numerator), 'denominator': str(x.denominator)}


def examine(matrix, *, deadline, max_bits=MAX_BITS):
    """Exact A-A^H residual and PSD of H=(A+A^H)/2, for rational pairs.

    A negative pivot gives a negative Schur-complement direction. A zero pivot
    with a nonzero remaining row implies a negative 2x2 determinant. Elimination
    by positive pivots is a congruence, so these are exact PSD decisions for H.
    """
    n = len(matrix)
    if not 1 <= n <= N or any(len(row) != n for row in matrix):
        raise ValueError('matrix shape')
    residual_real = ZERO
    residual_imag = ZERO
    h = [[None] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            a, b = matrix[i][j], conj(matrix[j][i])
            d = bounded_pair(sub(a, b), deadline, max_bits)
            residual_real = max(residual_real, abs(d[0]))
            residual_imag = max(residual_imag, abs(d[1]))
            s = add(a, b)
            h[i][j] = bounded_pair((s[0] / 2, s[1] / 2), deadline, max_bits)
    positive = 0
    for k in range(n):
        p, imag = h[k][k]
        checked(p, deadline, max_bits)
        if imag != 0:
            raise ValueError('internal non-Hermitian Schur complement')
        if p < 0:
            status = 'not_psd_negative_pivot'
            witness = {'index_zero_based': k, 'pivot': ratio(p)}
            break
        if p == 0:
            nonzero = next((j for j in range(k+1, n) if h[k][j] != (0, 0)), None)
            if nonzero is not None:
                status = 'not_psd_zero_pivot_nonzero_row'
                witness = {'index_zero_based': k, 'other_index_zero_based': nonzero,
                           'schur_offdiagonal_real': ratio(h[k][nonzero][0]),
                           'schur_offdiagonal_imag': ratio(h[k][nonzero][1])}
                break
            continue
        positive += 1
        for i in range(k+1, n):
            for j in range(i, n):
                term = mul(h[i][k], conj(h[j][k]))
                term = bounded_pair((term[0] / p, term[1] / p), deadline, max_bits)
                x = bounded_pair(sub(h[i][j], term), deadline, max_bits)
                h[i][j] = x
                h[j][i] = conj(x)
    else:
        status = 'psd_exact_hermitian_part'
        witness = None
    return {'status': status, 'positive_pivots_before_stop': positive,
            'max_abs_antihermitian_real_component': ratio(residual_real),
            'max_abs_antihermitian_imag_component': ratio(residual_imag),
            'witness': witness}


def decode_array(d, shape):
    if (not isinstance(d, dict) or d.get('shape') != shape or
        d.get('order') != 'MATLAB_column_major' or
        d.get('encoding') != 'ieee754_binary64_little_endian_base64'):
        raise ValueError('unsupported array format')
    count = math.prod(shape)
    def component(key):
        if key not in d:
            return [ZERO] * count
        raw = base64.b64decode(d[key], validate=True)
        if len(raw) != count * 8:
            raise ValueError('incorrect component length')
        numbers = struct.unpack('<' + str(count) + 'd', raw)
        if not all(math.isfinite(v) for v in numbers):
            raise ValueError('nonfinite matrix value')
        return [F.from_float(v) for v in numbers]
    if 'real_base64' not in d:
        raise ValueError('missing real component')
    return list(zip(component('real_base64'), component('imag_base64')))


def matrix_at(words, count, k):
    return [[words[k + count*r + count*N*c] for c in range(N)] for r in range(N)]


def read_json(path, cap):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('duplicate key')
            out[k] = v
        return out
    with path.open('rb') as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap:
        raise ValueError('input size cap')
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def validate_inputs(ao, q):
    if (ao.get('schema') != 'CASE13_ALL_AO_IDENTITY_COMPACT_FIELDS_V1' or
        q.get('schema') != 'CASE13_HU_Q_RATE_PROJECTION_V1' or
        len(ao['arrays']) != 1 or len(q['arrays']) != 7 or
        len(ao['events']) != 8 or len(q['events']) != 8):
        raise ValueError('fixed case13 projection schema')
    if tuple(e['ordinal'] for e in ao['events']) != ORDINALS:
        raise ValueError('AO event ordering')
    refs = [e['q_array_ref'] for e in q['events']]
    if any(type(x) is not int for x in refs) or refs != [0,1,2,2,3,4,5,6]:
        raise ValueError('fixed Q references')
    for ix, (a, b) in enumerate(zip(ao['events'], q['events'])):
        if (a['ordinal'], a['context']) != (b['ordinal'], b['context']):
            raise ValueError('AO and Q event association')
        context = a['context']
        for key, wanted in {'case_id':13, 'geometry_id':12013, 'U':1,
                            'beta':20, 'start_id':ix//4}.items():
            if type(context.get(key)) is not int or context[key] != wanted:
                raise ValueError('case13 fixed context')
        if context.get('scheme') != 'AO':
            raise ValueError('case13 AO scheme')
        if type(a['fields']['Psi']['array_ref']) is not int or a['fields']['Psi']['array_ref'] != 0:
            raise ValueError('shared Psi binding')


class BoundedJsonlWriter:
    """Use an already securely opened fresh binary stream."""
    def __init__(self, stream, *, durable=False):
        self.stream = stream
        self.durable = durable
        self.written = 0

    def emit(self, value, terminal=False):
        raw = (json.dumps(value, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')
        limit = MAX_OUTPUT if terminal else MAX_OUTPUT - TERMINAL_RESERVE
        if len(raw) > MAX_LINE or self.written + len(raw) > limit:
            raise ResourceLimit('result stream byte cap')
        written = self.stream.write(raw)
        if type(written) is int and written >= 0:
            self.written += written
        if written != len(raw):
            raise OSError('short result stream write')
        self.stream.flush()
        if self.durable:
            os.fsync(self.stream.fileno())


def run_projected(ao, q, writer, *, deadline):
    """Emit completed records immediately, then one honest terminal record.

    The unenabled caller must bind inputs and give the writer an exclusive file.
    A killed process or failed write may prevent a terminal line; the guard must
    retain the partial stream and its own exit/termination record in that case.
    """
    count = 0
    current = 'input_validation'
    try:
        if not REAL_CHECK_ENABLED:
            raise RuntimeError('disabled: real-data guard admission required')
        validate_inputs(ao, q)
        psi = decode_array(ao['arrays'][0], [15, N, N])
        for k in range(15):
            current = 'Psi:' + str(k+1)
            writer.emit({'kind':'matrix', 'matrix':'Psi', 'user_one_based':k+1,
                         **examine(matrix_at(psi, 15, k), deadline=deadline)})
            count += 1
        for e in q['events']:
            current = 'Q:' + str(e['ordinal'])
            ref = e['q_array_ref']
            if type(ref) is not int or not 0 <= ref < len(q['arrays']):
                raise ValueError('Q reference')
            words = decode_array(q['arrays'][ref], [1, N, N])
            writer.emit({'kind':'matrix', 'matrix':'Q', 'ordinal':e['ordinal'],
                         'q_array_ref':ref,
                         **examine(matrix_at(words, 1, 0), deadline=deadline)})
            count += 1
        failure = None
    except Exception as exc:
        failure = {'stage':current, 'type':type(exc).__name__, 'detail':str(exc)[:240]}
    terminal = {'kind':'terminal', 'schema':'CASE13_SAVED_HERMITIAN_PART_EXACT_PSD_PREPARED_V1',
                'completed':failure is None and count == 23, 'records_completed':count,
                'failure':failure, 'arithmetic':'exact rationals of retained binary64 entries',
                'historical_source_authenticated':False,
                'full_physical_convergence_reference_or_paper_pass':False}
    writer.emit(terminal, terminal=True)
    return terminal


def main():
    raise RuntimeError('disabled: no reviewed real-data guard adapter exists')


if __name__ == '__main__':
    main()
