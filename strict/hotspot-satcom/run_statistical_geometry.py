"""Original full statistical chains with declared source-compliant HU geometry.

No reference curves enter this module. Old radius15 results are not recycled.
"""
import argparse
import json
from pathlib import Path
import run_statistical as original
from scenario_geometry import sample_scenario
from rgd_spectral_controls import phase_rgd
from run_support import source_hashes,unchanged,save_receipt

PATHS=['statistical.py','scenario_geometry.py','core.py','termination.py',
       'run_statistical.py','run_support.py','rgd_numerical_controls.py',
       'rgd_spectral_controls.py','run_statistical_geometry.py','statistical_geometry_config.json']

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--full-case',action='store_true')
    parser.add_argument('--case-u',type=int);parser.add_argument('--case-beta',type=float);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--checkpoint-dir',type=Path);args=parser.parse_args()
    if args.full==args.full_case:raise SystemExit('Select exactly --full or --full-case; no scenario reduction')
    if args.full and (args.case_u is not None or args.case_beta is not None):raise SystemExit('Case selectors require --full-case; all original18full points remain unchanged')
    config=json.loads(Path(__file__).with_name('statistical_geometry_config.json').read_text())
    if args.case_u is not None:config['reported'].update(U=args.case_u,K=16-args.case_u)
    if args.case_beta is not None:config['reported']['kappa_satellite_db']=args.case_beta
    hashes=source_hashes(PATHS)
    original.sample_scenario=sample_scenario;original.phase_rgd=phase_rgd
    original.source_hashes=lambda paths:source_hashes(PATHS)
    result=original.run(config,args.full,args.checkpoint_dir)
    result.update(executed_source_hashes=hashes,source_unchanged_during_run=unchanged(hashes),
                  geometry_contract=config['geometry_contract'],historical_author_coordinates_recovered=False)
    save_receipt(args.output,result)
    print(json.dumps({'output':str(args.output),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()) or not result['source_unchanged_during_run']:raise SystemExit(1)
