"""All183 original configurations, native MAT latitudes and eight bad controls."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

import inventory_complete_native183_phase_and_QT_v2 as inventory


def run(args):
    phase=inventory.phase
    phase.require(not args.output.exists(),'Preserve previous configuration transport controls')
    before={str(p):phase.sha(p) for p in (Path(__file__),Path(inventory.__file__),args.index)}
    identities=phase.read(args.index)['cases'];phase.require([x['ordinal'] for x in identities]==list(range(183)),
        'Every original source case is required')
    receipts=[];prototype=None
    for identity in identities:
        n=identity['ordinal'];source=args.original_bank/f'case-{n:03d}'/'configuration.json'
        container=args.bank/f'case-{n:03d}-matlab.json';native=phase.read(container)
        matrix=container.parent/native['state_recording']['filename']
        protected={str(p):phase.sha(p) for p in (source,container,matrix)}
        phase.require(protected[str(source)]==identity['configuration_sha256'] and
            protected[str(matrix)]==native['state_recording']['sha256'],'Exact original/native source bytes differ')
        original=phase.read(source);receipt=inventory.configuration_transport(native['configuration'],original)
        data=loadmat(matrix,simplify_cells=True)['recording']['input']['configuration']
        actual=np.asarray(data['tuned_not_reported']['satellite_latitudes_deg'],dtype='<f8').reshape(-1)
        expected=np.asarray(original['tuned_not_reported']['satellite_latitudes_deg'],dtype='<f8').reshape(-1)
        phase.require(actual.size==expected.size==identity['full_reported_scene']['J'] and
            actual.tobytes()==expected.tobytes(),'An actual native MAT latitude byte differs')
        phase.require(protected=={p:phase.sha(Path(p)) for p in protected},'An original configuration or native input changed')
        if receipt:
            receipts.append(dict(ordinal=n,actual_transport=receipt,actual_native_MAT_vector_bytes_match=True))
            if prototype is None:prototype=(native['configuration'],original)
    phase.require(len(receipts)==48 and prototype is not None,'Exactly the48 actual J=1 JSON singleton cases are required')
    native,original=prototype;bad=[]
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
        a,b=deepcopy(native),deepcopy(original)
        if change_native is not None:change_native(a)
        if change_source is not None:change_source(b)
        try:inventory.configuration_transport(a,b)
        except ValueError as error:bad.append(dict(control=label,expected_rejection_observed=True,actual_reason=str(error)))
        else:raise AssertionError('Invalid configuration accepted: '+label)
    phase.require(before=={p:phase.sha(Path(p)) for p in before},'An active transport/control source changed')
    report=dict(actual_original_configurations_checked=183,actual_native_MAT_latitude_vectors_byte_checked=183,
        actual_J1_JSON_singleton_interpretations=48,all_original_JUNM_and_other_configuration_fields_equal=True,
        actual_negative_controls=len(bad),all_invalid_controls_rejected=True,
        source_JSON_MAT_or_numeric_values_modified=False,original_optimizer_or_RNG_calls=0,
        actual_control_source_SHA256=before,actual_transports=receipts,negative_controls=bad)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(phase.encode(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('actual_control_source_SHA256','actual_transports','negative_controls')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bank','original-bank','index','output'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
