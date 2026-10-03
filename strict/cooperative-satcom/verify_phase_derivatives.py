"""Independent all-coordinate scalar/contraction and finite-difference audit."""
import argparse
import copy
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.io import savemat
from scenario import make_scenario
from algorithms import mr_initial,feasible_scale
from models import (mr_components,channel_moments,mr_phase_value_gradient,
                    mr_phase_value_gradient_reference,ap_phase_value_gradient,
                    ap_phase_value_gradient_reference)


def verify(config):
    cases=[];fixture=None;rng=np.random.default_rng(10443)
    for kappa in (0,20):
        scene=copy.deepcopy(config);scene['reported']['kappa_leo_db']=kappa
        data,pl,il=make_scenario(scene);phi=np.exp(1j*rng.uniform(-np.pi,np.pi,data['r_mean'].shape))
        mean=channel_moments(data,phi)[0];W=feasible_scale(np.transpose(mean,(0,2,1)),data['gt_second'],pl,il)
        mrp={};checks=[]
        for tts in (False,True):
            coef=mr_components(data,phi,tts);p=mr_initial(coef,pl,il);mrp[tts]=p
            value,g=mr_phase_value_gradient(data,phi,p,.1,il,tts);old,oldg=mr_phase_value_gradient_reference(data,phi,p,.1,il,tts)
            errors=[]
            for u in range(phi.shape[0]):
                for m in range(phi.shape[1]):
                    plus,minus=phi.copy(),phi.copy();plus[u,m]*=np.exp(1j*1e-5);minus[u,m]*=np.exp(-1j*1e-5)
                    numeric=(mr_phase_value_gradient(data,plus,p,.1,il,tts)[0]-mr_phase_value_gradient(data,minus,p,.1,il,tts)[0])/2e-5
                    analytic=np.real(np.conj(1j*phi[u,m])*g[u,m]);errors.append(abs(analytic-numeric)/max(1,abs(numeric)))
            checks.append({'scheme':'MR-TTS' if tts else 'MR-S','value_error':abs(value-old),'gradient_relative_error':float(np.max(abs(g-oldg))/max(1,np.max(abs(oldg)))),
                           'finite_difference_relative_error_all50':max(errors)})
        value,g=ap_phase_value_gradient(data,phi,W);old,oldg=ap_phase_value_gradient_reference(data,phi,W);errors=[]
        for u in range(phi.shape[0]):
            for m in range(phi.shape[1]):
                plus,minus=phi.copy(),phi.copy();plus[u,m]*=np.exp(1j*1e-5);minus[u,m]*=np.exp(-1j*1e-5)
                numeric=(ap_phase_value_gradient(data,plus,W)[0][u]-ap_phase_value_gradient(data,minus,W)[0][u])/2e-5
                analytic=np.real(np.conj(1j*phi[u,m])*g[u,m]);errors.append(abs(analytic-numeric)/max(1,abs(numeric)))
        checks.append({'scheme':'AP','value_error':float(np.max(abs(value-old))),'gradient_relative_error':float(np.max(abs(g-oldg))/max(1,np.max(abs(oldg)))),
                       'finite_difference_relative_error_all50':max(errors)})
        cases.append({'kappa_leo_db':kappa,'checks':checks,'passed':all(c['value_error']<1e-10 and c['gradient_relative_error']<1e-10 and c['finite_difference_relative_error_all50']<1e-7 for c in checks)})
        fixture={'data':data,'phi':phi,'W':W,'p_stat':mrp[False],'p_tts':mrp[True],'limit':il,'smoothing':.1,
                 'AP_value':value,'AP_gradient':g,'MR_S_value':mr_phase_value_gradient(data,phi,mrp[False],.1,il,False)[0],
                 'MR_S_gradient':mr_phase_value_gradient(data,phi,mrp[False],.1,il,False)[1],
                 'MR_TTS_value':mr_phase_value_gradient(data,phi,mrp[True],.1,il,True)[0],
                 'MR_TTS_gradient':mr_phase_value_gradient(data,phi,mrp[True],.1,il,True)[1]}
    return {'scope':'original_full_dimension_analytic_derivative_contraction_component_audit_NOT_full_reproduction',
            'dimensions':{'J':3,'U':2,'N':16,'M':25,'K':1},'cases':cases,'all_passed':all(c['passed'] for c in cases),'full_reproduction_pass':False},fixture


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path(__file__).with_name('outputs')/'phase-derivative-contraction-python.json')
    parser.add_argument('--fixture',type=Path,default=Path(__file__).with_name('outputs')/'phase-derivative-contraction-fixture.mat');args=parser.parse_args();start=time.perf_counter()
    config=json.loads(Path(__file__).with_name('full_config.json').read_text());result,fixture=verify(config)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.fixture.parent.mkdir(parents=True,exist_ok=True);savemat(args.fixture,fixture)
    result.update(elapsed_seconds=time.perf_counter()-start,executed_source_sha256=hashlib.sha256(Path(__file__).with_name('models.py').read_bytes()).hexdigest(),
                  fixture_sha256=hashlib.sha256(args.fixture.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    if not result['all_passed']:raise SystemExit(1)
