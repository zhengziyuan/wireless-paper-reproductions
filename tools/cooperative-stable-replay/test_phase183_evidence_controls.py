"""Reject incomplete/substituted phase evidence and invalid unit-domain inputs.

Uses the real verified packet index for identity controls. The local-progress
substitution control reuses the already byte-verified restoration, so it neither
extracts a second full archive nor repeats any scientific calculation.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import mpmath as mp
import numpy as np

import phase183_evidence as phase
import audit_phase183_unit_domains as domain


def run(args):
    phase.require(not args.output.exists(), 'Preserve prior controls')
    manifest=phase.read(args.packet/'archive-manifest.json')
    index=phase.read(args.restored/'complete-phase-case-index.json')
    phase.require(index['original_cases']==183 and index['actual_phase_endpoints']==8362,
                  'Use the actual complete verified phase restoration')
    watched=[Path(__file__),Path(phase.__file__),Path(domain.__file__)]
    before={str(p):phase.sha(p) for p in watched}
    rows=[]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='phase183-negative-controls-',dir=args.output.parent) as temporary:
        root=Path(temporary)
        phase.require(root.resolve().is_relative_to(args.output.parent.resolve()),
                      'Temporary controls must stay inside the named output directory')

        def rejected(name,fn,errors=(ValueError,),message=None):
            try:
                fn()
            except errors as error:
                if message is not None:
                    phase.require(message in str(error),'A control failed at an unrelated guard')
                rows.append(dict(control=name,expected_rejection_observed=True,
                                 actual_exception_type=type(error).__name__,actual_reason=str(error)))
            else:
                raise AssertionError('Invalid evidence accepted: '+name)

        def packet(name,changed):
            directory=root/name;directory.mkdir()
            (directory/'archive-manifest.json').write_bytes(phase.encode(changed))
            return directory

        for name,key,value in (
            ('reduced182-original-case-population','original_cases',182),
            ('substituted-original-ordinal','exact_original_ordinals',list(range(182))+[183]),
            ('wrong-language-epoch','language','matlab'),
            ('wrong-evidence-scope','case_scope','selected-Python183-final-QT')):
            changed=deepcopy(manifest);changed[key]=value
            directory=packet(name,changed)
            rejected(name,lambda d=directory,n=name:phase.unpack(d,root/(n+'-output')),
                     message='complete selected original Python183 scope')

        directory=packet('missing-first-original-archive-part',deepcopy(manifest))
        rejected('missing-first-original-archive-part',
                 lambda:phase.unpack(directory,root/'missing-part-output'),(FileNotFoundError,))

        changed=deepcopy(manifest);first=changed['archive']['parts'][0]
        directory=packet('changed-byte-in-original-archive-part',changed)
        raw=bytearray((args.packet/first['file']).read_bytes());raw[-1]^=1
        (directory/first['file']).write_bytes(raw)
        rejected('changed-byte-in-original-archive-part',
                 lambda:phase.unpack(directory,root/'changed-byte-output'),message='Actual archive part differs')

        changed=deepcopy(manifest);changed['archive']['parts']=changed['archive']['parts'][:1]
        directory=packet('truncated-whole-original-archive',changed)
        (directory/first['file']).write_bytes((args.packet/first['file']).read_bytes())
        rejected('truncated-whole-original-archive',
                 lambda:phase.unpack(directory,root/'truncated-output'),message='Whole archive differs')

        changed=deepcopy(manifest);changed['archive']['parts'][0]['file']='../outside-original-part'
        directory=packet('archive-part-path-escape',changed)
        rejected('archive-part-path-escape',lambda:phase.unpack(directory,root/'escape-output'),
                 message='Unsafe or missing archive part')

        substituted=root/'substituted-complete-progress.json'
        substituted.write_bytes((args.restored/'actual-complete-selected183-progress.json').read_bytes()+b'\n')
        controls=SimpleNamespace(packet=args.packet,output_dir=root/'wrong-progress-output',
                                 reuse_exact_complete_local_progress=substituted)
        with patch.object(phase,'unpack',return_value=(manifest,index,args.restored)):
            rejected('different-progress-bytes-with-identical-JSON',lambda:phase.replay(controls),
                     message='exact actual complete183 progress')

        for name,values in (
            ('nonfinite-phase-NaN',np.array([complex(float('nan'),0)])),
            ('nonfinite-phase-infinity',np.array([complex(0,float('inf'))]))):
            rejected(name,lambda v=values:domain.unit_error(v,80),message='must be finite')

        for name,values in (
            ('finite-phase-below-unit-circle',np.array([.9+0j])),
            ('finite-phase-above-unit-circle',np.array([1.1+0j])),
            ('zero-phase',np.array([0j]))):
            errors={str(d):domain.unit_error(values,d) for d in (80,100)}
            phase.require(all(x>mp.mpf('1e-10') for x in errors.values()),
                          'An actual nonunit-domain input was accepted')
            rows.append(dict(control=name,expected_domain_failure_observed=True,
                             actual_errors={k:mp.nstr(v,105) for k,v in errors.items()}))

        phase.require(all(domain.unit_error(np.array([1+0j,1j,-1+0j,-1j]),d)==0 for d in (80,100)),
                      'Exact unit-circle positive control failed')

    phase.require(before=={str(p):phase.sha(p) for p in watched},'A control source changed')
    report=dict(actual_controls=len(rows),all_expected_invalid_evidence_and_domain_failures_observed=True,
        exact_unit_circle_positive_control_pass=True,
        actual_complete_original_archive_SHA256=manifest['archive']['sha256'],
        actual_original_cases=183,actual_original_phase_endpoints=8362,
        wrong_local_progress_guard_used_the_already_byte_verified_full_restoration=True,
        fresh_gradient_optimizer_or_RNG_calls=0,actual_control_source_SHA256=before,controls=rows)
    args.output.write_bytes(phase.encode(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('controls','actual_control_source_SHA256')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('packet','restored','output'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
