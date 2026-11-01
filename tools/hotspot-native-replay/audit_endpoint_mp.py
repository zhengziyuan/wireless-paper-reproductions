"""All243 saved native final metrics at independent MP80 and MP100.

Uses the unchanged previously prepared independent Gaussian moment formulas.
No generator, optimizer, convex solver or production engine is called here.
The pre-existing full18 field policy is absolute1e-9 plus relative1e-10;
original physical and solver tolerances are unchanged. The stricter float64
absolute-only audit and its 22 discrepancies remain separate saved evidence.
"""
import argparse
import json
from pathlib import Path
import time

import mpmath
import numpy as np

from audit_saved_native import read,sha,decode,decode_context,write
import independent_statistics_mp as F


def audit(bank,contexts,output):
    if output.exists():raise ValueError('Use a fresh directory; preserve previous evidence')
    entries=read(contexts/'index.json')['cases']
    if len(entries)!=18 or {(r['U'],r['beta_db']) for r in entries}!={(u,b) for u in range(1,7) for b in (0,10,20)}:
        raise ValueError('Complete original 18-case population required')
    output.mkdir(parents=True);began=time.perf_counter();rows=[];case_records=[]
    formula_sha=sha(Path(F.__file__))
    for entry in entries:
        context=read(contexts/entry['context_file']);path=bank/entry['result_filename']
        if sha(path)!=context['result_sha256']:raise ValueError('Changed native result')
        case=read(path)['cases'][0];x={k:decode_context(v) for k,v in context['mean_inputs'].items()}
        for key in ('direct_variance','matrix_variance','ground_variance','nhu_variance'):
            if np.max(abs(x[key].imag))!=0 or np.min(x[key].real)<0:raise ValueError('Invalid physical variance')
            x[key]=x[key].real
        lanes={};raws=[]
        for precision in (80,100):
            mp=mpmath.mp.clone();mp.dps=precision
            lanes[precision]=(mp,F.input_matrices(mp,x))
        for scheme in ('NoRIS','TwoStage','AO'):
            starts=case['schemes'][scheme]['all_start_records']
            if [r['start_id'] for r in starts]!=list(range(entry['U']+1)):raise ValueError('Missing required start')
            for record in starts:
                state=record['final_state'];phi_np=decode(state['phi']).reshape(-1);W_np=decode(state['W'])
                if W_np.shape!=(16,16) or phi_np.shape!=(25,):raise ValueError('Reduced/invalid final state')
                values={};checks={};errors={}
                for precision,(mp,mx) in lanes.items():
                    phi=[F.number(mp,z) for z in phi_np];W=F.matrix(mp,W_np)
                    Q,Psi,_,_=F.moments(mp,mx,phi,state['no_ris'])
                    e=F.evaluate(mp,Q,Psi,W,F.number(mp,float(context['noise'])))
                    values[precision]=e
                    actual=record['evaluation'];pairs=[('rate',e['hu_sum_rate'],actual['hu_sum_rate']),('power',e['power'],actual['total_power'])]
                    pairs += [(f'sinr{j}',value,source) for j,(value,source) in enumerate(zip(e['sinr'],np.asarray(actual['sinr']).reshape(-1)))]
                    error=[];ratios=[]
                    for name,value,source in pairs:
                        recorded=F.number(mp,float(source));delta=abs(value-recorded)
                        allowance=mp.mpf('1e-9')+mp.mpf('1e-10')*max(abs(value),abs(recorded))
                        error.append(delta);ratios.append(delta/allowance)
                    target=mp.power(10,-mp.mpf(3)/10)
                    physical=(e['power']<=F.number(mp,float(context['power']))*(1+mp.mpf('1e-5'))
                              and min(e['sinr'][entry['U']:])-target>=-mp.mpf('1e-5'))
                    checks[str(precision)]=dict(all_fields_match_preexisting_policy=max(ratios)<=1,original_power_and_QoS_gate=bool(physical))
                    errors[str(precision)]=dict(maximum_absolute_error=mp.nstr(max(error),50),maximum_fraction_of_field_allowance=mp.nstr(max(ratios),40))
                mp=lanes[100][0]
                a,b=values[80],values[100]
                # Use each MP80 value's full stored digits, not its default
                # short string formatting, for the independent precision test.
                cross=max([abs(mp.mpf(lanes[80][0].nstr(a[k],82))-b[k]) for k in ('hu_sum_rate','power')]
                          +[abs(mp.mpf(lanes[80][0].nstr(p,82))-q) for p,q in zip(a['sinr'],b['sinr'])])
                cross_pass=cross<=mp.mpf('1e-40')
                passed=cross_pass and all(all(c.values()) for c in checks.values())
                row=dict(U=entry['U'],beta_db=entry['beta_db'],scheme=scheme,start_id=record['start_id'],
                         passed=bool(passed),checks=checks,errors=errors,cross_precision_maximum_absolute_difference=mp.nstr(cross,50),
                         cross_precision_1e_minus40_pass=bool(cross_pass))
                rows.append(row);raws.append(row)
                write(output/'progress.json',dict(cases_completed=len(case_records),starts_checked=len(rows),failed_starts=sum(not r['passed'] for r in rows)))
        result=dict(U=entry['U'],beta_db=entry['beta_db'],starts=len(raws),failed_starts=sum(not r['passed'] for r in raws),records=raws)
        case_records.append(result);write(output/f"U{entry['U']}-beta{entry['beta_db']}.json",result)
        print(json.dumps({k:result[k] for k in ('U','beta_db','starts','failed_starts')}),flush=True)
    if len(rows)!=243:raise ValueError('Incomplete original population')
    if sha(Path(F.__file__))!=formula_sha:raise ValueError('Independent formulas changed')
    summary=dict(scope='all18_all243_native_saved_final_metric_independent_MP80_MP100',cases_checked=18,starts_checked=243,
                 failed_starts=sum(not r['passed'] for r in rows),all_checked_final_metrics_pass=all(r['passed'] for r in rows),
                 field_absolute_tolerance='1e-9',field_relative_tolerance='1e-10',cross_precision_tolerance='1e-40',
                 original_power_and_NHU_tolerance='1e-5',independent_formula_sha256=formula_sha,mpmath_version=mpmath.__version__,
                 optimizers_or_generators_called=0,full_inner_trajectory_replay=False,full54000_MC_replay=False,
                 historical_source_reference_agreement=False,full_reproduction_pass=False,elapsed_seconds=time.perf_counter()-began)
    write(output/'summary.json',summary);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bank',type=Path,required=True)
    p.add_argument('--contexts',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();result=audit(a.bank,a.contexts,a.output_dir);print(json.dumps(result))
    raise SystemExit(0 if result['all_checked_final_metrics_pass'] else 1)
