"""Optional Eq.69 derivative/curvature diagnostics; no production optimizer.

This module never changes Algorithm 1, its Eq.31 curvature, or correlated-ZF.
It uses the full N6/M5 component fixture, not a reduced paper simulation.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.special import j0,j1,jv
from core import los,spatial_covariance,correlated_mrt
from run import scenario


def coordinate_features(t,c,antenna):
    """Value, x-gradient and x-Hessian for q_m, tr(S^2), and LoS Gram powers."""
    wave=2*np.pi/c["wavelength"];dirs=np.asarray(c["directions"]);h=los(t,c)
    n,m=h.shape;s=spatial_covariance(t,c)
    q=np.real(np.sum(h.conj()*(s@h),axis=0));trace=float(np.trace(s@s))
    gram=abs(h.conj().T@h)**2
    gq=np.zeros((m,2));hq=np.zeros((m,2,2));gt=np.zeros(2);ht=np.zeros((2,2))
    gg=np.zeros((m,m,2));hg=np.zeros((m,m,2,2))
    for index in range(n):
        if index==antenna:continue
        delta=t[antenna]-t[index];r=np.linalg.norm(delta);z=wave*r;value=j0(z)
        if r==0:
            gs=np.zeros(2);hs=-wave**2/2*np.eye(2)
        else:
            unit=delta/r;outer=np.outer(unit,unit)
            gs=-wave*j1(z)*unit
            hs=-wave**2*(j0(z)-jv(2,z))/2*outer-wave*j1(z)/r*(np.eye(2)-outer)
        gt+=4*value*gs;ht+=4*(np.outer(gs,gs)+value*hs)
        for u in range(m):
            a=wave*dirs[u];phase=a@delta;co,si=np.cos(phase),np.sin(phase)
            gq[u]+=2*(gs*co-value*si*a)
            hq[u]+=2*(hs*co-(np.outer(gs,a)+np.outer(a,gs))*si-value*co*np.outer(a,a))
            for v in range(m):
                a=wave*(dirs[u]-dirs[v]);phase=a@delta
                gg[u,v]+=-2*np.sin(phase)*a
                hg[u,v]+=-2*np.cos(phase)*np.outer(a,a)
    return q,trace,gram,gq,hq,gt,ht,gg,hg


def derivatives(t,c,antenna):
    n,m=len(t),len(c["beta"]);beta=np.asarray(c["beta"]);kap=np.asarray(c["rician"])
    q,trace,gram,gq,hq,gt,ht,gg,hg=coordinate_features(t,c,antenna)
    a=beta**2*(n*n+(2*kap*q+trace)/(kap+1)**2)
    ga=beta[:,None]**2*(2*kap[:,None]*gq+gt)/(kap[:,None]+1)**2
    ha=beta[:,None,None]**2*(2*kap[:,None,None]*hq+ht)/(kap[:,None,None]+1)**2
    d=np.asarray(c["noise"])*n*beta.sum()/c["power"];gd=np.zeros((m,2));hd=np.zeros((m,2,2))
    for u in range(m):
        for v in range(m):
            if u==v:continue
            weight=beta[u]*beta[v]/((kap[u]+1)*(kap[v]+1))
            d[u]+=weight*(kap[u]*kap[v]*gram[u,v]+kap[u]*q[u]+kap[v]*q[v]+trace)
            gd[u]+=weight*(kap[u]*kap[v]*gg[u,v]+kap[u]*gq[u]+kap[v]*gq[v]+gt)
            hd[u]+=weight*(kap[u]*kap[v]*hg[u,v]+kap[u]*hq[u]+kap[v]*hq[v]+ht)
    gradient=np.sum((gd+ga)/(d+a)[:,None]-gd/d[:,None],axis=0)/np.log(2)
    hessian=np.zeros((2,2))
    for u in range(m):
        total=gd[u]+ga[u]
        hessian+=(hd[u]+ha[u])/(d[u]+a[u])-np.outer(total,total)/(d[u]+a[u])**2-hd[u]/d[u]+np.outer(gd[u],gd[u])/d[u]**2
    return float(np.log2(1+a/d).sum()),gradient,hessian/np.log(2)


def global_curvature(c,n):
    """Proved global Hessian-norm bound, not the original iid Eq.31 bound."""
    dirs=np.asarray(c["directions"]);beta=np.asarray(c["beta"]);kap=np.asarray(c["rician"])
    wave=2*np.pi/c["wavelength"];m=len(beta)
    gq=2*(n-1)*wave*(1+np.linalg.norm(dirs,axis=1))
    hq=2*(n-1)*wave**2*(1+np.linalg.norm(dirs,axis=1))**2
    gt=4*(n-1)*wave;ht=8*(n-1)*wave**2
    ga=beta**2*(2*kap*gq+gt)/(kap+1)**2;ha=beta**2*(2*kap*hq+ht)/(kap+1)**2
    gd=np.zeros(m);hd=np.zeros(m)
    for u in range(m):
        for v in range(m):
            if u==v:continue
            difference=np.linalg.norm(dirs[u]-dirs[v]);gg=2*(n-1)*wave*difference;hg=2*(n-1)*wave**2*difference**2
            weight=beta[u]*beta[v]/((kap[u]+1)*(kap[v]+1))
            gd[u]+=weight*(kap[u]*kap[v]*gg+kap[u]*gq[u]+kap[v]*gq[v]+gt)
            hd[u]+=weight*(kap[u]*kap[v]*hg+kap[u]*hq[u]+kap[v]*hq[v]+ht)
    amin=beta**2*n*n;dmin=np.asarray(c["noise"])*n*beta.sum()/c["power"]
    return float(np.sum((hd+ha)/(dmin+amin)+(gd+ga)**2/(dmin+amin)**2+hd/dmin+gd**2/dmin**2)/np.log(2))


def run_tests():
    folder=Path(__file__).parent;config=json.loads((folder/"full_config.json").read_text());fixture=json.loads((folder/"fixture.json").read_text())
    c,t=scenario(config,6,5,fixture["rician_linear"],geometry=fixture);t=np.asarray(fixture["positions"],dtype=float)
    gradient_error=hessian_error=value_error=0.;eps=1e-6;hesseps=1e-5
    for antenna in range(len(t)):
        value,gradient,hessian=derivatives(t,c,antenna);value_error=max(value_error,abs(value-correlated_mrt(t,c)))
        ng=np.zeros(2);nh=np.zeros((2,2))
        for d in range(2):
            plus,minus=t.copy(),t.copy();plus[antenna,d]+=eps;minus[antenna,d]-=eps
            ng[d]=(correlated_mrt(plus,c)-correlated_mrt(minus,c))/(2*eps)
            plus,minus=t.copy(),t.copy();plus[antenna,d]+=hesseps;minus[antenna,d]-=hesseps
            nh[:,d]=(derivatives(plus,c,antenna)[1]-derivatives(minus,c,antenna)[1])/(2*hesseps)
        gradient_error=max(gradient_error,float(np.max(abs(ng-gradient))));hessian_error=max(hessian_error,float(np.max(abs(nh-hessian))))
    curvature=global_curvature(c,len(t));value,gradient,_=derivatives(t,c,0)
    min_minorant_gap=np.inf;maximum_hessian_norm=0.
    # Deterministic diagnostic points, not a paper Monte Carlo simulation bank.
    for x in np.linspace(c["region_lower"][0],c["region_upper"][0],9):
        for y in np.linspace(c["region_lower"][1],c["region_upper"][1],9):
            trial=t.copy();trial[0]=[x,y];actual,_,hessian=derivatives(trial,c,0);delta=trial[0]-t[0]
            min_minorant_gap=min(min_minorant_gap,actual-(value+gradient@delta-curvature/2*(delta@delta)))
            maximum_hessian_norm=max(maximum_hessian_norm,float(np.max(abs(np.linalg.eigvalsh(hessian)))))
    coincident=t.copy();coincident[0]=coincident[1]
    _,cg,ch=derivatives(coincident,c,0)
    s=spatial_covariance(t,c);n,m=len(t),len(c["beta"]);trace_s2=float(np.trace(s@s))
    generalized_second=m*float(np.trace(s))**2+m*m*trace_s2
    standard_second=m*n*n+m*m*n
    checks={"gradient_max_error":gradient_error,"gradient_pass":gradient_error<1e-6,
        "hessian_max_error":hessian_error,"hessian_pass":hessian_error<1e-4,"production_Eq69_value_error":value_error,
        "global_curvature_bound":curvature,"max_tested_hessian_spectral_norm":maximum_hessian_norm,
        "curvature_test_points_pass":maximum_hessian_norm<=curvature,"minimum_tested_minorant_gap":float(min_minorant_gap),
        "minorant_test_points_pass":bool(min_minorant_gap>=-1e-8),"coincident_limit_finite":bool(np.all(np.isfinite(cg)) and np.all(np.isfinite(ch))),
        "generalized_Gram_second_moment":generalized_second,"standard_Wishart_second_moment":standard_second,
        "Wishart_second_moment_difference":generalized_second-standard_second,"Wishart_dimension_only_fix_counterexample":generalized_second>standard_second+1e-8}
    assert all(checks[k] for k in ["gradient_pass","hessian_pass","curvature_test_points_pass","minorant_test_points_pass","coincident_limit_finite","Wishart_dimension_only_fix_counterexample"])
    return {"paper_id":"two-timescale-ma","mode":"optional_derivative_component_test_not_optimization_or_full_figure",
        "source_equations":["68","69","71","72","74"],"new_derived_curvature_not_printed_algorithm":True,
        "production_optimizer_modified":False,"full_N":n,"full_M":m,"checks":checks,
        "test_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path);args=parser.parse_args();result=run_tests()
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,allow_nan=False))
