"""Prepared exact saved-point QoS checks, not an executable scientific batch.

Fractions represent each stored binary64 exactly. Matrices independently formed
from saved channel moments and separately stored Psi are distinct inputs, and
their two results must not be conflated. A reviewed external guard and fixed
source/terminal binding are required before the default flag can be changed.
"""
import base64
import math
import struct
from fractions import Fraction

REAL_SCIENCE_ENABLED = False
ORDINALS = (1327666, 1327713, 1327755, 1327778,
            1327876, 1327926, 1327964, 1328004)
N, K, J = 16, 15, 16


def need(value, message):
    if value is not True: raise ValueError(message)


def q(value):
    need(type(value) in (int, float) and math.isfinite(value), 'finite binary64 number')
    return Fraction.from_float(float(value))


def ratio(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def decode_words(words, count):
    need(type(words) is list and len(words) == count, 'hex word count')
    out = []
    for word in words:
        need(type(word) is str and len(word) == 16, 'binary64 word')
        raw = bytes.fromhex(word)
        need(len(raw) == 8, 'binary64 word size')
        out.append(q(struct.unpack('<d', raw)[0]))
    return out


def decode_array(desc, shape):
    need(type(desc) is dict and desc.get('shape') == shape and
         desc.get('order') == 'MATLAB_column_major', 'array shape and ordering')
    count = math.prod(shape)
    if desc.get('encoding') == 'ieee754_binary64_little_endian_base64':
        real = base64.b64decode(desc['real_base64'], validate=True)
        need(len(real) == 8 * count, 'real byte count')
        rr = list(map(q, struct.unpack('<' + str(count) + 'd', real)))
        if 'imag_base64' in desc:
            imag = base64.b64decode(desc['imag_base64'], validate=True)
            need(len(imag) == 8 * count, 'imaginary byte count')
            ii = list(map(q, struct.unpack('<' + str(count) + 'd', imag)))
        else: ii = [Fraction(0)] * count
    else:
        need(type(desc.get('real')) is list and len(desc['real']) == count,
             'decimal binary64 count')
        rr = list(map(q, desc['real']))
        im = desc.get('imag', [0.0] * count)
        need(type(im) is list and len(im) == count, 'decimal imaginary count')
        ii = list(map(q, im))
    return list(zip(rr, ii))


def abs2(z): return z[0] * z[0] + z[1] * z[1]


def product_conj_left(a, b):
    return (a[0] * b[0] + a[1] * b[1], a[0] * b[1] - a[1] * b[0])


def gain_moments(mu, variance, w):
    """mu is channel row: w^H (mu^H mu + diag(v)) w."""
    real = sum((m[0]*z[0]-m[1]*z[1] for m,z in zip(mu,w)), Fraction(0))
    imag = sum((m[0]*z[1]+m[1]*z[0] for m,z in zip(mu,w)), Fraction(0))
    return real*real + imag*imag + sum((v*abs2(z) for v,z in zip(variance,w)), Fraction(0))


def gain_saved(matrix, w):
    """Real part of w^H Psi w, using the stored matrix without symmetrizing."""
    total = Fraction(0)
    for row in range(len(w)):
        for col in range(len(w)):
            p = product_conj_left(w[row], w[col])
            a = matrix[row][col]
            total += a[0]*p[0] - a[1]*p[1]
    return total


def assess(mu_rows, var_rows, psi_rows, columns, noise, target):
    """Exact margins with all J-1 interferers; dual independent matrix paths."""
    rows = []
    for k in range(len(mu_rows)):
        j = k + 1
        gm = [gain_moments(mu_rows[k], var_rows[k], w) for w in columns]
        gs = [gain_saved(psi_rows[k], w) for w in columns]
        dm = noise + sum((v for i,v in enumerate(gm) if i != j), Fraction(0))
        ds = noise + sum((v for i,v in enumerate(gs) if i != j), Fraction(0))
        need(dm > 0 and ds > 0, 'strictly positive exact interference denominator')
        mm, ms = gm[j] - target[k]*dm, gs[j] - target[k]*ds
        rows.append({'user_one_based': j+1, 'moments_margin': ratio(mm),
                     'saved_Psi_margin': ratio(ms), 'moments_positive': mm > 0,
                     'moments_zero': mm == 0, 'saved_Psi_positive': ms > 0,
                     'saved_Psi_zero': ms == 0})
    return rows


def compute(moment, all_ao, first, final):
    need(REAL_SCIENCE_ENABLED, 'reviewed external guard admission required')
    need(moment.get('schema') == 'ACTUAL_NATIVE_CASE_NHU_AND_COMPOSITE_INPUT_V1' and
         moment.get('complete_geometry_and_design_NHU_raw_words_identical') is True,
         'saved Case13 moment inputs')
    need(moment['original_context']['case_id'] == 13 and moment['original_context']['geometry_id'] == 12013,
         'fixed case and geometry')
    mean, variance = moment['full_NHU_mean'], moment['full_NHU_variance']
    need(mean['header']['size'] == [K,N] and variance['header']['size'] == [K,N] and
         mean['header']['order'] == variance['header']['order'] == 'MATLAB_column_major' and
         mean['header']['isreal'] is False and variance['header']['isreal'] is True, 'moment shapes')
    mr = decode_words(mean['real_hex_column_major'], K*N)
    mi = decode_words(mean['imag_hex_column_major'], K*N)
    vv = decode_words(variance['real_hex_column_major'], K*N)
    need(all(v >= 0 for v in vv), 'nonnegative saved variance')
    mu = [[(mr[k+K*i], mi[k+K*i]) for i in range(N)] for k in range(K)]
    var = [[vv[k+K*i] for i in range(N)] for k in range(K)]
    events = all_ao['events']; arrays = all_ao['arrays']; finals = final['events']
    need(all_ao.get('schema') == 'CASE13_ALL_AO_IDENTITY_COMPACT_FIELDS_V1' and
         all_ao.get('historical_chunk_content_reverified') is False and
         all_ao.get('whole_event_atomic_snapshot_verified') is False and
         all_ao.get('scientific_or_convergence_or_physics_pass') is False and
         all_ao.get('first_six_fields_prior_result') == 'hotspot-case13-first-ao-identity-extract-actual-v1/results/result.json',
         'explicitly conditional 8-AO source and fixed first-result reference')
    need(len(events) == 8 and [e['ordinal'] for e in events] == list(ORDINALS), 'complete 8 AO events')
    need([e['ordinal'] for e in finals] == [1327779,1328005], 'two final parameter events')
    need(final.get('schema') == 'CASE13_AO_FINAL_PARAMETERS_IDENTITY_V1' and
         final.get('historical_chunk_content_reverified') is False and
         first['ordinal'] == ORDINALS[0] and first['context'] == events[0]['context'] and
         first.get('historical_chunk_content_reverified') is False, 'bound first and final saved sources')
    records = []
    matrix_comparison = None
    for ix,event in enumerate(events):
        start = 0 if ix < 4 else 1
        need(event['context']['case_id'] == 13 and event['context']['geometry_id'] == 12013 and
             event['context']['scheme'] == 'AO' and event['context']['start_id'] == start,
             'original AO context')
        fields = first['fields'] if ix == 0 else event['fields']
        w = decode_array(fields['W'], [N,J]); phi = decode_array(fields['phi'], [1,25])
        cols = [[w[i+N*j] for i in range(N)] for j in range(J)]
        param = finals[start]['fields']
        fctx = finals[start]['context']
        need(fctx['start_id'] == start and fctx['case_id'] == 13 and
             fctx['geometry_id'] == 12013 and fctx['scheme'] == 'AO' and
             fctx['U'] == 1 and fctx['beta'] == 20, 'final parameters match saved start')
        noise = decode_array(param['noise'], [1,1])[0][0]
        power = decode_array(param['power'], [1,1])[0][0]
        target = [x[0] for x in decode_array(param['target'], [K,1])]
        need(noise > 0 and power >= 0 and all(t >= 0 for t in target), 'parameter domain')
        psi_ref = event['fields']['Psi']['array_ref']
        need(type(psi_ref) is int and 0 <= psi_ref < len(arrays) and
             psi_ref == events[0]['fields']['Psi']['array_ref'],
             'all eight events refer to the same exactly deduplicated Psi')
        psi = decode_array(arrays[psi_ref], [K,N,N])
        psi_rows = [[[psi[k+K*r+K*N*c] for c in range(N)] for r in range(N)] for k in range(K)]
        maximum = Fraction(0); exact_count = 0
        for k in range(K):
            for r in range(N):
                for c in range(N):
                    z = product_conj_left(mu[k][r],mu[k][c])
                    if r == c: z = (z[0]+var[k][r], z[1])
                    saved = psi_rows[k][r][c]
                    exact_count += int(z == saved)
                    maximum = max(maximum, abs(z[0]-saved[0]), abs(z[1]-saved[1]))
        if matrix_comparison is None:
            matrix_comparison = {'complex_entries': K*N*N, 'exactly_equal': exact_count,
                                 'max_abs_component_difference': ratio(maximum)}
        else:
            need(matrix_comparison == {'complex_entries':K*N*N, 'exactly_equal':exact_count,
                 'max_abs_component_difference':ratio(maximum)}, 'same shared Psi in all events')
        power_sum = sum((abs2(z) for z in w), Fraction(0))
        max_phi_error = max(abs(abs2(z)-1) for z in phi)
        records.append({'ordinal':event['ordinal'], 'start_id':start,
                        'power_margin':ratio(power-power_sum),
                        'power_within_exact_bound': power_sum <= power,
                        'max_abs_unit_modulus_squared_error':ratio(max_phi_error),
                        'qos':assess(mu,var,psi_rows,cols,noise,target)})
    return {'schema':'CASE13_EIGHT_AO_EXACT_SAVED_QOS_V1', 'records':records,
            'independent_moment_vs_saved_Psi':matrix_comparison,
            'interference_streams_per_user':J-1,
            'arithmetic':'exact rationals of stored binary64',
            'historical_chunk_content_reverified':False,
            'whole_event_atomic_snapshot_verified':False,
            'no_quadrature_or_physical_units_certificate':True,
            'not_full_convergence_matlab_or_reference_validation':True,
            'full_paper_pass':False}
