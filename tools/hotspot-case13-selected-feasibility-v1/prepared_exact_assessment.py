"""Disabled exact assessment of saved selected-state projection.

No optimizer or propagation-model realization is run. Three final states are
independently checked against saved Psi and common saved NHU moment inputs.
Only separately reviewed resource-bounded execution may enable real input.
"""
import base64
from fractions import Fraction as F
import json
import math
import struct

ENABLED = False
SPECS = (('NoRIS', 1, 1327227, 1327229), ('TwoStage', 0, 1327398, 1327570),
         ('AO', 0, 1327779, 1328007))


def need(ok, text):
    if not ok: raise ValueError(text)


def ratio(q):
    return {'numerator': str(q.numerator), 'denominator': str(q.denominator)}


def decode(desc, allowed):
    need(isinstance(desc, dict) and desc.get('shape') in allowed and
         desc.get('order') == 'MATLAB_column_major' and
         desc.get('encoding') == 'ieee754_binary64_little_endian_base64', 'array ABI')
    n = math.prod(desc['shape'])
    def words(raw):
        b = base64.b64decode(raw, validate=True)
        need(len(b) == 8*n, 'binary64 byte length')
        v = struct.unpack('<'+str(n)+'d', b)
        need(all(math.isfinite(x) for x in v), 'nonfinite binary64')
        return [F.from_float(x) for x in v]
    re = words(desc['real_base64'])
    im = words(desc['imag_base64']) if 'imag_base64' in desc else [F(0)]*n
    return list(zip(re, im))


def bits_equal(a, b):
    return a['real_base64'] == b['real_base64'] and a.get('imag_base64') == b.get('imag_base64')


def hex_words(v, n):
    need(isinstance(v, list) and len(v) == n, 'moment count')
    out = []
    for h in v:
        need(isinstance(h, str) and len(h) == 16, 'moment binary64 word')
        raw = bytes.fromhex(h)
        x = struct.unpack('<d', raw)[0]
        need(math.isfinite(x), 'moment nonfinite')
        out.append(F.from_float(x))
    return out


def mul_conj(a, b): return (a[0]*b[0]+a[1]*b[1], a[0]*b[1]-a[1]*b[0])
def abs2(z): return z[0]*z[0] + z[1]*z[1]


def matrix_gain(psi, w):
    out = F(0)
    for i in range(16):
        for j in range(16):
            z = mul_conj(w[i], w[j])
            a = psi[i][j]
            out += a[0]*z[0] - a[1]*z[1]
    return out


def moment_gain(mu, var, w):
    re = sum((m[0]*z[0]-m[1]*z[1] for m,z in zip(mu,w)), F(0))
    im = sum((m[0]*z[1]+m[1]*z[0] for m,z in zip(mu,w)), F(0))
    return re*re + im*im + sum((v*abs2(z) for v,z in zip(var,w)), F(0))


