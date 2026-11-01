"""Independent exact recheck of previously projected case-13 selected states.

No optimizer, propagation-model run, original trajectory or PDF is read. The
checks apply only to the retained binary64 projections and current model.
"""
import base64
from fractions import Fraction as F
import gzip
import io
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'validation/hotspot-case13-selected-physical-v1'
MOMENTS = ROOT/'tools/hotspot-case13-evidence-v1/moment_projection.json'
SPECS = [('NoRIS', 1, 1327227, 1327229), ('TwoStage', 0, 1327398, 1327570),
         ('AO', 0, 1327779, 1328007)]


def need(condition, text):
    if not condition:
        raise ValueError(text)


def pairs(values):
    out = {}
    for key, value in values:
        need(key not in out, 'duplicate JSON key')
        out[key] = value
    return out


def parse(raw):
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def read(path, cap):
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    need(len(raw) <= cap, 'bounded file')
    return raw


def read_gzip(path, cap):
    compressed = read(path, cap)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(cap+1)
    need(len(raw) <= cap, 'bounded decompression')
    return raw


def decode(desc, shapes):
    need(type(desc) is dict and desc.get('shape') in shapes and
         desc.get('order') == 'MATLAB_column_major' and
         desc.get('encoding') == 'ieee754_binary64_little_endian_base64', 'array ABI')
    n = math.prod(desc['shape'])
    def words(name):
        b = base64.b64decode(desc[name], validate=True)
        need(len(b) == n*8, 'word count')
        vals = struct.unpack('<%dd' % n, b)
        need(all(math.isfinite(x) for x in vals), 'finite words')
        return [F.from_float(x) for x in vals]
    a = words('real_base64')
    b = words('imag_base64') if 'imag_base64' in desc else [F(0)]*n
    return list(zip(a, b))


def raw_hex(words, count):
    need(type(words) is list and len(words) == count, 'moment word count')
    out = []
    for word in words:
        need(type(word) is str and len(word) == 16, 'moment word')
        v = struct.unpack('<d', bytes.fromhex(word))[0]
        need(math.isfinite(v), 'finite moment word')
        out.append(F.from_float(v))
    return out


def exact_ratio(v):
    need(type(v) is dict and set(v) == {'numerator', 'denominator'}, 'rational schema')
    a, b = v['numerator'], v['denominator']
    need(type(a) is str and type(b) is str and len(a) <= 4096 and len(b) <= 4096,
         'rational length')
    den = int(b)
    need(den > 0, 'rational denominator')
    return F(int(a), den)


def mul(a, b): return a[0]*b[0]-a[1]*b[1], a[0]*b[1]+a[1]*b[0]
def conjugate(a): return a[0], -a[1]
def magnitude2(a): return a[0]*a[0]+a[1]*a[1]


def moment_gain(mu, variance, w):
    z = [F(0), F(0)]
    for a, b in zip(mu, w):
        t = mul(a, b)
        z[0] += t[0]
        z[1] += t[1]
    return magnitude2(z) + sum((v*magnitude2(a) for v, a in zip(variance, w)), F(0))


def matrix_gain(psi, w):
    total = F(0)
    for i in range(16):
        for j in range(16):
            total += mul(mul(conjugate(w[i]), psi[i][j]), w[j])[0]
    return total


def same_bytes(a, b):
    return (a['real_base64'] == b['real_base64'] and
            a.get('imag_base64') == b.get('imag_base64'))


