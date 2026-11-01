"""One captured failed state: independent saved-coefficient MP contractions."""
from pathlib import Path
import hashlib,io,json
import numpy as np
import mpmath as mp

import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
HERE=Path(__file__).resolve().parent;D=args.output_dir.resolve();assert not D.exists(),'Fresh output only';D.mkdir(parents=True)
O=HERE/'evidence';J=O/'actual-owned-terminal.json';CORE=HERE/'source-reference/original-core-physical-prefix.py'
manifest=json.loads((HERE/'MANIFEST.json').read_bytes())
for item in manifest['files']:
    assert hashlib.sha256((HERE/item['path']).read_bytes()).hexdigest()==item['SHA256'],'Published source/evidence bytes differ from manifest'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def q(value):
    n,d=float(value).as_integer_ratio();return mp.mpf(n)/mp.mpf(d)
def z(value):return mp.mpc(q(value.real),q(value.imag))
def text(value):return mp.nstr(value,70)
def whole_zero(a):return bool(np.count_nonzero(a)==0)

before={str(p):sha(p.read_bytes()) for p in [J,O/'actual-first-iota-guard-operands.npz',O/'actual-first-iota-guard-capture.json',O/'actual-failed-scheme-scene.json',O/'ACTUAL_SINGLE_SCHEME_FIRST_IOTA_GUARD_DIAGNOSTIC_OUTCOME_V1.json',CORE,Path(__file__).resolve(),HERE/'MANIFEST.json']}
j=read(J);capture=read(O/'actual-first-iota-guard-capture.json');outcome=read(O/'ACTUAL_SINGLE_SCHEME_FIRST_IOTA_GUARD_DIAGNOSTIC_OUTCOME_V1.json')
assert j['actual_child_terminal_exit_code']==0 and j['effective_host_exit_code']==0 and j['natural_wait_completed'] and j['exact_original_handle_birth_and_exit_match'] and j['all_watched_source_and_job_bytes_unchanged']
assert outcome['first_original_iota_guard_capture_complete'] and outcome['original_scheme_failed'] and outcome['source_closed'] and not outcome['observer_transport_errors']
raw=(O/'actual-first-iota-guard-operands.npz').read_bytes();assert sha(raw)==capture['raw_numeric_backup']['SHA256']=='0949b55d22eb395da936642ff402c217cf587f0a5abc9b6d52f0d08f730285aa'
with np.load(io.BytesIO(raw),allow_pickle=False) as f:arrays={key:f[key].copy() for key in f.files}
scene=read(O/'actual-failed-scheme-scene.json');assert all(float(v)==0 for key in ['br_gain_re','br_gain_im'] for v in scene[key])
assert whole_zero(arrays['bridge']) and float(arrays['overlap'])==0 and np.signbit(arrays['overlap'])==False
assert all(np.isfinite(a).all() for a in arrays.values())
targets=np.flatnonzero(arrays['pd']>0).tolist();assert targets==[40,57]
M,L=arrays['fs'].shape;streams=arrays['w'].shape[1]
old_iota=next(row['iota'] for row in capture['actual_original_call_stack'] if row['function']=='optimize')
lanes=[]
for precision in [80,100]:
    with mp.workdps(precision):
        x,y,az=[q(v) for v in arrays['r'][:3]]
        cx,sx,cy,sy,cz,sz=mp.cos(x),mp.sin(x),mp.cos(y),mp.sin(y),mp.cos(az),mp.sin(az)
        rx=mp.matrix([[1,0,0],[0,cx,-sx],[0,sx,cx]]);ry=mp.matrix([[cy,0,sy],[0,1,0],[-sy,0,cy]]);rz=mp.matrix([[cz,-sz,0],[sz,cz,0],[0,0,1]])
        rotation=rx*ry*rz
        cosines=[mp.fsum(rotation[a,2]*q(direction[a]) for a in range(3)) for direction in scene['bt_directions']]
        front=[i for i,v in enumerate(cosines) if v>0];back=[i for i,v in enumerate(cosines) if v<=0]
        reference_z=[];reference_p=[]
        for i in range(L):
            row=[mp.fsum(mp.conj(z(arrays['fs'][a,i]))*z(arrays['w'][a,s]) for a in range(M)) for s in range(streams)]
            reference_z.append(row);reference_p.append(mp.fsum(v.real*v.real+v.imag*v.imag for v in row))
        overlap=mp.fsum(q(arrays['pd'][i])*reference_p[i] for i in range(L))
        pattern_norm2=mp.fsum(v*v for v in reference_p);energy=mp.fsum(q(v)*q(v) for v in arrays['pd'])
        max_p_error=max(abs(reference_p[i]-q(arrays['p'][i])) for i in range(L))
        max_z_error=max(abs(reference_z[i][s]-z(arrays['z'][i,s])) for i in range(L) for s in range(streams))
        fixed_nmse=mp.mpf(1)+pattern_norm2/(q(old_iota)**2*energy)
        back_zero=all(whole_zero(arrays['fs'][:,i]) and whole_zero(arrays['z'][i]) and float(arrays['p'][i])==0 for i in back)
        all_target_exact_zero=all(reference_p[i]==0 and whole_zero(arrays['fs'][:,i]) for i in targets)
        assert overlap==0 and pattern_norm2>0 and all_target_exact_zero and back_zero
        lanes.append(dict(decimal_precision=precision,
          source_rotation_order='Rx @ Ry @ Rz; all saved binary64 angles/directions enter exactly through integer ratios',
          front_sensing_indices_zero_based=front,back_or_tangent_sensing_indices_zero_based=back,
          all_saved_back_columns_are_exact_zero=back_zero,
          desired_target_rows=[dict(sensing_index_zero_based=i,sensing_index_one_based=i+1,full_field_column_zero_based=i+int(arrays['k']),
            exact_binary64_direction=scene['bt_directions'][i],independent_MP_cosine=text(cosines[i]),
            saved_fs_column_all_exact_zero=whole_zero(arrays['fs'][:,i]),saved_z_row_all_exact_zero=whole_zero(arrays['z'][i]),
            saved_p_float_hex=float(arrays['p'][i]).hex(),independent_saved_coefficient_p=text(reference_p[i])) for i in targets],
          independent_same_coefficient_overlap=text(overlap),independent_pattern_norm_squared=text(pattern_norm2),desired_energy=text(energy),
          maximum_p_absolute_error_against_binary64_saved=text(max_p_error),maximum_z_complex_error_against_binary64_saved=text(max_z_error),
          beta_reparameterization='beta=1/iota; NMSE(beta)=||beta*p-pd||^2/||pd||^2',
          exact_nonnegative_beta_optimum='0',finite_positive_iota_minimizer_exists=False,NMSE_infimum='1',
          captured_previous_iota=old_iota,post_rotation_NMSE_at_that_fixed_iota=text(fixed_nmse),
          post_rotation_fixed_iota_excess_over_infimum=text(fixed_nmse-1),
          precision_scope='MP80/100 of full saved fs^H W and pattern contraction; independent high-precision Euler/cosine branch signs. No new channels/RNG/optimization, full gradients or entire trajectory claim.'))

