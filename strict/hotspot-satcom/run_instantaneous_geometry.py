"""Original full instantaneous QT/SDP/1000-draw chains, compliant HU geometry."""
import argparse
import json
from pathlib import Path
import run as original
from scenario_geometry import sample_scenario
from run_support import source_hashes,unchanged,save_receipt

PATHS=['core.py','scenario_geometry.py','termination.py','run.py','run_support.py',
       'instantaneous_sdr_guard.py','run_instantaneous_geometry.py','instantaneous_geometry_config.json']

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--full-case',action='store_true')
    parser.add_argument('--sweep');parser.add_argument('--checkpoint-dir',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.full==args.full_case:raise SystemExit('Select exactly --full or --full-case; no scenario reduction')
    if args.full_case and args.sweep:raise SystemExit('A full-case is not a figure sweep')
    config=json.loads(Path(__file__).with_name('instantaneous_geometry_config.json').read_text());hashes=source_hashes(PATHS)
    original.sample_scenario=sample_scenario;original.source_hashes=lambda paths:source_hashes(PATHS)
    result=original.full_run(config,args.sweep,'instantaneous',args.checkpoint_dir) if args.full else original.full_case(config)
    result.update(executed_source_hashes=hashes,source_unchanged_during_run=unchanged(hashes),configuration=config,
                  geometry_contract=config['geometry_contract'],historical_author_coordinates_recovered=False)
    save_receipt(args.output,result)
    print(json.dumps({'output':str(args.output),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()) or not result['source_unchanged_during_run']:raise SystemExit(1)
