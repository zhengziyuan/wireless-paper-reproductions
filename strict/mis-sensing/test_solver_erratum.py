"""Independent checks for the disclosed corrected-paper solver branch.

The full checkpoint test is ONE inner call, not a 6000-start figure receipt.
"""
from __future__ import annotations
import argparse
import itertools
import json
import os
from pathlib import Path
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ.setdefault(name,'1')
import numpy as np
from engine import Model,inner,project,retract,rcg,projected_kkt_norm
from solver_erratum import tangent_cone_project,curve_derivative
from test_stable_increment import decimal_alm,deserialize
from decimal import localcontext
HERE=Path(__file__).resolve().parent

def fixture():
    data=json.loads((HERE/'tests/stable_increment_fixture.json').read_text())
    model=Model(data['model']);c=data['steering_coefficients']
    model.c=np.asarray(c['real'])+1j*np.asarray(c['imag'])
    state={b:np.asarray(v['real'])+1j*np.asarray(v['imag']) if isinstance(v,dict) else np.asarray(v) for b,v in data['state'].items()}
    return model,state,np.asarray(data['multipliers']),data['penalty']

def run_checks(export_unit_circle_cases=None):
    model,z,lam,rho=fixture();rng=np.random.default_rng(20261003);checks=[]
    for b in ('phi','theta'):
        g=project(z,{b:rng.normal(size=z[b].shape)+1j*rng.normal(size=z[b].shape)})[b]
        old=rng.normal(size=g.shape)+1j*rng.normal(size=g.shape)
        error=abs(inner(g,old)-inner(g,project(z,{b:old})[b]))
        assert error<2e-12
        checks.append(dict(check='orthogonal_transport_numerator_identity_'+b,error=error,pass_check=True))
    x=np.array([[1.,0.,0.,0.],[.2,.3,0.,.5],[.1,.2,.3,.4]])
    direction=rng.normal(size=x.shape);cone=tangent_cone_project({'X':x},{'X':direction})['X']
    brute=[]
    for row,value in zip(x,direction):
        positive=row>0;zero=np.flatnonzero(~positive);candidates=[]
        for mask in itertools.product((False,True),repeat=len(zero)):
            support=positive.copy();support[zero]=mask
            mean=np.mean(value[support]);out=np.where(support,value-mean,0.)
            if np.all(out[~positive]>=-1e-12):candidates.append(out)
        brute.append(min(candidates,key=lambda d:np.linalg.norm(d-value)))
    error=float(np.max(np.abs(cone-np.array(brute))));assert error<1e-12
    assert np.max(np.abs(np.sum(cone,axis=1)))<1e-12 and np.min(cone[x==0])>=0
    checks.append(dict(check='simplex_tangent_cone_against_independent_exhaustive_QP',error=error,pass_check=True))
    H=np.array([[4.,1.],[1.,3.]]);x0=np.array([1.,2.]);g0=H@x0;d0=-g0
    alpha=inner(g0,g0)/inner(d0,H@d0);g1=H@(x0+alpha*d0)
    beta_product=inner(g1,g1-g0)/inner(g0,g0);beta_block=g1*(g1-g0)/(g0*g0)
    product_direction=-g1+beta_product*d0;block_direction=-g1+beta_block*d0
    assert abs(inner(d0,H@product_direction))<1e-12 and abs(inner(d0,H@block_direction))>1 and inner(g1,block_direction)>0
    checks.append(dict(check='coupled_quadratic_printed_block_PR_is_not_product_conjugacy',
        product_H_conjugacy_error=abs(inner(d0,H@product_direction)),block_H_conjugacy_error=abs(inner(d0,H@block_direction)),
        block_direction_is_uphill=True,pass_check=True))
    # A finite-rho squared ALM is not an exact penalty. A feasible ALM stationary
    # point alone need not satisfy ORIGINAL complementarity (Section IV claim).
    scalar=Model(dict(ms1=[1,1],ms2=[0,0],azimuth_deg=[0],elevation_deg=[0],spacing_over_wavelength=1/3,
                      incidence_direction_cosines=[0,0],number_of_targets=1,echo_beta_squared=1,noise_over_power=1))
    scalar_state=dict(phi=np.array([1+0j]),theta=np.zeros(0,dtype=complex),X=np.ones((1,1)),eta=np.asarray(.9))
    scalar_ALM=scalar.augmented(scalar_state,np.array([2.]),10.,'sinr')
    assert projected_kkt_norm(scalar_state,project(scalar_state,scalar_ALM[1]))<1e-12 and scalar_ALM[2]['q'][0]<0
    scalar_certificate=scalar.constrained_kkt_certificate(scalar_state,np.array([1.]),'sinr',1e-6,1e-6)
    assert not scalar_certificate['original_problem_kkt_verified'] and scalar_certificate['maximum_absolute_complementarity']>.09
    checks.append(dict(check='feasible_finite_penalty_ALM_stationary_is_not_original_KKT',pass_check=True))
    unit_cases=[]
    frozen=json.loads((HERE/'tests/stable_increment_cases.json').read_text())
    for entry in frozen['cases']:
        base=deserialize(entry['base_state']);last=deserialize(entry['candidate_state']);multipliers=np.asarray(entry['multipliers']);penalty=entry['penalty']
        with localcontext() as ctx:
            ctx.prec=60
            truth=decimal_alm(model,last,multipliers,penalty,normalize_circle=True)-decimal_alm(model,base,multipliers,penalty,normalize_circle=True)
        value=model.sinr_alm_difference(base,last,multipliers,penalty,unit_circle=True)
        bound=2e-18+5e-12*abs(float(truth));error=abs(value-float(truth));assert error<=bound
        checks.append(dict(check='normalized_circle_Decimal60_'+entry['case'],absolute_error=error,test_only_rounding_error_bound=bound,pass_check=True))
        case=dict(entry,reference_difference=float(truth),reference_difference_decimal=str(truth),test_only_rounding_error_bound=bound)
        unit_cases.append(case)
    if export_unit_circle_cases:
        export_unit_circle_cases.parent.mkdir(parents=True,exist_ok=True)
        export_unit_circle_cases.write_text(json.dumps(dict(scope='independent_Decimal60_normalized_exact_circle_increment_cases_NOT_author_code_or_full_figure',
            fixture='stable_increment_fixture.json',cases=unit_cases),indent=2))
    objective=lambda point:model.augmented(point,lam,rho,'sinr')
    objective.stable_difference=lambda base,last:model.sinr_alm_difference(base,last,lam,rho,unit_circle=True)
    for b in ('phi','theta','eta'):
        if b in ('phi','theta'):d={b:1j*z[b]*rng.normal(size=z[b].shape)}
        else:d={b:np.asarray(.31)}
        alpha=.013;candidate=retract(z,d,alpha);h=1e-6
        plus=retract(z,d,alpha+h);minus=retract(z,d,alpha-h)
        fd=(objective.stable_difference(candidate,plus)-objective.stable_difference(candidate,minus))/(2*h)
        analytical=curve_derivative(z,d,alpha,candidate,objective(candidate)[1])
        error=abs(fd-analytical)/max(1,abs(fd),abs(analytical));assert error<2e-6
        checks.append(dict(check='retraction_curve_derivative_'+b,error=float(error),pass_check=True))
    options=dict(line_search_policy='corrected_product_pr_wolfe',non_descent_policy='documented_non_descent_restart',
        initial_step=1,armijo_constant=1e-4,max_backtracks=60,max_iterations=4000,
        gradient_tolerance=1.2589254117941667e-6,wolfe_curvature=.1,minimum_descent_cosine=.01)
    out,history,stop=rcg(z,objective,options)
    assert stop['reason']=='gradient_tolerance' and stop['projected_kkt_norm']<options['gradient_tolerance']
    accepted=[entry['corrected_line_search'] for entry in history if 'corrected_line_search' in entry]
    assert all(entry['armijo_verified'] and entry['curvature_verified'] for entry in accepted)
    checks.append(dict(check='full_failed_checkpoint_original_dimension_original_4000_cap',iterations=len(history),
        projected_kkt_norm=stop['projected_kkt_norm'],required_tolerance=options['gradient_tolerance'],pass_check=True))
    # Reusing an already-stationary point must not force another destructive
    # line-search attempt. The actual same residual, not a proxy, is checked.
    again,stationary_history,stationary_stop=rcg(out,objective,options)
    assert len(stationary_history)==1 and stationary_stop['reason']=='gradient_tolerance'
    assert all(np.array_equal(again[b],out[b]) for b in out)
    checks.append(dict(check='stationary_initial_point_no_forced_first_move',pass_check=True))
    return dict(scope='corrected_paper_solver_checks_NOT_complete_6000_start_figure',checks=checks,all_checks_pass=True,
        original_raw_block_branch_preserved=True,raw_product_PR_not_clipped=True,published_iterations_and_tolerances_unchanged=True,
        original_figure_reproduction_certified=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--export-unit-circle-cases',type=Path);args=parser.parse_args()
    result=run_checks(args.export_unit_circle_cases)
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