assert lanes[0]['front_sensing_indices_zero_based']==lanes[1]['front_sensing_indices_zero_based']
assert lanes[0]['back_or_tangent_sensing_indices_zero_based']==lanes[1]['back_or_tangent_sensing_indices_zero_based']
after={p:sha(Path(p).read_bytes()) for p in before};assert before==after
report=dict(schema='actual-ISAC004-first-iota-guard-saved-state-zero-overlap-MP80-MP100-cause-v1',source_before=before,source_after=after,source_interval_closed=True,
  actual_diagnostic_held_terminal=dict(actual_child_terminal_exit_code=0,effective_host_exit_code=0,exact_original_handle_birth_and_exit_match=True,source_closed=True),
  original_scheme_failed_retained=True,actual_original_optimize_calls=outcome['new_original_scheme_optimizer_calls'],actual_initializations=outcome['actual_original_initializations'],
  actual_evaluate_call_ordinal_1based=capture['original_evaluate_call_ordinal_1based'],actual_outer_iteration_zero_based=3,
  binary64_observed=dict(overlap=float(arrays['overlap']),epsilon=float(arrays['iota_denominator_epsilon']),pattern_nonzero_count=int(np.count_nonzero(arrays['p'])),pattern_length=L,
    maximum_pattern=float(arrays['p'].max()),desired_support=targets,W_power=float(np.sum(abs(arrays['w'])**2)),bridge_all_exact_zero=whole_zero(arrays['bridge']),
    W_nonzero_complex_elements=int(np.count_nonzero(arrays['w'])),all_saved_operands_finite=True),
  MP_lanes=lanes,
  conclusion='Genuine p!=0, pd^T p=0 state. Both desired directions are strictly in the BS back hemisphere; original response cosine<=0 branch returns exact zeros. NoRIS bridge is exactly zero. Neither dot-product cancellation, underflow nor the positive epsilon creates the zero overlap.',
  epsilon_assessment='Reducing epsilon even to0 cannot make this exact-zero overlap positive; no epsilon fitting or threshold change is justified.',
  source_anchors=[dict(file='strict/rotatable-isac/core.py',lines=[18,19,22],claim='Back/tangent hemisphere response and derivatives return exact zeros'),
    dict(file='strict/rotatable-isac/core.py',lines=[44,45,46],claim='Sensing direct channel uses one BS response per target'),
    dict(file='strict/rotatable-isac/core.py',lines=[65,66],claim='NoRIS zero bridge leaves direct field'),
    dict(file='strict/rotatable-isac/core.py',lines=[79,80,81,82,83,84],claim='Automatic iota formula guard and normalized pattern error'),
    dict(file='strict/rotatable-isac/core.py',lines=[236,238,241,242,243,244],claim='Original outer order: fixed current iota during W/rotation, then automatic iota refresh after rotation')],
  mathematical_boundary=dict(p_all_zero_case_applies=False,actual_case='nonzero p orthogonal to desired support',
    identity='For E=pd^Tpd>0, S=p^Tp>0 and O=pd^Tp=0, NMSE(iota)=1+S/(E*iota^2)>1 for every finite positive iota; infimum1 only at iota->infinity.',
    original_finite_iota_formula_has_no_finite_optimum_here=True,
    possible_future_transparent_variants=['The paper practical c/(d+epsilon) branch is a separate future implementation; epsilon must be declared reconstruction metadata and not fitted.',
      'If the finite-iota original domain must be retained, add a source-supported admissibility/domain condition preserving positive desired overlap; this is a model/algorithm-domain change and requires justification.'],
    no_finite_iota_fallback_or_clamp_introduced=True),
  remaining_limits=['Only the failed returned state is captured; prior accepted rotation iterates/trials are not available, so the first crossing of a hemisphere boundary is not localized.',
    'Eq23 explicitly requires d>0; the paper also prints practical c/(d+epsilon), whose epsilon value is unspecified. Read evidence/manuscript-and-strict-implementation-scope.json; this strict guard is not that practical branch.',
    'Original500 failure, full-case scientific status, physical/reference and full-trajectory gates remain unchanged.'],
  optimizer_MC_RNG_or_sample_generation_calls_in_this_analysis=0,full_case_original_reference_or_paper_PASS=False)
p=D/'ACTUAL_ISAC004_ZERO_OVERLAP_BACK_HEMISPHERE_AND_NO_FINITE_IOTA_MP80_MP100_CAUSE_V1.json'
assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(report=str(p),SHA256=sha(p.read_bytes()),pattern_nonzero=report['binary64_observed']['pattern_nonzero_count'],targets=lanes[-1]['desired_target_rows'],pattern_norm_squared=lanes[-1]['independent_pattern_norm_squared'],fixed_iota_NMSE=lanes[-1]['post_rotation_NMSE_at_that_fixed_iota'],no_finite_positive_iota_minimizer=True,source_closed=True)))
