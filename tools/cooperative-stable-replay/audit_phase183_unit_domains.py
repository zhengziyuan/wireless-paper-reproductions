"""Every actual183-case saved phase domain at MP80/100; no optimizer or RNG.

This checks the unit-modulus phase domain only. Power/interference, QT, MC,
inner trajectories and original-reference agreement keep their separate gates.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mpmath as mp
import numpy as np
from scipy.io import loadmat

import audit_native_case as layout
import mp_phase_reference as reference
from phase183_evidence import read,sha,encode,require,input_binding


def unit_error(values,digits):
    require(np.isfinite(values).all(), 'Every actual phase component must be finite')
    with mp.workdps(digits):
        return max(abs(abs(reference.scalar(z))-1) for z in values.reshape(-1))


def audit(restored,output):
    require(not output.exists(),'Preserve prior complete domain evidence')
    index_path=restored/'complete-phase-case-index.json';index=read(index_path)
    require(index['case_scope']=='selected-Python183-phase' and index['language']=='python' and
        index['original_cases']==183 and [c['ordinal'] for c in index['cases']]==list(range(183)),
        'Every complete original183 phase case is required')
    watched=[Path(__file__),Path(__file__).with_name('phase183_evidence.py'),
             Path(layout.__file__),Path(reference.__file__),index_path]
    before={str(p):sha(p) for p in watched};cases=[];count=coordinates=0;all_gaps=[]
    maxima={80:mp.mpf(0),100:mp.mpf(0)}
    for case in index['cases']:
        container=restored/case['container'];matrix=restored/case['states']
        require(input_binding(container,matrix)==case['input_binding'], 'An actual phase input or math source changed')
        recording=loadmat(matrix,simplify_cells=True)['recording']
        phases=layout.sequence(recording['phase_endpoints'])
        require(len(phases)==case['actual_phase_endpoints'],'Every actual original phase endpoint is required')
        U,M=(case['actual_reported_scene_dimensions'][k] for k in ('U','M'));rows=[]
        for i,state in enumerate(phases):
            values=np.asarray(state['final_phi'],complex)
            require(values.size==U*M,'Every actual phase coordinate is required')
            errors={digits:unit_error(values,digits) for digits in (80,100)}
            with mp.workdps(110):
                gap=abs(errors[80]-errors[100]);all_gaps.append(gap)
                passed=all(x<=reference.real(1e-10) for x in errors.values()) and gap<=mp.mpf('1e-40')
                for digits,x in errors.items():maxima[digits]=max(maxima[digits],x)
                rows.append(dict(index=i,complex_phase_coordinates=values.size,
                    maximum_unit_modulus_error={str(d):mp.nstr(v,105) for d,v in errors.items()},
                    maximum_crossprecision_difference=mp.nstr(gap,105),passed=bool(passed)))
            count+=1;coordinates+=values.size
        require(input_binding(container,matrix)==case['input_binding'],'An actual input changed during domain calculation')
        cases.append(dict(ordinal=case['ordinal'],actual_phase_endpoints=len(phases),
            all_actual_phase_domains_pass=all(r['passed'] for r in rows),phases=rows))
        if len(cases)%12==0:print(json.dumps(dict(original_cases_domain_checked=len(cases),actual_phase_endpoints=count)),flush=True)
    require(count==index['actual_phase_endpoints'] and coordinates==index['complex_gradient_coordinates_per_precision'],
            'All original phase endpoints and every complex coordinate must be checked')
    require(before=={str(p):sha(p) for p in watched},'An active domain source or exact original index changed')
    with mp.workdps(110):
        report=dict(actual_original_cases=183,actual_phase_endpoints_checked=count,
            actual_complex_phase_coordinates_per_precision=coordinates,precisions=[80,100],
            original_unit_modulus_absolute_bound='1e-10',crossprecision_absolute_bound='1e-40',
            maximum_actual_unit_modulus_error={str(d):mp.nstr(v,105) for d,v in maxima.items()},
            maximum_MP80_MP100_difference=mp.nstr(max(all_gaps),105),
            all_actual_original_phase_unit_domains_and_precision_pass=all(c['all_actual_phase_domains_pass'] for c in cases),
            actual_input_and_current_source_SHA256=before,all_watched_source_and_index_bytes_unchanged=True,
            original_optimizer_or_RNG_calls=0,
            other_power_interference_QT_MC_inner_trajectory_source_curve_or_full_paper_pass=False,cases=cases)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(encode(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','actual_input_and_current_source_SHA256')}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--restored',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();r=audit(args.restored,args.output)
    if not r['all_actual_original_phase_unit_domains_and_precision_pass']:raise SystemExit(1)
