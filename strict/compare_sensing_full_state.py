"""Independently evaluate actual full-size MATLAB/Python sensing final states.

Two locally stationary optimizer outputs need not be identical. This check
compares each saved state's physical metrics with a fresh evaluation of that
same state, and recomputes the original constrained KKT. It never relabels
inner caps, overwrites a trajectory, or certifies all6000 starts/reference plots.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

PACKAGE=Path(__file__).resolve().parent/'mis-sensing'
sys.path.insert(0,str(PACKAGE))
import run as sensing


def read(path):
    if path.suffix=='.gz':
        with gzip.open(path,'rt',encoding='utf-8') as stream:return json.load(stream)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def state(value):
    result={}
    for key in ('phi','theta'):
        item=value[key]
        result[key]=(np.asarray(item['real'],float)+1j*np.asarray(item['imag'],float)).reshape(-1)
    result['X']=np.asarray(value['X'],float)
    result['eta']=np.asarray(value['eta'],float)
    return result


def compare(manifest,matlab,python):
    settings=manifest['settings'];figure=manifest['figure'];before=sensing.implementation_digest()[0]
    if (before!=manifest['implementation_digest'] or python['implementation_digest']!=before
        or python.get('bank_signature')!=manifest['signature'] or python.get('source_unchanged_during_run') is not True):
        raise ValueError('An unchanged full-size source-bound Python bank record is required')
    if (figure['id']!='fig3' or figure['objective']!='sinr' or len(figure['points'])!=1
        or matlab['settings']!=settings or matlab['configuration']!=figure['points'][0]
        or matlab['start']!=python['summary']['start'] or len(matlab['history'])!=30 or len(python['history'])!=30):
        raise ValueError('Same declared original Fig3 scene/settings/start and all30 actual outer calls required')
    model=sensing.make_model(figure['points'][0],settings)
    if (model.M,model.N,model.targets,model.U)!=(400,256,9,25):raise ValueError('No reduced-dimension state checks')
    checks=[]
    for language,raw in (('matlab',matlab),('python',python)):
        z=state(raw['state']);metrics=raw['metrics'];gamma=model.metric(z,'sinr')
        relaxed=np.sum(z['X']*gamma,axis=1);chosen=np.argmax(z['X'],axis=1)
        computed={'eta':float(z['eta']), 'min_relaxed_metric':float(np.min(relaxed)),
                  'min_binary_metric':float(np.min(gamma[np.arange(model.targets),chosen])),
                  'maximum_constraint':float(np.max(float(z['eta'])-relaxed))}
        errors={key:abs(computed[key]-metrics[key]) for key in computed}
        metric_gate=all(np.isclose(computed[key],metrics[key],rtol=1e-10,atol=1e-10) for key in computed)
        status=raw['solver_status'] if language=='matlab' else raw['summary']['solver_status']
        reevaluated=sensing.solver_diagnostics(raw['history'],settings,'sinr',model=model,state=z,metrics=metrics)
        required=('all_inner_tolerances_satisfied','prescribed_outer_budget_execution_complete',
                  'original_problem_kkt_verified','convergence_verified')
        stop_gate=all(status.get(key) is True and reevaluated.get(key) is True for key in required)
        stop_gate=stop_gate and status['inner_iteration_cap_exits']==reevaluated['inner_iteration_cap_exits']==0
        stop_gate=stop_gate and status['inner_failure_exits']==reevaluated['inner_failure_exits']==0
        checks.append(dict(language=language,saved_eta=metrics['eta'],same_saved_state_metric_errors=errors,
            same_saved_state_metric_recalculation_pass=bool(metric_gate),
            actual_all30_inner_stops_and_original_constraints_pass=bool(stop_gate),
            original_problem_kkt_recomputed=reevaluated['original_problem_kkt_certificate']))
    after=sensing.implementation_digest()[0]
    if after!=before:raise ValueError('Source changed during actual state evaluation')
    etas=[c['saved_eta'] for c in checks]
    return dict(scope='two_actual_full400_256_25_9_30outer_state_and_stop_checks_NOT_6000_start_or_reference_certificate',
        start=matlab['start'],checks=checks,all_same_state_metric_and_original_stop_checks_pass=all(
            c['same_saved_state_metric_recalculation_pass'] and c['actual_all30_inner_stops_and_original_constraints_pass'] for c in checks),
        separately_found_local_state_eta_difference=abs(etas[0]-etas[1]),
        identical_optimizer_states_or_global_optima_claimed=False,
        local_state_difference_is_not_an_error_tolerance_for_same_state_metrics=True,
        Python_bank_execution_source_identity_verified=True,
        MATLAB_execution_interval_identity_not_added_post_hoc=True,
        independent_state_evaluation_source_unchanged=True,implementation_digest=before,
        full6000_start_bank_completed=False,original_figure_reproduction_certified=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','matlab','python','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();result=compare(read(args.manifest),read(args.matlab),read(args.python))
    result['input_file_sha256']={name:hashlib.sha256(getattr(args,name).read_bytes()).hexdigest() for name in ('manifest','matlab','python')}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('all_same_state_metric_and_original_stop_checks_pass',
        'separately_found_local_state_eta_difference','original_figure_reproduction_certified')}))
    return 0 if result['all_same_state_metric_and_original_stop_checks_pass'] else 1


if __name__=='__main__':raise SystemExit(main())
