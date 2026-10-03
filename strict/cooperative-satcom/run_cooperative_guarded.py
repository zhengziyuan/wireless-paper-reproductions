"""Original full chains with exact-RGD spectral and same-QT numeric guards.

No model, optimizer framework, constraint, convergence threshold or original
figure grid is substituted. Failed/capped points remain explicitly invalid.
"""
import argparse
import hashlib
import json
from pathlib import Path
import algorithms
import run as original
from spectral_rmo import rmo_ascent
from qt_numerical_guard import install
from receipts import save


def actual_hashes():
    base=Path(__file__).parent;names=('core.py','models.py','increments.py','algorithms.py','spectral_rmo.py','qt_numerical_guard.py','termination.py','scenario.py','run.py','receipts.py','run_cooperative_guarded.py','spectral_config.json')
    return {n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('--sweep');p.add_argument('--case-power',type=float);p.add_argument('--checkpoint-dir',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.full:raise SystemExit('Select --full. No automatic sample, budget or dimension reduction.')
    config=json.loads(Path(__file__).with_name('spectral_config.json').read_text())
    if a.case_power is not None:
        if a.sweep!='base':raise SystemExit('--case-power requires explicit --sweep base; full original grids remain unchanged')
        config['reported']['power_w']=a.case_power
    algorithms.rmo_ascent=rmo_ascent;install();original.source_hashes=actual_hashes;original.unchanged=lambda h:actual_hashes()==h
    result=original.full_run(config,a.sweep,a.checkpoint_dir)
    result['numerical_controls']='same_original_RGD_spectral_step_seed_exact_increment_and_same_input_same_QT_conic_numerical_retry; all_original_gates_unchanged'
    save(a.output,result);print(json.dumps({'output':str(a.output),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()):raise SystemExit(1)