def assess(rows, moment, on_record=None):
    need(ENABLED, 'disabled pending reviewed bounded admission')
    need(on_record is None or callable(on_record), 'record callback')
    need(isinstance(rows,list) and len(rows)==3, 'three selected schemes')
    need(moment.get('schema') == 'ACTUAL_NATIVE_CASE_NHU_AND_COMPOSITE_INPUT_V1'
         and moment.get('complete_geometry_and_design_NHU_raw_words_identical') is True
         and moment['original_context'].get('case_id') == 13
         and moment['original_context'].get('geometry_id') == 12013
         and moment['original_context'].get('U') == 1
         and moment['original_context'].get('beta') == 20, 'saved moments')
    mn, var = moment['full_NHU_mean'], moment['full_NHU_variance']
    need(mn['header']['size']==[15,16] and var['header']['size']==[15,16]
         and mn['header']['order']==var['header']['order']=='MATLAB_column_major'
         and mn['header']['isreal'] is False and var['header']['isreal'] is True, 'moment ABI')
    mr=hex_words(mn['real_hex_column_major'],240);mi=hex_words(mn['imag_hex_column_major'],240)
    vv=hex_words(var['real_hex_column_major'],240);need(all(v>=0 for v in vv),'negative variance')
    mu=[[(mr[k+15*i],mi[k+15*i]) for i in range(16)] for k in range(15)]
    variance=[[vv[k+15*i] for i in range(16)] for k in range(15)]
    outputs=[]
    for row,(scheme,start,final,selected) in zip(rows,SPECS):
        need(row.get('schema')=='CASE13_SELECTED_FINAL_NUMERIC_PROJECTION_V1'
             and (row.get('scheme'),row.get('selected_start_id'),row.get('final_ordinal'),row.get('selected_ordinal'))
                 == (scheme,start,final,selected), 'selected event identity')
        saved=row['saved']; w=decode(saved['actual_W'],[[16,16]]); phi=decode(saved['actual_phi'],[[1,25],[25,1]])
        sw=decode(row['selected_W'],[[16,16]]);sp=decode(row['selected_phi'],[[1,25],[25,1]])
        no_ris=row['saved_no_ris'];s_no_ris=row['selected_no_ris']
        need(type(no_ris) is bool and type(s_no_ris) is bool, 'noRIS boolean')
        w_same=bits_equal(saved['actual_W'],row['selected_W']);phi_same=bits_equal(saved['actual_phi'],row['selected_phi'])
        need(row['selected_W_bitwise_equals_final'] is w_same and row['selected_phi_bitwise_equals_final'] is phi_same
             and row['selected_no_ris_equals_final'] is (no_ris==s_no_ris)
             and row['no_ris_flags_match_scheme'] is (no_ris==(scheme=='NoRIS') and s_no_ris==(scheme=='NoRIS')),
             'projection identity flags')
        psi=decode(saved['Psi'],[[15,16,16]])
        rows_psi=[[[psi[k+15*i+240*j] for j in range(16)] for i in range(16)] for k in range(15)]
        noise=decode(saved['noise'],[[1,1]])[0];power=decode(saved['power'],[[1,1]])[0]
        targets=decode(saved['target'],[[15,1]])
        need(noise[1]==0 and power[1]==0 and noise[0]>0 and power[0]>=0
             and all(z[1]==0 and z[0]>=0 for z in targets),'parameter domain')
        cols=[[w[i+16*j] for i in range(16)] for j in range(16)]
        margins=[]
        for k in range(15):
            # The real part of w^H Psi w equals the quadratic form of its
            # Hermitian part. Retain exact non-Hermitian residual separately.
            anti_re=max(abs(rows_psi[k][i][j][0]-rows_psi[k][j][i][0]) for i in range(16) for j in range(16))
            anti_im=max(abs(rows_psi[k][i][j][1]+rows_psi[k][j][i][1]) for i in range(16) for j in range(16))
            hermitian=anti_re==0 and anti_im==0
            gm=[moment_gain(mu[k],variance[k],col) for col in cols]
            gs=[matrix_gain(rows_psi[k],col) for col in cols]
            idx=k+1; dm=noise[0]+sum((v for j,v in enumerate(gm) if j!=idx),F(0))
            ds=noise[0]+sum((v for j,v in enumerate(gs) if j!=idx),F(0))
            need(dm>0 and ds>0,'nonpositive interference denominator')
            mm=gm[idx]-targets[k][0]*dm;ms=gs[idx]-targets[k][0]*ds
            margins.append({'user_one_based':k+2,'moments_margin':ratio(mm),
                            'saved_Psi_hermitian_part_margin':ratio(ms),
                            'moments_positive':mm>0,'saved_Psi_hermitian_part_positive':ms>0,
                            'moments_nonnegative':mm>=0,'saved_Psi_hermitian_part_nonnegative':ms>=0,
                            'saved_Psi_exactly_hermitian':hermitian,
                            'saved_Psi_antihermitian_max_real_component':ratio(anti_re),
                            'saved_Psi_antihermitian_max_imag_component':ratio(anti_im),
                            'saved_Psi_raw_matrix_qos_nonnegative_if_exact_hermitian':ms>=0 if hermitian else None})
        p_used=sum((abs2(z) for z in w),F(0)); phase_err=max(abs(abs2(z)-1) for z in phi)
        final={'power_margin':ratio(power[0]-p_used),'power_strict_pass':p_used<=power[0],
               'phase_max_squared_error':ratio(phase_err),
               'phase_modulus_strict_pass':None if no_ris else phase_err==0,
               'all_moment_qos_positive':all(m['moments_positive'] for m in margins),
               'all_saved_Psi_hermitian_part_qos_positive':all(m['saved_Psi_hermitian_part_positive'] for m in margins),
               'all_moment_qos_nonnegative':all(m['moments_nonnegative'] for m in margins),
               'all_saved_Psi_hermitian_part_qos_nonnegative':all(m['saved_Psi_hermitian_part_nonnegative'] for m in margins),
               'all_saved_Psi_exactly_hermitian':all(m['saved_Psi_exactly_hermitian'] for m in margins),
               'qos':margins}
        # In this implemented NoRIS branch, phi is ignored. It remains reported
        # separately even when it is irrelevant to the selected constraints.
        identity_ok=w_same and (no_ris or phi_same) and no_ris==s_no_ris and no_ris==(scheme=='NoRIS')
        record={'scheme':scheme,'selected_start_id':start,'selected_final_identity_for_constraints':identity_ok,
                        'selected_W_bitwise_equals_final':w_same,'selected_phi_bitwise_equals_final':phi_same,
                        'phase_irrelevant_to_this_constraint_assessment':no_ris,
                        'no_ris_flags_match_scheme':no_ris==(scheme=='NoRIS') and s_no_ris==(scheme=='NoRIS'),
                        'final_saved_binary64_assessment':final,
                        'selected_assessment_inherited':identity_ok}
        if on_record is not None: on_record(record)
        outputs.append(record)
    return {'schema':'CASE13_SELECTED_FINAL_EXACT_ASSESSMENT_V1','records':outputs,
            'arithmetic':'exact rationals of retained binary64 values; full J-1 interference',
            'original_source_authenticated':False,'whole_event_atomic_snapshot_verified':False,
            'mathematical_convergence_proved':False,'physical_model_paper_agreement_proved':False,
            'full_paper_pass':False}
