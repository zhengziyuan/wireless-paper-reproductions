"""Certified global solve of the SAME two-real-variable convex subproblem.

MRT: quadratic/linear over the original box/spacing polygon.
ZF: sum log of the original concave quadratic minorants, over that polygon.
All vertices, every edge maximum and any interior maximum are considered.
The final first-order global objective-gap certificate is solver-status free.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import brentq


def polygon(t,c,antenna):
    position=t[antenna];lo=np.asarray(c["region_lower"])-position;hi=np.asarray(c["region_upper"])-position
    A=[[-1.,0.],[0.,-1.],[1.,0.],[0.,1.]];b=[-lo[0],-lo[1],hi[0],hi[1]]
    for other in range(len(t)):
        if other==antenna:continue
        d=position-t[other];A.append(-2*d);b.append(d@d-c["minimum_distance"]**2)
    A=np.asarray(A);b=np.asarray(b);norm=np.linalg.norm(A,axis=1)
    if np.any((norm==0)&(b<0)):raise ValueError("Original spacing polygon is infeasible")
    keep=norm>0;A=A[keep]/norm[keep,None];b=b[keep]/norm[keep]
    tol=2e-12*max(1.,float(np.max(abs(b))));vertices=[]
    for i in range(len(A)):
        for j in range(i):
            matrix=A[[i,j]]
            if abs(np.linalg.det(matrix))<=1e-13:continue
            x=np.linalg.solve(matrix,b[[i,j]])
            if np.max(A@x-b)<=tol and not any(np.linalg.norm(x-y)<tol for y in vertices):vertices.append(x)
    if not vertices:raise ValueError("No vertices of the bounded original feasible polygon")
    return A,b,np.asarray(vertices),tol


def edge_interval(A,b,index,tolerance):
    base=A[index]*b[index];direction=np.array([-A[index,1],A[index,0]])
    lower=-np.inf;upper=np.inf
    for row,rhs in zip(A,b):
        slope=row@direction;remaining=rhs-row@base
        if abs(slope)<1e-13:
            if remaining < -tolerance:return None
        elif slope>0:upper=min(upper,remaining/slope)
        else:lower=max(lower,remaining/slope)
    if not np.isfinite(lower+upper) or lower>upper+tolerance:return None
    return base,direction,lower,upper


def solve(t,c,antenna,mode,*,gradient=None,curvature=None,base=None,minor_gradient=None,minor_curvature=None,objective_before=0.):
    settings=c["convex_solver"].get("options",{})
    A,b,vertices,feasibility_tolerance=polygon(t,c,antenna)
    candidates=[v.copy() for v in vertices];zero=np.zeros(2)
    if np.max(-b)<=feasibility_tolerance:candidates.append(zero)
    if mode=="MRT":
        g=np.asarray(gradient);q=float(curvature)
        if q<0:raise ValueError("Original MRT minorant is not concave")
        def evaluate(x):return float(g@x-q/2*(x@x)),g-q*x
        if q>0:
            unconstrained=g/q
            if np.max(A@unconstrained-b)<=feasibility_tolerance:candidates.append(unconstrained)
        for index in range(len(A)):
            edge=edge_interval(A,b,index,feasibility_tolerance)
            if edge is None:continue
            p,v,left,right=edge
            if q>0:parameter=np.clip(v@(g/q-p),left,right)
            else:parameter=right if g@v>0 else left
            candidates.append(p+parameter*v)
    elif mode=="ZF":
        a=np.asarray(base);G=np.asarray(minor_gradient);q=np.asarray(minor_curvature)
        if np.any(a<=0) or np.any(q<0):raise ValueError("Original ZF expansion domain/concavity invalid")
        def evaluate(x):
            change=G@x-q/2*(x@x);r=a+change
            if np.any(r<=0) or not np.all(np.isfinite(r)):return -np.inf,np.full(2,np.nan)
            vectors=G-q[:,None]*x
            logarithms=np.log1p(change/a) if np.all(change/a>-1) else np.log(r/a)
            return float(logarithms.sum()/np.log(2)),np.sum(vectors/r[:,None],axis=0)/np.log(2)
        # Unconstrained interior Newton, exact analytic derivatives. Domain
        # checks and line search change only how this convex subproblem solves.
        x=zero.copy()
        for _ in range(settings.get("interior_newton_iteration_budget",100)):
            value,g=evaluate(x);r=a+G@x-q/2*(x@x);vectors=G-q[:,None]*x
            negative_hessian=(np.sum(q/r)*np.eye(2)+vectors.T@((1/r**2)[:,None]*vectors))/np.log(2)
            if np.linalg.norm(g)<settings.get("interior_gradient_tolerance",1e-12):break
            eigenvalues,V=np.linalg.eigh(negative_hessian);positive=eigenvalues>np.finfo(float).eps*max(1.,float(eigenvalues[-1]))
            if not np.any(positive):break
            step=V[:,positive]@((V[:,positive].T@g)/eigenvalues[positive]);slope=g@step
            if slope<=0:break
            alpha=1.
            for _ in range(120):
                trial_value,_=evaluate(x+alpha*step)
                # Near a root, objective rounding can hide a valid Newton
                # refinement. Its admissibility is decided by the independent
                # final global gap certificate, not an accepted solver flag.
                if trial_value>=value+1e-4*alpha*slope or (slope<1e-14 and np.isfinite(trial_value)):break
                alpha/=2
            else:break
            trial=x+alpha*step
            if np.array_equal(trial,x):break
            x=trial
        if np.max(A@x-b)<=feasibility_tolerance and np.isfinite(evaluate(x)[0]):candidates.append(x)
        for index in range(len(A)):
            edge=edge_interval(A,b,index,feasibility_tolerance)
            if edge is None:continue
            p,v,left,right=edge
            constants=a+G@p-q/2*(p@p);linear=(G-q[:,None]*p)@v
            for constant,slope,quadratic in zip(constants,linear,q):
                if quadratic>0:
                    center=slope/quadratic;radius_squared=center**2+2*constant/quadratic
                    if radius_squared<=0:left=1.;right=0.;break
                    radius=np.sqrt(radius_squared);left=max(left,center-radius);right=min(right,center+radius)
                elif abs(slope)>0:
                    boundary=-constant/slope
                    if slope>0:left=max(left,boundary)
                    else:right=min(right,boundary)
                elif constant<=0:left=1.;right=0.;break
            if left>right:continue
            if np.isfinite(evaluate(p+left*v)[0]):candidates.append(p+left*v)
            if np.isfinite(evaluate(p+right*v)[0]):candidates.append(p+right*v)
            if right-left<=feasibility_tolerance:continue
            # Only finite-domain endpoints bracket the scalar derivative.
            # A geometric inward sequence avoids treating log-domain roots
            # as feasible endpoints; final global certificate detects misses.
            def interior_endpoint(endpoint,other):
                value=endpoint
                for _ in range(32):
                    if np.isfinite(evaluate(p+value*v)[0]):return value
                    value=np.nextafter(value,other)
                for fraction in [1e-14,1e-12,1e-10,1e-8,1e-6]:
                    value=endpoint+fraction*(other-endpoint)
                    if np.isfinite(evaluate(p+value*v)[0]):return value
                return None
            L=interior_endpoint(left,right);R=interior_endpoint(right,left)
            if L is None or R is None or L>R:continue
            def derivative(parameter):return float(evaluate(p+parameter*v)[1]@v)
            dL=derivative(L);dR=derivative(R)
            if dL<=0:parameter=L
            elif dR>=0:parameter=R
            else:parameter=brentq(derivative,L,R,xtol=5e-15,rtol=1e-14,maxiter=200)
            candidates.append(p+parameter*v)
    else:raise ValueError(mode)
    valid=[x for x in candidates if np.max(A@x-b)<=feasibility_tolerance and np.isfinite(evaluate(x)[0])]
    if not valid:raise RuntimeError("No finite feasible candidate of original coordinate problem")
    values=np.asarray([evaluate(x)[0] for x in valid]);maximum=float(values.max())
    tied=np.flatnonzero(values>=maximum-8*np.finfo(float).eps*max(1.,abs(maximum)))
    def candidate_quality(index):
        x=valid[index];_,gradient_value=evaluate(x)
        gap_value=float(np.max((vertices-x)@gradient_value)) if np.all(np.isfinite(gradient_value)) else np.inf
        return max(0.,gap_value),float(x@x)
    winner=valid[min(tied,key=candidate_quality)];value,g=evaluate(winner)
    if not np.all(np.isfinite(g)):raise RuntimeError("Finite exact2D certificate gradient required")
    # Concavity: F(y)<=F(x)+gradF(x)^T(y-x). Maximizing this linear upper
    # bound over ALL polygon vertices yields a rigorous global gap certificate.
    gap=max(0.,float(np.max((vertices-winner)@g)))
    gap_tolerance=max(settings.get("objective_gap_absolute_tolerance",1e-10),
        settings.get("objective_gap_relative_tolerance",1e-10)*abs(float(objective_before)))
    residual=max(0.,float(np.max(A@winner-b)))
    if not np.isfinite(gap+residual) or gap>gap_tolerance or residual>feasibility_tolerance:
        raise RuntimeError(f"Exact2D original subproblem certificate failed: gap={gap}, primal={residual}")
    return winner,{"backend":"exact_2D_original_subproblem_active_set",
        "global_objective_gap_upper_bound":gap,"global_objective_gap_tolerance":gap_tolerance,
        "maximum_normalized_constraint_violation":residual,"polygon_vertex_count":len(vertices),
        "normalized_constraint_tolerance":feasibility_tolerance,
        "finite_feasible_candidates":len(valid),"original_subproblem_unchanged":True,
        "certified_without_conic_solver_status":True,"minorant_increment":float(value)}
