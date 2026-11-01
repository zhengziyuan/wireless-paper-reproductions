"""Replay the compact cold-control states and original scalar stop contexts.

The complete190MB execution history is external. This command verifies all
packet bytes, every included AO/block scalar decision and five physical and
gradient states. It does not recreate the failed scheme or historical QCQPs.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from audit_cold_control import audit_states
from audit_cold_terminal_gradients import run as audit_gradients


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    if args.output_dir.exists():
        raise FileExistsError('Use a fresh output directory')
    packet = args.packet.resolve()
    manifest = json.loads((packet/'manifest.json').read_bytes())
    for row in manifest['files']:
        path = packet/row['name']
        assert path.is_file() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], row['name']
    scenario = packet/'original-scenario.json'
    scene = json.loads(scenario.read_bytes())
    result_path = packet/'compact-returned-gradient-input.json'
    result = json.loads(result_path.read_bytes())
    assert sha(scenario) == result['input_scenario_sha256'] == manifest['original_scenario_sha256']
    assert sha(packet/'original-run-config.json') == result['input_config_sha256'] == manifest['original_config_sha256']
    decisions = json.loads(gzip.decompress((packet/'all6015-stored-block-decisions.json.gz').read_bytes()))
    ao = json.loads((packet/'all2005-AO-decision-contexts.json').read_bytes())
    actual = json.loads((packet/'actual-complete-control-audit.json').read_bytes())
    seen = set()
    counts = {}
    for row in decisions:
        name, outer, kind = row['scheme'], row['outer_zero_based'], row['block']
        token = (name,outer,kind)
        assert token not in seen
        seen.add(token)
        h = ao[name]
        assert 0 <= outer < h['iterations']
        applicable = row['applicable']
        spec = scene[{'W':'W_solver','RIS':'RCG_solver','rotation':'PGA_solver'}[kind]]
        assert row['iteration_budget'] == (spec['maximum_iterations'] if applicable else 0)
        assert 0 <= row['iterations'] <= row['iteration_budget']
        assert row['budget_exhausted'] == (row['iterations'] >= row['iteration_budget'] if applicable else False)
        assert row['capped_unconverged'] == (not row['converged'])
        if kind == 'W':
            assert row['stored_QCQP_count'] == row['iterations']
            stop = row['relative_objective_improvement'] < spec['relative_tolerance'] or row['relative_step'] < spec['relative_tolerance']
        elif kind == 'RIS':
            stop = not applicable or row['last_checked_normalized_gradient_norm'] <= spec['gradient_tolerance']
        else:
            stop = row['last_checked_projected_gradient_norm'] <= spec['gradient_tolerance'] or (
                row['relative_step'] is not None and row['relative_step'] <= spec['relative_tolerance'])
        assert bool(stop) == row['converged']
        assert row['converged'] or row['budget_exhausted']
        value = counts.setdefault((name,kind),dict(blocks=0,original_stops=0,caps=0,final_gradient_above_tolerance=0,
            relative_step_stop_with_final_gradient_above_tolerance=0))
        value['blocks'] += 1
        value['original_stops'] += int(row['converged'])
        value['caps'] += int(not row['converged'])
        above = row.get('final_gradient_above_original_tolerance',False)
        value['final_gradient_above_tolerance'] += int(above)
        value['relative_step_stop_with_final_gradient_above_tolerance'] += int(above and row['termination_reason']=='relative_step_tolerance')
    assert len(seen) == 6015
    total = 0
    for name,h in ao.items():
        assert len(h['utility']) == h['iterations']+1
        assert h['iteration_budget'] == scene['AO_solver']['maximum_iterations']
        assert h['converged'] or h['budget_exhausted']
        differences = [(b-a)/max(abs(a),np.finfo(float).tiny) for a,b in zip(h['utility'],h['utility'][1:])]
        assert differences[-1] == h['relative_objective_improvement']
        assert all(x >= scene['AO_solver']['relative_tolerance'] for x in differences[:-1])
        assert (differences[-1] < scene['AO_solver']['relative_tolerance']) == h['converged']
        inner = all(counts[(name,kind)]['caps']==0 for kind in ('W','RIS','rotation'))
        assert inner == h['inner_all_converged']
        assert (inner and h['converged']) == h['full_converged']
        for outer in range(h['iterations']):
            assert all((name,outer,kind) in seen for kind in ('W','RIS','rotation'))
        for kind in ('W','RIS','rotation'):
            assert counts[(name,kind)] == actual['convergence_populations'][name]['blocks'][kind]
        total += h['iterations']
    assert total == 2005
    states = {k:v for k,v in result['metrics'].items() if 'w_re' in v}
    failed = {k:v for k,v in result['metrics'].items() if k not in states}
    assert len(states)==5 and failed == actual['failed_schemes']
    args.output_dir.mkdir(parents=True)
    physics = audit_states(states,scene,result['checks'])
    (args.output_dir/'new-five-state-physics-MP80-MP100.json').write_text(json.dumps(physics,indent=2)+'\n',encoding='utf-8')
    gradients = audit_gradients(SimpleNamespace(result=result_path,scenario=scenario,
        output=args.output_dir/'new-five-terminal-gradients-MP80-MP100.json'))
    assert physics['all_five_returned_physical_states_and_feasibility_pass']
    assert gradients['all_five_terminal_gradient_component_comparisons_pass']
    assert len(gradients['step_stops_with_independent_final_PGA_norm_above_original_tolerance']) == 3
    assert [name for name,h in ao.items() if h['full_converged']] == ['Fix-BS & No-RIS']
    for row in manifest['files']:
        assert sha(packet/row['name']) == row['sha256']
    out = dict(packet_payloads_verified=len(manifest['files']),actual_saved_AO_decisions=2005,
        actual_saved_block_scalar_decisions=6015,five_physical_and_gradient_states_recomputed=True,
        failed_scheme_state_or_all190MB_historical_execution_replayed=False,
        original_full_converged_schemes=['Fix-BS & No-RIS'],full_six_scheme_or_reference_or_paper_pass=False)
    (args.output_dir/'summary.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out),flush=True)
    return out


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    run(p.parse_args())
