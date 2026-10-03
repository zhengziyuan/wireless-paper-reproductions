"""WORK one full v3 numerical scene plus recording, not a promoted figure bank."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'wireless-paper-reproductions/strict/cooperative-satcom'
sys.path.insert(0,str(BASE))

import algorithms
import run as original
from increments_v2 import ap_increment_v2,mr_increment_v2
from qt_numerical_guard_v3 import install
from receipts import save
from spectral_rmo import rmo_ascent
from recording_v4_work import RecordingV4


def hashes(configuration):
    names=('core.py','models.py','increments.py','increments_v2.py','algorithms.py',
        'spectral_rmo.py','core_qt_factored_v3.py','qt_numerical_guard_v3.py',
        'termination.py','scenario.py','run.py','receipts.py')
    paths={n:BASE/n for n in names}
    paths.update({n:HERE/n for n in ('recording_v4_work.py','run_cooperative_v4_recording_work.py')})
    paths['actual_immutable_configuration']=configuration
    return {n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in paths.items()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--configuration',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--recording-prefix',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    assert not Path(str(args.recording_prefix)+'.json').exists()
    assert not Path(str(args.recording_prefix)+'.npz').exists()
    configuration=json.loads(args.configuration.read_text(encoding='utf-8-sig'))
    settings=configuration['tuned_not_reported']
    assert settings['monte_carlo_realizations']==1000
    assert settings['gradient_tolerance']==1e-6
    assert settings['rmo_max_iterations']==100000
    assert settings['mr_QT_representation'].startswith('sqrt(scale*v)=sqrt(scale)*sqrt(v), exact positive fixed-coordinate constant')
    algorithms.rmo_ascent=rmo_ascent
    algorithms.ap_increment=ap_increment_v2;algorithms.mr_increment=mr_increment_v2
    install()
    original.source_hashes=lambda:hashes(args.configuration)
    original.unchanged=lambda before:before==hashes(args.configuration)
    before=hashes(args.configuration)
    with RecordingV4(algorithms,original) as recorder:
        result=original.full_run(configuration,'base',None)
        recording=recorder.save(args.recording_prefix)
    after=hashes(args.configuration)
    assert before==after and result['source_unchanged_during_run']
    result['recording_only_protocol']={
        'actual_state_array_bank_sha256':recording['actual_saved_array_bank_sha256'],
        'actual_state_receipt_sha256':hashlib.sha256(Path(str(args.recording_prefix)+'.json').read_bytes()).hexdigest(),
        'adapter_and_numerical_sources_before':before,'adapter_and_numerical_sources_after':after,
        'no_additional_model_gradient_solver_or_random_draw_call':True,
        'independent_final_state_audit_pass':False,'new_formal183_bank_executed':False,
        'prior_source_bank_not_upgraded':True}
    save(args.output,result)
    print(json.dumps({'actual_original_gates':result['checks'],
        'source_interval_pass':before==after,'independent_final_state_audit_pass':False,
        'full_reproduction_pass':False}),flush=True)
    if not all(result['checks'].values()):raise SystemExit(1)


if __name__=='__main__':main()
