"""Original RGD with alternating positive BB1/BB2 seeds; unchanged direction.

The exact original objective increment callback is mandatory in full chains.
Armijo, retraction, constraints and gradient thresholds are unchanged.
"""
import numpy as np
from termination import gradient_stop


def rmo_ascent(phi,value_gradient,max_iterations,gradient_tolerance,vector_objective=False,status=None,increment=None):
    phi=phi.copy(); value,g=value_gradient(phi); history=[float(np.min(value))]
    initial_slope=np.sum(abs(g)**2,axis=1) if vector_objective else np.sum(abs(g)**2)
    seed=1/np.sqrt(np.maximum(initial_slope,np.finfo(float).tiny))
    for iteration in range(max_iterations):
        if np.linalg.norm(g)<gradient_tolerance: break
        slope=np.sum(abs(g)**2,axis=1) if vector_objective else np.sum(abs(g)**2)
        # Source AP optimizes each RIS independently. Its disclosed unreported
        # initial tangent step is one per RIS, before the same Armijo halving.
        alpha=np.asarray(seed).copy() if vector_objective else float(seed)
        if vector_objective:
            # Independently solved AP RIS blocks already below a stricter
            # per-row threshold stay fixed while other RIS blocks proceed.
            # This guarantees the unchanged joint gradient tolerance too.
            stationary=np.sqrt(slope)<gradient_tolerance/np.sqrt(len(slope))
            alpha[stationary]=0;slope[stationary]=0
        for search in range(60):
            candidate=phi+(alpha[:,None] if vector_objective else alpha)*g; candidate/=abs(candidate); trial,newg=value_gradient(candidate)
            if vector_objective:
                # A zero step must be the identity exactly, not a second
                # floating-point re-normalization of a stationary RIS row.
                candidate[stationary]=phi[stationary];trial,newg=value_gradient(candidate)
            difference=trial-value if increment is None else increment(phi,candidate)
            failed=difference<1e-4*alpha*slope
            if not np.any(failed): break
            if vector_objective:alpha[failed]*=0.5
            else:alpha*=0.5
        else:
            error=RuntimeError('Original RGD Armijo search failed; no phase substitute')
            error.receipt={'block':'RGD','iteration':len(history)-1,'gradient_norm':float(np.linalg.norm(g)),
                           'row_gradient_norms':np.linalg.norm(g,axis=1),'value':value,'last_trial':trial,
                           'last_step':alpha,'last_required_increase':1e-4*alpha*slope,'vector_objective':vector_objective}
            raise error
        step=np.angle(np.conj(phi)*candidate);old_theta=np.real(np.conj(1j*phi)*g);new_theta=np.real(np.conj(1j*candidate)*newg)
        axis=1 if vector_objective else None;curvature=np.sum(step*(old_theta-new_theta),axis=axis);distance=np.sum(step**2,axis=axis)
        yy=np.sum((old_theta-new_theta)**2,axis=axis)
        if vector_objective:
            positive=(curvature>0)&(distance>0);seed=2*alpha
            bb1=np.divide(distance,curvature,out=seed.copy(),where=positive)
            bb2=np.divide(curvature,yy,out=seed.copy(),where=positive)
            seed=bb2 if iteration%2==0 else bb1
        else:
            seed=(curvature/yy if iteration%2==0 else distance/curvature) if curvature>0 and distance>0 else 2*alpha
        seed=np.clip(seed,1e-12,1e12)
        improvement=float(np.min(trial)-np.min(value)); phi=candidate; value=trial; g=newg; history.append(float(np.min(value)))
    stop=gradient_stop(np.linalg.norm(g),len(history)-1,max_iterations,gradient_tolerance)
    stop['initial_step_contract']='alternating_positive_BB1_BB2_seeds_in_original_RGD_direction_before_original_Armijo; numerical_control_not_threshold_change'
    stop['objective_increment_contract']='exact_original_moment_polynomial_ratio_logsumexp_increment' if increment is not None else 'direct_objective_difference'
    if status is not None: status.update(stop)
    return phi,history
