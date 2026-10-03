"""Strict source-gated entry; component tests never replace full-paper runs."""
import argparse
import json
from pathlib import Path
import numpy as np
import cvxpy as cp
import copy
import time
from scipy.io import savemat
from core import (effective_rows,evaluate,active_qt_update,phase_sdr_update,
                  criterion_gradient,phase_rgd,phase_surrogate,qt_parameters,ao,two_stage,qt_loop)
from scenario import sample_scenario
from termination import scheme_status


def numerical_json(value):
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    raise TypeError(type(value).__name__)


def scene_test(config):
    rng=np.random.default_rng(config['tuned_not_reported']['seed']); f=sample_scenario(config,rng)
    hu=effective_rows(f['direct'],f['cascade'],f['phi0']); U=hu.shape[0]
    W=feasible_initialization(np.vstack((hu,f['nhu'])),np.r_[np.full(U,config['tuned_not_reported']['initial_hu_sinr']),f['nhu_target']],f['noise'],f['power'])
    out=evaluate(hu,f['nhu'],W,f['noise']); violation=max(0,out['total_power']-f['power'],np.max(f['nhu_target']-out['sinr'][U:]))
    return {'paper_id':'hotspot-satcom','scope':'full_dimension_physical_scenario_initialization_test_NOT_full_reproduction',
            'metrics':{'initial_rate':out['hu_sum_rate'],'initial_power':out['total_power']},
            'checks':{'physical_constraint_pass':bool(violation<1e-5),'physical_constraint_violation':float(violation),
                      'finite_rician_pass':bool(np.all(f['mean_inputs']['direct_variance']>0)&np.all(f['mean_inputs']['matrix_variance']>0))},
            'full_reproduction_pass':False}


def chain_test(config):
    rng=np.random.default_rng(config['tuned_not_reported']['seed']); f=sample_scenario(config,rng); t=config['tuned_not_reported']
    direct,R,nhu,phi=(f[k] for k in ('direct','cascade','nhu','phi0')); U=direct.shape[0]
    hu=effective_rows(direct,R,phi); W0=feasible_initialization(np.vstack((hu,nhu)),np.r_[np.full(U,t['initial_hu_sinr']),f['nhu_target']],f['noise'],f['power'])
    draws=[(rng.standard_normal((phi.size+1,16))+1j*rng.standard_normal((phi.size+1,16)))/np.sqrt(2) for _ in range(2)]
    diagnostics=[]; astop={}
    ap_phi,W,h=ao(direct,R,nhu,phi,W0,f['noise'],f['power'],f['nhu_target'],draws,2,t['relative_tolerance'],t['solver'],t['solver_options'],diagnostics,astop)
    ts_phi,tsW,hts=two_stage(direct,R,nhu,phi,W0,f['noise'],f['power'],f['nhu_target'],3,t['gradient_tolerance'],3,t['relative_tolerance'],t['solver'],t['solver_options'])
    ao_eval=evaluate(effective_rows(direct,R,ap_phi),nhu,W,f['noise']); ts_eval=evaluate(effective_rows(direct,R,ts_phi),nhu,tsW,f['noise'])
    violation=max(0,ao_eval['total_power']-f['power'],ts_eval['total_power']-f['power'],
                  np.max(f['nhu_target']-ao_eval['sinr'][U:]),np.max(f['nhu_target']-ts_eval['sinr'][U:]))
    return {'paper_id':'hotspot-satcom','scope':'full_dimension_original_algorithm_bounded_chain_test_NOT_full_reproduction',
            'settings_override_for_test':{'AO':2,'RGD':3,'QT':3,'randomization':16},
            'phase_method':'author_Algorithm_3-2_RGD_minimize_negative_F',
            'metrics':{'ao_hu_rate':ao_eval['hu_sum_rate'],'two_stage_hu_rate':ts_eval['hu_sum_rate']},
            'scheme_status':{'AO':scheme_status([astop],diagnostics,t),
                             'TwoStage':scheme_status(list(hts['termination'].values()),hts['solver_diagnostics'],t)},
            'convergence_status':'bounded_test_not_required_to_converge',
            'history':{'AO':h,'TwoStage':hts},'solver_diagnostics':{'AO':diagnostics,'TwoStage':hts['solver_diagnostics']},'checks':{'physical_constraint_pass':bool(violation<1e-5),
            'physical_constraint_violation':float(violation),'ao_monotone_pass':bool(np.all(np.diff(h)>=-1e-5))},'full_reproduction_pass':False}


