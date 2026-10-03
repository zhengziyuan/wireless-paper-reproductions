"""Versioned input boundary to the frozen v3 kernel; one full base case only.

This does not modify the original v3 entry or promote a formal183 figure bank.
Original model/gates/eight schemes and 1000 moment draws remain unchanged.
Actual runtime metadata describes this entry, never a fabricated old hash.
"""
import argparse
import hashlib
import json
from pathlib import Path

import algorithms
import run as original
from increments_v2 import ap_increment_v2,mr_increment_v2
from qt_numerical_guard_v3 import install
from receipts import save
from spectral_rmo import rmo_ascent


def actual_hashes(configuration_path):
    base=Path(__file__).resolve().parent
    names=('core.py','models.py','increments.py','increments_v2.py','algorithms.py',
        'spectral_rmo.py','core_qt_factored_v3.py','qt_numerical_guard_v3.py',
        'termination.py','scenario.py','run.py','receipts.py','run_cooperative_v3_configured.py')
    bindings={name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in names}
    bindings['actual_immutable_configuration']=hashlib.sha256(configuration_path.read_bytes()).hexdigest()
    return bindings


def _install_original_v3_controls():
    algorithms.rmo_ascent=rmo_ascent
    algorithms.ap_increment=ap_increment_v2
    algorithms.mr_increment=mr_increment_v2
    install()


def execute_configuration(configuration_path,output_path,full,sweep):
    if not full or sweep!='base':
        raise ValueError('Explicit --full --sweep base required; new full183/figure-bank promotion refused')
    configuration_path=Path(configuration_path);output_path=Path(output_path)
    if output_path.exists():raise FileExistsError('Fresh actual output required; prior results are not replaced')
    configuration=json.loads(configuration_path.read_text(encoding='utf-8-sig'))
    settings=configuration['tuned_not_reported']
    if settings['monte_carlo_realizations']!=1000 or settings['gradient_tolerance']!=1e-6:
        raise ValueError('The full original 1000 moment draws and 1e-6 phase stop are required')
    if settings['rmo_max_iterations']!=100000 or not settings['mr_QT_representation'].startswith('sqrt(scale*v)=sqrt(scale)*sqrt(v), exact positive fixed-coordinate constant'):
        raise ValueError('Use the explicitly declared frozen-v3 numerical-control configuration')
    _install_original_v3_controls()
    original.source_hashes=lambda:actual_hashes(configuration_path)
    original.unchanged=lambda before:before==actual_hashes(configuration_path)
    before=actual_hashes(configuration_path)
    result=original.full_run(configuration,'base',None)
    after=actual_hashes(configuration_path)
    if before!=after or not result['source_unchanged_during_run']:
        raise RuntimeError('Actual scientific/input/entry bytes changed; no mixed-source certificate')
    result['configured_v3_boundary']={
        'version':'new_input_only_v3_configured_boundary_NOT_rewritten_original_entry',
        'actual_entry_and_input_sources_before':before,'actual_entry_and_input_sources_after':after,
        'actual_configured_fullcase_execution_performed':True,
        'existing_original_eight_chain_numerical_call':'original.full_run(configuration,base,None)',
        'old_results_not_upgraded':True,'new_formal183_bank_executed':False,
        'independent_final_state_recording_performed_by_this_entry':False,
        'full_reproduction_pass':False}
    save(output_path,result)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--configuration',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--sweep',choices=('base',),required=True)
    args=parser.parse_args()
    result=execute_configuration(args.configuration,args.output,args.full,args.sweep)
    print(json.dumps({'actual_original_gates':result['checks'],
        'actual_source_interval_pass':result['source_unchanged_during_run'],
        'new_full183_certified':False,'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()):raise SystemExit(1)


if __name__=='__main__':main()
