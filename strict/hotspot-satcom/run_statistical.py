"""Full-size statistical CSI designs: explicitly corrected original QT erratum.

Original printed SOC remains available as an error branch, never silently
replaced. Full figure3-10 uses all 18 source U/kappa points and configured MC.
"""
import argparse
import copy
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.io import savemat
from scenario import sample_scenario
from core import evaluate as instantaneous_evaluate,effective_rows
from statistical import (moments,evaluate,active_qt_update,feasible_initialization,qt_loop,
                         rate_value_gradient,expected_projector_square,criterion_value_gradient,phase_rgd,
                         printed_soc_update)
from termination import scheme_status,relative_stop
from run_support import source_hashes,unchanged,save_receipt,checkpoint_contract,load_checkpoint


def designs(config,fixture=None):
    t=config['tuned_not_reported'];rng=np.random.default_rng(t['seed']);f=sample_scenario(config,rng) if fixture is None else fixture
    x=f['mean_inputs'];phi=f['phi0'];noise,power=f['noise'],f['power'];U=len(x['direct_mean'])
    target=np.full(len(x['nhu_mean']),10**(config['reported'].get('nhu_statistical_sinr_db',-3)/10))
    Q,Psi,mu,_=moments(x,phi);Q0,_,mu0,_=moments(x,phi,True)
    W0=feasible_initialization(Q,Psi,mu,x['nhu_mean'],noise,power,target,t['initialization_solver'],t['solver_options'])
    outputs={};states={};start=time.perf_counter()
    for name,q,initial in [('NoRIS',Q0,None)]:
        init=feasible_initialization(q,Psi,mu0,x['nhu_mean'],noise,power,target,t['initialization_solver'],t['solver_options'])
        W,h,stop,records=qt_loop(q,Psi,init,noise,power,target,t)
        outputs[name]={'evaluation':evaluate(q,Psi,W,noise),'history':h,'status':scheme_status([stop],records,t)}
        states[name]=(phi,W,True)
        print(json.dumps({'statistical_scheme_completed':name,'seconds':time.perf_counter()-start}),flush=True)
    P=expected_projector_square(x);tsphi,hp,sp=phase_rgd(phi,lambda v:criterion_value_gradient(x,v,P),t)
    tsQ,_,_,_=moments(x,tsphi);tsW,hr,sr,records=qt_loop(tsQ,Psi,W0,noise,power,target,t)
    outputs['TwoStage']={'evaluation':evaluate(tsQ,Psi,tsW,noise),'history':{'phase':hp,'QT':hr},'status':scheme_status([sp,sr],records,t)}
    states['TwoStage']=(tsphi,tsW,False)
    print(json.dumps({'statistical_scheme_completed':'TwoStage','seconds':time.perf_counter()-start}),flush=True)
    aophi=phi.copy();W=W0.copy();h=[evaluate(Q,Psi,W,noise)['hu_sum_rate']];stops=[];records=[]
    for iteration in range(t['ao_max_iterations']):
        Q,_,_,_=moments(x,aophi);W,info=active_qt_update(Q,Psi,W,noise,power,target,t['solver'],t['solver_options'])
        records.append(dict(info['solver_diagnostics'],qt_bound_max_violation=info['qt_bound_max_violation']))
        aophi,_,phase_stop=phase_rgd(aophi,lambda v:rate_value_gradient(x,v,W,noise),t);stops.append(phase_stop)
        Q,_,_,_=moments(x,aophi);value=evaluate(Q,Psi,W,noise)['hu_sum_rate']
        if value<h[-1]-1e-6:raise RuntimeError('Corrected statistical AO exact objective decreased')
        h.append(value)
        print(json.dumps({'statistical_AO_iteration':iteration+1,'exact_rate':value,'phase_converged':phase_stop['converged']}),flush=True)
        if (h[-1]-h[-2])/max(abs(h[-2]),1e-12)<t['relative_tolerance']:break
    stops.append(relative_stop(h,t['ao_max_iterations'],t['relative_tolerance']))
    outputs['AO']={'evaluation':evaluate(Q,Psi,W,noise),'history':h,'status':scheme_status(stops,records,t)};states['AO']=(aophi,W,False)
    # Fixed statistical designs are evaluated on fresh independent channels.
    # The source approximate ergodic objective and actual E[log] are separate.
    samples={name:[] for name in outputs};received_powers={name:[] for name in outputs}
    for index in range(t['monte_carlo_realizations']):
        draw=sample_scenario(config,rng)
        for name,(p,w,no_ris) in states.items():
            hu=draw['direct'] if no_ris else effective_rows(draw['direct'],draw['cascade'],p)
            samples[name].append(instantaneous_evaluate(hu,draw['nhu'],w,noise)['hu_sum_rate'])
            received_powers[name].append(abs(np.vstack((hu,draw['nhu']))@w)**2)
    for name in outputs:
        array=np.asarray(samples[name]);rp=np.mean(received_powers[name],axis=0);desired=np.diag(rp);sinr=desired/(np.sum(rp,axis=1)-desired+noise)
        outputs[name]['independent_MC']={'count':len(array),'exact_ergodic_sum_rate_estimate':float(np.mean(array)),
            'standard_error':float(np.std(array,ddof=1)/np.sqrt(len(array))),
            'ratio_of_empirical_expected_powers_sum_rate':float(np.sum(np.log2(1+sinr[:U]))),
            'ratio_of_expected_powers_source_approximation_is_not_exact_E_log':True,
            'hu_rate_samples':array.tolist()}
    physical=all(e['evaluation']['total_power']<=power*(1+1e-5) and np.min(e['evaluation']['sinr'][U:]-target)>=-1e-5 for e in outputs.values())
    return {'schemes':outputs,'checks':{'physical_constraint_pass':bool(physical),
             'convergence_pass':all(e['status']['converged'] for e in outputs.values()),
             'solver_primal_pass':all(e['status']['numerical']['solver_primal_pass'] for e in outputs.values()),
             'qt_sdr_bound_pass':all(e['status']['numerical']['qt_sdr_bound_pass'] for e in outputs.values())},
             'model':'full_finite_Rician_original_ratio_of_expected_powers','algorithm':'corrected_QT_erratum',
             'phase_method':'original_RGD_with_exact_statistical_moments','elapsed_seconds':time.perf_counter()-start},f


