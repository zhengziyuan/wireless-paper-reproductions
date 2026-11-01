"""Read returned cold-control states and every stored stopping decision.

The failed scheme has no saved terminal state or trial tape. This reader does
not reconstruct that execution. No optimizer, initializer or RNG is called.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

import mpmath as mp
import numpy as np

from mp_physical_reference import exact, field_parts


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical(state, scene):
    """Independent fields and received signals, using exact binary64 inputs."""
    h, g, bridge = field_parts(state['rotation'], scene)
    theta = [mp.mpc(exact(a), exact(b)) for a, b in zip(state['theta_re'], state['theta_im'])]
    w = mp.matrix([[mp.mpc(exact(a), exact(b)) for a, b in zip(re, im)]
                   for re, im in zip(state['w_re'], state['w_im'])])
    f = h + bridge * mp.diag(theta) * g
    y = f.conjugate().transpose() * w
    k = len(scene['noise'])
    power = [[abs(y[l, s])**2 for s in range(y.cols)] for l in range(y.rows)]
    sinr = [power[u][u] / (exact(scene['noise'][u]) + mp.fsum(v for s, v in enumerate(power[u]) if s != u)) for u in range(k)]
    rate = mp.fsum(mp.log1p(x) for x in sinr) / mp.log(2)
    pattern = [mp.fsum(row) for row in power[k:]]
    desired = [exact(x) for x in scene['desired_pattern']]
    optimal_iota = mp.fsum(p*p for p in pattern) / mp.fsum(p*d for p, d in zip(pattern, desired))
    iota = exact(state['iota'])
    nmse = mp.fsum((p-iota*d)**2 for p, d in zip(pattern, desired)) / (iota*iota*mp.fsum(d*d for d in desired))
    return dict(rate=rate, nmse=nmse, utility=rate-exact(scene['rho'])*nmse,
                iota=optimal_iota, sinr=sinr, pattern=pattern,
                transmit_power=mp.fsum(abs(v)**2 for v in w),
                unit_modulus_error=max(abs(abs(t)-1) for t in theta))


def stopping_rows(result, scene):
    """Decision consistency of saved scalars, without claiming trajectory physics."""
    rows, populations = [], {}
    tiny = np.finfo(float).tiny
    for name, h in result['history'].items():
        values = h['utility']
        assert len(values) == len(h['blocks']) + 1 == h['iterations'] + 1
        assert h['iteration_budget'] == scene['AO_solver']['maximum_iterations']
        assert all(np.isfinite(values))
        relative = [(b-a)/max(abs(a), tiny) for a, b in zip(values, values[1:])]
        assert all(x >= scene['AO_solver']['relative_tolerance'] for x in relative[:-1])
        assert all(b >= a-scene['verification_tolerance'] for a, b in zip(values, values[1:]))
        assert relative[-1] == h['relative_objective_improvement']
        assert bool(relative[-1] < scene['AO_solver']['relative_tolerance']) == h['converged']
        assert h['budget_exhausted'] == (h['iterations'] >= h['iteration_budget'])
        assert h['converged'] or h['budget_exhausted']
        inner = all(b[t]['converged'] for b in h['blocks'] for t in ('W', 'RIS', 'rotation'))
        assert inner == h['inner_all_converged']
        assert (inner and h['converged']) == h['full_converged'] == result['checks'][name]['full_converged']
        counts = {t: dict(blocks=0, original_stops=0, caps=0, final_gradient_above_tolerance=0,
                          relative_step_stop_with_final_gradient_above_tolerance=0) for t in ('W', 'RIS', 'rotation')}
        for outer, block in enumerate(h['blocks']):
            for kind in ('W', 'RIS', 'rotation'):
                v = block[kind]
                original = scene[{'W':'W_solver', 'RIS':'RCG_solver', 'rotation':'PGA_solver'}[kind]]
                applicable = v.get('applicable', True)
                assert v['iteration_budget'] == (original['maximum_iterations'] if applicable else 0)
                assert 0 <= v['iterations'] <= v['iteration_budget']
                assert v['budget_exhausted'] == (v['iterations'] >= v['iteration_budget']) if applicable else not v['budget_exhausted']
                assert v['capped_unconverged'] == (not v['converged'])
                scalar = {k:x for k,x in v.items() if not isinstance(x, (list, dict))}
                scalar.update(scheme=name, outer_zero_based=outer, block=kind,
                              saved_original_iota=block['iota'], applicable=applicable)
                if kind == 'W':
                    assert len(v['QCQP']) == v['iterations'] and len(v['objective']) == v['iterations']+1
                    obj = v['objective']
                    rel = (obj[-1]-obj[-2])/max(abs(obj[-2]), tiny)
                    assert rel == v['relative_objective_improvement']
                    stops = rel < original['relative_tolerance'] or v['relative_step'] < original['relative_tolerance']
                    assert stops == v['converged']
                    assert all(q['nu'] >= 0 and 0 <= q['power'] <= scene['power']+scene['verification_tolerance'] for q in v['QCQP'])
                    scalar['stored_QCQP_count'] = len(v['QCQP'])
                elif kind == 'RIS' and applicable:
                    assert len(v['objective']) == v['iterations'] and len(v['PR_coefficients']) == v['updates']
                    assert (v['last_checked_normalized_gradient_norm'] <= original['gradient_tolerance']) == v['converged']
                    scalar['final_gradient_above_original_tolerance'] = v['final_normalized_gradient_norm'] > original['gradient_tolerance']
                elif kind == 'rotation':
                    assert len(v['objective']) == v['iterations'] and len(v['steps']) == v['updates']
                    stops = v['last_checked_projected_gradient_norm'] <= original['gradient_tolerance'] or (
                        v['relative_step'] is not None and v['relative_step'] <= original['relative_tolerance'])
                    assert stops == v['converged']
                    scalar['final_gradient_above_original_tolerance'] = v['final_projected_gradient_norm'] > original['gradient_tolerance']
                if applicable:
                    assert v['converged'] or v['budget_exhausted']
                count = counts[kind]
                count['blocks'] += 1
                count['original_stops'] += int(v['converged'])
                count['caps'] += int(not v['converged'])
                above = scalar.get('final_gradient_above_original_tolerance', False)
                count['final_gradient_above_tolerance'] += int(above)
                count['relative_step_stop_with_final_gradient_above_tolerance'] += int(
                    above and v['termination_reason'] == 'relative_step_tolerance')
                rows.append(scalar)
        populations[name] = dict(AO_iterations=h['iterations'], AO_budget=h['iteration_budget'],
            original_AO_stop=h['converged'], original_full_stop=h['full_converged'],
            final_AO_relative_improvement=relative[-1], original_AO_tolerance=scene['AO_solver']['relative_tolerance'],
            blocks=counts, failed_scheme_tape_recovered=False)
    return rows, populations


def audit_states(states, scene, checks):
    lanes, numeric = {}, {}
    tolerance = scene['verification_tolerance']
    for digits in (80, 100):
        numeric[digits] = []
        lane = {}
        with mp.workdps(digits):
            for name, state in states.items():
                own = copy.deepcopy(scene)
                if 'No-RIS' in name:
                    own['br_gain_re'] = [0.]*len(own['br_gain_re'])
                    own['br_gain_im'] = [0.]*len(own['br_gain_im'])
                expected = physical(state, own)
                fields = {}
                for key in ('utility', 'rate', 'nmse', 'iota', 'sinr', 'pattern'):
                    original = state[key] if isinstance(state[key], list) else [state[key]]
                    ref = expected[key] if isinstance(expected[key], list) else [expected[key]]
                    errors = [abs(exact(x)-y) for x,y in zip(original, ref)]
                    assert len(original) == len(ref)
                    # SINR/iota use a disclosed1e-10 relative reader bound;
                    # utility/rate/NMSE/pattern retain the original absolute verification tolerance.
                    bounds = [exact(tolerance)+(mp.mpf('1e-10')*abs(y) if key in ('sinr','iota') else 0) for y in ref]
                    fields[key] = dict(components=len(ref), maximum_absolute_error=mp.nstr(max(errors),105),
                        checks_pass=all(a <= b for a,b in zip(errors,bounds)),
                        expected=[mp.nstr(x,105) for x in ref])
                    numeric[digits].extend(ref)
                width = [own.get('rotation_bs_half_width', own.get('rotation_half_width', np.pi/2)) if name.startswith('Rot-BS') else 0.]*3
                width += [own.get('rotation_ris_half_width', own.get('rotation_half_width', np.pi/2)) if ' & Rot-RIS' in name else 0.]*3
                feasible = dict(power=bool(expected['transmit_power'] <= exact(own['power'])+exact(tolerance)),
                    unit_modulus=bool(expected['unit_modulus_error'] <= mp.mpf('1e-12')),
                    rotation=all(abs(exact(v)) <= exact(b)+mp.mpf('1e-12') for v,b in zip(state['rotation'],width)))
                assert feasible['power'] == checks[name]['power_feasible']
                assert feasible['rotation'] == checks[name]['rotation_feasible']
                lane[name] = dict(fields=fields, feasibility=feasible,
                    transmit_power=mp.nstr(expected['transmit_power'],105),
                    unit_modulus_error=mp.nstr(expected['unit_modulus_error'],105),
                    physical_and_feasibility_pass=all(f['checks_pass'] for f in fields.values()) and all(feasible.values()))
                print(json.dumps(dict(digits=digits, scheme=name, physical_and_feasibility_pass=lane[name]['physical_and_feasibility_pass'])), flush=True)
        lanes[str(digits)] = lane
    with mp.workdps(110):
        gap = max(abs(a-b) for a,b in zip(numeric[80],numeric[100]))
        cross = gap < mp.mpf('1e-35')
    return dict(lanes=lanes, maximum_MP80_MP100_difference=mp.nstr(gap,105),
        MP80_MP100_bound='1e-35', original_absolute_verification_tolerance=tolerance,
        explicit_reader_SINR_and_iota_relative_bound='1e-10',
        all_five_returned_physical_states_and_feasibility_pass=cross and all(
            x['physical_and_feasibility_pass'] for lane in lanes.values() for x in lane.values()),
        full_six_scheme_convergence_or_original_reference_pass=False)


def run(args):
    if args.output.exists():
        raise FileExistsError('Preserve existing evidence')
    args.output.mkdir(parents=True)
    start = time.perf_counter()
    inputs = {str(p):sha(p) for p in (args.result, args.scenario, args.config)}
    result = json.loads(args.result.read_bytes())
    scene = json.loads(args.scenario.read_bytes())
    assert sha(args.config) == result['input_config_sha256']
    assert sha(args.scenario) == result['input_scenario_sha256']
    assert result['original_strict_files_unchanged']
    repo = Path(__file__).resolve().parents[2]
    for path, digest in result['executed_source_binding'].items():
        assert sha(repo/path) == digest, path
    assert result['original_controls'] == {k:scene[k] for k in ('W_solver','RCG_solver','PGA_solver','AO_solver')}
    rows, populations = stopping_rows(result, scene)
    states = {k:v for k,v in result['metrics'].items() if 'w_re' in v}
    failed = {k:v for k,v in result['metrics'].items() if k not in states}
    assert len(states) == 5 and len(failed) == 1
    physics = audit_states(states, scene, result['checks'])
    assert inputs == {str(p):sha(p) for p in (args.result, args.scenario, args.config)}
    sources = {str(p.relative_to(repo)).replace('\\','/'):sha(p) for p in (Path(__file__), Path(__file__).with_name('mp_physical_reference.py'))}
    witness = dict(states=states, checks=result['checks'], failed_schemes=failed,
                   source_binding=result['executed_source_binding'], original_controls=result['original_controls'])
    (args.output/'five-returned-states-and-failure.json').write_text(json.dumps(witness,indent=2)+'\n',encoding='utf-8')
    import gzip
    (args.output/'all6015-stored-block-decisions.json.gz').write_bytes(gzip.compress((json.dumps(rows,separators=(',',':'))+'\n').encode(),mtime=0))
    report = dict(scope='One actual cold six-scheme stable-arithmetic control at original budgets',
        inputs=inputs, original_sources_and_inputs_match_actual_return=True, sources=sources,
        terminal_tool_session=8355, actual_parent_exit_code_observed=0, actual_elapsed_seconds=result['elapsed_seconds'],
        returned_states=5, failed_schemes=failed, failed_scheme_state_or_trial_vectors_saved=False,
        all2005_AO_decisions_and6015_block_scalar_decisions_consistent=True,
        AO_steps=sum(p['AO_iterations'] for p in populations.values()), block_scalar_decisions=len(rows),
        convergence_populations=populations, physics=physics, numerical_solver_or_RNG_calls=0,
        historical_all_inner_state_physics_or_QCQP_KKT_certified=False,
        original_five_nonpassing_scheme_outcomes_preserved=True,
        full_six_scheme_or_paper_pass=False, elapsed_seconds=time.perf_counter()-start)
    assert report['AO_steps'] == 2005 and len(rows) == 6015
    (args.output/'actual-complete-control-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(returned_states=5, failed_schemes=list(failed), AO_steps=2005, block_decisions=6015,
        all_five_returned_physics_pass=physics['all_five_returned_physical_states_and_feasibility_pass'],
        full_six_scheme_pass=False, elapsed_seconds=report['elapsed_seconds'])), flush=True)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('result','config','scenario','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if not run(a)['physics']['all_five_returned_physical_states_and_feasibility_pass']:
        raise SystemExit(1)
