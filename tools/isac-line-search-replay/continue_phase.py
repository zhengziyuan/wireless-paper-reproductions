"""Continue the captured original phase block within its remaining budget only."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from equivalent_runtime import binding,load_core


def run(capture,output):
    if output.exists():raise FileExistsError('Preserve prior continuation')
    meta=json.loads((capture/'actual-failure.json').read_bytes())
    assert hashlib.sha256((capture/'actual-failure-arrays.npz').read_bytes()).hexdigest()==meta['array_sha256']
    c=json.loads((capture/'original-scenario.json').read_bytes());before=binding();model=load_core()
    with np.load(capture/'actual-failure-arrays.npz',allow_pickle=False) as archive:a={k:archive[k].copy() for k in archive.files}
    w,theta,r,oldg,oldd=a['w'],a['theta'],a['r'],a['oldg'],a['oldd'];iota=meta['iota'];spec=c['RCG_solver']
    started=time.perf_counter();base=model.channel_base(r,c);rows=[];converged=False;error=None
    for iteration in range(meta['iteration'],spec['maximum_iterations']):
        metric,(_,ambient,_)=model.evaluate(w,theta,r,c,iota,True,_fixed_rotation_base=base)
        g=model.tangent(theta,ambient);norm=float(np.linalg.norm(g)/np.sqrt(len(theta)))
        row=dict(original_iteration=iteration,utility=metric['utility'],normalized_gradient=norm)
        rows.append(row)
        if norm<=spec['gradient_tolerance']:converged=True;break
        beta=float(np.real(np.vdot(g,g-model.tangent(theta,oldg)))/np.real(np.vdot(oldg,oldg)))
        direction=g+beta*model.tangent(theta,oldd);slope=float(np.real(np.vdot(g,direction)));restart=False
        if slope<=0:
            if spec['mode']!='documented_non_ascent_restart':error='Original raw PR direction is not ascent';break
            direction=g;slope=float(np.real(np.vdot(g,g)));restart=True
        alpha=spec['initial_step'];accepted=False
        for backtracks in range(spec['maximum_backtracks']):
            trial=theta+alpha*direction;trial/=abs(trial)
            value=model.evaluate(w,trial,r,c,iota,_fixed_rotation_base=base)['utility']
            if value>=metric['utility']+spec['armijo']*alpha*slope:
                oldg,oldd=g,direction;theta=trial;accepted=True;break
            alpha*=spec['backtrack_factor']
        row.update(beta=beta,slope=slope,restart=restart,alpha=alpha,backtracks=backtracks,accepted=accepted)
        if not accepted:error='Original Armijo exhausted under equivalent arithmetic';break
    metric,(_,ambient,_)=model.evaluate(w,theta,r,c,iota,True,_fixed_rotation_base=base)
    after=binding();assert before==after
    output.mkdir(parents=True);np.savez(output/'continued-phase-state.npz',w=w,theta=theta,r=r,ambient=ambient)
    report=dict(scope='Mixed original saved prefix plus equivalent-arithmetic suffix of one RCG block, within original500 budget only',
        source_binding=before,source_unchanged=True,initial_original_iteration=meta['iteration'],original_iteration_budget=spec['maximum_iterations'],
        maximum_available_suffix_iterations=spec['maximum_iterations']-meta['iteration'],executed_suffix_iterations=len(rows),
        preserved_saved_old_gradient_and_direction=True,solver_controls=spec,rows=rows,converged_on_original_checked_gradient=converged,
        final_normalized_gradient=float(np.linalg.norm(model.tangent(theta,ambient))/np.sqrt(len(theta))),final_utility=metric['utility'],
        error=error,elapsed_seconds=time.perf_counter()-started,full_cold_phase_or_six_scheme_or_paper_pass=False)
    (output/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('executed_suffix_iterations','converged_on_original_checked_gradient','final_normalized_gradient','error','elapsed_seconds')}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();run(a.capture,a.output_dir)
