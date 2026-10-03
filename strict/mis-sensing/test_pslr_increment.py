"""Actual full-grid PSLR stable-difference tests; not a paper figure run.

60-digit scalar soft minima are evaluated independently from the production
log1p/expm1 identity. Test bounds never enter the optimizer acceptance rule.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, localcontext
import json
import os
from pathlib import Path
import time
for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ.setdefault(name,"1")
import numpy as np
from engine import inner, project, retract, softmin_increment
from run import PortableRandom, initialize, make_model

HERE=Path(__file__).resolve().parent


def independent_decimal(old,change,mu):
    with localcontext() as context:
        context.prec=60
        parameter=Decimal.from_float(float(mu))
        first=[Decimal.from_float(float(x)) for x in old]
        last=[x+Decimal.from_float(float(y)) for x,y in zip(first,change)]
        def evaluate(values):
            minimum=min(values)
            total=sum(((-(x-minimum)/parameter).exp() for x in values),Decimal(0))
            return minimum-parameter*total.ln()
        return str(evaluate(last)-evaluate(first))


def make_cases():
    rng=np.random.default_rng(9041);old=1+rng.random(3600)*10;cases=[]
    for mu in (10.,.001220703125):
        for name,first,delta in (
            ("tiny_all",old,rng.normal(size=3600)*1e-13),
            ("large_active_change",old,rng.normal(size=3600)*.6),
            ("huge_irrelevant_tiny_active",np.r_[1.,np.full(3599,1e12)],np.r_[-1e-14,np.full(3599,1e10)]),
            ("old_underflow_new_active",np.r_[1.,1e6,np.full(3598,1e8)],np.r_[.4,-1e6+.2,np.zeros(3598)]),
            ("large_softmin_increase",old,np.full(3600,10000.))):
            truth=independent_decimal(first,delta,mu)
            cases.append(dict(name=f"{name}_mu_{mu}",mu=mu,old=first.tolist(),change=delta.tolist(),new=(first+delta).tolist(),
                decimal60=truth,reference_difference=float(truth),test_only_bound=2e-16+3e-12*abs(float(truth))))
    return dict(scope="Frozen independent 3600-opponent LSE identity cases; no author data or private source",precision=60,cases=cases)


def full_model_checks(settings):
    model=make_model(dict(ms1=[20,20],ms2=[16,16],Kphi=3,Ktheta=3),settings,pslr=True)
    state=initialize(model,settings,PortableRandom(1));state["eta"]=np.asarray(2.)
    lam=np.linspace(.1,.9,model.targets);rho=1.2;checks=[]
    assert (model.M,model.N,model.K,model.U)==(400,256,3609,25)
    for mu in (10.,.001220703125):
        model.config["pslr_mu"]=mu
        f,eu,_=model.augmented(state,lam,rho,"pslr");g=project(state,eu)
        for block in ("phi","theta","X","eta"):
            direction={block:-g[block]/max(1.,np.sqrt(inner(g[block],g[block])))}
            for alpha in (1e-2,1e-6,1e-8):
                trial=retract(state,direction,alpha)
                stable=model.pslr_alm_difference(state,trial,lam,rho,unit_circle=True)
                naive=model.augmented(trial,lam,rho,"pslr")[0]-f
                predicted=alpha*inner(g[block],direction[block])
                bound=1e-9*max(1.,abs(f),abs(naive))
                relative=abs(stable/predicted-1) if predicted else 0.
                checks.append(dict(name=f"full_ALM_{block}_mu_{mu}_alpha_{alpha}",stable_difference=stable,direct_difference=naive,
                    absolute_identity_error=abs(stable-naive),test_only_bound=bound,linear_gradient_relative_error=relative,
                    passed=bool(abs(stable-naive)<=bound and (alpha>1e-6 or relative<2e-6))))
            # Independent symmetric derivative, with no close-objective subtraction.
            step=1e-6
            plus=retract(state,direction,step);minus=retract(state,direction,-step)
            fd=(model.pslr_alm_difference(state,plus,lam,rho,unit_circle=True)-model.pslr_alm_difference(state,minus,lam,rho,unit_circle=True))/(2*step)
            analytic=inner(g[block],direction[block]);error=abs(fd-analytic)/max(1.,abs(fd),abs(analytic))
            checks.append(dict(name=f"full_central_derivative_{block}_mu_{mu}",finite_difference=fd,analytic=analytic,relative_error=error,test_only_bound=2e-6,passed=bool(error<2e-6)))
        # Actual complete forward bundle: one field evaluation per ALM call.
        original_fields=model.fields;calls=0
        def counted(point):
            nonlocal calls
            calls+=1
            return original_fields(point)
        model.fields=counted
        model.augmented(state,lam,rho,"pslr")
        one_forward=calls==1
        prepared=original_fields(state);trial=retract(state,{"eta":np.asarray(.1)},1.)
        calls=0
        cached=model.pslr_alm_difference(state,trial,lam,rho,unit_circle=True,prepared_base=prepared)
        no_redundant_forward=calls==0
        uncached=model.pslr_alm_difference(state,trial,lam,rho,unit_circle=True)
        model.fields=original_fields
        checks.append(dict(name=f"full_explicit_forward_reuse_mu_{mu}",ALM_exactly_one_forward=one_forward,
            prepared_increment_no_redundant_forward=no_redundant_forward,cached_uncached_identical=bool(cached==uncached),
            passed=bool(one_forward and no_redundant_forward and cached==uncached)))
    # Original manuscript's fixed-epsilon limit is not the unregularized ratio.
    regularized=float(softmin_increment(np.array([[.5]]),np.array([[0.]]),np.array([[.5]]),1e-9)[0])+.5
    checks.append(dict(name="fixed_epsilon_softmin_limit_not_original_PSLR",Sk=1.,Sj=1.,epsilon=1.,finite_epsilon_mu_limit=regularized,
        original_unregularized_ratio=1.,passed=bool(regularized==.5 and regularized!=1.)))
    return checks


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    parser.add_argument("--export-lse-cases",type=Path)
    args=parser.parse_args();start=time.time()
    if args.export_lse_cases:
        inputs=make_cases();args.export_lse_cases.parent.mkdir(parents=True,exist_ok=True)
        args.export_lse_cases.write_text(json.dumps(inputs),encoding="utf-8")
    else:
        inputs=json.loads((HERE/"tests/pslr_lse_increment_cases.json").read_text())
    checks=[]
    for case in inputs["cases"]:
        value=float(softmin_increment(np.asarray(case["old"])[:,None],np.asarray(case["change"])[:,None],np.asarray(case["new"])[:,None],case["mu"])[0])
        error=abs(value-case["reference_difference"])
        checks.append(dict(name=case["name"],opponents=3600,value=value,reference_decimal60=case["decimal60"],absolute_error=error,
            test_only_bound=case["test_only_bound"],passed=bool(error<=case["test_only_bound"])))
    settings=json.loads((HERE/"settings_corrected.json").read_text());checks+=full_model_checks(settings)
    result=dict(scope="Full M400 N256 K3609 U25 PSLR increment/gradient identities, NOT solver convergence/6000 starts/paper figure",checks=checks,
        all_checks_pass=all(x["passed"] for x in checks),line_search_acceptance_slack_added=False,optimizer_stop_threshold_changed=False,
        original_figure_reproduction_certified=False,seconds=time.time()-start)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))
    if not result["all_checks_pass"]:raise SystemExit(1)

if __name__=="__main__":main()
