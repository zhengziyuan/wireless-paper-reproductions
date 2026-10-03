"""Same-model feasible-start/local-basin diagnosis, never historical curve fitting."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import savemat
from scenario_geometry import sample_scenario
from statistical import moments,evaluate,feasible_initialization,qt_loop
from termination import scheme_status
from run_support import save_receipt,source_hashes,unchanged


def asymmetric_start(Q,Psi,W0,noise,power,target,user):
    """Exact feasible candidate, not a replacement production precoder algorithm.

    Keep current NHU beams. Remove HU streams and restore one existing HU beam
    direction with the largest power that respects every original average QoS.
    This supplies an initialization for the unmodified original QT loop.
    """
    U=len(Q);candidate=W0.copy();direction=W0[:,user];direction=direction/np.linalg.norm(direction)
    candidate[:,:U]=0
    powers=np.real(np.einsum('nj,knm,mj->kj',np.conj(candidate),Psi,candidate));desired=np.diag(powers[:,U:]);den=np.sum(powers,axis=1)-desired+noise
    coupling=np.real(np.einsum('n,knm,m->k',np.conj(direction),Psi,direction));slack=desired/target-den
    if np.min(slack)<-1e-10:raise RuntimeError('Fixed NHU beams are not originally feasible')
    available=max(0.,power-float(np.sum(abs(candidate)**2)))
    allowed=min(available,float(np.min(np.maximum(slack,0)/coupling)))
    candidate[:,user]=np.sqrt(allowed)*direction
    e=evaluate(Q,Psi,candidate,noise)
    if e['total_power']>power*(1+1e-5) or np.min(e['sinr'][U:]-target)<-1e-5:raise RuntimeError('Constructed same-model start is not feasible')
    return candidate,{'selected_HU':user,'HU_power':allowed,'NHU_slack_before_restoring_HU':slack.tolist(),
                      'evaluation':e,'physical_feasibility_pass':True}


if __name__=='__main__':
    base=Path(__file__).parent;config=json.loads((base/'statistical_geometry_config.json').read_text());config['reported'].update(U=3,K=13,kappa_satellite_db=20,kappa_ground_db=20)
    hashes=source_hashes(['scenario_geometry.py','statistical.py','termination.py','core.py','run_support.py','diagnose_no_ris_initialization.py','statistical_geometry_config.json'])
    f=sample_scenario(config,np.random.default_rng(config['tuned_not_reported']['seed']));x=f['mean_inputs'];Q,Psi,mu,_=moments(x,f['phi0'],True);noise,power=f['noise'],f['power'];target=np.full(13,10**(-3/10));t=config['tuned_not_reported']
    W0=feasible_initialization(Q,Psi,mu,x['nhu_mean'],noise,power,target,t['initialization_solver'],t['solver_options'])
    out=[];fixture={'Q':Q,'Psi':Psi,'noise':float(noise),'power':float(power),'target':target,'W0':W0}
    for user in range(3):
        initial,proof=asymmetric_start(Q,Psi,W0,noise,power,target,user);W,h,stop,records=qt_loop(Q,Psi,initial,noise,power,target,t)
        status=scheme_status([stop],records,t);e=evaluate(Q,Psi,W,noise)
        out.append({'user':user,'initial_feasibility_proof':proof,'original_QT_full_budget_history':h,'evaluation':e,'actual_status':status})
        fixture['candidate_'+str(user)]=initial
        print(json.dumps({'user':user,'candidate_initial_rate':proof['evaluation']['hu_sum_rate'],'original_QT_final_rate':e['hu_sum_rate'],'converged':status['converged']}),flush=True)
    W,h,stop,records=qt_loop(Q,Psi,W0,noise,power,target,t);status=scheme_status([stop],records,t);e=evaluate(Q,Psi,W,noise)
    output={'scope':'same_original_average_SINR_full_dimension_QT_initialization_basin_diagnosis_NOT_figures',
            'configuration':config,'source_unchanged_during_run':unchanged(hashes),'executed_source_hashes':hashes,
            'original_symmetric_initialization':{'evaluation':e,'actual_status':status,'history':h},
            'independent_feasible_asymmetric_original_QT_starts':out,'original_geometry_contract_pass':True,
            'reference_ordinates_used':False,'full_reproduction_pass':False}
    path=base/'outputs'/'no-ris-original-QT-start-fixture.mat';savemat(path,fixture)
    output['fixture_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();save_receipt(base/'outputs'/'no-ris-initialization-diagnosis-python.json',output)
    print(json.dumps({'symmetric_original_QT_rate':e['hu_sum_rate'],'best_complete_asymmetric_original_QT_rate':max(a['evaluation']['hu_sum_rate'] for a in out),'source_unchanged_during_run':output['source_unchanged_during_run']}),flush=True)
