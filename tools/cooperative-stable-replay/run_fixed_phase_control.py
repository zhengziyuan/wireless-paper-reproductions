"""Two prospective first-phase controls with identical native channel inputs.

Only the two actual saved NoRIS fixed powers are varied. Both controls use the
same recorded initial phase, mu=1, unchanged Python positive-Wick evaluator,
original RGD/Armijo/BB controls, 100000 cap and strict1e-6 stop. No convex
solver, RNG, final power allocation or new full-case curve is executed.
"""
import argparse
from pathlib import Path
import sys
import time

import mpmath as mp
import numpy as np
from scipy.io import loadmat,savemat

from audit_native_case import channel_data,sequence,sha
from audit_phase_divergence import cells,load_witness
from build_power_curve_views import read,require,write
import mp_phase_reference as ref


def execute(directory,output):
    require(not output.exists(),'Preserve every prior phase-control result')
    witness,index=load_witness(directory);contexts={c['label']:c for c in sequence(witness['contexts'])}
    c=contexts['matlab'];data=channel_data(c['data'],3,2,16,25);initial=np.asarray(witness['phases']['initial']).reshape(2,25)
    limit=np.asarray(c['interferenceLimit']).reshape(-1);mu=float(c['mu'])
    require(mu==1 and index['original_rmo_max_iterations']==100000 and index['original_gradient_tolerance']==1e-6,'Exact original first-phase controls required')
    strict=Path(__file__).resolve().parents[2]/'strict/cooperative-satcom';sys.path.insert(0,str(strict))
    from models import mr_phase_value_gradient
    from increments_v2 import mr_increment_v2
    from spectral_rmo import rmo_ascent
    paths=[directory/'witness-index.json',directory/index['witness_file'],Path(__file__),Path(__file__).with_name('audit_phase_divergence.py'),*sorted(strict.glob('*.py'))]
    before={str(p):sha(p) for p in paths};output.mkdir(parents=True);started=time.perf_counter();states=[]
    write(output/'execution-start.json',dict(scope=__doc__,source_and_inputs_before=before,optimizer_phase_calls_expected=2,new_full_case_or_MC_calls=0))
    try:
        for name in ('python','matlab'):
            p=np.asarray(contexts[name]['p0']).reshape(3,2).copy();stop={};start=time.perf_counter()
            print('Starting same-native-data fixed power from '+name,flush=True)
            fg=lambda x:mr_phase_value_gradient(data,x,p,mu,limit,True)
            phi,history=rmo_ascent(initial,fg,100000,1e-6,status=stop,
                increment=lambda old,new:mr_increment_v2(data,old,new,p,mu,limit,True))
            value,gradient=fg(phi)
            state=dict(label=name,data=data,p0=p,mu=mu,interferenceLimit=limit,initial_phi=initial.copy(),
                final_phi=phi,value=value,gradient=gradient,status=stop,history=np.asarray(history),elapsed_seconds=time.perf_counter()-start)
            states.append(state)
            savemat(output/('fixed-power-'+name+'-actual-phase.mat'),dict(state=state),do_compression=True,long_field_names=True)
            print(dict(power_from=name,iterations=stop['iterations'],converged=stop['converged'],criterion=float(value),elapsed_seconds=state['elapsed_seconds']),flush=True)
    except BaseException as error:
        write(output/'execution-error.json',dict(type=type(error).__name__,error=str(error),closed_phase_calls=len(states),all_checks_pass=False))
        raise
    after={str(p):sha(p) for p in paths};require(before==after,'Input/provider/control bytes changed during execution')
    report=dict(scope=__doc__,phase_calls=2,original_initial_phase_unchanged=True,common_native_channel_data=True,
        only_fixed_power_changes_between_controls=True,source_inputs_before=before,source_and_inputs_unchanged=True,
        files={('fixed-power-'+s['label']+'-actual-phase.mat'):sha(output/('fixed-power-'+s['label']+'-actual-phase.mat')) for s in states},
        original_caps_and_strict_tolerances_retained=True,elapsed_seconds=time.perf_counter()-started,
        whole_case_curve_values_changed=False,Monte_Carlo_or_convex_solver_calls=0,independent_physics_or_unique_original_cause_proved=False)
    write(output/'execution-summary.json',report)
    return report


def audit(directory,output):
    require(not output.exists(),'Preserve independent phase audit')
    summary=read(directory/'execution-summary.json');paths=[directory/'execution-summary.json',Path(__file__),Path(ref.__file__)]
    paths.extend(directory/name for name in summary['files']);before={str(p):sha(p) for p in paths};lanes={};numbers={}
    states=[]
    for name,h in summary['files'].items():
        require(sha(directory/name)==h,'Actual control endpoint changed')
        states.append(loadmat(directory/name,simplify_cells=True)['state'])
    for digits in (80,100):
        rows=[];values=[]
        with mp.workdps(digits):
            for state in states:
                data=channel_data(state['data'],3,2,16,25)
                v=ref.FixedContext(data,np.asarray(state['final_phi']).reshape(2,25),np.asarray(state['p0']).reshape(3,2),
                    float(state['mu']),np.asarray(state['interferenceLimit']).reshape(-1),True).gradient()
                grad=[z for row in v['complex_gradient'] for z in row]
                err=[abs(ref.scalar(a)-b) for a,b in zip(np.asarray(state['gradient']).reshape(-1),grad)]
                fields=all(e<=ref.real(1e-9)+ref.real(1e-10)*abs(b) for e,b in zip(err,grad))
                fields=fields and abs(ref.real(state['value'])-v['criterion'])<=ref.real(1e-9)+ref.real(1e-10)*abs(v['criterion'])
                stop=v['norm']<ref.real(1e-6)
                rows.append(dict(fixed_power_from=state['label'],criterion=mp.nstr(v['criterion'],105),gradient_norm=mp.nstr(v['norm'],105),
                    maximum_gradient_error=mp.nstr(max(err),105),fields_pass=bool(fields),original_strict_gradient_stop_pass=bool(stop)))
                values.extend([v['criterion'],v['norm'],*grad])
        lanes[str(digits)]=rows;numbers[digits]=values
    with mp.workdps(110):gap=max(abs(a-b) for a,b in zip(numbers[80],numbers[100]))
    report=dict(scope='Independent MP80/100 actual first-phase controls with identical native input data and initial phase; fixed p0 alone varied',
        source_and_inputs_unchanged=before=={str(p):sha(p) for p in paths},source_inputs_sha256=before,
        lanes=lanes,maximum_MP80_MP100_difference=mp.nstr(gap,105),precision_bound='1e-40',
        all_fields_strict_original_stops_and_precision_pass=bool(gap<mp.mpf('1e-40') and all(r['fields_pass'] and r['original_strict_gradient_stop_pass'] for lane in lanes.values() for r in lane)),
        optimizer_or_MC_calls_by_auditor=0,full_case_curve_values_replaced=False,unique_cause_or_global_optimality_proved=False)
    report['all_fields_strict_original_stops_and_precision_pass']=report['all_fields_strict_original_stops_and_precision_pass'] and report['source_and_inputs_unchanged']
    write(output,report);print(report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('execute');q.add_argument('--witness-directory',type=Path,required=True);q.add_argument('--output-dir',type=Path,required=True)
    q=sub.add_parser('audit');q.add_argument('--directory',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='execute':execute(a.witness_directory,a.output_dir)
    elif not audit(a.directory,a.output)['all_fields_strict_original_stops_and_precision_pass']:raise SystemExit(1)
