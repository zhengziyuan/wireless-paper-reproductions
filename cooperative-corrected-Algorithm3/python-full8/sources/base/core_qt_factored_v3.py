"""Prospective v3: exact fixed sqrt(scale) factor outside same MR-QT cone.

Same original input/auxiliary/constraints/precision gates; no model replacement.
All19 actual old failure inputs independently tested at80decimal digits.
"""
import numpy as np
import core
cp=core.cp


def mr_qt_update(p0,signal,cross,power,leak,offset,power_limit,interference_limit,
                 solver='CLARABEL',solver_options=None):
    p0=np.asarray(p0,float);J,U=p0.shape;before=core.mr_evaluate(p0,signal,cross,power,leak,offset)
    y=np.sqrt(np.maximum(p0*signal,0))/before['denominator'][None,:]
    scale=np.asarray(power_limit)[:,None]/np.maximum(power,1e-300)
    for k in range(leak.shape[2]):scale=np.minimum(scale,np.asarray(interference_limit)[k]/np.maximum(leak[:,:,k],1e-300))
    normalized=cp.Variable((J,U),nonneg=True);variable=cp.multiply(scale,normalized);gamma=cp.Variable()
    objective_scale=max(1e-6,float(np.max(np.sum(scale*signal,axis=0)/offset)));constraints=[]
    for u in range(U):
        B=cross[:,u,:].copy();B[:,u]-=signal[:,u]
        if np.min(B)<-1e-9:raise ValueError('Desired/cross coefficient inconsistency')
        B=np.maximum(B,0)
        den=cp.sum(cp.multiply(B,variable))+offset[u]
        # Same concave expression, no tiny physical-p cone multiplied by huge coefficients.
        lower=cp.sum(cp.multiply(2*y[:,u]*np.sqrt(signal[:,u]*scale[:,u]),cp.sqrt(normalized[:,u]))) - np.sum(y[:,u]**2)*den
        constraints.append(gamma<=lower/objective_scale)
    for j in range(J):constraints.append(cp.sum(cp.multiply(power[j]/power_limit[j],variable[j]))<=1)
    for k in range(leak.shape[2]):constraints.append(cp.sum(cp.multiply(leak[:,:,k]/interference_limit[k],variable))<=1)
    problem=cp.Problem(cp.Maximize(gamma),constraints);problem.solve(solver=solver,**(solver_options or {}))
    if problem.status not in ('optimal','optimal_inaccurate') or normalized.value is None:raise RuntimeError(f'MR QT subproblem: {problem.status}')
    p=np.maximum(scale*normalized.value,0);after=core.mr_evaluate(p,signal,cross,power,leak,offset)
    qt=np.sum(2*y*np.sqrt(p0*signal),axis=0)-np.sum(y*y,axis=0)*before['denominator'];diagnostics=core.solver_diagnostics(problem)
    physical=max(0,float(np.max(after['satellite_power']/power_limit-1)),float(np.max(after['gt_interference']/interference_limit-1)))
    diagnostics['physical_normalized_constraint_max_violation']=physical
    diagnostics['constraint_max_relative_violation']=max(diagnostics['constraint_max_relative_violation'],physical)
    return p,{'solver_status':problem.status,'surrogate_minimum_sinr':float(gamma.value*objective_scale),
              'solver_diagnostics':diagnostics,'qt_bound_max_violation':float(max(0,gamma.value*objective_scale-np.min(after['sinr']))),
              'qt_tightness_error':float(np.max(abs(qt-before['sinr']))),'before':before,'after':after}

