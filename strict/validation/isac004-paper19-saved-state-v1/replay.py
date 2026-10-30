"""Replay one saved NoRIS state; no optimizer, channel generator, or samples."""
from argparse import ArgumentParser
from decimal import Decimal, getcontext
from pathlib import Path
import json
import numpy as np

getcontext().prec=80
parser=ArgumentParser()
parser.add_argument('--input-dir', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path, help='New JSON file; existing files are never overwritten')
args=parser.parse_args()
if args.output.exists():
    raise FileExistsError('Output exists; choose a new output file.')
scene=json.loads((args.input_dir/'scene.json').read_text(encoding='utf-8'))
with np.load(args.input_dir/'operands.npz',allow_pickle=False) as f:
    if set(f.files)!={'w','r','p','pd','bridge','fs'}:
        raise ValueError('Unexpected operand set.')
    w,r,p,pd,bridge,fs=(f[k].copy() for k in ('w','r','p','pd','bridge','fs'))
if w.shape!=(4,6) or r.shape!=(6,) or p.shape!=(66,) or pd.shape!=(66,) or bridge.shape!=(4,36) or fs.shape!=(4,66):
    raise ValueError('Unexpected shapes; this reader is for the documented state.')
if not all(np.all(np.isfinite(a)) for a in (w,r,p,pd,bridge,fs)):
    raise ValueError('Nonfinite values.')
if not np.all(bridge==0) or not np.all(p>=0) or not np.all((pd==0)|(pd==1)):
    raise ValueError('Expected NoRIS, nonnegative powers and binary desired pattern.')
if not np.array_equal(np.flatnonzero(pd),np.array([40,57])):
    raise ValueError('Unexpected desired pattern support.')
full_power=np.sum(abs(fs.conj().T@w)**2,axis=1)
if not np.allclose(full_power,p,rtol=4e-14,atol=4e-14):
    raise ValueError('Saved p does not match saved field and W.')
x,y,z=r[:3];cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
q=(np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]) @ np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]) @ np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]]))
u=np.asarray(scene['bt_directions']);coords=np.asarray(scene['bs_coordinates']);center=np.asarray(scene['bs_center'])
positions=coords@q.T+center
steering=np.exp(1j*(2*np.pi/scene['wavelength'])*(u@positions.T))
cosines=u@q[:,2]
gain=scene['maximum_gain']*np.maximum(cosines,0)**scene['directivity_exponent']
printed_direct=np.sum(abs(steering.conj()@w)**2,axis=1)
corrected=gain*printed_direct
if not np.allclose(corrected,p,rtol=4e-14,atol=4e-14):
    raise ValueError('Saved state does not match corrected direct-channel power.')
if not (np.all(cosines[[40,57]]<0) and np.all(p[[40,57]]==0) and np.all(printed_direct[[40,57]]>0)):
    raise ValueError('Expected saved back-hemisphere counterexample is absent.')
D=lambda a:Decimal.from_float(float(a))
pp=[D(t) for t in p];dd=[D(t) for t in pd]
c=sum(t*t for t in pp); e=sum(t*t for t in dd); d=sum(a*b for a,b in zip(pp,dd)); prev=D(scene['previous_iota'])
if not (c>0 and e>0 and d==0 and prev>0):
    raise ValueError('Expected saved positive energy, positive iota and zero overlap are absent.')
limit=c/prev
previous_excess=c/(e*prev*prev)
report={
 'scope':'One saved ISAC004 Rot-BS and No-RIS state, not an optimizer run or whole-paper acceptance.',
 'paper_version':'arXiv:2512.20987v2, 28 Feb 2026',
 'paper_url':'https://arxiv.org/html/2512.20987v2#S2.SS4',
 'printed_eq19':'Direct coefficient is 1; mixed coefficient is 2*sqrt(G_B*G_R); reflected-power coefficient is sqrt(G_B*G_R).',
 'correct_eq19':'Expanding the channel in Eq.14 within Eq.18 gives direct coefficient G_B, mixed coefficient 2*sqrt(G_B*G_R), reflected-power coefficient G_R.',
 'target_directions':[{'index_zero_based':int(i),'boresight_cosine':float(cosines[i]),'bs_gain':float(gain[i]),'eq18_saved_power':float(p[i]),'printed_eq19_power':float(printed_direct[i])} for i in (40,57)],
 'max_absolute_saved_field_replay_minus_saved_power':float(np.max(abs(full_power-p))),
 'max_absolute_corrected_direct_minus_saved_power':float(np.max(abs(corrected-p))),
 'nonzero_RIS_case_verified':False,
 'saved_binary64_coefficients_treated_as_exact':{'c':str(c),'d':str(d),'e':str(e),'previous_iota':str(prev)},
 'statewise_regularization':'For c,e>0, d>=0, eps>0 and iota_eps=c/(d+eps), NMSE_eps=1+(eps^2-d^2)/(e*c). The fixed-state update does not increase NMSE relative to finite iota0>0 iff eps<=abs(c/iota0-d). At this state d=0, finite iota has NMSE>1, and the infimum 1 is approached only as iota tends to positive infinity.',
 'this_state_epsilon_upper_bound_for_nonincrease':str(limit),
 'previous_iota_nmse_excess_above_infimum':str(previous_excess),
 'author_epsilon':'Not specified by this evidence; no epsilon selected or fitted.',
 'whole_paper_or_trajectory_or_convergence_or_reference_agreement_passed':False,
}
with args.output.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
print('Saved-state checks passed; wrote new report:',args.output)

