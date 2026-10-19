"""Replay every supplied original ray/gain observation and exact certificate."""
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

import evidence as e
import exact_geometry as kernel


def rows(path,limit):
    with gzip.open(path,'rb') as stream:
        for i,line in enumerate(stream):
            e.require(i<limit and len(line)<=128*1024,'An original bounded whole-population row stream changed')
            yield json.loads(line)


def primitive_scene(fact):
    def decode(vectors,columns):
        e.require(len(vectors)==2 and all(len(row)==columns for row in vectors),'Every complete original ray/gain coordinate is required')
        result=[[float.fromhex(x) for x in row] for row in vectors]
        e.require(all(math.isfinite(x) and float(x).hex()==s for row,old in zip(result,vectors) for x,s in zip(row,old)),
            'A canonical finite exact-binary primitive coordinate changed')
        return result
    br,rb=decode(fact['br_directions_hex'],3),decode(fact['rb_directions_hex'],3)
    gains=decode(fact['br_complex_gains_hex'],2)
    gain=float.fromhex(fact['maximum_gain_hex'])
    e.require(math.isfinite(gain) and gain>0,'A finite positive original element gain is required')
    return dict(initial_angles=fact['initial_angles'],bs_center=fact['bs_center'],ris_center=fact['ris_center'],
        maximum_gain=gain,directivity_exponent=fact['directivity_exponent'],
        br_directions=br,rb_directions=rb,br_gain_re=[x[0] for x in gains],br_gain_im=[x[1] for x in gains])


def source_metadata(root):
    d=e.read(root/'source/source-version-and-bibliographic-identity.json')
    e.require(d['supplied_R1_TeX_SHA256']=='aa71da008c68caa605ec3ed17520fcb81796561f315667eeb2f7dddf1487d2d2' and
        d['public_arxiv_v2_TeX_SHA256']=='cfff38c69713dc60bc915622c0293654124ede1f2c55132f927db4ec9d437604',
        'The explicitly qualified original manuscript versions changed')
    assets=d['actual_assets'];e.require(len(assets)==17 and {a['figure'] for a in assets}==set(range(1,18)),
        'Every actual original source asset binding is required')
    e.require(all(a['complete_EPS_bytes_identical_after_CRLF_to_LF_only'] for a in assets if a['asset'].endswith('.eps')) and
        sum(a['asset'].endswith('.eps') for a in assets)==16,'The complete numerical-figure source comparison changed')
    e.require(d['NoRIS_wording_difference']['RU_only_literal_public_v2_and_complete_RIS_absence_must_be_separate_model_variants'] and
        d['NoRIS_wording_difference']['existing_run_mismatch_to_the_broader_supplied_R1_wording_proved'] is False,
        'A source wording ambiguity was silently relabeled as an R1 implementation error')
    e.require(d['actual_deposited_publisher_metadata']['DOI'].lower()=='10.1109/jstsp.2026.3693227' and
        d['actual_deposited_publisher_metadata']['primary_URL'].rstrip('/')=='https://ieeexplore.ieee.org/document/11520277',
        'The exact publisher-deposited bibliographic identity changed')
    e.require(d['actual_source_full_files_read_by_default_public_replay']==0 and
        d['actual_publisher_full_texts_read_by_default_public_replay']==0 and
        d['publisher_final_full_text_equivalence_verified'] is False and d['full_manuscripts_EPS_or_source_archives_redistributed'] is False,
        'Public metadata replay was inflated into a fresh complete-source/publisher-text audit')
    return dict(qualified_manuscript_version_and_all17_asset_metadata_pass=True,
        actual_fresh_author_source_or_publisher_full_text_reads=0,final_publisher_equivalence_pass=False)


