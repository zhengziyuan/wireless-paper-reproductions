"""Independent MP80/100 full-physics stop check of a saved fixed-W phase probe."""
import argparse
import json
from pathlib import Path
import mpmath as mp
import numpy as np
from audit_failure import FixedObjective,mpmatrix,sha
from mp_physical_reference import field_parts,exact
import mp_physical_reference as reference


def audit(capture,probe,output):
    if output.exists():raise FileExistsError('Preserve prior precise phase audit')
    meta=json.loads((capture/'actual-failure.json').read_bytes());c=json.loads((capture/'original-scenario.json').read_bytes())
    record=json.loads((probe/'summary.json').read_bytes())
    if not record['original_phase_stop_reached']:raise ValueError('No original stop was reported; retain failure')
    assert record['captured_array_sha256']==meta['array_sha256'] and record['previous_original_PR_history_continued'] is False
    with np.load(probe/'actual-probe-arrays.npz',allow_pickle=False) as data:w,theta,r,ambient=(data[k].copy() for k in ('w','theta','r','ambient'))
    with np.load(capture/'actual-failure-arrays.npz',allow_pickle=False) as data:
        assert np.array_equal(w,data['w']) and np.array_equal(r,data['r']);initial=data['theta'].copy()
    sources=dict(auditor=sha(Path(__file__)),objective=sha(Path(__file__).with_name('audit_failure.py')),physical_reference=sha(Path(reference.__file__)),
        captured_manifest=sha(capture/'actual-failure.json'),probe_summary=sha(probe/'summary.json'),actual_arrays=sha(probe/'actual-probe-arrays.npz'))
    lanes={};numbers={}
    for digits in (80,100):
        with mp.workdps(digits):
            model=FixedObjective(mpmatrix(w),c,meta['iota'],field_parts(r.tolist(),c));t=[exact(complex(x)) for x in theta]
            final=model.evaluate(t,True);origin=model.evaluate([exact(complex(x)) for x in initial]);gradient=final.pop('ambient')
            projected=[v-mp.re(v*mp.conj(z))*z for z,v in zip(t,gradient)]
            norm=mp.sqrt(mp.fsum(abs(x)**2 for x in projected)/len(t));radius=max(abs(abs(z)-1) for z in t)
            power=mp.fsum(abs(exact(complex(z)))**2 for z in w.reshape(-1));tolerance=exact(c['RCG_solver']['gradient_tolerance'])
            passed=norm<=tolerance and radius<=exact(1e-10) and power<=exact(c['power'])+exact(c['verification_tolerance'])
            maxerror=max(abs(exact(complex(x))-y) for x,y in zip(ambient,gradient));component=maxerror<exact(1e-5)
            lanes[str(digits)]=dict(normalized_gradient=mp.nstr(norm,digits),original_gradient_tolerance=mp.nstr(tolerance,digits),original_gradient_stop_pass=bool(norm<=tolerance),
                utility=mp.nstr(final['utility'],digits),starting_frozen_state_utility=mp.nstr(origin['utility'],digits),actual_utility_increment=mp.nstr(final['utility']-origin['utility'],digits),
                maximum_radius_error=mp.nstr(radius,digits),transmit_power=mp.nstr(power,digits),original_physical_domain_pass=bool(passed),
                stored_ambient_maxerror=mp.nstr(maxerror,digits),unchanged_component_bound_pass=bool(component),
                complex_gradient=[dict(real=mp.nstr(z.real,digits),imag=mp.nstr(z.imag,digits)) for z in gradient])
            numbers[digits]=[norm,final['utility'],origin['utility'],radius,power]+gradient
    with mp.workdps(110):gap=max(abs(a-b) for a,b in zip(numbers[80],numbers[100]));precision=gap<mp.mpf('1e-40')
    assert sources['actual_arrays']==sha(probe/'actual-probe-arrays.npz') and sources['objective']==sha(Path(__file__).with_name('audit_failure.py'))
    report=dict(scope='Actual full-size fixed-W phase probe only, warm-started at original failed point, independent full physical paths atMP80/100',
        source_input_sha256=sources,dimensions=dict(M=4,N=36,K=2,A=66,streams=6),original_unreported_cap=record['original_unreported_safety_cap'],
        explicit_unreported_cap=record['selected_unreported_safety_cap'],actual_new_call_iterations=record['iterations'],previous_original_PR_history_continued=False,
        lanes=lanes,maximum_MP80_MP100_difference=mp.nstr(gap,105),precision_absolute_bound='1e-40',
        all_full_physics_original_phase_stop_and_precision_checks_pass=bool(precision and all(v['original_physical_domain_pass'] and v['unchanged_component_bound_pass'] for v in lanes.values())),
        full_cold_six_scheme_or_original_reference_or_paper_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(all_precise_phase_checks_pass=report['all_full_physics_original_phase_stop_and_precision_checks_pass'],norm_MP100=lanes['100']['normalized_gradient'],iterations=record['iterations'])),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','probe','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if not audit(a.capture,a.probe,a.output)['all_full_physics_original_phase_stop_and_precision_checks_pass']:raise SystemExit(1)
