"""Independent physical replay of a native start's complete saved mu-endpoint view.

The transport view preserves every numeric input/endpoint but omits the local
record-folder metadata and unsaved inner states. Actual complete MAT/JSON trees
are separately checked by audit_native_start.py on the numerical-data host.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import independent_physical as oracle


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(source,output):
    if output.exists():raise FileExistsError('Preserve previous independent replay')
    before=sha(source);data=json.loads(source.read_bytes());settings=data['settings'];scheme=data['scheme'];start=data['start']
    assert data['scope']=='actual_native_all_mu_numerical_endpoint_view_not_all_inner_states'
    assert settings['number_of_starts']==6000 and settings['rcg_max_iterations']==100000 and settings['rcg_gradient_tolerance']==1e-6
    config,rebuilt,indices=oracle.geometry(settings,scheme)
    assert config==data['configuration'] and indices==data['indices_zero_based']
    coefficient_error=max(float(np.max(abs(np.asarray(data['coefficients'][k])-np.asarray(rebuilt[k])))) for k in ('real','imag'))
    assert coefficient_error<=2e-15
    before_rng,after_rng,initial=oracle.initial_input(settings,scheme,start)
    assert [before_rng,after_rng]==data['initial_rng_before_after']
    for phase in ('phi','theta'):
        for key in ('real','imag'):
            assert np.max(abs(np.asarray(initial[phase][key])-np.asarray(data['initial_state'][phase][key])),initial=0)<=2e-15
    assert np.max(abs(np.asarray(initial['X'])-np.asarray(data['initial_state']['X'])))<=2e-15
    mus=oracle.prescribed_mu(settings,start);assert [v['mu'] for v in data['endpoints']]==mus
    rows=[]
    for index,(item,mu) in enumerate(zip(data['endpoints'],mus)):
        value=oracle.physical(config,data['coefficients'],indices,item['state'],mu);stop=item['stop']
        norm_error=abs(value['projected_kkt_norm']-stop['projected_kkt_norm']);objective_error=abs(value['objective']-stop['objective'])
        assert norm_error<=5e-13 and objective_error<=5e-12+5e-14*abs(stop['objective']) and value['domain_feasible']
        passed=value['unchanged_implemented_1e_minus6_gate_pass'] and stop['reason']=='gradient_tolerance'
        rows.append(dict(index=index,mu=mu,independent=value,saved_norm_error=norm_error,saved_objective_error=objective_error,original_stop_pass=passed))
    final=rows[-1]['independent']
    for name in ('min_relaxed_snr','min_binary_snr'):assert abs(final[name]-data['final_metrics'][name])<=5e-14
    assert final['binary_schedule']==data['final_metrics']['binary_schedule'] and sha(source)==before
    result=dict(scope='One actual full native start: every saved original mu endpoint and source-bound numeric view',scheme=scheme,start=start,
        source_view_sha256=before,original_native_input_hashes=data['original_native_input_hashes'],
        oracle_sha256=sha(Path(oracle.__file__)),auditor_sha256=sha(Path(__file__)),endpoints=rows,
        all_saved_endpoint_physics_domains_and_original_stops_pass=all(x['original_stop_pass'] for x in rows),
        all12000_or_original_figure_or_unsaved_inner_state_or_full_paper_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(scheme=scheme,start=start,endpoints=len(rows),all_saved_checks_pass=result['all_saved_endpoint_physics_domains_and_original_stops_pass'])),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not audit(a.input,a.output)['all_saved_endpoint_physics_domains_and_original_stops_pass']:raise SystemExit(1)
