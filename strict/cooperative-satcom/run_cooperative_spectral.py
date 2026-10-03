"""Complete original chains with explicit unreported spectral RGD controls.

No alternate channel, optimizer, penalty, constraint or stopping tolerance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import algorithms
import run as original
from spectral_rmo import rmo_ascent
from receipts import save


def actual_hashes():
    root=Path(__file__).parent
    names=('core.py','models.py','increments.py','algorithms.py','spectral_rmo.py','termination.py','scenario.py','run.py','receipts.py','run_cooperative_spectral.py','spectral_config.json')
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in names}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('--sweep');p.add_argument('--checkpoint-dir',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.full:raise SystemExit('Select --full. No automatic budget, sample or dimension reduction.')
    config=json.loads(Path(__file__).with_name('spectral_config.json').read_text());hashes=actual_hashes()
    algorithms.rmo_ascent=rmo_ascent;original.source_hashes=actual_hashes;original.unchanged=lambda h:actual_hashes()==h
    result=original.full_run(config,a.sweep,a.checkpoint_dir)
    result['numerical_controls']='original_RGD_direction_retraction_Armijo_threshold_with_alternating_positive_BB1_BB2_seed_and_exact_original_increment'
    save(a.output,result);print(json.dumps({'output':str(a.output),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()):raise SystemExit(1)