def full_run(config,sweep_id=None,csi='instantaneous'):
    if csi!='instantaneous':
        raise RuntimeError(config['statistical_csi_issue']+' Statistical branch is not implemented; no LoS/SCA substitute run.')
    sweeps=config['sweeps'] if sweep_id is None else [s for s in config['sweeps'] if s['id']==sweep_id]
    if sweep_id=='base': sweeps=[{'id':'base','parameter':'power_w','values':[config['reported']['power_w']]}]
    if not sweeps: raise ValueError('Unknown sweep id')
    results=[]; started=time.perf_counter()
    for sweep in sweeps:
        for value in sweep['values']:
            scene=copy.deepcopy(config); scene['reported'][sweep['parameter']]=value
            for k in ('U','kappa_satellite_db'):
                if k in sweep: scene['reported'][k]=sweep[k]
            scene['reported']['K']=scene['reported']['J']-scene['reported']['U']; t=scene['tuned_not_reported']
            rng=np.random.default_rng(t['seed']); samples=[]
            for index in range(t['monte_carlo_realizations']):
                try:
                    sample=full_sample(scene,rng); sample['index']=index
                except (RuntimeError,ValueError,cp.error.SolverError) as error:
                    sample={'index':index,'status':'failed','error':str(error),'physical_constraint_pass':False,
                            'convergence_pass':False,'solver_primal_pass':False,'qt_sdr_bound_pass':False,'valid_sample':False}
                samples.append(sample)
                print(json.dumps({'progress':sweep['id'],'value':value,'completed_mc':index+1,'required_mc':t['monte_carlo_realizations'],'elapsed_seconds':time.perf_counter()-started}),flush=True)
            raw={scheme:float(np.mean([x[scheme]['hu_sum_rate'] for x in samples])) if all(scheme in x for x in samples) else None for scheme in ('AO','TwoStage','NoRIS')}
            valid=bool(len(samples)==t['monte_carlo_realizations'] and all(x['valid_sample'] for x in samples))
            results.append({'sweep':sweep['id'],'parameter':sweep['parameter'],'value':value,'samples':samples,
                            'raw_unvalidated_means':raw,'means':raw if valid else None,'valid_figure_point':valid,
                            'failed_or_capped_samples':sum(not x['valid_sample'] for x in samples),
                            'mean_policy':'No failed/capped sample is dropped; means are valid only when every required sample passes.'})
    return {'paper_id':'hotspot-satcom','source_version':'author_thesis','final_publisher_conformance':'unverified',
            'scope':'instantaneous_author_model_original_AO_QT_SDR_and_RGD_QT_full_dimensions_full_configured_MC',
            'phase_method':'author_Algorithm_3-2_RGD_minimize_negative_F',
            'metrics':{'completed_scenario_points':len(results)},'history':{'sweep_ids':[x['sweep'] for x in results]},
            'elapsed_seconds':time.perf_counter()-started,'results':results,
            'checks':{key:all(x[key] for r in results for x in r['samples']) for key in ('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')},
            'overall_implemented_scope_success':bool(results and all(r['valid_figure_point'] for r in results)),
            'all_configured_sweeps_requested':sweep_id is None,
            'full_reproduction_pass':False,'remaining':['Statistical CSI original mathematical consistency','Final publication equivalence','Agreement with published figure data']}


