"""Durable complete MIS-communications start banks, with unchanged solvers.

Every original-size point and both required MIS/SMS banks contain all6000
starts. Portable RNG jump-ahead is algebraically identical to serial draws.
Worker count limits CPU only. Every failed start is retained and reported.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'mis-communications'
sys.path.insert(0,str(PACKAGE))
import numpy as np
import run as comm
from engine import communication_solve,serialize

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    replace_after_transient_lock(temporary,path)

def replace_after_transient_lock(temporary,path):
    """Windows readers/OneDrive may briefly lock a receipt, not its science."""
    for attempt in range(100):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt==99:raise
            time.sleep(.05)

def validate_resume(existing,current,accepted_previous_runner=None):
    """An explicitly acknowledged runner-only I/O repair may reuse exact jobs.

    Source, settings, figure, RNG and population fields must still be identical.
    The original immutable manifest/signature is retained, never overwritten.
    """
    if existing['signature']==current['signature']:return existing
    excluded={'signature','runner_sha256'}
    old={k:v for k,v in existing.items() if k not in excluded}
    new={k:v for k,v in current.items() if k not in excluded}
    if (old!=new or not accepted_previous_runner or
            existing['runner_sha256']!=accepted_previous_runner):
        raise ValueError('Immutable bank source/configuration mismatch; preserve old results')
    return existing

def point_model(point,baseline,settings):
    config=dict(point)
    if baseline=='SMS':
        config['ms2']=[0,0]
        if 'total' in point:config['ms1']=[int(np.sqrt(point['total']))]*2
    return comm.make_model(config,settings)

def execute_start(task):
    manifest_path,index,baseline,start=task
    manifest=json.loads(Path(manifest_path).read_text())
    signature=manifest['signature']
    destination=Path(manifest_path).parent/'starts'/f'point-{index:04d}-{baseline}-{start+1:04d}.json.gz'
    if destination.exists():
        with gzip.open(destination,'rt',encoding='utf-8') as stream:saved=json.load(stream)
        if saved['bank_signature']!=signature:raise ValueError('Changed bank checkpoint rejected')
        return saved['summary']
    digest,_=comm.implementation_digest()
    if digest!=manifest['implementation_digest'] or sha(PACKAGE/'figures.json')!=manifest['figures_sha256']:
        raise ValueError('Runtime source changed; preserve this bank and use a new directory')
    settings=manifest['settings'];point=manifest['figure']['points'][index]
    model=point_model(point,baseline,settings)
    offset=index*1000 if baseline=='MIS' else 500000+index
    seed=settings['initialization']['seed']+offset
    draws=model.targets*model.U+model.M+model.N
    # Park-Miller's state after n draws is seed*a^n mod the prime modulus.
    state=(int(seed)*pow(16807,start*draws,2147483647))%2147483647
    rng=comm.PortableRandom(state);z=comm.initialize(model,settings,rng)
    options=comm.solver_options(settings)
    options['initial_mu']=settings['initial_mu_values'][start%len(settings['initial_mu_values'])]
    began=time.perf_counter();z,history,metrics=communication_solve(model,z,options)
    status=comm.solver_diagnostics(history,settings,'communications')
    domain=bool(np.max(np.abs(np.abs(z['phi'])-1))<1e-12 and
        (model.N==0 or np.max(np.abs(np.abs(z['theta'])-1))<1e-12) and
        np.max(np.abs(np.sum(z['X'],axis=1)-1))<1e-12 and np.min(z['X'])>=0)
    if comm.implementation_digest()[0]!=digest:raise ValueError('Source changed during a start; do not save a mixed-source result')
    summary={'point_index':index,'baseline':baseline,'start':start+1,
        'score':metrics['min_binary_snr'],'domain_feasible':domain,
        'solver_status':status,'elapsed_seconds':time.perf_counter()-began}
    result={'paper_id':'mis-communications','scope':'one_start_in_complete_6000_bank_not_full_figure',
        'bank_signature':signature,'summary':summary,'metrics':metrics,
        'history':history,'state':serialize(z),'source_correction_id':point.get('source_correction_id')}
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix(destination.suffix+'.tmp')
    with gzip.open(temporary,'wt',encoding='utf-8') as stream:json.dump(result,stream,allow_nan=False)
    replace_after_transient_lock(temporary,destination)
    return summary

def execute(figure_id,bank,workers,settings_path,accepted_previous_runner=None):
    settings=json.loads(settings_path.read_text());figures=json.loads((PACKAGE/'figures.json').read_text())
    figure=next(f for f in figures if f['id']==figure_id)
    if settings['kind']!='communications' or settings['number_of_starts']!=6000 or settings['rcg_max_iterations']!=4000:
        raise ValueError('Full original6000-start/4000-inner banks required')
    digest,source=comm.implementation_digest()
    manifest={'paper_id':'mis-communications','figure':figure,'settings':settings,
        'implementation_digest':digest,'source_manifest':source,'figures_sha256':sha(PACKAGE/'figures.json'),
        'runner_sha256':sha(__file__),'portable_RNG_jump':'seed*16807**(start_index*draws_per_start) mod2147483647',
        'starts_per_baseline_per_point':6000,'expected_jobs':len(figure['points'])*12000,
        'original_figure_reproduction_certified':False}
    manifest['signature']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    bank.mkdir(parents=True,exist_ok=True);manifest_path=bank/'manifest.json'
    if manifest_path.exists():
        manifest=validate_resume(json.loads(manifest_path.read_text()),manifest,accepted_previous_runner)
    else:atomic(manifest_path,manifest)
    runtime_path=bank/'execution-runtime-history.json'
    runtimes=json.loads(runtime_path.read_text()) if runtime_path.exists() else []
    runtimes.append({'runner_sha256':sha(__file__),'immutable_manifest_runner_sha256':manifest['runner_sha256'],
        'bank_signature':manifest['signature'],'accepted_previous_runner':accepted_previous_runner,
        'resume_reason':'explicit_runner_only_transient_file_lock_repair' if accepted_previous_runner else 'same_source_execution',
        'started_at_unix':time.time()})
    atomic(runtime_path,runtimes)
    tasks=((str(manifest_path.resolve()),i,b,s) for i in range(len(figure['points']))
           for s in range(6000) for b in ('MIS','SMS'))
    began=time.perf_counter();records=[]
    def receipt():
        success=sum(r['domain_feasible'] and r['solver_status']['convergence_verified'] for r in records)
        return {'paper_id':'mis-communications','figure':figure_id,'bank_signature':manifest['signature'],
            'scope':'full_original_scene_and_complete_start_bank_execution',
            'expected_jobs':manifest['expected_jobs'],'finished_jobs':len(records),
            'converged_feasible_starts':success,'failed_or_unverified_starts':len(records)-success,
            'workers':workers,'blas_threads_per_worker':1,'elapsed_seconds':time.perf_counter()-began,
            'full_bank_execution_complete':len(records)==manifest['expected_jobs'],
            'original_figure_reproduction_certified':False,'records':records}
    atomic(bank/'execution-progress.json',receipt())
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending={}
        for _ in range(workers*2):
            item=next(tasks,None)
            if item is not None:pending[pool.submit(execute_start,item)]=item
        while pending:
            completed,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in completed:
                item=pending.pop(future);records.append(future.result())
                following=next(tasks,None)
                if following is not None:pending[pool.submit(execute_start,following)]=following
            if len(records)%12<workers*2 or not pending:
                atomic(bank/'execution-progress.json',receipt())
                print(json.dumps({'finished_jobs':len(records),'expected_jobs':manifest['expected_jobs'],
                    'elapsed_seconds':time.perf_counter()-began}),flush=True)
    data={'paper_id':'mis-communications','figure':figure_id,
          'scope':'full_size_full_budget_independent_reimplementation','settings':settings,
          'bank_signature':manifest['signature'],'points':[]}
    for i,point in enumerate(figure['points']):
        entry={'configuration':point}
        for baseline in ('MIS','SMS'):
            subset=sorted((r for r in records if r['point_index']==i and r['baseline']==baseline),key=lambda r:r['start'])
            if len(subset)!=6000 or [r['start'] for r in subset]!=list(range(1,6001)):raise ValueError('Incomplete original bank')
            # Exact serial best-feasible rule and first-start tie-breaking.
            eligible=[r for r in subset if r['domain_feasible']]
            chosen=max(eligible,key=lambda r:r['score'])
            file=bank/'starts'/f'point-{i:04d}-{baseline}-{chosen["start"]:04d}.json.gz'
            with gzip.open(file,'rt',encoding='utf-8') as stream:saved=json.load(stream)
            selected=dict(score=chosen['score'],start=chosen['start'],metrics=saved['metrics'],
                history=saved['history'],state=saved['state'],solver_status=chosen['solver_status'],binary_eta_feasible=True)
            summaries=[dict(start=r['start'],feasible=r['domain_feasible'],binary_eta_feasible=True,
                score=r['score'],solver_status=r['solver_status'],min_binary_metric=r['score']) for r in subset]
            success=chosen['solver_status']['convergence_verified']
            result={'best_feasible':selected,'all_start_summaries':summaries,'number_of_starts':6000,
                'implementation_digest':digest,'source_manifest':source,
                'full_start_budget_execution_complete':True,'selected_best_convergence_verified':success,
                'overall_full_success':success,'original_figure_reproduction_certified':False}
            model=point_model(point,baseline,settings)
            if figure_id in ('fig7','fig8'):
                samples=comm.communication_beampattern_samples(model,saved['state'])
                if baseline=='MIS':entry['beampattern_samples']=samples
                else:result['beampattern_samples']=samples
            entry['result' if baseline=='MIS' else 'SMS']=result
        if 'dynamic_RIS' in figure['baselines']:entry['dynamic_RIS']={'minimum_snr':settings['reference_snr']*np.prod(point['ms1'])**2}
        data['points'].append(entry)
    data.update(comm.figure_execution_status(data['points'],len(figure['points'])))
    atomic(bank/'full-result-python.json',data);atomic(bank/'execution-summary.json',receipt())
    return receipt()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--figure',required=True);parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=1);parser.add_argument('--settings',type=Path,default=PACKAGE/'settings.json')
    parser.add_argument('--resume-runner-from',help='Explicit previous runner SHA256 after an I/O-only repair; no scientific manifest field may differ')
    args=parser.parse_args()
    if not 1<=args.workers<=3:raise ValueError('CPU worker count1 through3; bank population never changes')
    completed=execute(args.figure,args.bank,args.workers,args.settings,args.resume_runner_from)
    print(json.dumps({k:v for k,v in completed.items() if k!='records'}),flush=True)
