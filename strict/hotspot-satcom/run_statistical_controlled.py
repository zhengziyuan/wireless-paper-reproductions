"""Explicit full-scenario entry for original RGD numerical controls, not a model substitute."""
import argparse
import json
from pathlib import Path
import run_statistical
from rgd_numerical_controls import phase_rgd
from run_support import source_hashes,unchanged,save_receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--full-case',action='store_true')
    parser.add_argument('--case-u',type=int);parser.add_argument('--case-beta',type=float);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--checkpoint-dir',type=Path);args=parser.parse_args()
    if not(args.full or args.full_case):raise SystemExit('Select --full or --full-case; no automatic scenario reduction')
    config=json.loads(Path(__file__).with_name('full_config.json').read_text())
    if args.case_u is not None:config['reported'].update(U=args.case_u,K=16-args.case_u)
    if args.case_beta is not None:config['reported']['kappa_satellite_db']=args.case_beta
    paths=['statistical.py','scenario.py','core.py','termination.py','run_statistical.py','run_support.py','rgd_numerical_controls.py','run_statistical_controlled.py','full_config.json']
    hashes=source_hashes(paths)
    config['tuned_not_reported']['rgd_initial_step']='positive_BB_spectral_seed_in_original_RGD_direction; original_Armijo_and_gradient_threshold_unchanged'
    config['tuned_not_reported']['exact_increment_numerical_controls_source_hashes']={p:hashes[p] for p in ('rgd_numerical_controls.py','run_statistical_controlled.py')}
    run_statistical.phase_rgd=phase_rgd
    result=run_statistical.run(config,args.full,args.checkpoint_dir)
    result.update(executed_source_hashes=hashes,source_unchanged_during_run=unchanged(hashes))
    result['numerical_controls']='same_original_RGD_direction_retraction_and_Armijo_with_positive_BB_seed_and_exact_objective_increment_NOT_theoretical_erratum'
    save_receipt(args.output,result);print(json.dumps({'output':str(args.output),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()):raise SystemExit(1)
