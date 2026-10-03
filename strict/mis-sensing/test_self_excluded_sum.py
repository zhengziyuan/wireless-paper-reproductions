"""Same complete SINR formula: independent self-exclusion/roundoff regression.

Frozen inputs are our computed failed state, NOT original author experiments.
The high-gain cases independently test true ascent signs as well as numeric
roundoff bounds. Such test bounds NEVER relax Armijo or optimizer thresholds.
"""
from __future__ import annotations
import argparse,json,os
from decimal import localcontext
from pathlib import Path
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(name,'1')
import numpy as np
from engine import Model,self_excluded_sum
from test_stable_increment import decimal_alm,deserialize


def run_checks():
    base=Path(__file__).resolve().parent
    data=json.loads((base/'tests/self_excluded_sum_fixture.json').read_text())
    model=Model(data['model']);c=data['steering_coefficients']
    model.c=np.asarray(c['real'])+1j*np.asarray(c['imag'])
    assert (model.M,model.N,model.U,model.K)==(400,256,25,9)
    z=deserialize(data['base_state']);lam=np.asarray(data['multipliers']);rho=data['penalty']
    checks=[]
    for label,values,wanted in [('positive_interference',np.array([[1e30],[1.],[2.]]),3.),
                                 ('signed_exact_increment',np.array([[1e30],[-1.],[2.]]),1.)]:
        direct=float(self_excluded_sum(values,1)[0,0]);legacy=float(values.sum(axis=0)[0]-values[0,0])
        checks.append(dict(check=label,explicit_excluded_sum=direct,exact_sum=wanted,
                           legacy_total_minus_wanted=legacy,pass_check=direct==wanted and legacy!=wanted))
    with localcontext() as ctx:
        ctx.prec=60;reference_base=decimal_alm(model,z,lam,rho,normalize_circle=True)
        for case in data['cases']:
            trial=deserialize(case['candidate_state'])
            reference=decimal_alm(model,trial,lam,rho,normalize_circle=True)-reference_base
            assert str(reference)==case['reference_decimal60']
            expected=float(reference);value=model.sinr_alm_difference(z,trial,lam,rho,unit_circle=True)
            bound=case['test_only_roundoff_bound'];error=abs(value-expected)
            correct_sign=expected>0 and value>0
            checks.append(dict(check='full_near_stationary_alpha_'+str(case['alpha']),
                               reference_difference_decimal60=str(reference),stable_difference=value,
                               absolute_error=error,test_only_roundoff_bound=bound,
                               legacy_subtraction_difference=case['legacy_subtraction_difference'],
                               canonical_armijo_false_acceptance_prevented=bool(correct_sign),
                               pass_check=bool(error<=bound and correct_sign)))
    report=dict(scope=data['scope'],fixture_kind=data['fixture_kind'],number_of_checks=len(checks),
                all_checks_pass=all(x['pass_check'] for x in checks),checks=checks,
                independent_reference='Decimal60 explicit complex forward sums and exact normalized circle endpoints',
                line_search_acceptance_slack_added=False,optimizer_tolerance_changed=False,
                full_6000_start_figure_completed=False,original_figure_reproduction_certified=False)
    assert report['all_checks_pass'],[x for x in checks if not x['pass_check']]
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    report=run_checks()
    if args.output:
        from run import atomic_json
        atomic_json(args.output,report)
    print(json.dumps(report),flush=True)