def verify(rows, moments, report):
    need(type(rows) is list and len(rows) == 3 and type(report) is list and len(report) == 4,
         'expected three records and terminal')
    terminal = report[3]
    need(terminal.get('kind') == 'terminal' and
         terminal.get('schema') == 'CASE13_SELECTED_PHYSICAL_STREAM_V1' and
         terminal.get('completed') is True and terminal.get('schemes_durably_confirmed') == 3 and
         terminal.get('historical_source_authenticated') is False and
         terminal.get('scientific_or_paper_pass') is False, 'terminal')
    need(moments.get('schema') == 'ACTUAL_NATIVE_CASE_NHU_AND_COMPOSITE_INPUT_V1' and
         moments.get('complete_geometry_and_design_NHU_raw_words_identical') is True, 'moment source')
    ctx = moments['original_context']
    need(all(ctx.get(k) == v for k, v in {'case_id':13, 'geometry_id':12013, 'U':1, 'beta':20}.items()),
         'moment case context')
    a, b = moments['full_NHU_mean'], moments['full_NHU_variance']
    need(a['header']['size'] == b['header']['size'] == [15,16] and
         a['header']['order'] == b['header']['order'] == 'MATLAB_column_major' and
         a['header']['isreal'] is False and b['header']['isreal'] is True, 'moment ABI')
    re, im, var = (raw_hex(a['real_hex_column_major'],240), raw_hex(a['imag_hex_column_major'],240),
                   raw_hex(b['real_hex_column_major'],240))
    need(all(x >= 0 for x in var), 'nonnegative variance')
    compared = 0
    for row, result, (scheme, start, final, selected) in zip(rows, report[:3], SPECS):
        need(row.get('schema') == 'CASE13_SELECTED_FINAL_NUMERIC_PROJECTION_V1' and
             (row.get('scheme'),row.get('selected_start_id'),row.get('final_ordinal'),row.get('selected_ordinal')) ==
             (scheme,start,final,selected) and result.get('kind') == 'scheme' and
             result.get('scheme') == scheme and result.get('selected_start_id') == start, 'scheme identity')
        s = row['saved']; w = decode(s['actual_W'],[[16,16]]); phi = decode(s['actual_phi'],[[1,25],[25,1]])
        decode(row['selected_W'],[[16,16]]); decode(row['selected_phi'],[[1,25],[25,1]])
        ws, ps = same_bytes(s['actual_W'],row['selected_W']), same_bytes(s['actual_phi'],row['selected_phi'])
        nr, snr = row['saved_no_ris'], row['selected_no_ris']
        need(type(nr) is bool and type(snr) is bool, 'NoRIS flags')
        scheme_ok = nr == (scheme == 'NoRIS') and snr == (scheme == 'NoRIS')
        ident = ws and (nr or ps) and nr == snr and scheme_ok
        for key, value in {'selected_W_bitwise_equals_final':ws, 'selected_phi_bitwise_equals_final':ps,
                           'no_ris_flags_match_scheme':scheme_ok,
                           'selected_final_identity_for_constraints':ident,
                           'selected_assessment_inherited':ident,
                           'phase_irrelevant_to_this_constraint_assessment':nr}.items():
            need(result.get(key) is value, 'identity discrepancy')
        need(row['selected_W_bitwise_equals_final'] is ws and row['selected_phi_bitwise_equals_final'] is ps and
             row['selected_no_ris_equals_final'] is (nr == snr) and row['no_ris_flags_match_scheme'] is scheme_ok,
             'projection identity discrepancy')
        psi = decode(s['Psi'],[[15,16,16]])
        noise, power = decode(s['noise'],[[1,1]])[0], decode(s['power'],[[1,1]])[0]
        target = decode(s['target'],[[15,1]])
        need(noise[1] == power[1] == 0 and noise[0] > 0 and power[0] >= 0 and
             all(t[1] == 0 and t[0] >= 0 for t in target), 'parameter domain')
        out = result['final_saved_binary64_assessment']
        p_margin = power[0] - sum((magnitude2(z) for z in w),F(0))
        phase_error = max(abs(magnitude2(z)-1) for z in phi)
        need(exact_ratio(out['power_margin']) == p_margin and out['power_strict_pass'] is (p_margin >= 0),
             'power discrepancy')
        need(exact_ratio(out['phase_max_squared_error']) == phase_error and
             out['phase_modulus_strict_pass'] is (None if nr else phase_error == 0), 'phase discrepancy')
        qos = out['qos']; need(type(qos) is list and len(qos) == 15, 'QoS count')
        cols = [w[16*j:16*(j+1)] for j in range(16)]
        mm_all, ms_all, herm_all = [], [], []
        for k in range(15):
            mu = [(re[k+15*i],im[k+15*i]) for i in range(16)]
            vv = [var[k+15*i] for i in range(16)]
            matrix = [[psi[k+15*i+240*j] for j in range(16)] for i in range(16)]
            ar = max(abs(matrix[i][j][0]-matrix[j][i][0]) for i in range(16) for j in range(16))
            ai = max(abs(matrix[i][j][1]+matrix[j][i][1]) for i in range(16) for j in range(16))
            herm = ar == 0 and ai == 0
            gm = [moment_gain(mu,vv,c) for c in cols]; gs = [matrix_gain(matrix,c) for c in cols]
            idx = k+1
            dm = noise[0]+sum((v for j,v in enumerate(gm) if j != idx),F(0))
            ds = noise[0]+sum((v for j,v in enumerate(gs) if j != idx),F(0))
            need(dm > 0 and ds > 0, 'positive interference denominator')
            mm, ms = gm[idx]-target[k][0]*dm, gs[idx]-target[k][0]*ds
            r = qos[k]; need(r['user_one_based'] == k+2, 'QoS user index')
            need(exact_ratio(r['moments_margin']) == mm and exact_ratio(r['saved_Psi_hermitian_part_margin']) == ms and
                 exact_ratio(r['saved_Psi_antihermitian_max_real_component']) == ar and
                 exact_ratio(r['saved_Psi_antihermitian_max_imag_component']) == ai, 'QoS/residual discrepancy')
            for key,value in {'moments_positive':mm>0,'moments_nonnegative':mm>=0,
                'saved_Psi_hermitian_part_positive':ms>0,'saved_Psi_hermitian_part_nonnegative':ms>=0,
                'saved_Psi_exactly_hermitian':herm,
                'saved_Psi_raw_matrix_qos_nonnegative_if_exact_hermitian':(ms>=0 if herm else None)}.items():
                need(r.get(key) is value, 'QoS flag discrepancy')
            mm_all.append(mm);ms_all.append(ms);herm_all.append(herm);compared += 1
        for key,value in {'all_moment_qos_positive':all(x>0 for x in mm_all),
            'all_moment_qos_nonnegative':all(x>=0 for x in mm_all),
            'all_saved_Psi_hermitian_part_qos_positive':all(x>0 for x in ms_all),
            'all_saved_Psi_hermitian_part_qos_nonnegative':all(x>=0 for x in ms_all),
            'all_saved_Psi_exactly_hermitian':all(herm_all)}.items():
            need(out.get(key) is value, 'aggregate discrepancy')
    return {'schema':'CASE13_SELECTED_INDEPENDENT_EXACT_RECHECK_V1','schemes_compared':3,
            'qos_users_compared':compared,'moments_and_matrix_compared':True,
            'power_phase_and_identity_compared':True,'historical_source_authenticated':False,
            'whole_event_atomic_snapshot_verified':False,'full_paper_pass':False}


def main():
    state = read_gzip(EVIDENCE/'selected-input.jsonl.gz',512*1024)
    report = read(EVIDENCE/'recorded-assessment.jsonl',512*1024)
    need(state.endswith(b'\n') and report.endswith(b'\n'),'complete JSONL')
    rows = [parse(x) for x in state.splitlines()]
    results = [parse(x) for x in report.splitlines()]
    print(json.dumps(verify(rows,parse(read(MOMENTS,32768)),results),sort_keys=True))


if __name__ == '__main__':
    main()
