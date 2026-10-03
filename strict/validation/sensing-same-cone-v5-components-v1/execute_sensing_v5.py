"""Durable full6000-start sensing Fig3/4 banks; unchanged production solvers.

RNG jump-ahead equals the serial initializer exactly. Every start retains the
full30-outer/4000-inner budgets and all PSLR continuation stages when requested.
The highest feasible source-style incumbent is NOT silently replaced by a
lower verified start. Its numerical certificate and a separate verified-best
ledger are both saved. No partial/survivor bank is a completed figure.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'scientific-source-v5'
sys.path.insert(0,str(PACKAGE))
import numpy as np
import run as sensing
from engine import sensing_solve,serialize


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace(temporary,destination):
    for attempt in range(100):
        try:temporary.replace(destination);return
        except PermissionError:
            if attempt==99:raise
            time.sleep(.05)


def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,allow_nan=False)+'\n',encoding='utf-8')
    replace(temporary,path)


def compressed(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    with gzip.open(temporary,'wt',encoding='utf-8') as stream:json.dump(value,stream,allow_nan=False)
    replace(temporary,path)


def read_compressed(path):
    with gzip.open(path,'rt',encoding='utf-8') as stream:return json.load(stream)


def jumped_initial_state(model,settings,point_index,start_index):
    draws=model.targets*model.U+model.M+model.N
    seed=settings['initialization']['seed']+point_index*1000
    rng=sensing.PortableRandom(int(seed)*pow(16807,start_index*draws,2147483647)%2147483647)
    return sensing.initialize(model,settings,rng)


def validate_population(settings,figure):
    if (settings.get('kind')!='sensing' or settings.get('number_of_starts')!=6000
        or settings.get('outer_iterations')!=30 or settings.get('rcg_max_iterations')!=4000):
        raise ValueError('Original full6000 starts,30 outer,4000 inner budgets required')
    if figure['id'] not in ('fig3','fig4') or len(figure['points'])!=1:
        raise ValueError('This complete-bank adapter covers original Fig3/4 only; no partial sweep alias')
    point=figure['points'][0]
    if point['ms1']!=[20,20] or point['ms2']!=[16,16] or point['Kphi']!=3 or point['Ktheta']!=3:
        raise ValueError('Original400/256 elements and all nine targets required')
    if figure['objective']=='pslr' and settings['pslr_grid']!=[60,60]:
        raise ValueError('All3600 original dense-grid clutter directions required')


def _execute_start(task):
    manifest_path,point_index,start_index=task
    manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    bank=Path(manifest_path).parent;signature=manifest['signature']
    destination=bank/'starts'/f'point-{point_index:04d}-start-{start_index+1:04d}.json.gz'
    digest,source=sensing.implementation_digest()
    if (digest!=manifest['implementation_digest'] or sha(PACKAGE/'figures.json')!=manifest['figures_sha256']
        or sha(__file__)!=manifest['runner_sha256']):
        raise ValueError('Scientific/runtime/runner source changed; keep old bank and use a new version')
    if destination.exists():
        saved=read_compressed(destination)
        if saved['bank_signature']!=signature:raise ValueError('Mismatched immutable checkpoint')
        return saved['summary']
    settings=manifest['settings'];figure=manifest['figure'];objective=figure['objective']
    model=sensing.make_model(figure['points'][point_index],settings,pslr=objective=='pslr')
    state=jumped_initial_state(model,settings,point_index,start_index)
    options=sensing.solver_options(settings);began=time.perf_counter()
    if objective=='pslr':
        history=[];mu=settings['pslr_mu_initial']
        while mu>=settings['pslr_mu_terminal']:
            model.config['pslr_mu']=mu
            state,outer,metrics=sensing_solve(model,state,options,objective)
            history.append({'mu':mu,'outer':outer});mu*=settings['pslr_mu_factor']
    else:state,history,metrics=sensing_solve(model,state,options,objective)
    status=sensing.solver_diagnostics(history,settings,objective,model=model,state=state,metrics=metrics)
    domain=bool(np.max(abs(abs(state['phi'])-1))<1e-12 and
        np.max(abs(abs(state['theta'])-1))<1e-12 and
        np.max(abs(np.sum(state['X'],axis=1)-1))<1e-12 and np.min(state['X'])>=0)
    feasible=bool(domain and metrics['maximum_constraint']<=settings['feasibility_tolerance'])
    binary=bool(metrics['eta']-metrics['min_binary_metric']<=settings['feasibility_tolerance'])
    if sensing.implementation_digest()[0]!=digest or sha(__file__)!=manifest['runner_sha256']:
        raise ValueError('Source changed during full start; do not certify mixed-source execution')
    summary={'point_index':point_index,'start':start_index+1,'feasible':feasible,
        'domain_feasible':domain,'binary_eta_feasible':binary,'score':float(metrics['eta']),
        'min_binary_metric':float(metrics['min_binary_metric']),'solver_status':status,
        'elapsed_seconds':time.perf_counter()-began,
        'exit_status':'converged_feasible' if feasible and binary and status['convergence_verified'] else 'failed_or_unverified'}
    compressed(destination,{'paper_id':'mis-sensing','scope':'one_full_start_in_complete6000_bank_NOT_complete_figure',
        'bank_signature':signature,'source_manifest':source,'implementation_digest':digest,
        'source_unchanged_during_run':True,'summary':summary,'history':history,
        'state':serialize(state),'metrics':metrics})
    return summary


def execute_start(task):
    """Retain per-start numerical exceptions, without calling them completed solves.

    A failed solve gets a source-bound structured error receipt. It cannot
    enter an incumbent, contribute a fabricated mean, or certify convergence.
    This orchestration correction does not catch interrupts or change RCG.
    """
    try:
        return _execute_start(task)
    except Exception as error:
        manifest_path,point_index,start_index=task
        manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
        bank=Path(manifest_path).parent;digest,source=sensing.implementation_digest()
        unchanged=bool(digest==manifest['implementation_digest'] and sha(__file__)==manifest['runner_sha256'])
        initial=None;initial_sha=None;initialization_error=None
        try:
            settings=manifest['settings'];figure=manifest['figure']
            model=sensing.make_model(figure['points'][point_index],settings,pslr=figure['objective']=='pslr')
            initial=serialize(jumped_initial_state(model,settings,point_index,start_index))
            initial_sha=hashlib.sha256(json.dumps(initial,sort_keys=True,allow_nan=False).encode()).hexdigest()
        except Exception as initial_error:
            initialization_error=type(initial_error).__name__+': '+str(initial_error)
        summary={'point_index':point_index,'start':start_index+1,'feasible':False,
            'domain_feasible':False,'binary_eta_feasible':False,'score':None,'min_binary_metric':None,
            'solver_status':{'convergence_verified':False,'all_inner_tolerances_satisfied':False,
                'original_problem_kkt_verified':False,'prescribed_outer_budget_execution_complete':False,
                'execution_exception':True},'exit_status':'execution_error',
            'exception_type':type(error).__name__,'exception':str(error)}
        destination=bank/'starts'/f'point-{point_index:04d}-start-{start_index+1:04d}.json.gz'
        if destination.exists():
            raise RuntimeError('Never overwrite an existing result with an exception receipt') from error
        compressed(destination,{'paper_id':'mis-sensing','scope':'one_attempted_start_with_preserved_exception_NOT_completed_full30',
            'bank_signature':manifest['signature'],'implementation_digest':digest,'source_manifest':source,
            'source_unchanged_during_run':unchanged,'expected_implementation_digest':manifest['implementation_digest'],
            'summary':summary,'history':None,'state':None,'metrics':None,
            'initial_state':initial,'initial_state_sha256':initial_sha,'initialization_capture_error':initialization_error,
            'exception_traceback':traceback.format_exc(),
            'full_per_start_budget_execution_complete':False,'convergence_verified':False})
        return summary


def best_record(bank,records,verified=False):
    eligible=sorted((r for r in records if r['feasible'] and
        (not verified or (r['binary_eta_feasible'] and r['solver_status']['convergence_verified']))),key=lambda r:r['start'])
    if not eligible:return None
    chosen=max(eligible,key=lambda r:r['score'])
    saved=read_compressed(bank/'starts'/f'point-{chosen["point_index"]:04d}-start-{chosen["start"]:04d}.json.gz')
    return dict(score=chosen['score'],start=chosen['start'],metrics=saved['metrics'],history=saved['history'],
        state=saved['state'],solver_status=chosen['solver_status'],binary_eta_feasible=chosen['binary_eta_feasible'])


def execute(figure_id,bank,workers,settings_path):
    settings=json.loads(Path(settings_path).read_text(encoding='utf-8'))
    figure=next(f for f in json.loads((PACKAGE/'figures.json').read_text(encoding='utf-8')) if f['id']==figure_id)
    validate_population(settings,figure)
    digest,source=sensing.implementation_digest()
    manifest={'paper_id':'mis-sensing','figure':figure,'settings':settings,'implementation_digest':digest,
        'source_manifest':source,'figures_sha256':sha(PACKAGE/'figures.json'),'runner_sha256':sha(__file__),
        'portable_RNG_jump':'seed*16807**(start_index*draws_per_start) mod2147483647',
        'expected_jobs':6000,'original_figure_reproduction_certified':False}
    manifest['signature']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    bank=Path(bank);manifest_path=bank/'manifest.json'
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding='utf-8'))!=manifest:
            raise ValueError('Immutable science/runner mismatch; no source-mixed resume')
    else:atomic(manifest_path,manifest)
    records=[];began=time.perf_counter()
    def receipt():
        passed=sum(r['feasible'] and r['binary_eta_feasible'] and r['solver_status']['convergence_verified'] for r in records)
        return {'paper_id':'mis-sensing','figure':figure_id,'bank_signature':manifest['signature'],
            'expected_jobs':6000,'finished_jobs':len(records),'converged_feasible_starts':passed,
            'failed_or_unverified_starts':len(records)-passed,
            'execution_error_starts':sum(r['exit_status']=='execution_error' for r in records),
            'full_population_attempts_complete':len(records)==6000,
            'full_bank_execution_complete':len(records)==6000 and all(r['exit_status']!='execution_error' for r in records),
            'full_bank_convergence_verified':len(records)==6000 and passed==6000,
            'workers':workers,'blas_threads_per_worker':1,'elapsed_seconds':time.perf_counter()-began,
            'original_figure_reproduction_certified':False}
    tasks=iter((str(manifest_path.resolve()),0,start) for start in range(6000))
    atomic(bank/'execution-progress.json',receipt())
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending={}
        for _ in range(workers*2):
            task=next(tasks,None)
            if task is not None:pending[pool.submit(execute_start,task)]=task
        while pending:
            completed,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in completed:
                pending.pop(future);records.append(future.result())
                task=next(tasks,None)
                if task is not None:pending[pool.submit(execute_start,task)]=task
            atomic(bank/'execution-progress.json',receipt())
            print(json.dumps(receipt()),flush=True)
    records.sort(key=lambda r:r['start']);best=best_record(bank,records)
    verified_best=best_record(bank,records,True);outer=[];violations=[]
    if figure['objective']=='sinr':
        for row in records:
            if row['exit_status']=='execution_error':continue
            saved=read_compressed(bank/'starts'/f'point-0000-start-{row["start"]:04d}.json.gz');h=saved['history']
            outer.append([h[min(j,len(h)-1)]['eta'] for j in range(30)])
            violations.append([max(0,max(h[min(j,len(h)-1)]['q'])) for j in range(30)])
    selected_ok=bool(best and best['solver_status']['convergence_verified'] and best['binary_eta_feasible'])
    result={'best_feasible':best,'best_numerically_verified':verified_best,'all_start_summaries':records,
        'number_of_starts':6000,'full_population_attempts_complete':len(records)==6000,
        'full_start_budget_execution_complete':receipt()['full_bank_execution_complete'],
        'selected_best_convergence_verified':selected_ok,'overall_full_success':selected_ok,
        'full_bank_convergence_verified':receipt()['full_bank_convergence_verified'],
        'implementation_digest':digest,'source_manifest':source,'original_figure_reproduction_certified':False,
        'mean_outer_eta':np.mean(outer,axis=0).tolist() if outer else [],
        'mean_outer_violation':np.mean(violations,axis=0).tolist() if violations else [],
        'mean_outer_counts':[len(outer)]*30 if outer else [],
        'mean_contains_every_required_start':len(outer)==6000 if figure['objective']=='sinr' else False,
        'exceptions_preserved_not_survivor_replacement':True}
    model=sensing.make_model(figure['points'][0],settings,pslr=figure['objective']=='pslr')
    if figure['objective']=='pslr' and best:model.config['pslr_mu']=best['history'][-1]['mu']
    entry={'configuration':figure['points'][0],'result':result,'closed_form':sensing.evaluate_closed(sensing.make_model(figure['points'][0],settings))}
    if best:
        selected=np.argmax(np.asarray(best['metrics']['binary_schedule']),axis=1)
        entry['beampattern_samples']=sensing.beampattern_samples(model,best['state'],selected,figure['objective'])
    data={'paper_id':'mis-sensing','figure':figure_id,'scope':'full_size_full_budget_independent_reimplementation',
        'settings':settings,'points':[entry],'bank_signature':manifest['signature'],
        'full_bank_convergence_verified':receipt()['full_bank_convergence_verified']}
    data.update(sensing.figure_execution_status(data['points'],1))
    atomic(bank/'full-result-python.json',data);atomic(bank/'execution-summary.json',receipt())
    return receipt()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figure',required=True,choices=['fig3','fig4']);parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--workers',type=int,choices=[1,2,3],default=1)
    parser.add_argument('--settings',type=Path,default=PACKAGE/'settings_corrected.json')
    args=parser.parse_args();print(json.dumps(execute(args.figure,args.bank,args.workers,args.settings)),flush=True)
