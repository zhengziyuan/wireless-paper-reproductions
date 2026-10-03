"""Original full model/RGD direction and1e-6 stop, larger unreported safety cap.

Phase-only diagnostic is not a replacement figure point or a smaller scenario.
"""
import copy
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.io import savemat
from scenario_geometry import sample_scenario
from statistical import expected_projector_square,criterion_value_gradient
from rgd_spectral_controls import phase_rgd
from run_support import source_hashes,unchanged,save_receipt


def diagnose(config):
    f=sample_scenario(config,np.random.default_rng(config['tuned_not_reported']['seed']));x=f['mean_inputs'];P=expected_projector_square(x)
    settings=copy.deepcopy(config['tuned_not_reported']);settings['rgd_max_iterations']=100000
    start=time.perf_counter();phi,h,stop=phase_rgd(f['phi0'],lambda v:criterion_value_gradient(x,v,P),settings)
    value,g=criterion_value_gradient(x,phi,P)
    return {'actual_termination':stop,'phase_history':h,'elapsed_seconds':time.perf_counter()-start,
            'independently_recomputed_gradient_norm':float(np.linalg.norm(g)),'recomputed_criterion':value,
            'original_gradient_threshold':1e-6,'unreported_safety_cap':100000}, {'inputs':x,'phi0':f['phi0'],'projector_square':P,
             'settings':settings,'noise':1.,'python_phase':phi,'python_gradient':g,'python_criterion':value}


if __name__=='__main__':
    base=Path(__file__).parent;config=json.loads((base/'statistical_geometry_config.json').read_text());config['reported'].update(U=6,K=10,kappa_satellite_db=0,kappa_ground_db=20)
    hashes=source_hashes(['scenario_geometry.py','statistical.py','rgd_numerical_controls.py','rgd_spectral_controls.py','termination.py','diagnose_geometry_phase_budget.py','statistical_geometry_config.json'])
    print(json.dumps({'scope':'isolated_U6beta0_original_phase_diagnostic','dimensions':{'N':16,'J':16,'U':6,'K':10,'M':25},'gradient_threshold':1e-6,'unreported_safety_cap':100000}),flush=True)
    result,fixture=diagnose(config);folder=base/'outputs';path=folder/'source-geometry-U6beta0-phase-budget-fixture.mat';savemat(path,fixture,long_field_names=True)
    result.update(scope='same_full_model_original_RGD_unreported_budget_diagnostic_NOT_figure_or_complete_chain',
                  configuration=config,executed_source_hashes=hashes,source_unchanged_during_run=unchanged(hashes),
                  fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),full_reproduction_pass=False)
    save_receipt(folder/'source-geometry-U6beta0-phase-budget-python.json',result)
    print(json.dumps({k:result[k] for k in ('actual_termination','elapsed_seconds','independently_recomputed_gradient_norm','source_unchanged_during_run')}),flush=True)
