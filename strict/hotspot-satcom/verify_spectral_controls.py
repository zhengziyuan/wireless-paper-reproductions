"""Shared-language bounded trajectory for the same original RGD controls.

This deliberately bounded full-dimensional synthetic test does not certify
convergence, Monte Carlo performance or an original-paper figure.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import savemat
from verify_statistical import make_fixture
from statistical import expected_projector_square,criterion_value_gradient,rate_value_gradient
from rgd_spectral_controls import phase_rgd


def verify():
    x,phi,W=make_fixture();P=expected_projector_square(x);noise=.1;s={'rgd_max_iterations':12,'gradient_tolerance':1e-12}
    # Lexical closures are the declared evaluator contract used by production.
    def criterion():return lambda v:criterion_value_gradient(x,v,P)
    def rate():return lambda v:rate_value_gradient(x,v,W,noise)
    cp,ch,cs=phase_rgd(phi,criterion(),s);rp,rh,rs=phase_rgd(phi,rate(),s)
    errors={'unit_modulus_max_error':float(max(np.max(abs(abs(cp)-1)),np.max(abs(abs(rp)-1)))),
            'minimum_criterion_increment':float(min(np.diff(ch))),'minimum_rate_increment':float(min(np.diff(rh)))}
    result={'scope':'synthetic_full_dimension_12_step_original_RGD_trajectory_NOT_convergence_or_paper_reproduction',
            'dimensions':{'N':16,'U':6,'K':10,'M':25},'checks':errors,
            'all_passed':bool(errors['unit_modulus_max_error']<1e-12 and errors['minimum_criterion_increment']>=-1e-12 and errors['minimum_rate_increment']>=-1e-12),
            'actual_stops':{'criterion':cs,'rate':rs},'full_reproduction_pass':False}
    fixture={'x':x,'phi':phi,'W':W,'P':P,'noise':noise,'settings':s,'criterion_phi':cp,'criterion_history':ch,'rate_phi':rp,'rate_history':rh}
    return result,fixture


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,default=Path(__file__).with_name('outputs')/'spectral-controls-fixture.mat');p.add_argument('--output',type=Path,default=Path(__file__).with_name('outputs')/'spectral-controls-python.json');a=p.parse_args()
    result,fixture=verify();a.fixture.parent.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True);savemat(a.fixture,fixture)
    result['fixture_sha256']=hashlib.sha256(a.fixture.read_bytes()).hexdigest();result['executed_source_hashes']={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ('verify_spectral_controls.py','rgd_spectral_controls.py','rgd_numerical_controls.py','statistical.py','verify_statistical.py')}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    if not result['all_passed']:raise SystemExit(1)