def full_sample(scene,rng):
    """One intact MC sample, retaining original updates plus independent receipts."""
    t=scene['tuned_not_reported']; f=sample_scenario(scene,rng)
    direct,R,nhu,phi=(f[k] for k in ('direct','cascade','nhu','phi0')); U=direct.shape[0]
    hu=effective_rows(direct,R,phi); noise,power,target=f['noise'],f['power'],f['nhu_target']
    W0=feasible_initialization(np.vstack((hu,nhu)),np.r_[np.full(U,t['initial_hu_sinr']),target],noise,power,t['initialization_solver'])
    draws=[(rng.standard_normal((phi.size+1,t['randomization_count']))+1j*rng.standard_normal((phi.size+1,t['randomization_count'])))/np.sqrt(2) for _ in range(t['ao_max_iterations'])]
    diagnostics=[]; astop={}; bstop={}; bdiagnostics=[]
    clock=time.perf_counter(); ap_phi,W,h=ao(direct,R,nhu,phi,W0,noise,power,target,draws,t['ao_max_iterations'],t['relative_tolerance'],t['solver'],t['solver_options'],diagnostics,astop)
    ao_time=time.perf_counter()-clock; ao_eval=evaluate(effective_rows(direct,R,ap_phi),nhu,W,noise)
    clock=time.perf_counter(); ts_phi,tsW,hts=two_stage(direct,R,nhu,phi,W0,noise,power,target,t['rgd_max_iterations'],t['gradient_tolerance'],t['qt_max_iterations'],t['relative_tolerance'],t['solver'],t['solver_options'])
    ts_time=time.perf_counter()-clock; ts_eval=evaluate(effective_rows(direct,R,ts_phi),nhu,tsW,noise)
    baseline_init=feasible_initialization(np.vstack((direct,nhu)),np.r_[np.full(U,t['initial_hu_sinr']),target],noise,power,t['initialization_solver'])
    baselineW,hbase=qt_loop(direct,nhu,baseline_init,noise,power,target,t['qt_max_iterations'],t['relative_tolerance'],t['solver'],t['solver_options'],bdiagnostics,bstop)
    baseline_eval=evaluate(direct,nhu,baselineW,noise); violations=[]
    for e in (ao_eval,ts_eval,baseline_eval): violations.extend([e['total_power']-power,float(np.max(target-e['sinr'][U:]))])
    statuses={'AO':scheme_status([astop],diagnostics,t),'TwoStage':scheme_status(list(hts['termination'].values()),hts['solver_diagnostics'],t),
              'NoRIS':scheme_status([bstop],bdiagnostics,t)}
    sample={'status':'executed','AO':ao_eval,'TwoStage':ts_eval,'NoRIS':baseline_eval,'scheme_status':statuses,
            'solver_diagnostics':{'AO':diagnostics,'TwoStage':hts['solver_diagnostics'],'NoRIS':bdiagnostics},
            'history':{'AO':h,'TwoStage':hts,'NoRIS':hbase},'cpu_seconds':{'AO':ao_time,'TwoStage':ts_time},
            'physical_constraint_pass':bool(max(violations)<t['physical_constraint_tolerance']),
            'convergence_pass':all(s['converged'] for s in statuses.values()),
            'solver_primal_pass':all(s['numerical']['solver_primal_pass'] for s in statuses.values()),
            'qt_sdr_bound_pass':all(s['numerical']['qt_sdr_bound_pass'] for s in statuses.values())}
    sample['valid_sample']=all(sample[k] for k in ('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass'))
    return sample


