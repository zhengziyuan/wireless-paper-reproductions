"""Reject incomplete/substituted complete native183 evidence without gradients."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from scipy.io import loadmat

import native183_evidence as native


def run(args):
    phase=native.phase
    phase.require(not args.output.exists(),'Preserve previous native controls')
    manifest=phase.read(args.packet/'archive-manifest.json')
    index=phase.read(args.restored/'complete-native183-case-index.json')
    phase.require(index['scope']==native.SCOPE and index['actual_original_cases']==183 and
        [c['ordinal'] for c in index['cases']]==list(range(183)), 'Use the actual complete native restoration')
    watched=[Path(__file__),Path(native.__file__),Path(native.original.__file__)]
    before={str(p):phase.sha(p) for p in watched};rows=[];transports=[];prototype=None
    for case in index['cases']:
        container=args.restored/case['container'];matrix=args.restored/case['states']
        source=args.restored/case['original_configuration']
        protected={str(p):phase.sha(p) for p in (container,matrix,source)}
        actual=phase.read(container)['configuration'];expected=phase.read(source)
        receipt=native.original.configuration_transport(actual,expected)
        phase.require(receipt==case['actual_configuration_transport_receipt'],
                      'A complete original native configuration transport differs')
        data=loadmat(matrix,simplify_cells=True)['recording']['input']['configuration']
        vector=np.asarray(data['tuned_not_reported']['satellite_latitudes_deg'],dtype='<f8').reshape(-1)
        target=np.asarray(expected['tuned_not_reported']['satellite_latitudes_deg'],dtype='<f8').reshape(-1)
        phase.require(vector.size==target.size==case['dimensions']['J'] and vector.tobytes()==target.tobytes(),
                      'An actual native MAT latitude byte differs from the full original source vector')
        phase.require(protected=={p:phase.sha(Path(p)) for p in protected},'An actual public native input changed')
        if receipt:
            transports.append(dict(ordinal=case['ordinal'],actual_transport=receipt))
            if prototype is None:prototype=(actual,expected)
    phase.require(len(transports)==48 and prototype is not None,'All48 actual singleton transports are required')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='native183-evidence-controls-',dir=args.output.parent) as name:
        root=Path(name);phase.require(root.resolve().is_relative_to(args.output.parent.resolve()),
            'Temporary controls must stay inside the named output directory')
        def rejected(label,fn,errors=(ValueError,),message=None):
            try:fn()
            except errors as error:
                if message is not None:phase.require(message in str(error),'A control failed at an unrelated guard')
                rows.append(dict(control=label,expected_rejection_observed=True,
                    actual_exception_type=type(error).__name__,actual_reason=str(error)))
            else:raise AssertionError('Invalid original native evidence accepted: '+label)
        def packet(label,value):
            directory=root/label;directory.mkdir()
            (directory/'archive-manifest.json').write_bytes(phase.encode(value));return directory
        for label,key,value in (
            ('reduced182-native-population','actual_original_cases',182),
            ('substituted-original-native-slot','exact_original_ordinals',list(range(182))+[183]),
            ('wrong-language-epoch','language','python'),
            ('wrong-evidence-scope','scope','selected-Python183-phase')):
            changed=deepcopy(manifest);changed[key]=value;directory=packet(label,changed)
            rejected(label,lambda d=directory,n=label:native.unpack(d,root/(n+'-output')),
                message='complete original native183 scope')
        directory=packet('missing-first-native-part',deepcopy(manifest))
        rejected('missing-first-native-part',lambda:native.unpack(directory,root/'missing-output'),(FileNotFoundError,))
        changed=deepcopy(manifest);first=changed['archive']['parts'][0]
        directory=packet('changed-byte-in-native-part',changed)
        raw=bytearray((args.packet/first['file']).read_bytes());raw[-1]^=1;(directory/first['file']).write_bytes(raw)
        rejected('changed-byte-in-native-part',lambda:native.unpack(directory,root/'changed-output'),
            message='Actual original native archive part differs')
        changed=deepcopy(manifest);changed['archive']['parts']=changed['archive']['parts'][:1]
        directory=packet('truncated-original-native-archive',changed)
        (directory/first['file']).write_bytes((args.packet/first['file']).read_bytes())
        rejected('truncated-original-native-archive',lambda:native.unpack(directory,root/'truncated-output'),
            message='Whole original native archive differs')
        changed=deepcopy(manifest);changed['archive']['parts'][0]['file']='../outside-native-part'
        directory=packet('native-part-path-escape',changed)
        rejected('native-part-path-escape',lambda:native.unpack(directory,root/'escape-output'),
            message='Unsafe or missing original native archive part')
        substitute=root/'different-inventory-bytes.json'
        substitute.write_bytes((args.restored/'actual-complete-native183-inventory.json').read_bytes()+b'\n')
        params=SimpleNamespace(packet=args.packet,output_dir=root/'wrong-inventory-output',
            reuse_exact_complete_local_inventory=substitute)
        with patch.object(native,'unpack',return_value=(manifest,index,args.restored)):
            rejected('different-inventory-bytes-with-identical-JSON',lambda:native.replay(params),
                message='exact complete native183 inventory bytes')
        original_native,original_source=prototype
        for label,change_native,change_source in (
            ('changed-latitude-value',lambda c:c['tuned_not_reported'].__setitem__('satellite_latitudes_deg',
                float(np.nextafter(c['tuned_not_reported']['satellite_latitudes_deg'],np.inf))),None),
            ('nonfinite-latitude',lambda c:c['tuned_not_reported'].__setitem__('satellite_latitudes_deg',float('nan')),None),
            ('boolean-latitude',lambda c:c['tuned_not_reported'].__setitem__('satellite_latitudes_deg',True),None),
            ('nested-latitude-axis',lambda c:c['tuned_not_reported'].__setitem__('satellite_latitudes_deg',
                [[c['tuned_not_reported']['satellite_latitudes_deg']]]),None),
            ('native-J2-substitution',lambda c:c['reported'].__setitem__('J',2),None),
            ('source-J2-substitution',None,lambda c:c['reported'].__setitem__('J',2)),
            ('source-two-latitudes-for-J1',None,lambda c:c['tuned_not_reported']['satellite_latitudes_deg'].append(0.)),
            ('unrelated-original-N-change',lambda c:c['reported'].__setitem__('N',c['reported']['N']-1),None)):
            a,b=deepcopy(original_native),deepcopy(original_source)
            if change_native is not None:change_native(a)
            if change_source is not None:change_source(b)
            rejected('configuration-'+label,lambda x=a,y=b:native.original.configuration_transport(x,y))
    phase.require(before=={str(p):phase.sha(p) for p in watched},'An active native control source changed')
    report=dict(actual_controls=len(rows),all_invalid_complete_native_evidence_controls_rejected=True,
        actual_original_cases=183,actual_original_archive_SHA256=manifest['archive']['sha256'],
        actual_original_configurations_and_native_MAT_latitude_vectors_checked=183,
        actual_lossless_singleton_configuration_transports=48,
        original_JSON_MAT_or_numeric_values_modified=False,
        wrong_local_inventory_guard_used_the_already_byte_verified_full_restoration=True,
        actual_gradient_optimizer_or_RNG_calls=0,actual_control_source_SHA256=before,controls=rows)
    args.output.write_bytes(phase.encode(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('controls','actual_control_source_SHA256')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('packet','restored','output'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
