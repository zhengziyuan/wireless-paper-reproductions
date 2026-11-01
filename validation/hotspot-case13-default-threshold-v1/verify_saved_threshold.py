"""Independently verify saved-state lower-bound threshold observations.

No trajectory, optimizer or new channel realization is used. A false flag is
unknown at 3 dB, not a feasibility pass.
"""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
helper_path=ROOT/'tools/hotspot-case13-selected-independent-v1/verify_selected_exact.py'
spec=importlib.util.spec_from_file_location('_selected_exact_basis',helper_path)
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)


def need(value, msg):
    if value is not True: raise ValueError(msg)


def flags(g, noise, target_index):
    """Return strict <1.99 witnesses; absence of one is inconclusive."""
    need(len(g)==16 and 1<=target_index<16 and noise>0 and all(v>=0 for v in g),'invalid powers')
    desired=g[target_index]
    full=noise+sum((value for j,value in enumerate(g) if j!=target_index),F(0))
    k_only=noise+sum((g[j] for j in range(1,16) if j!=target_index),F(0))
    need(full>0 and k_only>0,'nonpositive denominator')
    return {'K_only_proved_below_1_99': desired*100 < 199*k_only,
            'full_J_proved_below_1_99': desired*100 < 199*full}


def verify(rows,moments,actual):
    need(199**10 < 1000*100**10,'strict 1.99 < 3 dB rational proof')
    need(type(rows) is list and len(rows)==3 and type(actual) is list and len(actual)==4,'record count')
    term=actual[3]
    need(term.get('kind')=='terminal' and term.get('schema')=='CASE13_DEFAULT_THRESHOLD_STREAM_V1' and
         term.get('completed') is True and term.get('schemes_durably_confirmed')==3 and
         term.get('historical_source_authenticated') is False and term.get('scientific_or_paper_pass') is False,
         'terminal scope')
    need(moments.get('schema')=='ACTUAL_NATIVE_CASE_NHU_AND_COMPOSITE_INPUT_V1' and
         moments.get('complete_geometry_and_design_NHU_raw_words_identical') is True,'moments')
    ctx=moments['original_context']
    need(all(ctx.get(k)==v for k,v in {'case_id':13,'geometry_id':12013,'U':1,'beta':20}.items()),'context')
    m,v=moments['full_NHU_mean'],moments['full_NHU_variance']
    need(m['header']['size']==v['header']['size']==[15,16] and
         m['header']['order']==v['header']['order']=='MATLAB_column_major' and
         m['header']['isreal'] is False and v['header']['isreal'] is True,'moment ABI')
    re=h.raw_hex(m['real_hex_column_major'],240);im=h.raw_hex(m['imag_hex_column_major'],240)
    variances=h.raw_hex(v['real_hex_column_major'],240);need(all(x>=0 for x in variances),'variance')
    counts={}
    for row,observed,(scheme,start,final,selected) in zip(rows,actual[:3],h.SPECS):
        need(row.get('schema')=='CASE13_SELECTED_FINAL_NUMERIC_PROJECTION_V1' and
             (row.get('scheme'),row.get('selected_start_id'),row.get('final_ordinal'),row.get('selected_ordinal'))==
              (scheme,start,final,selected) and observed.get('kind')=='scheme' and
             observed.get('scheme')==scheme and observed.get('start_id')==start,'state mapping')
        saved=row['saved']; w=h.decode(saved['actual_W'],[[16,16]])
        h.decode(row['selected_W'],[[16,16]])
        need(h.same_bytes(saved['actual_W'],row['selected_W']) and
             h.same_bytes(saved['actual_phi'],row['selected_phi']) and
             row['saved_no_ris']==row['selected_no_ris']==(scheme=='NoRIS'),'selected identity')
        psi=h.decode(saved['Psi'],[[15,16,16]])
        noise=h.decode(saved['noise'],[[1,1]])[0];need(noise[1]==0 and noise[0]>0,'noise')
        cols=[[w[i+16*j] for i in range(16)] for j in range(16)]
        users=observed['users'];need(len(users)==15,'user count')
        c={'K_only_saved_Psi':0,'full_J_saved_Psi':0,'K_only_saved_moments':0,'full_J_saved_moments':0}
        for k,user in enumerate(users):
            need(user['nhu_user_one_based']==k+2,'user order')
            matrix=[[psi[k+15*i+240*j] for j in range(16)] for i in range(16)]
            need(all(matrix[i][j]==h.conjugate(matrix[j][i]) for i in range(16) for j in range(16)),
                 'stored matrix not Hermitian')
            mean=[(re[k+15*i],im[k+15*i]) for i in range(16)]
            var=[variances[k+15*i] for i in range(16)]
            expected={'saved_Psi':flags([h.matrix_gain(matrix,x) for x in cols],noise[0],k+1),
                      'saved_moments':flags([h.moment_gain(mean,var,x) for x in cols],noise[0],k+1)}
            for source,result in expected.items():
                need(user[source]==result and all(type(x) is bool for x in user[source].values()),'witness discrepancy')
                c['K_only_'+source]+=result['K_only_proved_below_1_99']
                c['full_J_'+source]+=result['full_J_proved_below_1_99']
        counts[scheme]=c
    return {'schema':'CASE13_DEFAULT_THRESHOLD_INDEPENDENT_RECHECK_V1',
            'stored_states_recomputed':3,'users_per_state':15,'counts_of_proved_below_1_99':counts,
            'one_point_nine_nine_strictly_below_3dB_proved':True,
            'false_flag_is_inconclusive_not_a_pass':True,
            'original_historical_source_authenticated':False,'full_paper_pass':False}


def main():
    states=h.read_gzip(ROOT/'validation/hotspot-case13-selected-physical-v1/selected-input.jsonl.gz',512*1024)
    need(states.endswith(b'\n'),'partial state stream')
    rows=[h.parse(line) for line in states.splitlines()]
    moments=h.parse(h.read(ROOT/'tools/hotspot-case13-evidence-v1/moment_projection.json',32768))
    output=h.read(HERE/'recorded-threshold.jsonl',512*1024);need(output.endswith(b'\n'),'partial output stream')
    result=verify(rows,moments,[h.parse(line) for line in output.splitlines()])
    print(json.dumps(result,sort_keys=True,indent=2,allow_nan=False))


if __name__=='__main__':main()