def feasible_initialization(C,targets,noise,power,solver='CLARABEL'):
    """Tuned/not-reported minimum-power SOCP initialization, no ZF replacement."""
    J,N=C.shape; W=cp.Variable((N,J),complex=True); constraints=[]
    for u in range(J):
        interference=[i for i in range(J) if i!=u]; desired=C[u]@W[:,u]
        constraints += [cp.imag(desired)==0,
                        cp.norm(cp.hstack([C[u]@W[:,interference],np.sqrt(noise)]))<=cp.real(desired)/np.sqrt(targets[u])]
    constraints.append(cp.sum_squares(cp.abs(W))<=power)
    problem=cp.Problem(cp.Minimize(cp.sum_squares(cp.abs(W))),constraints); problem.solve(solver=solver)
    if problem.status not in ('optimal','optimal_inaccurate') or W.value is None:
        raise RuntimeError('SOCP initialization infeasible; no target reduction performed')
    return W.value


def make_component_fixture():
    # Explicitly synthetic finite-fading component inputs, full N/U/K/M counts.
    # These are NOT a satellite orbit, original sample data, or published curves.
    rng=np.random.default_rng(470271); N,U,K,M=16,6,10,25
    normal=lambda shape:(rng.standard_normal(shape)+1j*rng.standard_normal(shape))/np.sqrt(2)
    n=np.arange(N); m=np.arange(M)
    direct=np.array([0.3*np.exp(-1j*np.pi*n*(0.025+0.008*u))+0.03*normal((N,)) for u in range(U)])
    nhu=np.array([0.3*np.exp(-1j*np.pi*n*(-0.82+0.17*k))+0.03*normal((N,)) for k in range(K)])
    G=0.02*np.outer(np.exp(1j*np.pi*m*0.2),np.exp(-1j*np.pi*n*0.04))+0.004*normal((M,N))
    cascade=np.array([(0.5*np.exp(-1j*np.pi*m*(-0.3+0.1*u))+0.05*normal((M,)))[:,None]*G for u in range(U)])
    phi=np.exp(1j*(0.2+0.02*m)); noise=0.01; power=100.0; target=np.full(K,10**(3/10))
    hu=effective_rows(direct,cascade,phi)
    W0=feasible_initialization(np.vstack((hu,nhu)),np.r_[np.full(U,0.001),target],noise,power)
    draws=normal((M+1,16))  # component test only; not an original Lrand default
    return {'direct':direct,'cascade':cascade,'nhu':nhu,'phi0':phi,'W0':W0,
            'normal_draws':draws,'noise':noise,'power':power,'nhu_target':target}


