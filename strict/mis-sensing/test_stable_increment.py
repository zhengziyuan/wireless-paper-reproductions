"""Full-size SINR ALM increment regression against independent Decimal 60.

Saved inputs are from this independent reproduction's failed checkpoint, not
original author code or a completed paper experiment. No optimizer is run.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, localcontext
import json
import os
from pathlib import Path
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ.setdefault(name,'1')
import numpy as np
from engine import Model, project, retract, serialize

HERE=Path(__file__).resolve().parent
FIXTURE=HERE/'tests/stable_increment_fixture.json'


def decimal_alm(model,point,multipliers,penalty,*,normalize_circle=False):
    """Independent forward evaluation: explicit complex sums, no Model.metric.

    Decimal.from_float preserves the exact stored input coefficients. Every
    echo/interference term and positive-part branch is recomputed at 60 digits.
    """
    def val(value):return Decimal.from_float(float(value))
    def comp(value):return (val(np.real(value)),val(np.imag(value)))
    def multiply(first,last):
        return (first[0]*last[0]-first[1]*last[1],first[0]*last[1]+first[1]*last[0])
    with localcontext() as ctx:
        ctx.prec=60
        phi=[comp(value) for value in point['phi']]
        theta=[comp(value) for value in point['theta']]
        if normalize_circle:
            def normalized(value):
                length=(value[0]*value[0]+value[1]*value[1]).sqrt()
                return value[0]/length,value[1]/length
            phi=[normalized(value) for value in phi]
            theta=[normalized(value) for value in theta]
        coefficients=[[comp(value) for value in row] for row in model.c]
        patterns=[]
        for indices in model.indices:
            pattern=list(phi)
            for j,m in enumerate(indices):pattern[m]=multiply(phi[m],theta[j])
            patterns.append(pattern)
        echoes=[]
        for k,coefficient in enumerate(coefficients):
            target=[]
            for pattern in patterns:
                real=Decimal(0);imag=Decimal(0)
                for cm,vm in zip(coefficient,pattern):
                    product=multiply(cm,vm);real+=product[0];imag+=product[1]
                power=real*real+imag*imag
                target.append(val(model.beta[k])*power*power)
            echoes.append(target)
        noise=val(model.config['noise_over_power'])
        eta=val(point['eta']);rho=val(penalty);total=Decimal(0)
        for k in range(model.targets):
            scheduled=Decimal(0)
            for u in range(model.U):
                denominator=sum(echoes[j][u] for j in range(model.K) if j!=k)+noise
                scheduled+=val(point['X'][k,u])*echoes[k][u]/denominator
            chi=max(Decimal(0),val(multipliers[k])+rho*(eta-scheduled))
            total+=chi*chi
        return -eta+total/(2*rho)


def deserialize(raw):
    return {name:np.asarray(value['real'])+1j*np.asarray(value['imag']) if isinstance(value,dict) else np.asarray(value)
            for name,value in raw.items()}


def stable_increment_checks(require_naive_wrong_sign=False,capture_cases=False):
    fixture=json.loads(FIXTURE.read_text(encoding='utf-8'))
    model=Model(fixture['model'])
    coefficients=fixture['steering_coefficients']
    # Test-only exact coefficient freeze: tiny math-library/BLAS differences
    # must not change the reference domain for sub-1e-18 increment checks.
    model.c=np.asarray(coefficients['real'])+1j*np.asarray(coefficients['imag'])
    assert (model.M,model.N,model.U,model.K)==(400,256,25,9)
    state=deserialize(fixture['state']);lam=np.asarray(fixture['multipliers']);rho=fixture['penalty']
    rows=[];cases=[]
    def check(label,base,candidate,multipliers,penalty):
        with localcontext() as ctx:
            ctx.prec=60
            reference=decimal_alm(model,candidate,multipliers,penalty)-decimal_alm(model,base,multipliers,penalty)
        increment=model.sinr_alm_difference(base,candidate,multipliers,penalty)
        naive=model.augmented(candidate,np.asarray(multipliers),penalty,'sinr')[0]-model.augmented(base,np.asarray(multipliers),penalty,'sinr')[0]
        expected=float(reference)
        # This tests the independent evaluation's rounding error. It is NEVER
        # used as Armijo slack, an optimizer tolerance or a convergence gate.
        bound=2e-18+abs(expected)*5e-12
        error=abs(increment-expected)
        record={'case':label,'reference_difference_decimal_60':str(reference),
                'stable_difference':increment,'naive_difference':naive,'absolute_error':error,
                'test_only_rounding_error_bound':bound,'increment_identity_pass':bool(error<=bound)}
        rows.append(record)
        assert record['increment_identity_pass'],record
        if capture_cases:
            cases.append({'case':label,'base_state':serialize(base),'candidate_state':serialize(candidate),
                          'multipliers':np.asarray(multipliers).tolist(),'penalty':float(penalty),
                          'reference_difference_decimal_60':str(reference),'reference_difference':expected,
                          'test_only_rounding_error_bound':bound})
        return record

    gradient=project(state,model.augmented(state,lam,rho,'sinr')[1])
    for block,halvings in (('phi',10),('theta',9),('eta',6)):
        candidate=retract(state,{block:-gradient[block]},.5**halvings)
        record=check('saved_failed_checkpoint_'+block,state,candidate,lam,rho)
        assert float(record['reference_difference_decimal_60'])<0 and record['stable_difference']<0
        if block in ('phi','theta'):
            record['naive_wrong_sign_observed']=bool(record['naive_difference']>0)
            # The sign of floating-point evaluation noise is platform/BLAS
            # dependent. Request the local original counterexample assertions
            # explicitly; the Decimal identity is mandatory on every platform.
            if require_naive_wrong_sign:assert record['naive_wrong_sign_observed'],record

    rng=np.random.default_rng(4002562509)
    base={'phi':np.exp(1j*rng.uniform(-np.pi,np.pi,model.M)),
          'theta':np.exp(1j*rng.uniform(-np.pi,np.pi,model.N)),
          'X':rng.uniform(.1,1,(model.targets,model.U)),'eta':np.asarray(.4)}
    base['X']/=np.sum(base['X'],axis=1,keepdims=True)
    direction={'phi':1j*base['phi']*rng.normal(size=model.M),
               'theta':1j*base['theta']*rng.normal(size=model.N),
               'X':rng.normal(size=base['X'].shape),'eta':np.asarray(.1)}
    direction['X']-=np.mean(direction['X'],axis=1,keepdims=True)
    for alpha in (1e-1,1e-3,1e-5,1e-7):
        candidate=retract(base,direction,alpha)
        check('full_random_simultaneous_alpha_'+str(alpha),base,candidate,np.linspace(.1,.9,model.targets),1.7)

    rates=np.sum(base['X']*model.metric(base,'sinr'),axis=1)
    cross_base={name:np.array(value,copy=True) for name,value in base.items()}
    cross_base['eta']=np.asarray(float(np.min(rates))-.4)
    targets=np.array([-.3,-.1,.1,.3,0.,-.2,.2,-.15,.15]);penalty=1.7
    cross_lam=penalty*(rates-float(cross_base['eta'])-targets)
    assert np.all(cross_lam>=0)
    for movement in (-.2,.2,1e-8,-1e-8):
        candidate={name:np.array(value,copy=True) for name,value in cross_base.items()}
        candidate['eta']+=movement
        record=check('eta_only_active_crossing_'+str(movement),cross_base,candidate,cross_lam,penalty)
        raw=cross_lam+penalty*(float(cross_base['eta'])-rates)
        record['old_active_count']=int(np.count_nonzero(raw>0))
        record['new_active_count']=int(np.count_nonzero(raw+penalty*movement>0))
    assert len(rows)==11
    report={'scope':'full_dimension_400_256_25_9_increment_identity_test_not_paper_figure',
            'method_under_test':'engine.Model.sinr_alm_difference_plain_stored_endpoints',
            'precision_reference':'independent_Decimal_60_explicit_complex_forward_model',
            'fixture_kind':fixture['fixture_kind'],'number_of_checks':len(rows),
            'all_checks_pass':all(row['increment_identity_pass'] for row in rows),
            'naive_wrong_sign_assertions_required':require_naive_wrong_sign,
            'line_search_acceptance_slack_added':False,'optimizer_stop_threshold_changed':False,
            'original_figure_reproduction_certified':False,'checks':rows}
    if capture_cases:
        report['export_cases']={'fixture_kind':fixture['fixture_kind'],
                               'scope':'frozen_cross_language_exact_increment_tests_not_paper_figure',
                               'steering_coefficients_from':'stable_increment_fixture.json',
                               'number_of_cases':len(cases),'cases':cases}
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--require-naive-wrong-sign',action='store_true',
                        help='Also assert both original local floating-point sign-flip counterexamples')
    parser.add_argument('--export-cases',type=Path,help='Export generated exact trial states for independent cross-language checks')
    args=parser.parse_args()
    report=stable_increment_checks(args.require_naive_wrong_sign,capture_cases=args.export_cases is not None)
    export=report.pop('export_cases',None)
    if args.export_cases:
        args.export_cases.parent.mkdir(parents=True,exist_ok=True)
        args.export_cases.write_text(json.dumps(export,indent=2),encoding='utf-8')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
