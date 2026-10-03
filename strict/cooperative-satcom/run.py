"""Fail-closed full runner and explicitly labelled full-dimensional component test."""
import argparse
import json
from pathlib import Path
import numpy as np
import copy
import time
from cvxpy.error import SolverError
from core import (rician_effective_moments, statistical_mr_coefficients,
                  tts_mr_coefficients, mr_qt_update, ap_qt_update)
from models import channel_moments,mr_components,mr_phase_value_gradient,ap_phase_value_gradient,sample_effective
from scenario import make_scenario
from algorithms import run_all_schemes,mr_initial


def numerical_json(value):
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    raise TypeError(type(value).__name__)


def model_test(config):
    data,pl,il=make_scenario(config); U,M=data['r_mean'].shape
    phi=np.exp(1j*(0.2+0.01*np.arange(M)))*np.ones((U,1))
    errors=[]; exact_errors=[]
    for tts in (False,True):
        coef=mr_components(data,phi,tts); p0=mr_initial(coef,pl,il)
        value,g=mr_phase_value_gradient(data,phi,p0,1,il,tts)
        for u,m in ((0,0),(1,M//2)):
            plus,minus=phi.copy(),phi.copy(); plus[u,m]*=np.exp(1j*1e-6); minus[u,m]*=np.exp(-1j*1e-6)
            fp=mr_phase_value_gradient(data,plus,p0,1,il,tts)[0]; fm=mr_phase_value_gradient(data,minus,p0,1,il,tts)[0]
            analytic=np.real(np.conj(1j*phi[u,m])*g[u,m]); numeric=(fp-fm)/2e-6
            errors.append(abs(analytic-numeric)/max(1,abs(numeric)))
    mean,C,_,_,offset=channel_moments(data,phi); W=np.transpose(mean,(0,2,1))*0.0001
    value,g=ap_phase_value_gradient(data,phi,W)
    for u,m in ((0,0),(1,M//2)):
        plus,minus=phi.copy(),phi.copy(); plus[u,m]*=np.exp(1j*1e-6); minus[u,m]*=np.exp(-1j*1e-6)
        fp=ap_phase_value_gradient(data,plus,W)[0][u]; fm=ap_phase_value_gradient(data,minus,W)[0][u]
        numeric=(fp-fm)/2e-6; analytic=np.real(np.conj(1j*phi[u,m])*g[u,m])
        exact_errors.append(abs(analytic-numeric)/max(1,abs(numeric)))
    return {'paper_id':'cooperative-satcom','scope':'full_dimension_geometry_and_analytic_gradient_test_NOT_full_reproduction',
            'metrics':{'mr_gradient_relative_error':max(errors),'ap_gradient_relative_error':max(exact_errors)},
            'checks':{'mr_gradient_pass':bool(max(errors)<1e-6),'ap_gradient_pass':bool(max(exact_errors)<1e-6),
                      'finite_nlos_pass':bool(np.all(data['d_var']>0)&np.all(data['G_var']>0)&np.all(data['r_var']>0))},
            'full_reproduction_pass':False}


def chain_test(config):
    data,pl,il=make_scenario(config); settings=copy.deepcopy(config['tuned_not_reported'])
    # Explicit bounded integration test, not a full run/default downsize.
    settings.update(qt_max_iterations=3,ao_max_iterations=1,rmo_max_iterations=2,
                    smoothing_initial=1,smoothing_final=0.5,smoothing_progress_tolerance=1)
    schemes=run_all_schemes(data,settings,pl,il); violations=[]
    for entry in schemes.values():
        e=entry['evaluation']; violations.extend(e['satellite_power']-pl); violations.extend(e['gt_interference']-il)
    return {'paper_id':'cooperative-satcom','scope':'full_dimension_eight_scheme_bounded_integration_test_NOT_full_reproduction',
            'settings_override_for_test':{'qt_iterations':3,'ao_iterations':1,'rmo_iterations':2,'smoothing_final':0.5},
            'metrics':{name:float(np.min(entry['evaluation']['sinr'])) for name,entry in schemes.items()},
            'scheme_status':{name:entry['status'] for name,entry in schemes.items()},
            'convergence_status':'bounded_test_not_required_to_converge',
            'checks':{'physical_constraint_pass':bool(max(violations)<1e-5),'physical_constraint_violation':float(max(0,max(violations)))},
            'full_reproduction_pass':False}


def full_run(config,sweep_id=None):
    results=[]; started=time.perf_counter()
    available=copy.deepcopy(config['sweeps']); comparison=config['multi_vs_single']
    if comparison['enabled']:
        for kappa in comparison['kappa_leo_db']:
            available.append({'id':f'multi_vs_single_multi_kL{kappa}','parameter':'interference_to_noise_db',
                'values':comparison['interference_values_db'],'kappa_leo_db':kappa,'satellite_mode':'multi'})
            for offset in comparison['offsets_deg']:
                available.append({'id':f'multi_vs_single_single_{offset}_kL{kappa}','parameter':'interference_to_noise_db',
                    'values':comparison['interference_values_db'],'kappa_leo_db':kappa,'satellite_mode':'single','offset_deg':offset})
    sweeps=available if sweep_id is None else [s for s in available if s['id']==sweep_id]
    if sweep_id=='base': sweeps=[{'id':'base','parameter':'power_w','values':[config['reported']['power_w']], 'kappa_leo_db':config['reported']['kappa_leo_db']}]
    if not sweeps: raise ValueError('Unknown sweep id')
    for sweep in sweeps:
        for value in sweep['values']:
            scene=copy.deepcopy(config); scene['reported'][sweep['parameter']]=value
            scene['reported']['kappa_leo_db']=sweep['kappa_leo_db']
            if sweep.get('satellite_mode')=='single':
                scene['reported'].update(J=1,N=comparison['single_N'],power_w=comparison['single_power_w'])
                scene['tuned_not_reported']['satellite_latitudes_deg']=[sweep['offset_deg']]
                scene['tuned_not_reported']['upa_shape']=comparison['single_upa_shape']
            data,pl,il=make_scenario(scene)
            try:
                schemes=run_all_schemes(data,scene['tuned_not_reported'],pl,il)
            except (RuntimeError,ValueError,SolverError) as error:
                results.append({'sweep':sweep['id'],'parameter':sweep['parameter'],'value':value,'status':'failed','error':str(error),
                                'constraint_pass':False,'convergence_pass':False,'solver_primal_pass':False,'qt_bound_pass':False,'valid_figure_point':False})
                continue
            constraint_errors=[]
            for entry in schemes.values():
                evaluation=entry['evaluation']; constraint_errors.extend(evaluation['satellite_power']-pl); constraint_errors.extend(evaluation['gt_interference']-il)
            count=scene['tuned_not_reported']['monte_carlo_realizations']; rng=np.random.default_rng(scene['tuned_not_reported']['seed'])
            phi=np.ones(data['r_mean'].shape,complex); _,_,Q,fourth,_=channel_moments(data,phi)
            powers=[]; fourths=[]
            for _ in range(count):
                h=sample_effective(data,phi,rng); p=np.sum(abs(h)**2,axis=2); powers.append(p); fourths.append(p*p)
            empirical2=np.mean(powers,axis=0); empirical4=np.mean(fourths,axis=0); exact2=np.trace(Q,axis1=2,axis2=3).real
            mc={'count':count,'second_moment_max_relative_error':float(np.max(abs(empirical2-exact2)/exact2)),
                'fourth_moment_max_relative_error':float(np.max(abs(empirical4-fourth)/fourth)),
                'purpose':'Independent channel-moment validation, not synthetic hardcoded performance arrays'}
            result={'sweep':sweep['id'],'parameter':sweep['parameter'],'value':value,'schemes':schemes,'monte_carlo':mc,
                    'constraint_pass':bool(max(constraint_errors)<scene['tuned_not_reported']['solver_objective_tolerance']),
                    'convergence_pass':all(entry['status']['converged'] and entry['status'].get('phase_source_converged',True) for entry in schemes.values()),
                    'solver_primal_pass':all(entry['status']['numerical']['solver_primal_pass'] for entry in schemes.values()),
                    'qt_bound_pass':all(entry['status']['numerical']['qt_bound_pass'] for entry in schemes.values())}
            result['valid_figure_point']=bool(result['constraint_pass'] and result['convergence_pass'] and result['solver_primal_pass'] and result['qt_bound_pass'])
            result['status']='converged_and_validated' if result['valid_figure_point'] else 'executed_but_capped_or_numerically_unvalidated'
            results.append(result); print(json.dumps({'progress':sweep['id'],'value':value,'elapsed_seconds':time.perf_counter()-started}),flush=True)
    return {'paper_id':'cooperative-satcom','source_version':config['source_version'],'final_publisher_conformance':config['final_publisher_conformance'],
            'scope':'author_model_all_eight_algorithm_chains_full_dimensions_tuned_sweeps', 'elapsed_seconds':time.perf_counter()-started,
            'metrics':{'completed_scenario_points':len(results)},'history':{'sweep_ids':[x['sweep'] for x in results]},
            'results':results,'checks':{key:all(x[key] for x in results) for key in ('constraint_pass','convergence_pass','solver_primal_pass','qt_bound_pass')},
            'overall_implemented_scope_success':bool(results and all(x['valid_figure_point'] for x in results)),
            'all_configured_sweeps_requested':sweep_id is None,
            'figure_validation_policy':'Any failed/capped/numerically-unvalidated point invalidates the selected sweep; no point is discarded.',
            'full_reproduction_pass':False,'remaining':['Exact publisher-version conformance','Original unreported numerical values and figure grids','Agreement with published figure data']}


def component_test():
    # N/J/U/M retain the candidate publication counts. These analytic test
    # channels are synthetic component inputs, NOT a fabricated paper scenario.
    J,U,N,M,K=3,2,16,25,1
    mean=np.zeros((J,U,N),complex); covariance=np.zeros((J,U,N,N),complex)
    second=np.zeros_like(covariance); fourth=np.zeros((J,U)); gt=np.zeros((J,K,N,N),complex)
    gaussian_identity=0.0
    for j in range(J):
        a=np.exp(1j*np.pi*np.arange(N)*(0.12+0.07*j))
        gm=0.01*a
        gt[j,0]=np.outer(gm,np.conj(gm))+0.0002*np.eye(N)
        for u in range(U):
            n=np.arange(N); m=np.arange(M)
            d=0.12*np.exp(1j*np.pi*n*(0.02+0.12*u+0.04*j))
            G=0.015*np.outer(np.exp(1j*np.pi*n*(0.01+0.15*u-0.04*j)),np.exp(-1j*np.pi*m*(0.04+0.01*j)))
            r=0.2*np.exp(1j*np.pi*m*(0.08-0.07*u)); phi=np.exp(1j*(0.2+0.01*m+0.1*u))
            q=rician_effective_moments(d,0.005,G,0.0001,r,0.003,phi)
            mean[j,u]=q['mean']; covariance[j,u]=q['covariance']; second[j,u]=q['second']; fourth[j,u]=q['norm_fourth']
            g=rician_effective_moments(d,0.005,G,0.0,r,0.003,phi)
            expected=np.trace(g['second']).real**2+np.trace(g['covariance']@g['covariance']).real+2*np.vdot(g['mean'],g['covariance']@g['mean']).real
            gaussian_identity=max(gaussian_identity,abs(expected-g['norm_fourth']))
    p0=np.full((J,U),0.2); offset=np.array([1.1,1.2]); power_limit=np.full(J,50.0); interference_limit=np.array([0.4])
    s,b,p,l=statistical_mr_coefficients(mean,second,gt)
    _,stat=mr_qt_update(p0,s,b,p,l,offset,power_limit,interference_limit)
    st,bt,pt,lt=tts_mr_coefficients(second,fourth,gt)
    _,tts=mr_qt_update(p0,st,bt,pt,lt,offset,power_limit,interference_limit)
    W0=np.transpose(mean,(0,2,1))*0.2
    _,ap=ap_qt_update(W0,mean,covariance,gt,offset,power_limit,interference_limit)
    violation=0.0
    for x in (stat,tts,ap):
        violation=max(violation,float(np.max(x['after']['satellite_power']-power_limit)),float(np.max(x['after']['gt_interference']-interference_limit)))
    tight=max(x['qt_tightness_error'] for x in (stat,tts,ap))
    checks={'qt_identity_pass':bool(tight<1e-10),'qt_identity_error':float(tight),
            'physical_constraint_pass':bool(violation<1e-5),'physical_constraint_violation':float(violation),
            'gaussian_limit_identity_pass':bool(gaussian_identity<1e-10),'gaussian_limit_identity_error':float(gaussian_identity),
            'finite_cascade_fourth_jensen_pass':bool(np.all(fourth>=np.trace(second,axis1=2,axis2=3).real**2)),
            'ap_qt_lower_bound_pass':bool(ap['surrogate_minimum_sinr']<=np.min(ap['after']['sinr'])+1e-5)}
    return {'paper_id':'cooperative-satcom','scope':'synthetic_full-dimensional_component_test_NOT_paper_reproduction',
            'dimensions':{'J':J,'U':U,'N':N,'M':M,'K':K},
            'metrics':{'stat_mr_before_min':float(np.min(stat['before']['sinr'])),'stat_mr_after_min':float(np.min(stat['after']['sinr'])),
                       'tts_mr_before_min':float(np.min(tts['before']['sinr'])),'tts_mr_after_min':float(np.min(tts['after']['sinr'])),
                       'ap_before_min':float(np.min(ap['before']['sinr'])),'ap_after_min':float(np.min(ap['after']['sinr']))},
            'checks':checks,'full_reproduction_pass':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--component-test',action='store_true'); p.add_argument('--model-test',action='store_true')
    p.add_argument('--chain-test',action='store_true')
    p.add_argument('--full',action='store_true'); p.add_argument('--config',type=Path,default=Path(__file__).with_name('full_config.json'))
    p.add_argument('--sweep'); p.add_argument('--output',type=Path)
    args=p.parse_args(); contract=json.loads(Path(__file__).with_name('source_contract.json').read_text())
    config=json.loads(args.config.read_text())
    if args.component_test: result=component_test()
    elif args.model_test: result=model_test(config)
    elif args.chain_test: result=chain_test(config)
    elif args.full: result=full_run(config,args.sweep)
    else: raise SystemExit('Choose --component-test, --model-test, --chain-test, or explicitly --full. Full runs retain source dimensions and configured 1000 MC draws; there is no automatic downsize.')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,allow_nan=False,default=numerical_json)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False,default=numerical_json))
    if not all(v for k,v in result['checks'].items() if k.endswith('_pass')):
        raise SystemExit(1)
