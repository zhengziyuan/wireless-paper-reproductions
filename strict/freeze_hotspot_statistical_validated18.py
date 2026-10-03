"""Independently audit actual243 starts and replay54x1000 fixed-design MC.

No optimizer is rerun, no failed start can be discarded, no author manuscript
or private local path is published. This certifies the declared corrected
implementation only, not original historical geometry/curve agreement.
"""
import argparse
import copy
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'hotspot-satcom'
sys.path.insert(0,str(BASE))
from scenario_geometry import sample_scenario
from statistical import moments,criterion_value_gradient,rate_value_gradient,expected_projector_square

GATES=('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')
NAMES=('NoRIS','TwoStage','AO')


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def decode(x):return np.asarray(x['real'])+1j*np.asarray(x['imag'])
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def require(condition,message):
    if not condition:raise ValueError(message)
def moment_evaluation(Q,Psi,W,noise,U):
    matrices=np.concatenate((Q,Psi),axis=0)
    received=np.real(np.einsum('nj,knm,mj->kj',W.conj(),matrices,W))
    desired=np.diag(received);denominator=received.sum(axis=1)-desired+noise
    sinr=desired/denominator
    return sinr,float(np.sum(np.log2(1+sinr[:U]))),float(np.sum(abs(W)**2))
def contract(config,hashes):
    result={'configuration':config,'executed_source_hashes':hashes}
    result['sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return result


def audit(rawPath,checkpointDir,outputDir):
    begin=time.perf_counter();raw=read(rawPath);config=raw['configuration'];t=config['tuned_not_reported']
    hashes=raw['executed_source_hashes'];startHashes={name:sha(BASE/name) for name in hashes}
    require(raw['source_unchanged_during_run'] is True and startHashes==hashes,'Actual executed/current source binding fails')
    require(raw['full_reproduction_pass'] is False and raw['historical_author_coordinates_recovered'] is False,'Historical scope must remain uncertified')
    require(raw['reference_ordinates_used'] is False,'Reference values cannot enter this scientific run')
    require(all(raw['checks'].get(k) is True for k in GATES),'Original aggregate gates failed')
    require(t['monte_carlo_realizations']==1000,'All original1000 fresh draws required')
    require(t['gradient_tolerance']==1e-6 and t['relative_tolerance']==1e-4,'Source stopping thresholds changed')
    require(t['solver_primal_relative_tolerance']==1e-5 and t['qt_bound_tolerance']==1e-5,'Original precision gates changed')
    cases=raw['cases'];expected={(U,beta) for U in range(1,7) for beta in (0,10,20)}
    require(len(cases)==18 and {(x['U'],x['kappa_satellite_db']) for x in cases}==expected,'Original18 cases incomplete')
    require(len(list(checkpointDir.glob('*/*-start*.json')))==243,'Actual required243 checkpoint receipts incomplete/extra')
    small=[];allStops=[];nativeHashes=[];count=0;maximumMetricError=0.;maximumMCError=0.;maximumFinalGradient=0.
    for case in cases:
        U=int(case['U']);beta=case['kappa_satellite_db'];scene=copy.deepcopy(config)
        scene['reported'].update(U=U,K=16-U,kappa_satellite_db=beta,kappa_ground_db=20,nhu_statistical_sinr_db=-3)
        expectedContract=contract(scene,hashes);folder=checkpointDir/f'U{U}-beta{beta:g}'
        casePath=folder/'complete-case.json';actualCase=read(casePath)
        require(actualCase['contract']==expectedContract and actualCase['case']==case,'Actual source/config/case checkpoint mismatch')
        nativeHashes.append({'relative_file':f'outputs/statistical-validated18-final/{folder.name}/complete-case.json','sha256':sha(casePath)})
        require(case['declared_HU_pair_distance_contract_pass'] is True and case['all_original_source_constraints_verified'] is False,'Only specific declared distance contract is certified')
        f=sample_scenario(scene,np.random.default_rng(int(t['seed'])));x=f['mean_inputs'];noise=f['noise'];power=f['power']
        require(len(x['direct_mean'])==U and len(x['nhu_mean'])==16-U,'Full16-stream source dimensions changed')
        P=expected_projector_square(x);selected={};metrics={};target=10**(-3/10)
        for name in NAMES:
            output=case['schemes'][name];records=output['all_start_records'];ids=[r['start_id'] for r in records]
            require(ids==list(range(U+1)) and len(records)==U+1,'Missing or repeated required ensemble start')
            require(output['ensemble']['all_required_starts_executed'] is True and output['ensemble']['all_required_starts_pass'] is True,'Failed/capped ensemble cannot certify selected design')
            require(output['ensemble']['required_start_ids']==ids and output['ensemble']['executed_start_ids']==ids,'Ensemble ID contract mismatch')
            for record in records:
                count+=1;sid=record['start_id'];path=folder/f'{name}-start{sid}.json';actualStart=read(path)
                require(actualStart['contract']==expectedContract and actualStart['actual_start']==record,'Actual raw start checkpoint mismatch')
                nativeHashes.append({'relative_file':f'outputs/statistical-validated18-final/{folder.name}/{path.name}','sha256':sha(path)})
                require(record.get('executed') is True and 'exception' not in record and all(record['checks'].get(k) is True for k in GATES),'Failed start cannot be dropped')
                status=record['status'];require(status['converged'] is True and status['algorithm_success'] is True,'Original stop/solver chain failed')
                for stop in status['blocks']:
                    residual=stop['final_residual'];threshold=stop['threshold'];rule=stop['stop_rule']
                    require(stop['converged'] is True and np.isfinite(residual),'Actual stop record unavailable/nonfinite')
                    if rule=='Riemannian_gradient_norm':
                        require(threshold==1e-6 and 0<=residual<=threshold and stop['termination']=='gradient_tolerance','Actual original gradient stop not reached')
                    elif rule=='signed_relative_objective_increase':
                        require(threshold==1e-4 and residual<threshold and stop['termination']=='relative_improvement','Actual original relative stop not reached')
                    else:raise ValueError('Unknown or substituted stop rule')
                    allStops.append({'U':U,'beta_db':beta,'scheme':name,'start_id':sid,**stop})
                numerical=status['numerical']
                require(numerical['solver_primal_pass'] is True and numerical['qt_sdr_bound_pass'] is True,'Source-bound numeric gate fails')
                require(0<=numerical['maximum_primal_relative_violation']<=1e-5 and 0<=numerical['maximum_qt_sdr_bound_violation']<=1e-5,'Actual solver residual gate fails')
                state=record['final_state'];phi=decode(state['phi']);W=decode(state['W']);no_ris=state['no_ris']
                require(W.shape==(16,16) and phi.shape==(25,) and no_ris==(name=='NoRIS'),'Full state dimensions/scheme mismatch')
                require(np.max(abs(abs(phi)-1))<=1e-12,'Unit-modulus phase changed')
                Q,Psi,_,_=moments(x,phi,no_ris);sinr,rate,totalPower=moment_evaluation(Q,Psi,W,noise,U)
                e=record['evaluation'];error=max(abs(rate-e['hu_sum_rate']),float(np.max(abs(sinr-np.asarray(e['sinr'])))),abs(totalPower-e['total_power']))
                maximumMetricError=max(maximumMetricError,error);require(error<=1e-9,'Independent original physical moment metric disagrees')
                require(totalPower<=power*(1+1e-5) and np.min(sinr[U:]-target)>=-1e-5,'Actual final source power/NHUQoS infeasible')
                initial=record['initial_state'];initialQ,initialPsi,_,_=moments(x,decode(initial['phi']),no_ris)
                initialSinr,_,initialPower=moment_evaluation(initialQ,initialPsi,decode(initial['W']),noise,U)
                require(initialPower<=power*(1+1e-5) and np.min(initialSinr[U:]-target)>=-1e-5,'Declared initial ensemble point infeasible')
                if name!='NoRIS':
                    _,g=criterion_value_gradient(x,phi,P) if name=='TwoStage' else rate_value_gradient(x,phi,W,noise)
                    tangent=1j*phi*np.real(np.conj(1j*phi)*g);norm=float(np.linalg.norm(tangent))
                    maximumFinalGradient=max(maximumFinalGradient,norm);require(norm<=1e-6,'Independent final original phase gradient stop fails')
                if name=='NoRIS':history=record['history']
                elif name=='TwoStage':history=record['history']['QT']
                else:history=record['history']
                relative=(history[-1]-history[-2])/max(abs(history[-2]),1e-12)
                require(relative<1e-4 and abs(relative-status['blocks'][-1]['final_residual'])<=1e-12,'Actual outer/QT history does not reach reported original stop')
            best=max(records,key=lambda r:(r['evaluation']['hu_sum_rate'],-r['start_id']))
            require(output['ensemble']['selected_start_id']==best['start_id'] and output['evaluation']==best['evaluation'],'Declared best-complete-start rule mismatch')
            mc=output['independent_MC'];require(mc['count']==1000 and len(mc['hu_rate_samples'])==1000,'All selected fixed-design original1000 samples required')
            selected[name]=(decode(best['final_state']['phi']),decode(best['final_state']['W']),best['final_state']['no_ris'])
            metrics[name]={'U':U,'beta_db':beta,'scheme':name,'selected_start_id':best['start_id'],
                           'required_starts':U+1,'source_expected_power_approximate_rate':best['evaluation']['hu_sum_rate'],
                           'source_expected_power_SINR_all16':best['evaluation']['sinr'],'total_power':best['evaluation']['total_power'],
                           'MC_count':1000,'MC_seed_sequence':[int(t['seed']),U,271828]}
        rng=np.random.default_rng(np.random.SeedSequence([int(t['seed']),U,271828]))
        samples={name:[] for name in NAMES};receivedPowers={name:np.zeros((16,16)) for name in NAMES}
        for drawIndex in range(1000):
            draw=sample_scenario(scene,rng)
            for name,(phi,W,no_ris) in selected.items():
                hu=draw['direct'].copy()
                if not no_ris:hu+=np.einsum('m,umn->un',phi,draw['cascade'])
                received=np.vstack((hu,draw['nhu']))@W;powers=abs(received)**2;desired=np.diag(powers)
                sinr=desired/(powers.sum(axis=1)-desired+noise);rate=float(np.sum(np.log2(1+sinr[:U])))
                samples[name].append(rate);receivedPowers[name]+=powers
        for name in NAMES:
            array=np.asarray(samples[name]);actual=case['schemes'][name]['independent_MC'];stored=np.asarray(actual['hu_rate_samples'])
            require(np.all(np.isfinite(stored)) and np.min(stored)>=0,'Actual raw MC samples invalid')
            error=float(np.max(abs(array-stored)));maximumMCError=max(maximumMCError,error);require(error<=1e-8,'Independent seed/draw/fixed-design MC replay disagrees')
            mean=float(np.mean(array));standardError=float(np.std(array,ddof=1)/np.sqrt(1000))
            rp=receivedPowers[name]/1000;desired=np.diag(rp);sinr=desired/(rp.sum(axis=1)-desired+noise)
            empiricalApprox=float(np.sum(np.log2(1+sinr[:U])))
            require(abs(mean-actual['exact_ergodic_sum_rate_estimate'])<=1e-9 and abs(standardError-actual['standard_error'])<=1e-9,'All raw Elog mean/SE contract fails')
            require(abs(empiricalApprox-actual['ratio_of_empirical_expected_powers_sum_rate'])<=1e-8,'All paired empirical expected powers contract fails')
            metrics[name].update(MC_exact_Elog_mean=mean,MC_standard_error=standardError,MC_empirical_expected_power_approximate_rate=empiricalApprox,
                raw_replay_maximum_rate_error=error,expected_power_source_metric_is_not_Elog=True)
            small.append(metrics[name])
        print(json.dumps({'audited_actual_case':[U,beta],'actual_starts_checked':count,'paired_fresh_draws_replayed':1000}),flush=True)
    require(count==243 and len(small)==54,'Required all-start/selected-design counts changed')
    endHashes={name:sha(BASE/name) for name in hashes};require(endHashes==startHashes,'Actual audit source interval changed')
    receipt={'paper_id':'hotspot-satcom','scope':'independent_actual_complete_corrected_statistical18_243starts_54fixeddesigns1000pairedMC',
        'actual_implemented_numerical_scope_pass':True,'actual_complete_case_count':18,'actual_required_start_count':243,
        'all_required_starts_executed_and_all_original_stops_reached':True,'selected_fixed_statistical_design_count':54,
        'fresh_paired_channel_draws_per_case':1000,'fixed_design_MC_evaluations_total':54000,
        'no_optimized_instantaneous_MC_claim':True,'all_four_original_gates_pass':True,
        'maximum_independent_moment_metric_error':maximumMetricError,'maximum_independent_final_phase_gradient_norm':maximumFinalGradient,
        'maximum_all54000_independent_MC_rate_replay_error':maximumMCError,'all_raw_MC_means_standard_errors_and_counts_verified':True,
        'source_unchanged_during_original_run':True,'source_unchanged_during_independent_audit':True,
        'executed_source_hashes':hashes,'actual_native_full_result_sha256':sha(rawPath),
        'actual_native_checkpoint_receipts':nativeHashes,'independent_audit_source_sha256':sha(__file__),
        'actual_stop_record_count':len(allStops),'actual_stop_records':allStops,'selected_design_metrics':small,
        'original_run_elapsed_seconds':raw['elapsed_seconds'],'independent_audit_elapsed_seconds':time.perf_counter()-begin,
        'declared_HU_pair_distance_contract_pass':True,'all_original_source_constraints_verified':False,
        'historical_author_coordinates_recovered':False,'final_publisher_conformance_verified':False,
        'published_original_curve_agreement_verified':False,'original_printed_algorithm_reproduction_pass':False,
        'uses_explicit_corrected_QT_erratum':True,'full_reproduction_pass':False,'reference_ordinates_used':False,
        'unrecovered_source_scope':'Physical ESA amplitude/power convention and finite-Rician covariance reduction disclosed; historical author feed/phase/footprint means unreported; no historical full-figure agreement certificate.'}
    outputDir.mkdir(parents=True,exist_ok=True);save(outputDir/'independent-complete-scope-receipt.json',receipt)
    save(outputDir/'manifest.json',{'public_files':[{'filename':'independent-complete-scope-receipt.json','sha256':sha(outputDir/'independent-complete-scope-receipt.json')}],
        'executed_scientific_source_hashes':hashes,'actual_native_full_result_sha256':sha(rawPath),'independent_audit_sha256':sha(__file__),
        'no_private_author_manuscript_or_artwork_included':True,'full_reproduction_pass':False})
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=BASE/'outputs'/'statistical-validated18-final-python.json')
    p.add_argument('--checkpoints',type=Path,default=BASE/'outputs'/'statistical-validated18-final')
    p.add_argument('--output',type=Path,default=ROOT/'validation'/'hotspot-statistical-validated18-python-v1')
    args=p.parse_args();result=audit(args.raw,args.checkpoints,args.output)
    print(json.dumps({k:result[k] for k in ('actual_implemented_numerical_scope_pass','actual_required_start_count','fixed_design_MC_evaluations_total','maximum_independent_moment_metric_error','maximum_all54000_independent_MC_rate_replay_error','full_reproduction_pass')}),flush=True)
