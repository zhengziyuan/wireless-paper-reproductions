"""Declared all-scheme feasible starts; unchanged complete original QT/RGD chains.

This is a numerical initialization policy, not an alternative optimizer. Every
declared start must execute and pass its original stopping/primal/bound gates.
Selecting a good completed start never repairs a failed or capped ensemble.
"""
import time
import hashlib
import numpy as np
from core import evaluate as instantaneous_evaluate,effective_rows
from statistical import (moments,evaluate,active_qt_update,feasible_initialization,
                         qt_loop,rate_value_gradient,expected_projector_square,
                         criterion_value_gradient)
from rgd_spectral_controls import phase_rgd
from termination import scheme_status,relative_stop

NAMES=('NoRIS','TwoStage','AO')
GATES=('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')


def encode(array):
    array=np.asarray(array)
    return {'real':array.real.tolist(),'imag':array.imag.tolist()}


def decode(value):
    return np.asarray(value['real'])+1j*np.asarray(value['imag'])


def start_phases(phi0,seed,U):
    """Same declared phase schedule for TS/AO; NoRIS has no phase variable.

    start0 is the historical scenario draw. Starts1..U use an independent
    fixed-seed stream; seeds contain no observed rate or reference coordinate.
    """
    phases=[np.asarray(phi0).copy()]
    for start_id in range(1,U+1):
        # First13 hex digits are an exactly representable52-bit integer. This
        # language-independent schedule has an explicit MATLAB counterpart.
        uniform=[int(hashlib.sha256(f'{int(seed)}:3309957:{int(U)}:100000:{start_id}:{m}'.encode('ascii')).hexdigest()[:13],16)/2**52 for m in range(len(phi0))]
        phases.append(np.exp(2j*np.pi*np.asarray(uniform)))
    return phases


def feasible_start(Q,Psi,W0,noise,power,target,start_id):
    """Conservative start0 or exact same-QoS single-HU feasible start1..U.

    For fixed NHU beams, q_k/eta_k-I_k is the exact remaining interference
    allowance. Restoring power p in unit direction v adds p v^H Psi_k v.
    p=min(P-||W_NHU||_F^2, min_k allowance_k/(v^H Psi_k v)) therefore
    preserves all original constraints, with no changed QoS or evaluator.
    """
    U=len(Q);candidate=np.asarray(W0).copy();target=np.asarray(target)
    if not 0<=start_id<=U:raise ValueError('Start ID outside declared0..U ensemble')
    proof={'start_id':int(start_id),'selected_HU':None,'same_original_constraints':True}
    if start_id:
        user=start_id-1;direction=candidate[:,user];norm=np.linalg.norm(direction)
        if not norm>0:raise ValueError('Original conservative HU beam has zero direction')
        direction=direction/norm;candidate[:,:U]=0
        rp=np.real(np.einsum('nj,knm,mj->kj',np.conj(candidate),Psi,candidate))
        desired=np.diag(rp[:,U:]);den=np.sum(rp,axis=1)-desired+noise
        allowance=desired/target-den
        if np.min(allowance)<-1e-10:raise RuntimeError('Original fixed NHU beams are not feasible')
        coupling=np.real(np.einsum('n,knm,m->k',np.conj(direction),Psi,direction))
        if np.min(coupling)<-1e-10:raise RuntimeError('Original NHU moment is not PSD')
        available=max(0.,power-float(np.sum(abs(candidate)**2)))
        limits=np.divide(np.maximum(allowance,0),coupling,out=np.full_like(coupling,np.inf),where=coupling>0)
        allocated=min(available,float(np.min(limits)))
        candidate[:,user]=np.sqrt(allocated)*direction
        proof.update(selected_HU=int(user),HU_power=float(allocated),
                     NHU_slack_before_restoring_HU=allowance.tolist(),coupling=coupling.tolist())
    e=evaluate(Q,Psi,candidate,noise);proof['evaluation']=e
    proof['physical_feasibility_pass']=physical(e,U,power,target)
    if not proof['physical_feasibility_pass']:raise RuntimeError('Declared initialization violates original physical constraints')
    return candidate,proof


def physical(e,U,power,target):
    return bool(e['total_power']<=power*(1+1e-5) and np.min(np.asarray(e['sinr'])[U:]-target)>=-1e-5)


