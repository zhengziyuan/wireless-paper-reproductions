"""Unchanged exact numerical kernels from the complete local source-bound audits."""

from fractions import Fraction

import mpmath as mp

from evidence import require

def frac(d):
    require(isinstance(d,dict) and set(d)=={'numerator','denominator'},'Exact rational components missing')
    require(isinstance(d['numerator'],int) and isinstance(d['denominator'],int) and d['denominator']>0,'Invalid exact rational')
    return Fraction(d['numerator'],d['denominator'])

def verify_row(row,scene,expected):
    require(row['input_fingerprint']==expected['input_fingerprint'],'An original immutable fingerprint changed')
    require(row['filename']==expected['filename'],'An original case name changed')
    require(scene['initial_angles']==[0]*6 and scene['bs_center']==[0]*3 and scene['ris_center']==[10,0,0],'Actual geometry/init differs')
    require(scene['maximum_gain']>0 and scene['directivity_exponent'] in (0,2),'A positive half-space model is required')
    br=scene['br_directions'];rb=scene['rb_directions']
    require(len(br)==len(rb)==2 and all(len(x)==3 for x in br+rb),'Every original complete ray vector is required')
    encoded_br=[[float(x).hex() for x in v] for v in br];encoded_rb=[[float(x).hex() for x in v] for v in rb]
    require(row['actual_full_BR_directions_hex']==encoded_br and row['actual_full_RB_directions_hex']==encoded_rb,
        'A complete binary direction coordinate differs from the actual input')
    require(all(v[2]!=0 and all(abs(x)<=1 for x in v) for v in br+rb),'A shadow-margin premise is absent')
    require(row['actual_nonzero_complex_path_gains'] and all(a!=0 or b!=0 for a,b in zip(scene['br_gain_re'],scene['br_gain_im'])),
        'An actual nonzero rank-one ray gain is required')
    masks=[Fraction.from_float(a[2])>0 and Fraction.from_float(b[2])>0 for a,b in zip(br,rb)];n=sum(masks)
    require(row['actual_initial_joint_visible_paths']==masks and row['actual_initial_visible_path_count']==n,'Joint ray support differs')
    require(row['zero_bridge_proved_by_all_path_supports_blocked']==(n==0),'A zero-bridge support conclusion changed')
    require(row['every_bridge_entry_nonzero_proved_by_single_visible_nonzero_rank1_path']==(n==1),
        'The exact single-path nonzero claim is invalid')
    require(row['two_path_full_bridge_nonzero_not_inferred_from_support_count']==(n==2),
        'A two-ray cancellation assumption was introduced')
    geometric=br[0]==[1,0,0] and rb[0]==[-1,0,0]
    require(row['actual_first_BR_RB_pair_matches_center_to_center_LoS']==geometric,'The source-qualified first-LoS geometry label changed')
    error=max(abs(Fraction.from_float(x)-y) for a,b in ((br[0],[1,0,0]),(rb[0],[-1,0,0])) for x,y in zip(a,b))
    require(frac(row['exact_maximum_first_LoS_direction_coordinate_error'])==error,'The exact first-LoS coordinate residual changed')
    if n==0:
        margin=min(max(-Fraction.from_float(a[2]),-Fraction.from_float(b[2])) for a,b in zip(br,rb))
        delta=frac(row['exact_safe_each_axis_rotation_neighborhood_half_width'])
        require(margin>0 and frac(row['exact_minimum_blocked_side_cosine_margin'])==margin,'A complete exact shadow margin differs')
        require(delta>0 and delta.numerator==1 and delta.denominator&(delta.denominator-1)==0,'A positive exact dyadic radius is required')
        require(36*delta<=margin,'The claimed full rotation neighborhood can cross a visibility boundary')
        require(row['full_bridge_remains_zero_in_same_shadow_neighborhood'] and
            row['fixed_BS_orientation_objective_locally_independent_of_RIS_phase_and_RIS_rotation'] and
            row['BS_rotation_may_leave_this_neighborhood_and_activate_RIS'],'A conditional locality qualification is missing')
    return n,geometric

def dot(a,b):return sum(x*y for x,y in zip(a,b))

def verify_pair(encoded,certificate):
    require(len(encoded)==2 and all(len(v)==3 for v in encoded),'Both complete three-coordinate first-ray vectors are required')
    a,b=[[Fraction.from_float(float.fromhex(x)) for x in v] for v in encoded]
    aa,bb,ab=dot(a,a),dot(b,b),dot(a,b);ad,bd=10*a[0],10*b[0]
    determinant=aa*bb-ab*ab
    require(determinant>0,'A nonsingular closest-lines Gram matrix is required')
    t=(bb*ad-ab*bd)/determinant;s=(ab*ad-aa*bd)/determinant
    residual=[t*x-s*y-d for x,y,d in zip(a,b,(10,0,0))]
    require(dot(residual,a)==dot(residual,b)==0,'Exact closest-line orthogonality/KKT residuals differ')
    distance_squared=dot(residual,residual)
    require(distance_squared>0,'The supplied disjoint-line conclusion changed')
    require(frac(certificate['exact_minimum_infinite_line_separation_squared_m2'])==distance_squared,
        'The independent exact Gram distance disagrees with the cross-product certificate')
    require(frac(certificate['exact_squared_cross_norm'])==determinant,'The exact cross-product/Gram determinant identity differs')
    triple=10*(a[1]*b[2]-a[2]*b[1])
    require(frac(certificate['exact_center_offset_scalar_triple_product'])==triple,'A signed exact triple-product coordinate changed')
    require(certificate['exact_disjoint_supporting_lines_proved'] is True,'The source-qualified disjoint-line label changed')
    above=distance_squared>Fraction(1,10**16)
    require(certificate['above_disclosed1e_minus8_m_diagnostic_scale']==above,'The disclosed diagnostic distance comparison changed')
    require(all(name in certificate for name in ('MP80_line_separation_m','MP100_line_separation_m')),'One complete MP precision lane is absent')
    with mp.workdps(120):
        exact=mp.sqrt(mp.mpf(distance_squared.numerator)/distance_squared.denominator)
        p80,p100=mp.mpf(certificate['MP80_line_separation_m']),mp.mpf(certificate['MP100_line_separation_m'])
        require(abs(exact-p80)<=mp.mpf('1e-60') and abs(exact-p100)<=mp.mpf('1e-90'),
            'A complete arbitrary-precision line-distance ordinate differs from the exact Gram result')
        require(abs(p80-p100)<=mp.mpf('1e-60'),'The complete MP80/MP100 line-distance lanes disagree')
    return distance_squared,above
