"""Full-dimension same-model feasible-start and language-independent schedule fixture."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import savemat
from scenario_geometry import sample_scenario
from statistical import moments,feasible_initialization
from statistical_ensemble import feasible_start,start_phases
from run_support import source_hashes,unchanged,save_receipt


if __name__=='__main__':
    base=Path(__file__).parent;config=json.loads((base/'statistical_validated_config.json').read_text());t=config['tuned_not_reported']
    hashes=source_hashes(['scenario_geometry.py','statistical.py','core.py','statistical_ensemble.py','verify_ensemble.py','statistical_validated_config.json'])
    fixture={};results=[]
    for U in range(1,7):
        scene=copy.deepcopy(config);scene['reported'].update(U=U,K=16-U,kappa_satellite_db=20,kappa_ground_db=20,nhu_statistical_sinr_db=-3)
        f=sample_scenario(scene,np.random.default_rng(t['seed']));schedule=start_phases(f['phi0'],t['seed'],U)
        for no_ris in [False,True]:
            Q,Psi,mu,_=moments(f['mean_inputs'],f['phi0'],no_ris);target=np.full(16-U,10**(-3/10))
            W0=feasible_initialization(Q,Psi,mu,f['mean_inputs']['nhu_mean'],f['noise'],f['power'],target,t['initialization_solver'],t['solver_options'])
            record={'U':U,'no_ris':no_ris,'Q':Q,'Psi':Psi,'W0':W0,'noise':float(f['noise']),'power':float(f['power']),
                    'target':target,'phi0':f['phi0'],'phase_schedule':np.vstack(schedule),'seed':float(t['seed'])}
            cases=[]
            for start_id in range(U+1):
                W,proof=feasible_start(Q,Psi,W0,f['noise'],f['power'],target,start_id)
                record[f'W_start{start_id}']=W;cases.append(proof)
            fixture[f'case_U{U}_noRIS{int(no_ris)}']=record
            results.append({'U':U,'no_ris':no_ris,'original_full_dimensions':{'N':16,'J':16,'K':16-U,'M':25},
                            'all_start_proofs':cases,'all_feasible':all(p['physical_feasibility_pass'] for p in cases)})
    path=base/'outputs'/'uniform-ensemble-fixture.mat';path.parent.mkdir(exist_ok=True);savemat(path,fixture)
    result={'scope':'full_dimension_declared_initial_ensemble_component_NOT_algorithm_stops_or_figures',
            'cases':results,'all_passed':all(r['all_feasible'] for r in results),'all_schemes_same_initialization_policy':True,
            'fixture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'executed_source_hashes':hashes,
            'source_unchanged_during_run':unchanged(hashes),'full_reproduction_pass':False,'reference_ordinates_used':False}
    save_receipt(base/'outputs'/'uniform-ensemble-component-python.json',result)
    print(json.dumps({'all_passed':result['all_passed'],'fixture_sha256':result['fixture_sha256'],'source_unchanged_during_run':result['source_unchanged_during_run']}),flush=True)
    if not result['all_passed'] or not result['source_unchanged_during_run']:raise SystemExit(1)
