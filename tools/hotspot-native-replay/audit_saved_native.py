"""Consume all saved native statistical starts without running an optimizer.

Physical moments and received powers are independently reconstructed below.
Final phase gradients are separately labelled cross-language checks using the
Python formula implementation. Historical inner-iterate/RNG/reference gates
are not inferred from this endpoint audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decode(value):
    return np.asarray(value['real']) + 1j*np.asarray(value['imag'])


def decode_context(value):
    array=decode(value).reshape(tuple(value['shape']),order='F')
    if value['order']!='F' or not np.all(np.isfinite(array)):
        raise ValueError('Invalid complete native context transport')
    return array


def physical_moments(x,phi,no_ris):
    """Expand the second moment of d + sum_m phi_m r_m G_m.

    Independent complex Gaussian hop fluctuations contribute their complete
    covariance, including the product of the two finite variances. No LoS
    replacement or normalized-mean projector is used.
    """
    dm,dv,G,gv,r,rv=[x[k] for k in ('direct_mean','direct_variance','matrix_mean','matrix_variance','ground_mean','ground_variance')]
    U,N=dm.shape;M=G.shape[0]
    Q=[]
    for u in range(U):
        mu=dm[u].copy();C=np.diag(dv[u]).astype(complex)
        if not no_ris:
            for m in range(M):
                mu+=phi[m]*r[u,m]*G[m]
                C+=rv[u,m]*np.outer(G[m].conj(),G[m])
                C+=np.diag((abs(r[u,m])**2+rv[u,m])*gv[m])
        Q.append(np.outer(mu.conj(),mu)+C)
    Psi=[np.outer(row.conj(),row)+np.diag(variance) for row,variance in zip(x['nhu_mean'],x['nhu_variance'])]
    return np.asarray(Q),np.asarray(Psi)


def physical_evaluation(Q,Psi,W,noise,U):
    received=[]
    for covariance in [*Q,*Psi]:
        received.append([float(np.real(np.vdot(W[:,j],covariance@W[:,j]))) for j in range(W.shape[1])])
    received=np.asarray(received)
    desired=np.diag(received);denominator=received.sum(axis=1)-desired+noise
    if not np.all(np.isfinite(received)) or np.min(denominator)<=0:
        raise ValueError('Nonfinite/invalid physical received powers')
    sinr=desired/denominator
    return sinr,float(np.log2(1+sinr[:U]).sum()),float(np.vdot(W.ravel(),W.ravel()).real)


def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,allow_nan=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


def audit(bank,contexts,output):
    if output.exists():
        raise ValueError('Use a fresh output directory; preserve previous checks')
    index=read(contexts/'index.json')
    entries=index['cases']
    if len(entries)!=18 or {(e['U'],e['beta_db']) for e in entries}!={(u,b) for u in range(1,7) for b in (0,10,20)}:
        raise ValueError('Complete original 18-case population required')
    package=Path(__file__).resolve().parents[2]/'strict'/'hotspot-satcom'
    sys.path.insert(0,str(package))
    from statistical import criterion_value_gradient,rate_value_gradient,expected_projector_square
    output.mkdir(parents=True)
    cases=[];start_count=0;stop_count=0;selected=[];began=time.perf_counter()
    gates=('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')
    gradient_sources={name:sha(package/name) for name in ('statistical.py','core.py','termination.py')}
    for entry in entries:
        U,beta=entry['U'],entry['beta_db'];context=read(contexts/entry['context_file'])
        source=bank/entry['result_filename'];raw=read(source)
        if sha(source)!=context['result_sha256'] or context['result_sha256']!=entry['result_sha256']:
            raise ValueError('Saved native result changed after context replay')
        x={k:decode_context(v) for k,v in context['mean_inputs'].items()}
        for key in ('direct_variance','matrix_variance','ground_variance','nhu_variance'):
            if np.max(abs(x[key].imag))!=0 or np.min(x[key].real)<0:
                raise ValueError('Invalid full finite-Rician variance')
            x[key]=x[key].real
        if x['direct_mean'].shape!=(U,16) or x['matrix_mean'].shape!=(25,16) or x['nhu_mean'].shape!=(16-U,16):
            raise ValueError('Original complete native dimensions changed')
        case=raw['cases'][0];records=[];errors=[];P=expected_projector_square(x)
        for scheme in ('NoRIS','TwoStage','AO'):
            result=case['schemes'][scheme];starts=result['all_start_records']
            if [r['start_id'] for r in starts]!=list(range(U+1)):
                raise ValueError('Missing/reordered original start bank')
            for start in starts:
                row={'U':U,'beta_db':beta,'scheme':scheme,'start_id':start['start_id']};issues=[]
                def require(condition,message):
                    if not bool(condition):issues.append(message)
                require(start.get('executed') is True and 'exception' not in start,'Failed original start')
                require(all(start['checks'].get(k) is True for k in gates),'Producer gate failed')
                state=start['final_state'];phi=decode(state['phi']).reshape(-1);W=decode(state['W']);no_ris=state['no_ris']
                require(W.shape==(16,16) and phi.shape==(25,) and no_ris==(scheme=='NoRIS'),'State/scheme dimensions')
                require(np.max(abs(abs(phi)-1))<=1e-12,'Phase domain')
                Q,Psi=physical_moments(x,phi,no_ris)
                sinr,rate,power=physical_evaluation(Q,Psi,W,context['noise'],U)
                saved=start['evaluation'];metric_error=max(abs(rate-saved['hu_sum_rate']),abs(power-saved['total_power']),float(np.max(abs(sinr-np.asarray(saved['sinr']).reshape(-1)))))
                require(metric_error<=1e-9,'Independent physical metric mismatch')
                target=10**(-3/10)
                margin=float(np.min(sinr[U:]-target));power_margin=context['power']-power
                require(power<=context['power']*(1+1e-5) and margin>=-1e-5,'Final original power/NHU QoS infeasible')
                initial=start['initial_state'];iq,ip=physical_moments(x,decode(initial['phi']).reshape(-1),no_ris)
                isi,_,ipo=physical_evaluation(iq,ip,decode(initial['W']),context['noise'],U)
                require(ipo<=context['power']*(1+1e-5) and np.min(isi[U:]-target)>=-1e-5,'Initial ensemble infeasible')
                gradient_norm=None
                if scheme!='NoRIS':
                    _,gradient=(criterion_value_gradient(x,phi,P) if scheme=='TwoStage' else rate_value_gradient(x,phi,W,context['noise']))
                    tangent=1j*phi*np.real(np.conj(1j*phi)*gradient);gradient_norm=float(np.linalg.norm(tangent))
                    require(gradient_norm<=1e-6,'Cross-language final phase gradient exceeds original threshold')
                status=start['status'];require(status['converged'] is True and status['algorithm_success'] is True,'Stored convergence fields')
                blocks=status['blocks'];blocks=[blocks] if isinstance(blocks,dict) else blocks
                for stop in blocks:
                    stop_count+=1;r,t=stop['final_residual'],stop['threshold']
                    require(stop['converged'] is True and np.isfinite(r),'Unconverged stored stop')
                    require(0<=stop['iterations']<=stop['iteration_cap'],'Iteration/cap record')
                    if stop['stop_rule']=='Riemannian_gradient_norm':
                        require(t==1e-6 and 0<=r<=t and stop['termination']=='gradient_tolerance','Original phase stop')
                    elif stop['stop_rule']=='signed_relative_objective_increase':
                        require(t==1e-4 and r<t and stop['termination']=='relative_improvement','Original relative stop')
                    else:issues.append('Unknown/substituted stop rule')
                history=start['history']['QT'] if scheme=='TwoStage' else start['history']
                relative=(history[-1]-history[-2])/max(abs(history[-2]),1e-12)
                require(relative<1e-4 and abs(relative-blocks[-1]['final_residual'])<=1e-12,'Stored terminal history/stop disagree')
                numeric=status['numerical']
                require(numeric['solver_primal_pass'] is True and numeric['qt_sdr_bound_pass'] is True,'Stored solver gate')
                require(0<=numeric['maximum_primal_relative_violation']<=1e-5 and 0<=numeric['maximum_qt_sdr_bound_violation']<=1e-5,'Stored solver residual')
                row.update(metric_max_absolute_error=metric_error,power_margin=power_margin,minimum_NHU_margin=margin,
                           cross_language_final_phase_gradient_norm=gradient_norm,passed=not issues,issues=issues)
                records.append(row);start_count+=1
            winner=max(starts,key=lambda r:(r['evaluation']['hu_sum_rate'],-r['start_id']))
            if result['ensemble']['selected_start_id']!=winner['start_id'] or result['evaluation']!=winner['evaluation']:
                errors.append('Selected maximum/earliest-exact-tie mismatch: '+scheme)
            selected.append({'U':U,'beta_db':beta,'scheme':scheme,'start_id':winner['start_id'],'reported_statistical_rate':winner['evaluation']['hu_sum_rate']})
        summary={'U':U,'beta_db':beta,'starts':len(records),'failed_starts':sum(not r['passed'] for r in records),
                 'case_errors':errors,'maximum_metric_error':max(r['metric_max_absolute_error'] for r in records),'records':records}
        cases.append(summary);write(output/f'U{U}-beta{beta}.json',summary)
        write(output/'progress.json',{'cases_completed':len(cases),'starts_checked':start_count,'failed_starts':sum(c['failed_starts'] for c in cases)})
        print(json.dumps({k:summary[k] for k in ('U','beta_db','starts','failed_starts','maximum_metric_error')}),flush=True)
    if start_count!=243 or len(selected)!=54:raise ValueError('Original population incomplete')
    if gradient_sources!={name:sha(package/name) for name in gradient_sources}:raise ValueError('Gradient implementation changed')
    result={'scope':'all18_native_all243_saved_initial_final_states_and_stored_stop_fields',
            'cases_checked':18,'starts_checked':243,'selected_designs':54,'stored_stop_records_checked':stop_count,
            'failed_starts':sum(c['failed_starts'] for c in cases),'case_error_count':sum(len(c['case_errors']) for c in cases),
            'maximum_independent_physical_metric_error':max(c['maximum_metric_error'] for c in cases),
            'all_endpoint_and_stored_stop_checks_passed':all(c['failed_starts']==0 and not c['case_errors'] for c in cases),
            'independent_implemented_model_moments_and_powers':True,'phase_gradient_scope':'cross-language Python formula check, not independent high-precision full-trajectory replay',
            'historical_inner_trajectories_independently_replayed':False,'all54000_MC_samples_replayed':False,
            'original_source_geometry_pattern_and_reference_certified':False,'full_reproduction_pass':False,
            'gradient_sources':gradient_sources,'selected':selected,'elapsed_seconds':time.perf_counter()-began}
    write(output/'summary.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank',type=Path,required=True);parser.add_argument('--contexts',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    result=audit(args.bank,args.contexts,args.output_dir)
    print(json.dumps({k:result[k] for k in ('starts_checked','failed_starts','maximum_independent_physical_metric_error','all_endpoint_and_stored_stop_checks_passed')}))
    raise SystemExit(0 if result['all_endpoint_and_stored_stop_checks_passed'] else 1)
