"""Check the five saved final W/RIS/rotation gradients at their last PGA iota.

The PGA has the returned W and theta fixed. Its last saved block iota therefore
permits a real final projected-gradient check, including relative-step stops.
This does not reconstruct intermediate W/RIS states or failed trial vectors.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import mpmath as mp
import numpy as np

from audit_stable_derivatives import reference
from equivalent_runtime import binding, load_core
from mp_physical_reference import exact


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    if args.output.exists():
        raise FileExistsError('Preserve previous evidence')
    started = time.perf_counter()
    inputs = {str(p):sha(p) for p in (args.result,args.scenario)}
    source_before = binding()
    result = json.loads(args.result.read_bytes())
    c = json.loads(args.scenario.read_bytes())
    assert result['input_scenario_sha256'] == sha(args.scenario)
    assert all(source_before[k] == v for k,v in result['executed_source_binding'].items() if k in source_before)
    model = load_core()
    lanes, values = {}, {}
    for digits in (80,100):
        values[digits] = []
        rows = {}
        with mp.workdps(digits):
            for name, state in result['metrics'].items():
                if 'w_re' not in state:
                    continue
                scene = dict(c)
                if 'No-RIS' in name:
                    scene.update(br_gain_re=[0.]*len(c['br_gain_re']),br_gain_im=[0.]*len(c['br_gain_im']))
                w = np.asarray(state['w_re'])+1j*np.asarray(state['w_im'])
                theta = np.asarray(state['theta_re'])+1j*np.asarray(state['theta_im'])
                r = np.asarray(state['rotation'])
                block = result['history'][name]['blocks'][-1]
                iota = block['iota']
                refs = reference(w,theta,r.tolist(),scene,iota)
                _, got = model.evaluate(w,theta,r,scene,iota,True)
                components = {}
                for kind, original, ref in zip(('W','RIS','rotation'),got,refs):
                    numeric = list(np.asarray(original).reshape(-1))
                    expected = list(np.asarray(ref,dtype=object).reshape(-1))
                    err = max(abs(exact(complex(a))-b) for a,b in zip(numeric,expected))
                    components[kind] = dict(components=len(expected),maximum_absolute_error=mp.nstr(err,105),
                        original_component_1e_minus5_bound_pass=bool(err < mp.mpf('1e-5')),
                        reference=[dict(real=mp.nstr(mp.re(z),105),imag=mp.nstr(mp.im(z),105)) for z in expected])
                    values[digits].extend(expected)
                ris = [z-mp.re(z*mp.conj(exact(complex(t))))*exact(complex(t)) for z,t in zip(refs[1],theta)]
                risnorm = mp.sqrt(mp.fsum(abs(z)**2 for z in ris)/len(theta))
                width = [scene.get('rotation_bs_half_width',scene.get('rotation_half_width',np.pi/2)) if name.startswith('Rot-BS') else 0.]*3
                width += [scene.get('rotation_ris_half_width',scene.get('rotation_half_width',np.pi/2)) if ' & Rot-RIS' in name else 0.]*3
                residual = []
                for z,x,b in zip(refs[2],r,width):
                    if b == 0:
                        z = mp.mpf(0)
                    else:
                        if x <= -b:
                            z = max(mp.mpf(0),z)
                        if x >= b:
                            z = min(mp.mpf(0),z)
                    residual.append(z)
                norm = mp.sqrt(mp.fsum(z*z for z in residual))
                saved = block['rotation']['final_projected_gradient_norm']
                rows[name] = dict(last_saved_fixed_iota=iota,all_gradient_components=components,
                    final_RIS_normalized_gradient=mp.nstr(risnorm,105),RIS_is_applicable='No-RIS' not in name,
                    RIS_at_returned_after_PGA_state_is_same_as_last_RIS_check_state=False,
                    final_PGA_projected_gradient=mp.nstr(norm,105),
                    independent_PGA_gradient_stop_pass=bool(norm <= exact(scene['PGA_solver']['gradient_tolerance'])),
                    saved_final_PGA_projected_gradient=saved,
                    saved_PGA_norm_absolute_error=mp.nstr(abs(norm-exact(saved)),105),
                    original_PGA_stop=block['rotation']['converged'],
                    original_PGA_stop_reason=block['rotation']['termination_reason'],
                    original_PGA_relative_step=block['rotation']['relative_step'],
                    original_PGA_gradient_tolerance=scene['PGA_solver']['gradient_tolerance'],
                    new_optimizer_or_RNG_calls=0)
                values[digits].extend([risnorm,norm])
                print(json.dumps(dict(digits=digits,scheme=name,independent_PGA_norm=mp.nstr(norm,15),
                    all_component_checks_pass=all(x['original_component_1e_minus5_bound_pass'] for x in components.values()))),flush=True)
        lanes[str(digits)] = rows
    with mp.workdps(110):
        gap = max(abs(a-b) for a,b in zip(values[80],values[100]))
    assert source_before == binding() and inputs == {str(p):sha(p) for p in (args.result,args.scenario)}
    repo = Path(__file__).resolve().parents[2]
    source_files = (Path(__file__),Path(__file__).with_name('audit_stable_derivatives.py'),
                    Path(__file__).with_name('mp_physical_reference.py'),Path(__file__).with_name('audit_failure.py'))
    passed = gap < mp.mpf('1e-35') and all(v['original_component_1e_minus5_bound_pass']
        for lane in lanes.values() for row in lane.values() for v in row['all_gradient_components'].values())
    report = dict(scope='Five actual returned final W/RIS/rotation gradient states, at last fixed PGA iota',
        inputs=inputs,source_binding=source_before,sources={str(p.relative_to(repo)).replace('\\','/'):sha(p) for p in source_files},
        rotation_reference='MP central difference at1e-20; W/RIS independent analytic derivatives',
        continuum_interval_or_history_KKT_certificate=False,source_and_input_unchanged=True,
        lanes=lanes,maximum_MP80_MP100_difference=mp.nstr(gap,105),MP80_MP100_bound='1e-35',
        all_five_terminal_gradient_component_comparisons_pass=bool(passed),
        step_stops_with_independent_final_PGA_norm_above_original_tolerance=[name for name,row in lanes['100'].items()
            if row['original_PGA_stop_reason']=='relative_step_tolerance' and not row['independent_PGA_gradient_stop_pass']],
        full_convergence_or_paper_pass=False,elapsed_seconds=time.perf_counter()-started)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(all_five_terminal_gradient_comparisons_pass=passed,
        step_stops_above_gradient_tolerance=report['step_stops_with_independent_final_PGA_norm_above_original_tolerance'],
        elapsed_seconds=report['elapsed_seconds'])),flush=True)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('result','scenario','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if not run(a)['all_five_terminal_gradient_component_comparisons_pass']:
        raise SystemExit(1)