def execute_start(name,config,f,phi,start_id,P):
    """Each scheme runs its entire source algorithm, including all inner stops."""
    start=time.perf_counter();t=config['tuned_not_reported'];x=f['mean_inputs'];noise,power=f['noise'],f['power'];U=len(x['direct_mean'])
    target=np.full(len(x['nhu_mean']),10**(config['reported'].get('nhu_statistical_sinr_db',-3)/10))
    no_ris=name=='NoRIS';Q,Psi,mu,_=moments(x,phi,no_ris)
    W0=feasible_initialization(Q,Psi,mu,x['nhu_mean'],noise,power,target,t['initialization_solver'],t['solver_options'])
    W0,proof=feasible_start(Q,Psi,W0,noise,power,target,start_id)
    if name=='NoRIS':
        W,h,stop,records=qt_loop(Q,Psi,W0,noise,power,target,t)
        status=scheme_status([stop],records,t);finalphi=phi
    elif name=='TwoStage':
        finalphi,hp,sp=phase_rgd(phi,lambda v:criterion_value_gradient(x,v,P),t)
        Q,_,_,_=moments(x,finalphi)
        W,hr,sr,records=qt_loop(Q,Psi,W0,noise,power,target,t)
        h={'phase':hp,'QT':hr};status=scheme_status([sp,sr],records,t)
    elif name=='AO':
        finalphi=np.asarray(phi).copy();W=W0.copy();h=[evaluate(Q,Psi,W,noise)['hu_sum_rate']];stops=[];records=[]
        for iteration in range(t['ao_max_iterations']):
            Q,_,_,_=moments(x,finalphi)
            W,info=active_qt_update(Q,Psi,W,noise,power,target,t['solver'],t['solver_options'])
            records.append(dict(info['solver_diagnostics'],qt_bound_max_violation=info['qt_bound_max_violation']))
            finalphi,_,stop=phase_rgd(finalphi,lambda v:rate_value_gradient(x,v,W,noise),t);stops.append(stop)
            Q,_,_,_=moments(x,finalphi);value=evaluate(Q,Psi,W,noise)['hu_sum_rate']
            if value<h[-1]-1e-6:raise RuntimeError('Original exact statistical AO objective decreased')
            h.append(value)
            if (h[-1]-h[-2])/max(abs(h[-2]),1e-12)<t['relative_tolerance']:break
        stops.append(relative_stop(h,t['ao_max_iterations'],t['relative_tolerance']))
        status=scheme_status(stops,records,t)
    else:raise ValueError(name)
    e=evaluate(Q,Psi,W,noise)
    checks={'physical_constraint_pass':physical(e,U,power,target),
            'convergence_pass':bool(status['converged']),
            'solver_primal_pass':bool(status['numerical']['solver_primal_pass']),
            'qt_sdr_bound_pass':bool(status['numerical']['qt_sdr_bound_pass'])}
    return {'start_id':int(start_id),'scheme':name,'executed':True,'status':status,
            'checks':checks,'evaluation':e,'history':h,'initial_feasibility_proof':proof,
            'initial_state':{'phi':encode(phi),'W':encode(W0)},
            'final_state':{'phi':encode(finalphi),'W':encode(W),'no_ris':no_ris},
            'elapsed_seconds':time.perf_counter()-start}


def summarize_starts(records,required_ids):
    """All starts gate certification; best completed trajectory chooses design."""
    required_ids=list(required_ids);actual=[r['start_id'] for r in records]
    all_executed=len(actual)==len(required_ids) and sorted(actual)==sorted(required_ids) and all(r.get('executed') is True for r in records)
    checks={k:bool(all_executed and all(r.get('checks',{}).get(k) is True for r in records)) for k in GATES}
    accepted=[r for r in records if r.get('executed') is True and all(r.get('checks',{}).get(k) is True for k in GATES)]
    selected=None if not accepted else max(accepted,key=lambda r:(r['evaluation']['hu_sum_rate'],-r['start_id']))
    return {'required_start_ids':required_ids,'executed_start_ids':actual,'all_required_starts_executed':all_executed,
            'all_required_starts_pass':all(checks.values()),'checks':checks,
            'selected_start_id':None if selected is None else selected['start_id'],
            'selection_rule':'maximum original source approximate sum-rate among completed physically feasible trajectories; lowest start ID breaks exact ties',
            'selection_does_not_certify_failed_or_capped_ensemble':True},selected


