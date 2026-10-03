"""Same-original-RGD step-seed diagnosis, never a substitute figure result.

No running production source is edited. The full original criterion, circle
direction/retraction/Armijo1e-4, gradient1e-6 and configured cap are retained.
"""
import argparse
import copy
import json
import time
from pathlib import Path
import numpy as np
from scenario import sample_scenario
from statistical import expected_projector_square,criterion_value_gradient
from rgd_numerical_controls import criterion_increment
from run_support import source_hashes,unchanged,save_receipt


def diagnose(config,strategy):
    config=copy.deepcopy(config);config['reported'].update(U=4,K=12,kappa_satellite_db=10,kappa_ground_db=20,nhu_statistical_sinr_db=-3)
    s=config['tuned_not_reported'];f=sample_scenario(config,np.random.default_rng(s['seed']));x=f['mean_inputs'];P=expected_projector_square(x)
    phi=f['phi0'];value,g=criterion_value_gradient(x,phi,P);seed=1/max(np.linalg.norm(g),np.finfo(float).tiny);trace=[];history=[value];start=time.perf_counter();backtracks=0
    for it in range(s['rgd_max_iterations']):
        norm2=float(np.vdot(g,g).real)
        if np.sqrt(norm2)<=s['gradient_tolerance']:break
        alpha=seed
        for search in range(60):
            new=phi+alpha*g;new/=abs(new);delta=criterion_increment(x,phi,new,P)
            if delta>=1e-4*alpha*norm2:break
            alpha/=2;backtracks+=1
        else:raise RuntimeError('Same-original RGD exact-increment Armijo exhausted')
        trial,newg=criterion_value_gradient(x,new,P);step=np.angle(np.conj(phi)*new)
        oldtheta=np.real(np.conj(1j*phi)*g);newtheta=np.real(np.conj(1j*new)*newg);ydiff=oldtheta-newtheta
        curvature=float(step@ydiff);distance=float(step@step);yy=float(ydiff@ydiff)
        if curvature>0 and distance>0:
            bb1=distance/curvature;bb2=curvature/yy
            seed=bb2 if strategy=='BB2' or (strategy=='alternating_BB1_BB2' and it%2==0) else bb1
        else:seed=2*alpha
        seed=float(np.clip(seed,1e-12,1e12));phi,value,g=new,trial,newg;history.append(value)
        if it%250==0:
            trace.append({'iteration':it+1,'gradient_norm':float(np.linalg.norm(g)),'accepted_step':alpha,'next_seed':seed})
            print(json.dumps({'step_seed_diagnostic':strategy,**trace[-1]}),flush=True)
    return {'strategy':strategy,'scope':'single_full_dimension_original_TS_phase_control_diagnosis_NOT_full_figure_or_MC',
            'elapsed_seconds':time.perf_counter()-start,'iterations':len(history)-1,'iteration_cap':s['rgd_max_iterations'],
            'gradient_norm':float(np.linalg.norm(g)),'threshold':s['gradient_tolerance'],'converged':bool(np.linalg.norm(g)<=s['gradient_tolerance']),
            'backtracks':backtracks,'history':history,'trace':trace,'criterion_final':value,'full_reproduction_pass':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--strategy',choices=['BB2','alternating_BB1_BB2'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    names=['diagnose_phase_seed.py','scenario.py','statistical.py','rgd_numerical_controls.py','run_support.py','full_config.json'];hashes=source_hashes(names)
    result=diagnose(json.loads(Path(__file__).with_name('full_config.json').read_text()),a.strategy)
    result.update(executed_source_hashes=hashes,source_unchanged_during_run=unchanged(hashes));save_receipt(a.output,result);print(json.dumps({k:v for k,v in result.items() if k not in ('history','trace','executed_source_hashes')}))
