"""Prospective distinct v3: original full chains, exact numerical identities, original gates.

Requires independently recorded MATLAB full-M30 preflight before a formal new
all-183 figure bank; this entry does not silently certify that external check.
No old-source checkpoint is reused or upgraded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import algorithms
import run as original
from spectral_rmo import rmo_ascent
from increments_v2 import ap_increment_v2,mr_increment_v2
from qt_numerical_guard_v3 import install
from receipts import save


def actual_hashes():
    base=Path(__file__).parent
    names=('core.py','models.py','increments.py','increments_v2.py','algorithms.py',
           'spectral_rmo.py','core_qt_factored_v3.py','qt_numerical_guard_v3.py','termination.py','scenario.py',
           'run.py','receipts.py','run_cooperative_v3.py','v3_config.json')
    return {n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('--sweep')
    p.add_argument('--case-power',type=float);p.add_argument('--checkpoint-dir',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.sweep!='base':raise SystemExit('Prospective v3 preflight only: select --sweep base. Formal new183/grid runs await native full preflights and source-bound approval.')
    if not a.full:raise SystemExit('Select --full. No dimension, count, constraint or stopping reduction.')
    config=json.loads(Path(__file__).with_name('v3_config.json').read_text())
    if a.case_power is not None:
        if a.sweep!='base':raise SystemExit('--case-power requires explicit --sweep base')
        config['reported']['power_w']=a.case_power
    algorithms.rmo_ascent=rmo_ascent;algorithms.ap_increment=ap_increment_v2;algorithms.mr_increment=mr_increment_v2
    install();original.source_hashes=actual_hashes;original.unchanged=lambda h:actual_hashes()==h
    result=original.full_run(config,a.sweep,a.checkpoint_dir)
    result['numerical_controls']='prospective_v3_same_v2_circle_softmin_and_declared100000_cap_plus_exact_constant_factored_MR_QT; original_model_gradient_direction_retraction_Armijo_and_all_gates_unchanged'
    result['prior_source_bank_not_upgraded']=True
    save(a.output,result)
    print(json.dumps({'output':str(a.output),'checks':result['checks'],'source_unchanged_during_run':result['source_unchanged_during_run'],'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()) or not result['source_unchanged_during_run']:raise SystemExit(1)