def designs(config,f,load_start=None,save_start=None,emit=None):
    x=f['mean_inputs'];U=len(x['direct_mean']);t=config['tuned_not_reported'];begin=time.perf_counter()
    phases=start_phases(f['phi0'],t['seed'],U);P=expected_projector_square(x);outputs={};states={}
    for name in NAMES:
        records=[]
        for start_id,phi in enumerate(phases):
            record=None if load_start is None else load_start(name,start_id)
            if record is None:
                try:record=execute_start(name,config,f,phi,start_id,P)
                except Exception as error:
                    record={'start_id':start_id,'scheme':name,'executed':True,'exception':str(error),
                            'exception_type':type(error).__name__,'failure_receipt':getattr(error,'receipt',None),
                            'checks':{k:False for k in GATES}}
                if save_start is not None:save_start(name,start_id,record)
            records.append(record)
            if emit is not None:emit({'scheme':name,'start_id':start_id,'checks':record['checks'],
                                     'elapsed_seconds':time.perf_counter()-begin})
        ensemble,selected=summarize_starts(records,range(U+1))
        if selected is None:
            outputs[name]={'ensemble':ensemble,'all_start_records':records,'status':{'converged':False,'algorithm_success':False,
                'numerical':{'solver_primal_pass':ensemble['checks']['solver_primal_pass'],'qt_sdr_bound_pass':ensemble['checks']['qt_sdr_bound_pass']}}}
            continue
        selected_status=selected['status'];maximum_primal=max(r.get('status',{}).get('numerical',{}).get('maximum_primal_relative_violation',0) or 0 for r in records)
        maximum_bound=max(r.get('status',{}).get('numerical',{}).get('maximum_qt_sdr_bound_violation',0) or 0 for r in records)
        outputs[name]={'evaluation':selected['evaluation'],'history':selected['history'],
            'selected_actual_status':selected_status,'ensemble':ensemble,'all_start_records':records,
            'status':{'converged':ensemble['checks']['convergence_pass'],'algorithm_success':ensemble['all_required_starts_pass'],
                'termination':'all_declared_starts_reached_all_original_stop_rules' if ensemble['checks']['convergence_pass'] else 'one_or_more_declared_starts_failed_or_capped',
                'blocks_by_start':[{ 'start_id':r['start_id'],'actual_blocks':r.get('status',{}).get('blocks',[])} for r in records],
                'numerical':{'solver_primal_pass':ensemble['checks']['solver_primal_pass'],
                    'qt_sdr_bound_pass':ensemble['checks']['qt_sdr_bound_pass'],
                    'maximum_primal_relative_violation':maximum_primal,'maximum_qt_sdr_bound_violation':maximum_bound,
                    'solver_primal_relative_tolerance':t.get('solver_primal_relative_tolerance',1e-5),'qt_bound_tolerance':t.get('qt_bound_tolerance',1e-5)}}}
        state=selected['final_state'];states[name]=(decode(state['phi']),decode(state['W']),state['no_ris'])
    # Same fresh channel draws across all selected fixed statistical designs.
    rng=np.random.default_rng(np.random.SeedSequence([int(t['seed']),int(U),271828]))
    samples={name:[] for name in states};rp={name:np.zeros((16,16)) for name in states}
    from scenario_geometry import sample_scenario
    for _ in range(t['monte_carlo_realizations']):
        draw=sample_scenario(config,rng)
        for name,(phi,W,no_ris) in states.items():
            hu=draw['direct'] if no_ris else effective_rows(draw['direct'],draw['cascade'],phi)
            samples[name].append(instantaneous_evaluate(hu,draw['nhu'],W,f['noise'])['hu_sum_rate'])
            rp[name]+=abs(np.vstack((hu,draw['nhu']))@W)**2
    for name in states:
        array=np.asarray(samples[name]);received=rp[name]/len(array);desired=np.diag(received)
        sinr=desired/(np.sum(received,axis=1)-desired+f['noise'])
        outputs[name]['independent_MC']={'count':len(array),'exact_ergodic_sum_rate_estimate':float(np.mean(array)),
            'standard_error':float(np.std(array,ddof=1)/np.sqrt(len(array))),
            'ratio_of_empirical_expected_powers_sum_rate':float(np.sum(np.log2(1+sinr[:U]))),
            'ratio_of_expected_powers_source_approximation_is_not_exact_E_log':True,'hu_rate_samples':array.tolist()}
    return {'schemes':outputs,'checks':{k:all(v['ensemble']['checks'][k] for v in outputs.values()) for k in GATES},
            'model':'full_finite_Rician_original_ratio_of_expected_powers','algorithm':'corrected_QT_erratum',
            'phase_method':'original_RGD_direction_retraction_Armijo_and_threshold_with_declared_unreported_positive_step_controls',
            'initialization_policy':config['initialization_ensemble'],'elapsed_seconds':time.perf_counter()-begin,
            'declared_HU_pair_distance_contract_pass':True,'all_original_source_constraints_verified':False,
            'historical_author_coordinates_recovered':False,'reference_ordinates_used':False}
