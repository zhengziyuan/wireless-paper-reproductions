"""Explicit corrected-paper RCG branch on the SAME MIS objective and scene.

The printed independent block-PR branch remains available in engine.py. This
branch uses one RAW Polak--Ribiere coefficient in the product inner product,
closed-simplex tangent-cone feasibility, active-face restarts, and a declared
curvature-checked line search. It is not PR+, Newton, BB, or a model surrogate.
"""
from __future__ import annotations
import numpy as np
from engine import inner, norm, project, retract, projected_kkt_norm, objective_increment
from same_cone_projection import project_rows


def tangent_cone_project(z,value):
    """Euclidean projection onto circle tangents and the closed-simplex cone.

    Positive simplex coordinates are free to decrease; zero coordinates may
    only increase. The scalar row threshold enforces the zero row-sum exactly.
    Interior rows reduce to the printed row-mean tangent projection.
    """
    out=project(z,value)
    if "X" not in value:
        return out
    # Same Euclidean cone: finite sorted threshold, exact uncertain-row fallback.
    # The old floating active-set loop could alternate membership at a raw tie.
    out["X"]=project_rows(z["X"],np.asarray(value["X"]))
    return out


def curve_derivative(z,d,alpha,candidate,euclidean_gradient):
    """d/dalpha L(Retr_z(alpha*d)), including normalization and active faces."""
    result=0.
    for b in d:
        if b in ("phi","theta"):
            denominator=np.abs(z[b]+alpha*d[b])
            velocity=(d[b]-candidate[b]*np.real(np.conj(candidate[b])*d[b]))/denominator
        elif b=="X":
            active=candidate[b]>0
            count=np.sum(active,axis=1,keepdims=True)
            mean=np.sum(np.where(active,d[b],0),axis=1,keepdims=True)/count
            velocity=np.where(active,d[b]-mean,0)
        else:
            velocity=d[b]
        result+=inner(euclidean_gradient[b],velocity)
    return result


def product_line_search(z,g,d,evaluate,f,options,initial=1.):
    """Canonical Armijo plus strong curvature on the original retraction curve.

    Published backtracking constants are absent. Bracketing and safeguarded
    derivative interpolation are explicit corrected-branch numerical choices.
    The maximum line evaluations, objective, tolerance and RCG cap are unchanged.
    """
    slope0=sum(inner(g[b],d[b]) for b in d)
    if not np.isfinite(slope0) or slope0>=0:
        return z,0.,{"reason":"non_descent_curve","evaluations":0}
    c1=options["armijo_constant"]
    c2=options.get("wolfe_curvature",.1)
    if not (0<c1<c2<1):
        raise ValueError("Corrected line search requires 0 < Armijo < curvature < 1")
    safeguard_upper=options.get("interpolation_safeguard_upper",.5)
    if not (.1<safeguard_upper<1):
        raise ValueError("Interpolation upper safeguard must lie between .1 and 1")
    alpha=float(initial);lo=0.;hi=None;lo_slope=slope0;hi_slope=None
    for ls in range(options["max_backtracks"]):
        candidate=retract(z,d,alpha)
        predicted=alpha*slope0
        change=objective_increment(evaluate,z,candidate,f)
        eg=evaluate(candidate)[1]
        slope=curve_derivative(z,d,alpha,candidate,eg)
        armijo=np.isfinite(change) and change<=c1*predicted
        curvature=np.isfinite(slope) and abs(slope)<=c2*abs(slope0)
        if armijo and curvature:
            return candidate,alpha,{"reason":None,"evaluations":ls+1,
                "objective_increment":float(change),"armijo_bound":float(c1*predicted),
                "initial_curve_slope":float(slope0),"accepted_curve_slope":float(slope),
                "curvature_ratio":float(abs(slope/slope0)),"armijo_verified":True,"curvature_verified":True,
                "interpolation_safeguard_upper":float(safeguard_upper)}
        if not armijo or not np.isfinite(slope) or slope>=0:
            hi=alpha;hi_slope=slope
        else:
            lo=alpha;lo_slope=slope
        if hi is None:
            alpha*=2
        else:
            secant=lo-lo_slope*(hi-lo)/(hi_slope-lo_slope) if np.isfinite(hi_slope) and hi_slope!=lo_slope else (hi+lo)/2
            alpha=float(np.clip(secant,lo+.1*(hi-lo),lo+safeguard_upper*(hi-lo)))
    return z,alpha,{"reason":"corrected_curve_search_exhausted","evaluations":options["max_backtracks"],
                  "interpolation_safeguard_upper":float(safeguard_upper)}


