"""Fresh source-geometry full bank, uniform declared initialization ensemble.

All source dimensions, constraints, stopping tolerances and algorithm directions
are retained. Old capped/single-start/incorrect-geometry checkpoints cannot enter.
"""
import argparse
import copy
import json
import time
from pathlib import Path
import numpy as np
from scenario_geometry import sample_scenario
from statistical_ensemble import designs,GATES
from run_support import source_hashes,unchanged,save_receipt,checkpoint_contract,load_checkpoint

PATHS=['statistical.py','scenario_geometry.py','core.py','termination.py','run_support.py',
       'rgd_numerical_controls.py','rgd_spectral_controls.py','statistical_ensemble.py',
       'run_statistical_validated.py','statistical_validated_config.json']


def run(config,full,checkpoint_dir=None):
    hashes=source_hashes(PATHS);cases=[];begin=time.perf_counter()
    grid=[(u,b) for b in (0,10,20) for u in range(1,7)] if full else [(config['reported']['U'],config['reported']['kappa_satellite_db'])]
    for u,b in grid:
        scene=copy.deepcopy(config);scene['reported'].update(U=u,K=16-u,kappa_satellite_db=b,kappa_ground_db=20,nhu_statistical_sinr_db=-3)
        contract=checkpoint_contract(scene,hashes)
        folder=None if checkpoint_dir is None else Path(checkpoint_dir)/f'U{u}-beta{b:g}'
        path=None if folder is None else folder/'complete-case.json'
        cached=None if path is None else load_checkpoint(path,contract)
        if cached is not None:cases.append(cached['case']);continue
        def load_start(name,start_id):
            if folder is None:return None
            receipt=load_checkpoint(folder/f'{name}-start{start_id}.json',contract)
            return None if receipt is None else receipt['actual_start']
        def save_start(name,start_id,record):
            if not unchanged(hashes):raise RuntimeError('Executed numerical sources changed during a declared start')
            if folder is not None:save_receipt(folder/f'{name}-start{start_id}.json',{'contract':contract,'actual_start':record})
        f=sample_scenario(scene,np.random.default_rng(scene['tuned_not_reported']['seed']))
        value=designs(scene,f,load_start,save_start,lambda message:print(json.dumps({'case_U':u,'beta_db':b,'actual_start_completed':message}),flush=True))
        value.update(U=u,kappa_satellite_db=b,status='executed')
        if not unchanged(hashes):raise RuntimeError('Executed numerical sources changed; refusing a mixed-source case')
        if path is not None:save_receipt(path,{'contract':contract,'case':value})
        cases.append(value);print(json.dumps({'case_completed':{'U':u,'beta_db':b},'checks':value['checks'],'elapsed_seconds':time.perf_counter()-begin}),flush=True)
    return {'paper_id':'hotspot-satcom','algorithm':'corrected_QT_erratum_NOT_original_printed_invalid_SOC',
        'scope':'full_original_figure3-10_U1to6_beta0_10_20_uniform_declared_feasible_ensemble' if full else 'single_full_dimension_complete_original_algorithm_ensemble_NOT_all_figures',
        'source_settings':{'ground_rician_db':20,'nhu_average_sinr_db':-3,'source':'author_table3-1_statistical_LoS-labelled_entries'},
        'configuration':config,'cases':cases,'checks':{k:all(c['checks'][k] for c in cases) for k in GATES},
        'elapsed_seconds':time.perf_counter()-begin,'geometry_contract':config['geometry_contract'],
        'historical_author_coordinates_recovered':False,'full_reproduction_pass':False,
        'original_printed_algorithm_reproduction_pass':False,'publisher_version_and_original_curve_agreement_verified':False,
        'executed_source_hashes':hashes,'source_unchanged_during_run':unchanged(hashes),
        'all_declared_starts_required_for_certification':True,'reference_ordinates_used':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--full-case',action='store_true')
    parser.add_argument('--case-u',type=int);parser.add_argument('--case-beta',type=float);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--checkpoint-dir',type=Path);args=parser.parse_args()
    if args.full==args.full_case:raise SystemExit('Select exactly --full or --full-case; no scenario reduction')
    if args.full and (args.case_u is not None or args.case_beta is not None):raise SystemExit('Case selectors require --full-case')
    config=json.loads(Path(__file__).with_name('statistical_validated_config.json').read_text())
    if args.case_u is not None:config['reported'].update(U=args.case_u,K=16-args.case_u)
    if args.case_beta is not None:config['reported']['kappa_satellite_db']=args.case_beta
    result=run(config,args.full,args.checkpoint_dir);save_receipt(args.output,result)
    print(json.dumps({'output':str(args.output),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()) or not result['source_unchanged_during_run']:raise SystemExit(1)
