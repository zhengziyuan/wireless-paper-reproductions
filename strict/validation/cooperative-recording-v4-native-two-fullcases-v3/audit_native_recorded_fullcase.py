"""Portable actual native-state audit adapter; no numerical body edits.

Requires h5py, the repository's existing Python reproduction dependencies, and
the complete byte-exact recorded MAT state. No MATLAB or optimizer is invoked.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]/'cooperative-satcom'
SOURCES=HERE/'executed-sources'
sys.path.insert(0,str(BASE));sys.path.insert(0,str(SOURCES))
import audit_cooperative_native_v4_actual_v3_work as native
native.HERE=SOURCES
native.BASE=BASE

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('actual_result',type=Path)
    p.add_argument('runtime_binding',type=Path);p.add_argument('configuration',type=Path)
    p.add_argument('output',type=Path);p.add_argument('--native-rng-replay',type=Path,required=True)
    args=p.parse_args();receipt=Path(str(args.output)+'.portable-binding.json')
    assert not receipt.exists() and not args.output.exists()
    bound=[Path(__file__),SOURCES/'audit_cooperative_native_v4_actual_v3_work.py',
        SOURCES/'mat73_readonly_v2_work.py',SOURCES/'audit_recording_v4_actual_work.py']
    before={p.name:sha(p) for p in bound}
    native.audit(args)
    after={p.name:sha(p) for p in bound};assert before==after
    proof={'scope':'ACTUAL_portable_readonly_native_savedstate_audit_not_reoptimization',
        'adapter_route_only':'Frozen module globals HERE/BASE resolve byte-exact copied sources and current repository science; numerical function bodies unmodified',
        'adapter_and_frozen_auditor_sources_before':before,
        'adapter_and_frozen_auditor_sources_after':after,
        'source_interval_pass':before==after,'actual_independent_audit_sha256':sha(args.output),
        'actual_saved_state_sha256':sha(Path(str(args.actual_result)+'.states.mat')),
        'full183_or_historical_reproduction_pass':False}
    receipt.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