def corrected_product_rcg(z,evaluate,options):
    """A distinct, disclosed corrected-paper branch; RAW PR is never clipped."""
    oldg=oldd=None;oldface=None;history=[];reason="iteration_cap"
    for iteration in range(options["max_iterations"]):
        f,eg,_=evaluate(z)
        g=project(z,eg)
        kkt=float(projected_kkt_norm(z,g))
        entry={"iteration":iteration,"objective":float(f),"gradient_norm":float(norm(g)),"projected_kkt_norm":kkt}
        history.append(entry)
        # A stationary supplied initial point is already a valid inner answer.
        # Do not force an unnecessary first move that can only introduce error.
        if kkt<options["gradient_tolerance"]:
            reason="gradient_tolerance"
            break
        pg={b:-v for b,v in tangent_cone_project(z,{b:-v for b,v in eg.items()}).items()}
        face=z["X"]>0
        beta=0.;restart=[]
        if oldg is not None and np.array_equal(face,oldface):
            transported_gradient=project(z,oldg)
            denominator=sum(inner(oldg[b],oldg[b]) for b in pg)
            beta=sum(inner(pg[b],pg[b]-transported_gradient[b]) for b in pg)/denominator if denominator>0 else 0.
            transported_direction=project(z,oldd)
            raw_d={b:-pg[b]+beta*transported_direction[b] for b in pg}
        else:
            raw_d={b:-v for b,v in pg.items()}
            if oldg is not None:restart.append("simplex_active_face_changed")
        raw_slope=sum(inner(g[b],raw_d[b]) for b in g)
        d=tangent_cone_project(z,raw_d)
        slope=sum(inner(g[b],d[b]) for b in g)
        cosine_min=options.get("minimum_descent_cosine",.01)
        if not np.isfinite(slope) or slope>=-cosine_min*norm(pg)*norm(d):
            d={b:-v for b,v in pg.items()};restart.append("not_gradient_related")
        candidate,alpha,receipt=product_line_search(z,g,d,evaluate,f,options,options["initial_step"])
        if receipt["reason"] is not None:
            d={b:-v for b,v in pg.items()};restart.append("curve_search_exhausted")
            candidate,alpha,receipt=product_line_search(z,g,d,evaluate,f,options,options["initial_step"])
        entry.update(raw_pr_beta={b:float(beta) for b in g},raw_product_pr_beta=float(beta),
            raw_pr_slope=float(raw_slope),non_descent_restart=bool(restart),corrected_restart_reasons=restart,
            tangent_cone_gradient_norm=float(norm(pg)),corrected_step_size=float(alpha),corrected_line_search=receipt)
        if receipt["reason"] is not None:
            reason=receipt["reason"]
            break
        oldg,oldd,oldface=pg,d,face
        z=candidate
    f,eg,_=evaluate(z);g=project(z,eg)
    return z,history,{"reason":reason,"objective":float(f),"gradient_norm":float(norm(g)),
        "projected_kkt_norm":float(projected_kkt_norm(z,g)),"stationarity_measure":"projected_simplex_KKT",
        "solver_branch":"corrected_paper_product_raw_PR_with_curvature_line_search"}
