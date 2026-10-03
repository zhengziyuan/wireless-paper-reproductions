"""Independent exact-objective increment evidence and MATLAB fixture.

Synthetic full-rank component inputs are labelled as such. No paper curves are
provided by this test and no full-reproduction claim follows from it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import savemat
from verify_statistical import make_fixture
from statistical import expected_projector_square,criterion_value_gradient,rate_value_gradient
from rgd_numerical_controls import criterion_increment,rate_increment


def verify():
    x,old,W=make_fixture();P=expected_projector_square(x);rng=np.random.default_rng(8450)
    new=np.asarray([old*np.exp(1j*scale*rng.normal(size=25)) for scale in (1.,1e-2,1e-4,1e-6,1e-8)])
    criterion=np.asarray([criterion_increment(x,old,v,P) for v in new]);rate=np.asarray([rate_increment(x,old,v,W,.1) for v in new])
    cf0=criterion_value_gradient(x,old,P)[0];rf0=rate_value_gradient(x,old,W,.1)[0]
    ce=max(abs(criterion[i]-(criterion_value_gradient(x,v,P)[0]-cf0)) for i,v in enumerate(new))
    re=max(abs(rate[i]-(rate_value_gradient(x,v,W,.1)[0]-rf0)) for i,v in enumerate(new))
    identity=max(abs(criterion_increment(x,old,old,P)),abs(rate_increment(x,old,old,W,.1)))
    result={'scope':'synthetic_full_rank_full_dimension_exact_increment_component_NOT_paper_reproduction',
            'dimensions':{'N':16,'U':6,'K':10,'M':25},'criterion_difference_max_absolute_error':float(ce),
            'rate_difference_max_absolute_error':float(re),'zero_step_exact_identity_error':float(identity),
            'all_passed':bool(ce<1e-11 and re<1e-11 and identity==0),'full_reproduction_pass':False}
    fixture={'x':x,'old':old,'new':new,'W':W,'noise':.1,'P':P,'criterion_increment':criterion,'rate_increment':rate}
    return result,fixture


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path(__file__).with_name('outputs')/'rgd-controls-python.json')
    p.add_argument('--fixture',type=Path,default=Path(__file__).with_name('outputs')/'rgd-controls-fixture.mat');a=p.parse_args();result,fixture=verify()
    a.fixture.parent.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True);savemat(a.fixture,fixture)
    result['fixture_sha256']=hashlib.sha256(a.fixture.read_bytes()).hexdigest()
    result['executed_source_hashes']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('verify_rgd_controls.py','rgd_numerical_controls.py','statistical.py','verify_statistical.py')}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    if not result['all_passed']:raise SystemExit(1)
