"""Independent exact-original AP/MR objective increment identities.

All configured physical dimensions are retained. Tests are component evidence,
not source-paper curves or a certification of the complete algorithm chains.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import savemat
from scenario import make_scenario
from algorithms import feasible_scale,mr_initial
from models import channel_moments,mr_components,ap_phase_value_gradient,mr_phase_value_gradient
from increments import ap_increment,mr_increment


def verify(config):
    rng=np.random.default_rng(24560);cases=[];fixture=None
    for kappa in (0,20):
        scene=copy.deepcopy(config);scene['reported']['kappa_leo_db']=kappa
        data,pl,il=make_scenario(scene);old=np.exp(1j*rng.normal(size=data['r_mean'].shape));mean=channel_moments(data,old)[0]
        W=feasible_scale(np.transpose(mean,(0,2,1)),data['gt_second'],pl,il);new=np.asarray([old*np.exp(1j*scale*rng.normal(size=old.shape)) for scale in (1.,1e-2,1e-4,1e-6,1e-8)])
        ap0=ap_phase_value_gradient(data,old,W)[0];ap=np.asarray([ap_increment(data,old,v,W) for v in new]);ae=max(np.max(abs(ap[k]-(ap_phase_value_gradient(data,v,W)[0]-ap0))) for k,v in enumerate(new))
        check={'AP_max_error':float(ae),'AP_identity_error':float(np.max(abs(ap_increment(data,old,old,W))))};ps={};ms={}
        for tts in (False,True):
            p=mr_initial(mr_components(data,old,tts),pl,il);ps[tts]=p
            f0=mr_phase_value_gradient(data,old,p,.1,il,tts)[0];inc=np.asarray([mr_increment(data,old,v,p,.1,il,tts) for v in new]);ms[tts]=inc
            error=max(abs(inc[k]-(mr_phase_value_gradient(data,v,p,.1,il,tts)[0]-f0)) for k,v in enumerate(new))
            prefix='MR_TTS' if tts else 'MR_S';check[prefix+'_max_error']=float(error);check[prefix+'_identity_error']=abs(mr_increment(data,old,old,p,.1,il,tts))
        cases.append({'kappa_leo_db':kappa,'checks':check,'all_passed':all(v<1e-11 for v in check.values())})
        fixture={'data':data,'old':old,'new':new,'W':W,'p_stat':ps[False],'p_tts':ps[True],'limit':il,'smoothing':.1,
                 'AP_increment':ap,'MR_S_increment':ms[False],'MR_TTS_increment':ms[True]}
    return {'scope':'full_dimension_exact_original_objective_increment_component_NOT_paper_reproduction',
            'dimensions':{'J':3,'U':2,'N':16,'M':25,'K':1},'cases':cases,
            'all_passed':all(c['all_passed'] for c in cases),'full_reproduction_pass':False},fixture


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path(__file__).with_name('outputs')/'phase-increments-python.json')
    p.add_argument('--fixture',type=Path,default=Path(__file__).with_name('outputs')/'phase-increments-fixture.mat');args=p.parse_args()
    result,fixture=verify(json.loads(Path(__file__).with_name('full_config.json').read_text()));args.fixture.parent.mkdir(parents=True,exist_ok=True);args.output.parent.mkdir(parents=True,exist_ok=True)
    savemat(args.fixture,fixture);result['fixture_sha256']=hashlib.sha256(args.fixture.read_bytes()).hexdigest()
    result['executed_source_hashes']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('verify_increments.py','increments.py','models.py','core.py','scenario.py','algorithms.py','full_config.json')}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    if not result['all_passed']:raise SystemExit(1)