def run(config,full=False,checkpoint_dir=None):
    cases=[];start=time.perf_counter();grid=[(u,b) for b in (0,10,20) for u in range(1,7)] if full else [(config['reported']['U'],config['reported']['kappa_satellite_db'])]
    hashes=source_hashes(['statistical.py','scenario.py','core.py','termination.py','run_statistical.py','run_support.py'])
    for u,b in grid:
        scene=copy.deepcopy(config);scene['reported'].update(U=u,K=16-u,kappa_satellite_db=b,kappa_ground_db=20,nhu_statistical_sinr_db=-3)
        contract=checkpoint_contract(scene,hashes);checkpoint=None if checkpoint_dir is None else Path(checkpoint_dir)/f'U{u}-beta{b}.json'
        cached=None if checkpoint is None else load_checkpoint(checkpoint,contract)
        if cached is not None:
            cases.append(cached['case']);print(json.dumps({'statistical_case_resumed':{'U':u,'beta_db':b},'same_source_and_configuration':True}),flush=True);continue
        try:
            value,fixture=designs(scene);value.update(U=u,kappa_satellite_db=b,status='executed')
        except Exception as error:
            value={'U':u,'kappa_satellite_db':b,'status':'failed','error':str(error),
                   'failure_receipt':getattr(error,'receipt',None),
                   'checks':{k:False for k in ('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')}}
            if hasattr(error,'fixture'):
                folder=Path(__file__).with_name('outputs');folder.mkdir(parents=True,exist_ok=True)
                savemat(folder/'statistical-failing-QT.mat',error.fixture)
        cases.append(value)
        if not unchanged(hashes):raise RuntimeError('Executed numerical sources changed; stop instead of freezing a mixed-source bank.')
        if checkpoint is not None:save_receipt(checkpoint,{'contract':contract,'case':value})
        print(json.dumps({'statistical_case_completed':{'U':u,'beta_db':b},'checks':value['checks'],'elapsed_seconds':time.perf_counter()-start}),flush=True)
    return {'paper_id':'hotspot-satcom','algorithm':'corrected_QT_erratum_NOT_original_printed_invalid_SOC',
            'scope':'full_original_figure3-10_U1to6_beta0_10_20' if full else 'single_full_dimension_complete_algorithm_budget_statistical_case_NOT_all_figures',
            'source_settings':{'ground_rician_db':20,'nhu_average_sinr_db':-3,'source':'author_table3-1_statistical_LoS-labelled_entries'},
            'configuration':config,'cases':cases,'checks':{k:all(c['checks'][k] for c in cases) for k in cases[0]['checks']},
            'elapsed_seconds':time.perf_counter()-start,'full_reproduction_pass':False,
            'original_printed_algorithm_reproduction_pass':False,'publisher_version_and_original_curve_agreement_verified':False,
            'executed_source_hashes':hashes,'source_unchanged_during_run':unchanged(hashes)}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--full-case',action='store_true')
    parser.add_argument('--printed-original',action='store_true');parser.add_argument('--config',type=Path,default=Path(__file__).with_name('full_config.json'));parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--checkpoint-dir',type=Path,help='Resume only exact source/configuration-matched full cases; failed/capped cases are retained, never dropped.')
    args=parser.parse_args()
    if args.printed_original:printed_soc_update()
    if not(args.full or args.full_case):raise SystemExit('Select explicit --full or --full-case')
    result=run(json.loads(args.config.read_text()),args.full,args.checkpoint_dir);save_receipt(args.output,result)
    print(json.dumps({'output':str(args.output),'completed_cases':len(result['cases']),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()):raise SystemExit(1)