def component_test(f):
    direct,cascade,nhu,phi,W0=(f[k] for k in ('direct','cascade','nhu','phi0','W0'))
    hu=effective_rows(direct,cascade,phi); noise,power,target=(f[k] for k in ('noise','power','nhu_target'))
    W,active,a=active_qt_update(hu,nhu,W0,noise,power,target)
    rounded,sdr=phase_sdr_update(direct,cascade,phi,W,a,noise,f['normal_draws'])
    after=evaluate(effective_rows(direct,cascade,rounded),nhu,W,noise)
    value,g=criterion_gradient(direct,cascade,nhu,phi); delta=1e-6; errors=[]
    x=np.r_[np.conj(phi),1]; V=np.outer(x,np.conj(x)); lifted=[]; U,M,_=cascade.shape
    for u in range(U):
        b=np.conj(a[u])*(cascade[u]@W[:,u]); L=np.zeros((M+1,M+1),complex); L[:M,M]=b/2;L[M,:M]=np.conj(b)/2
        q=2*np.real(np.conj(a[u])*(direct[u]@W[:,u]))+2*np.trace(L@V).real-abs(a[u])**2*noise
        for j in range(W.shape[1]):
            if j!=u:
                c=np.r_[cascade[u]@W[:,j],direct[u]@W[:,j]];q-=abs(a[u])**2*np.trace(np.outer(c,np.conj(c))@V).real
        lifted.append(q)
    lift_identity=abs(float(np.sum(np.log2(1+np.asarray(lifted))))-phase_surrogate(direct,cascade,phi,W,a,noise))
    for m in range(phi.size):
        plus,minus=phi.copy(),phi.copy(); plus[m]*=np.exp(1j*delta); minus[m]*=np.exp(-1j*delta)
        numeric=(criterion_gradient(direct,cascade,nhu,plus)[0]-criterion_gradient(direct,cascade,nhu,minus)[0])/(2*delta)
        analytic=np.real(np.conj(1j*phi[m])*g[m]); errors.append(abs(numeric-analytic))
    _,history=phase_rgd(direct,cascade,nhu,phi,5,1e-8)  # bounded component check, NOT full RGD cap
    violation=max(0.0,after['total_power']-power,float(np.max(target-after['sinr'][hu.shape[0]:])))
    checks={'qt_identity_pass':active['qt_tightness_error']<1e-8,'qt_identity_error':active['qt_tightness_error'],
            'physical_constraint_pass':bool(violation<1e-5),'physical_constraint_violation':violation,
            'sdr_psd_pass':bool(sdr['smallest_sdp_eigenvalue']>=-1e-5),'sdr_diagonal_pass':bool(sdr['diagonal_error']<1e-5),
            'rounding_unit_modulus_pass':sdr['unit_modulus_error']<1e-12,
            'surrogate_bound_pass':sdr['rounded_surrogate']<=sdr['sdr_upper_bound']+1e-5,
            'phase_gradient_pass':bool(max(errors)<1e-7),'phase_gradient_error':float(max(errors)),
            'phase_gradient_tangent_pass':bool(np.max(abs(np.real(np.conj(phi)*g)))<1e-10),
            'phase_lift_objective_identity_pass':bool(lift_identity<1e-10),'phase_lift_objective_identity_error':float(lift_identity),
            'phase_criterion_monotone':bool(np.all(np.diff(history)>=-1e-12))}
    return {'paper_id':'hotspot-satcom','scope':'synthetic_full-dimensional_component_test_NOT_paper_reproduction',
            'phase_method':'author_Algorithm_3-2_RGD_minimize_negative_F',
            'dimensions':{'N':16,'U':6,'K':10,'M':25},'metrics':{'initial_hu_rate':active['before']['hu_sum_rate'],
            'qt_hu_rate':active['after']['hu_sum_rate'],'sdr_rounded_hu_rate':after['hu_sum_rate'],
            'sdr_upper_bound':sdr['sdr_upper_bound'],'rounded_surrogate':sdr['rounded_surrogate']},
            'checks':checks,'full_reproduction_pass':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--component-test',action='store_true')
    parser.add_argument('--scenario-test',action='store_true'); parser.add_argument('--full',action='store_true')
    parser.add_argument('--chain-test',action='store_true')
    parser.add_argument('--config',type=Path,default=Path(__file__).with_name('full_config.json')); parser.add_argument('--sweep')
    parser.add_argument('--csi',default='instantaneous',choices=['instantaneous','statistical'])
    parser.add_argument('--output',type=Path); parser.add_argument('--fixture-output',type=Path)
    args=parser.parse_args()
    config=json.loads(args.config.read_text())
    if args.component_test:
        fixture=make_component_fixture()
        if args.fixture_output:
            args.fixture_output.parent.mkdir(parents=True,exist_ok=True); savemat(args.fixture_output,fixture)
        result=component_test(fixture)
    elif args.scenario_test: result=scene_test(config)
    elif args.chain_test: result=chain_test(config)
    elif args.full: result=full_run(config,args.sweep,args.csi)
    else: raise SystemExit('Choose explicit --component-test, --scenario-test or --full. Full configured 1000 MC realizations and 1000 SDP randomizations are never silently reduced.')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,allow_nan=False,default=numerical_json)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False,default=numerical_json))
    if not all(v for k,v in result['checks'].items() if k.endswith('_pass')):
        raise SystemExit(1)
