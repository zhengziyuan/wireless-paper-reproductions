"""Self-contained synthetic tests; no saved state or paper is read."""
import base64
import copy
from fractions import Fraction as F
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_selected_exact as v


def array(shape, values):
    return {'shape':shape,'order':'MATLAB_column_major',
            'encoding':'ieee754_binary64_little_endian_base64',
            'real_base64':base64.b64encode(struct.pack('<%dd'%len(values),*values)).decode('ascii')}


def word(x): return struct.pack('<d',x).hex()
def ratio(x): return {'numerator':str(x.numerator),'denominator':str(x.denominator)}


def fixtures(target=0.5):
    moments={'schema':'ACTUAL_NATIVE_CASE_NHU_AND_COMPOSITE_INPUT_V1',
      'complete_geometry_and_design_NHU_raw_words_identical':True,
      'original_context':{'case_id':13,'geometry_id':12013,'U':1,'beta':20},
      'full_NHU_mean':{'header':{'size':[15,16],'order':'MATLAB_column_major','isreal':False},
                       'real_hex_column_major':[word(0.0)]*240,'imag_hex_column_major':[word(0.0)]*240},
      'full_NHU_variance':{'header':{'size':[15,16],'order':'MATLAB_column_major','isreal':True},
                           'real_hex_column_major':[word(1.0)]*240}}
    psi=[0.0]*(15*16*16)
    for k in range(15):
        for i in range(16):psi[k+15*i+240*i]=1.0
    saved={'Psi':array([15,16,16],psi),'actual_W':array([16,16],[0.0]*256),
           'actual_phi':array([1,25],[1.0]*25),'noise':array([1,1],[1.0]),
           'power':array([1,1],[1.0]),'target':array([15,1],[target]*15)}
    rows=[];report=[]; margin=-F.from_float(target)
    for name,start,final,selected in v.SPECS:
        nr=name=='NoRIS'
        rows.append({'schema':'CASE13_SELECTED_FINAL_NUMERIC_PROJECTION_V1','scheme':name,
          'selected_start_id':start,'final_ordinal':final,'selected_ordinal':selected,
          'saved':copy.deepcopy(saved),'selected_W':copy.deepcopy(saved['actual_W']),
          'selected_phi':copy.deepcopy(saved['actual_phi']),'saved_no_ris':nr,'selected_no_ris':nr,
          'selected_W_bitwise_equals_final':True,'selected_phi_bitwise_equals_final':True,
          'selected_no_ris_equals_final':True,'no_ris_flags_match_scheme':True})
        q=[]
        for k in range(15):
            q.append({'user_one_based':k+2,'moments_margin':ratio(margin),
              'saved_Psi_hermitian_part_margin':ratio(margin),'moments_positive':margin>0,
              'moments_nonnegative':margin>=0,'saved_Psi_hermitian_part_positive':margin>0,
              'saved_Psi_hermitian_part_nonnegative':margin>=0,'saved_Psi_exactly_hermitian':True,
              'saved_Psi_antihermitian_max_real_component':ratio(F(0)),
              'saved_Psi_antihermitian_max_imag_component':ratio(F(0)),
              'saved_Psi_raw_matrix_qos_nonnegative_if_exact_hermitian':margin>=0})
        report.append({'kind':'scheme','scheme':name,'selected_start_id':start,
          'selected_W_bitwise_equals_final':True,'selected_phi_bitwise_equals_final':True,
          'no_ris_flags_match_scheme':True,'selected_final_identity_for_constraints':True,
          'selected_assessment_inherited':True,'phase_irrelevant_to_this_constraint_assessment':nr,
          'final_saved_binary64_assessment':{'power_margin':ratio(F(1)),'power_strict_pass':True,
            'phase_max_squared_error':ratio(F(0)),'phase_modulus_strict_pass':None if nr else True,
            'all_moment_qos_positive':margin>0,'all_moment_qos_nonnegative':margin>=0,
            'all_saved_Psi_hermitian_part_qos_positive':margin>0,
            'all_saved_Psi_hermitian_part_qos_nonnegative':margin>=0,
            'all_saved_Psi_exactly_hermitian':True,'qos':q}})
    report.append({'kind':'terminal','schema':'CASE13_SELECTED_PHYSICAL_STREAM_V1',
                   'completed':True,'schemes_durably_confirmed':3,'historical_source_authenticated':False,
                   'scientific_or_paper_pass':False})
    return rows,moments,report


class Tests(unittest.TestCase):
    def test_conjugate_direction(self):
        z=(F(0),F(0)); one=(F(1),F(0)); im=(F(0),F(1)); minus=(F(0),F(-1))
        q=[[z for _ in range(16)] for _ in range(16)]
        q[0][0]=one;q[0][1]=im;q[1][0]=minus;q[1][1]=one
        self.assertEqual(v.matrix_gain(q,[one,im]+[z]*14),0)
        self.assertEqual(v.matrix_gain(q,[one,minus]+[z]*14),4)

    def test_all_45_synthetic_margins(self):
        r,m,o=fixtures(); result=v.verify(r,m,o)
        self.assertEqual(result['qos_users_compared'],45)
        self.assertFalse(result['full_paper_pass'])

    def test_zero_qos_margin_is_nonnegative(self):
        r,m,o=fixtures(0.0);result=v.verify(r,m,o)
        self.assertEqual(result['qos_users_compared'],45)
        self.assertTrue(o[0]['final_saved_binary64_assessment']['all_moment_qos_nonnegative'])
        self.assertFalse(o[0]['final_saved_binary64_assessment']['all_moment_qos_positive'])

    def test_tampered_exact_margin_rejected(self):
        r,m,o=fixtures();o[0]['final_saved_binary64_assessment']['qos'][0]['moments_margin']=ratio(F(0))
        with self.assertRaisesRegex(ValueError,'QoS/residual discrepancy'):v.verify(r,m,o)

    def test_wrong_context_rejected(self):
        r,m,o=fixtures();m['original_context']['beta']=10
        with self.assertRaisesRegex(ValueError,'moment case context'):v.verify(r,m,o)

    def test_noris_selected_phase_may_differ(self):
        r,m,o=fixtures();r[0]['selected_phi']=array([1,25],[0.0]+[1.0]*24)
        r[0]['selected_phi_bitwise_equals_final']=False;o[0]['selected_phi_bitwise_equals_final']=False
        self.assertTrue(v.verify(r,m,o)['power_phase_and_identity_compared'])

    def test_incomplete_terminal_rejected(self):
        r,m,o=fixtures();o[-1]['completed']=False
        with self.assertRaisesRegex(ValueError,'terminal'):v.verify(r,m,o)


if __name__ == '__main__': unittest.main()