def replay(root):
    root=Path(root);scope=e.read(root/'scope.json')
    e.require(scope['scope']==e.SCOPE and scope['original_full_scene_jobs']==11200 and
        scope['actual_original_first_user_pair_rows']==23900 and scope['actual_public_primitive_real_coordinate_observations']==322600 and
        scope['literal_first_LoS_geometry_conformance_pass'] is False and scope['full_six_paper_goal_or_dual_language_pass'] is False,
        'The full original scope or retained physical-model failure changed')
    metadata=source_metadata(root);facts={};case_pairs={f:set() for f in e.EXPECTED_SCENES};expected_users=set();primitive_coordinates=0
    for fact in rows(root/'primitives/all11200-actual-BR-RB-rays-and-gains.jsonl.gz',11200):
        family= fact['family'];name=fact['filename'];key=(family,name)
        e.require(family in e.EXPECTED_SCENES and key not in facts,'Duplicate/foreign original primitive input')
        match=re.fullmatch(r'case-(\d{3})-mc-(\d{3})\.json',name)
        e.require(match is not None,'An original case/realization name changed')
        case,realization=map(int,match.groups())
        e.require(case==fact['case_index'] and realization==fact['realization'] and 0<=realization<100,'A complete original channel slot changed')
        declared=scope['families'][family]['original_cases'][str(case)]
        e.require((fact['actual_M'],fact['actual_N'],fact['actual_K'])==(declared['M'],declared['N'],declared['K']) and
            fact['actual_N']==36 and fact['actual_K']>=2,'An original array/user dimension was reduced')
        scene=primitive_scene(fact)
        e.require(scene['initial_angles']==[0]*6 and scene['bs_center']==[0]*3 and scene['ris_center']==[10,0,0],
            'The original zero-angle/fixed-center experiment changed')
        e.require(re.fullmatch(r'[0-9a-f]{64}',fact['original_input_fingerprint']) and
            re.fullmatch(r'[0-9a-f]{64}',fact['original_full_scene_SHA256']),'Original local full-input lineage is missing')
        facts[key]=(fact,scene);case_pairs[family].add((case,realization));expected_users.update((family,name,k) for k in range(fact['actual_K']))
        primitive_coordinates+=16
    e.require(len(facts)==11200 and primitive_coordinates==179200 and len(expected_users)==23900,'The complete ray/gain population is incomplete')
    for family,total in e.EXPECTED_SCENES.items():
        e.require(case_pairs[family]=={(c,r) for c in range(total//100) for r in range(100)},
            'Every original 100-channel point must be retained')
    selected={};seen=set();support_counts=Counter();bridge_groups={};source_directions=0
    for row in rows(root/'reference/all11200-original-exact-support.jsonl.gz',11200):
        key=(row['family'],row['filename']);e.require(key in facts and key not in seen,'An original full support row is absent/duplicated');seen.add(key)
        fact,scene=facts[key]
        e.require(row['actual_input_SHA256']==fact['original_full_scene_SHA256'],'A sealed support/full-source lineage changed')
        entry=dict(filename=fact['filename'],input_fingerprint=fact['original_input_fingerprint'])
        count,geometric=kernel.verify_row(row,scene,entry);e.require(not geometric,'The source-qualified initial first-LoS finding changed')
        support_counts[count]+=1;source_directions+=12
        group=hashlib.sha256(json.dumps([scene['br_directions'],scene['rb_directions'],scene['br_gain_re'],scene['br_gain_im']],
            separators=(',',':')).encode()).hexdigest()
        if group in bridge_groups:e.require(bridge_groups[group]==count,'An exact original bridge input alias changed')
        else:bridge_groups[group]=count
        if count not in selected:selected[count]=(row,scene,entry)
    e.require(seen==set(facts) and source_directions==134400 and dict(support_counts)==e.EXPECTED_SUPPORT and len(bridge_groups)==1100,
        'The complete original support/alias population or finding changed')
    with gzip.open(root/'reference/all3700-distinct-exact-LoS-certificates.json.gz','rb') as stream:certificates=json.load(stream)
    e.require(len(certificates)==3700,'Every complete distinct first-LoS geometry certificate is required')
    seen_users=set();counts=Counter();verified={};pair_coordinates=0;first=None
    for row in rows(root/'reference/all23900-original-first-user-pairs.jsonl.gz',23900):
        key=(row['family'],row['filename'],row['user_zero_based'])
        e.require(key in expected_users and key not in seen_users,'An original complete user-ray slot is missing/duplicated');seen_users.add(key)
        fact,_=facts[key[:2]]
        e.require(row['input_fingerprint']==fact['original_input_fingerprint'] and row['actual_full_input_SHA256']==fact['original_full_scene_SHA256'],
            'An original user-ray/full-input association changed')
        encoded=row['actual_complete_first_BU_RU_direction_vectors_hex']
        e.require(len(encoded)==2 and all(len(v)==3 for v in encoded),'A complete actual first-ray vector is absent')
        e.require(all(math.isfinite(float.fromhex(x)) and float.fromhex(x).hex()==x for v in encoded for x in v),
            'A complete first-ray binary64 coordinate is nonfinite/noncanonical')
        group=hashlib.sha256(json.dumps(encoded,separators=(',',':')).encode()).hexdigest()
        e.require(group==row['exact_pair_geometry_group'] and group in certificates,'An exact complete first-LoS alias changed')
        if group not in verified:
            distance,above=kernel.verify_pair(encoded,certificates[group]);verified[group]=(distance,above)
            if first is None:first=(encoded,certificates[group])
        distance,above=verified[group]
        e.require(kernel.frac(row['exact_squared_line_separation_m2'])==distance and
            row['above_disclosed1e_minus8_m_diagnostic_scale']==above and above and
            row['no_common_user_point_exists_on_both_infinite_lines_for_these_exact_inputs'] is True,
            'A complete user-ray geometry finding changed')
        counts[group]+=1;pair_coordinates+=6
    e.require(seen_users==expected_users and pair_coordinates==143400 and set(counts)==set(certificates) and
        all(counts[g]==c['actual_original_alias_observations'] for g,c in certificates.items()),
        'An original complete user-ray observation or alias multiplicity is missing')
    result=dict(actual_complete_original_scene_primitive_rows=11200,actual_complete_original_first_user_pair_rows=23900,
        actual_complete_BR_RB_direction_coordinates=134400,actual_complete_complex_ray_gain_real_coordinates=44800,
        actual_complete_first_user_direction_coordinates=143400,actual_all_primitive_real_coordinate_observations=322600,
        actual_exact_initial_visible_path_counts=dict(support_counts),actual_distinct_bridge_input_groups=1100,
        actual_distinct_exact_first_user_Gram_solves=3700,
        every_exact_first_user_Gram_and_cross_product_distance_and_MP_ordinate_comparison_pass=True,
        every_original_zero_bridge_shadow_neighborhood_bound_pass=True,
        all_original_scope_and_alias_multiplicities_retained=True,
        literal_first_LoS_geometry_conformance_pass=False,
        actual_fresh_full_original_optimizer_scenario_files_read=0,
        actual_fresh_initial_H_G_B_channel_matrix_contractions=0,
        actual_fresh_original_optimizer_or_native_MC_stream_calls=0,
        public_given_primitive_replay_and_previous_local_full_source_binding_are_distinct=True,
        full_paper_performance_dual_language_or_original_reference_pass=False,source_metadata=metadata)
    return result,dict(selected_support=selected,first_pair=first,seen_users=seen_users,expected_users=expected_users)


def controls(context,output):
    output=Path(output);e.require(not output.exists(),'Preserve every exact-control epoch');output.mkdir();negative=[]
    def reject_support(name,count,change):
        original,scene,entry=context['selected_support'][count];modified=deepcopy(original);change(modified)
        p=output/(name+'.json');e.write(p,modified)
        try:kernel.verify_row(modified,scene,entry)
        except ValueError as error:negative.append(dict(control=name,rejected=True,reason=str(error),SHA256=e.sha(p)));return
        raise AssertionError('Invalid exact support evidence accepted: '+name)
    reject_support('wrong_joint_visible_ray_count',1,lambda x:x.update(actual_initial_visible_path_count=0))
    reject_support('unsafe_full_shadow_neighborhood',0,lambda x:x.update(exact_safe_each_axis_rotation_neighborhood_half_width={'numerator':1,'denominator':1}))
    reject_support('two_paths_misreported_as_dense_rank1_nonzero',2,lambda x:x.update(every_bridge_entry_nonzero_proved_by_single_visible_nonzero_rank1_path=True))
    reject_support('wrong_center_to_center_first_LoS_label',1,lambda x:x.update(actual_first_BR_RB_pair_matches_center_to_center_LoS=True))
    def flip_support(x):
        v=x['actual_full_BR_directions_hex'][0];v[2]=(-float.fromhex(v[2])).hex()
    reject_support('support_direction_sign_changed_preserving_norm',1,flip_support)
    reject_support('one_full_support_direction_coordinate_missing',1,lambda x:x['actual_full_RB_directions_hex'][0].pop())
    reject_support('positive_LoS_coordinate_error_replaced_by_zero',1,lambda x:x.update(exact_maximum_first_LoS_direction_coordinate_error={'numerator':0,'denominator':1}))
    reject_support('wrong_full_original_input_fingerprint',1,lambda x:x.update(input_fingerprint='0'*64))
    def reject_pair(name,change_vectors=None,change_certificate=None):
        vectors,certificate=deepcopy(context['first_pair'])
        if change_vectors:change_vectors(vectors)
        if change_certificate:change_certificate(certificate)
        p=output/(name+'.json');e.write(p,dict(vectors=vectors,certificate=certificate))
        try:kernel.verify_pair(vectors,certificate)
        except ValueError as error:negative.append(dict(control=name,rejected=True,reason=str(error),SHA256=e.sha(p)));return
        raise AssertionError('Invalid exact first-LoS geometry evidence accepted: '+name)
    reject_pair('skew_lines_misreported_as_zero_distance',change_certificate=lambda c:c.update(exact_minimum_infinite_line_separation_squared_m2={'numerator':0,'denominator':1}))
    reject_pair('wrong_exact_Gram_determinant',change_certificate=lambda c:c.update(exact_squared_cross_norm={'numerator':1,'denominator':1}))
    def flip_triple(c):c['exact_center_offset_scalar_triple_product']['numerator']*=-1
    reject_pair('triple_sign_changed_preserving_its_square',change_certificate=flip_triple)
    reject_pair('one_first_user_direction_coordinate_missing',change_vectors=lambda v:v[0].pop())
    def flip_pair(v):v[0][1]=(-float.fromhex(v[0][1])).hex()
    reject_pair('first_user_direction_sign_changed_preserving_norm',change_vectors=flip_pair)
    reject_pair('one_MP100_geometry_ordinate_changed',change_certificate=lambda c:c.update(MP100_line_separation_m='20'))
    reject_pair('complete_MP80_geometry_lane_missing',change_certificate=lambda c:c.pop('MP80_line_separation_m'))
    reject_pair('wrong_disclosed_geometry_scale_decision',change_certificate=lambda c:c.update(above_disclosed1e_minus8_m_diagnostic_scale=False))
    try:e.require((context['seen_users']-{next(iter(context['seen_users']))})==context['expected_users'],'One original full user pair is missing')
    except ValueError as error:negative.append(dict(control='one_full_original_user_pair_missing',rejected=True,reason=str(error)))
    else:raise AssertionError('Incomplete original geometry scope accepted')
    e.require(len(negative)==17,'All original support/geometry controls are required')
    return dict(actual_negative_controls=17,all_expected_invalid_support_geometry_precision_or_scope_controls_rejected=True,controls=negative)
