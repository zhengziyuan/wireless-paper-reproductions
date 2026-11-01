"""Finite-Rician analytical blocks and genuine unrestricted paper QT subproblems.

These are development components, not a gated full-scenario reproduction.
Channels and full scenario settings must be supplied; no reduced LoS fallback exists.
"""
from __future__ import annotations
import numpy as np
import cvxpy as cp


def psd_factor(Q):
    """Exact PSD quadratic factor, with roundoff-only negative eigenvalue clipping."""
    values,vectors=np.linalg.eigh((Q+Q.conj().T)/2)
    if np.min(values)<-1e-9*max(1.0,float(np.max(abs(values)))):
        raise ValueError('Channel quadratic matrix is not PSD')
    return np.sqrt(np.maximum(values,0))[:,None]*vectors.conj().T


def rician_effective_moments(direct_mean, direct_variance, matrix_mean,
                             matrix_variance, ris_mean, ris_variance, phi):
    """Exact first, second and norm-fourth moments of d+G diag(phi) r.

    Independent circular Gaussian NLoS entries; variances are beta^2, not dB.
    This retains the non-Gaussian product G_NLoS*r_NLoS in the fourth moment.
    Conditioning on r makes h CN(d_mean+A*r, v(r)*I). No Gaussian approximation
    to the cascaded channel is made.
    """
    d = np.asarray(direct_mean, complex).reshape(-1)
    G = np.asarray(matrix_mean, complex)
    r = np.asarray(ris_mean, complex).reshape(-1)
    phi = np.asarray(phi, complex).reshape(-1)
    N, M = G.shape
    if d.size != N or r.size != M or phi.size != M:
        raise ValueError('Inconsistent channel dimensions')
    if np.max(abs(abs(phi)-1)) > 1e-10:
        raise ValueError('Moment block requires paper unit-modulus phase constraints')
    if min(direct_variance, matrix_variance, ris_variance) < 0:
        raise ValueError('NLoS variances must be nonnegative')
    A = G * phi[None, :]
    mean = d + A @ r
    Cr = float(ris_variance)
    Cb = Cr * A @ A.conj().T
    er2 = float(np.vdot(r, r).real + M*Cr)
    eb2 = float(np.vdot(mean, mean).real + np.trace(Cb).real)
    variance_scalar_mean = direct_variance + matrix_variance*er2
    covariance = Cb + variance_scalar_mean*np.eye(N)
    second = covariance + np.outer(mean, np.conj(mean))
    eb4 = eb2**2 + np.trace(Cb@Cb).real + 2*np.vdot(mean, Cb@mean).real
    er4 = er2**2 + M*Cr**2 + 2*Cr*np.vdot(r, r).real
    er2b2 = er2*eb2 + Cr**2*np.sum(abs(A)**2) + 2*Cr*np.real(np.vdot(r, A.conj().T@mean))
    evb2 = direct_variance*eb2 + matrix_variance*er2b2
    ev2 = direct_variance**2 + 2*direct_variance*matrix_variance*er2 + matrix_variance**2*er4
    fourth = float(eb4 + 2*(N+1)*evb2 + N*(N+1)*ev2)
    return {'mean': mean, 'covariance': covariance, 'second': second, 'norm_fourth': fourth}


def statistical_mr_coefficients(mean, second, gt_second):
    """Eq25/26 statistical MR coefficients; full independent p[j,u]."""
    mean, second, gt_second = map(np.asarray, (mean, second, gt_second))
    J, U, _ = mean.shape
    K = gt_second.shape[1]
    signal = np.zeros((J,U)); cross = np.zeros((J,U,U))
    power = np.zeros((J,U)); leak = np.zeros((J,U,K))
    for j in range(J):
        for u in range(U):
            power[j,u] = np.vdot(mean[j,u],mean[j,u]).real
            signal[j,u] = power[j,u]**2
            for i in range(U):
                cross[j,u,i] = np.vdot(mean[j,i],second[j,u]@mean[j,i]).real
            for k in range(K):
                leak[j,u,k] = np.vdot(mean[j,u],gt_second[j,k]@mean[j,u]).real
    return signal,cross,power,leak


def tts_mr_coefficients(second, norm_fourth, gt_second):
    """Exact finite-Rician two-timescale MR moments (no sample surrogate).

    h[j,u] and h[j,i] are independent for distinct user-specific RIS paths.
    Their cross moment is tr(Q[j,u] Q[j,i]); own fourth moment is supplied by
    the exact conditional-Gaussian block above, not a Gaussian approximation.
    """
    second, norm_fourth, gt_second = map(np.asarray, (second,norm_fourth,gt_second))
    J,U,_,_ = second.shape; K=gt_second.shape[1]
    signal=np.zeros((J,U)); cross=np.zeros((J,U,U)); power=np.zeros((J,U)); leak=np.zeros((J,U,K))
    for j in range(J):
        for u in range(U):
            power[j,u]=np.trace(second[j,u]).real
            signal[j,u]=power[j,u]**2
            for i in range(U):
                cross[j,u,i] = norm_fourth[j,u] if i==u else np.trace(second[j,u]@second[j,i]).real
            for k in range(K):
                leak[j,u,k]=np.trace(gt_second[j,k]@second[j,u]).real
    return signal,cross,power,leak


def mr_evaluate(p, signal, cross, power, leak, offset):
    J,U=p.shape
    numerator=np.sum(p*signal,axis=0); denominator=np.array(offset,float).copy()
    for u in range(U):
        denominator[u]+=np.sum(p*cross[:,u,:])-numerator[u]
    if np.min(denominator)<=0:
        raise ValueError('Nonpositive MR denominator')
    return {'sinr':numerator/denominator,'denominator':denominator,
            'satellite_power':np.sum(p*power,axis=1),'gt_interference':np.einsum('ju,juk->k',p,leak)}


def mr_qt_update(p0, signal, cross, power, leak, offset, power_limit, interference_limit,
                 solver='CLARABEL', solver_options=None):
    """Original unrestricted MR power quadratic-transform convex update.

    Per-satellite power uses the physical original P5/Eq25c coefficient;
    author-PDF Eq30d's apparently different coefficient is an unresolved
    final-source gate, not silently advertised as reconciled.
    """
    p0=np.asarray(p0,float); J,U=p0.shape
    before=mr_evaluate(p0,signal,cross,power,leak,offset)
    y=np.sqrt(np.maximum(p0*signal,0))/before['denominator'][None,:]
    # Exact diagonal change of optimization coordinates: p=scale*v. Individual
    # maximal feasible powers balance very different aligned/off-axis GT links.
    # All J*U variables remain independent; no share is fixed.
    scale=np.asarray(power_limit)[:,None]/np.maximum(power,1e-300)
    for k in range(leak.shape[2]):
        scale=np.minimum(scale,np.asarray(interference_limit)[k]/np.maximum(leak[:,:,k],1e-300))
    normalized=cp.Variable((J,U),nonneg=True); variable=cp.multiply(scale,normalized); gamma=cp.Variable()
    objective_scale=max(1e-6,float(np.max(np.sum(scale*signal,axis=0)/offset)))
    constraints=[]
    for u in range(U):
        B=cross[:,u,:].copy(); B[:,u]-=signal[:,u]
        if np.min(B)<-1e-9:
            raise ValueError('Desired/cross coefficient inconsistency')
        B=np.maximum(B,0)  # only machine-roundoff negativity is clipped
        den=cp.sum(cp.multiply(B,variable))+offset[u]
        lower=cp.sum(cp.multiply(2*y[:,u]*np.sqrt(signal[:,u]),cp.sqrt(variable[:,u]))) - np.sum(y[:,u]**2)*den
        constraints.append(gamma<=lower/objective_scale)
    for j in range(J):
        constraints.append(cp.sum(cp.multiply(power[j]/power_limit[j],variable[j]))<=1)
    for k in range(leak.shape[2]):
        constraints.append(cp.sum(cp.multiply(leak[:,:,k]/interference_limit[k],variable))<=1)
    problem=cp.Problem(cp.Maximize(gamma),constraints)
    problem.solve(solver=solver,**(solver_options or {}))
    if problem.status not in ('optimal','optimal_inaccurate') or normalized.value is None:
        raise RuntimeError(f'MR QT subproblem: {problem.status}')
    p=np.maximum(scale*normalized.value,0)
    after=mr_evaluate(p,signal,cross,power,leak,offset)
    qt_at_current=np.sum(2*y*np.sqrt(p0*signal),axis=0)-np.sum(y*y,axis=0)*before['denominator']
    diagnostics=solver_diagnostics(problem)
    physical=max(0,float(np.max(after['satellite_power']/power_limit-1)),float(np.max(after['gt_interference']/interference_limit-1)))
    diagnostics['physical_normalized_constraint_max_violation']=physical
    diagnostics['constraint_max_relative_violation']=max(diagnostics['constraint_max_relative_violation'],physical)
    return p,{'solver_status':problem.status,'surrogate_minimum_sinr':float(gamma.value*objective_scale),
              'solver_diagnostics':diagnostics,
              'qt_bound_max_violation':float(max(0,gamma.value*objective_scale-np.min(after['sinr']))),
              'qt_tightness_error':float(np.max(abs(qt_at_current-before['sinr']))),
              'before':before,'after':after}


def ap_evaluate(W,mean,covariance,gt_second,offset):
    J,N,U=W.shape; desired=np.zeros(U); denominator=np.asarray(offset,float).copy()
    for u in range(U):
        for j in range(J):
            desired[u]+=abs(np.vdot(mean[j,u],W[j,:,u]))**2
            for i in range(U):
                Q=covariance[j,u] if i==u else covariance[j,u]+np.outer(mean[j,u],np.conj(mean[j,u]))
                denominator[u]+=np.vdot(W[j,:,i],Q@W[j,:,i]).real
    leakage=np.zeros(gt_second.shape[1])
    for k in range(leakage.size):
        for j in range(J):
            for i in range(U):
                leakage[k]+=np.vdot(W[j,:,i],gt_second[j,k]@W[j,:,i]).real
    return {'sinr':desired/denominator,'denominator':denominator,
            'satellite_power':np.sum(abs(W)**2,axis=(1,2)),'gt_interference':leakage}


def ap_qt_update(W0,mean,covariance,gt_second,offset,power_limit,interference_limit,
                 solver='CLARABEL',solver_options=None):
    """Genuine statistical AP QT convex precoder block, no MR substitution.

    Theta=m*m^H is rank-one. Its exact one-row factor m^H avoids a failing
    strictly-PD Cholesky or artificial jitter. This is algebraically the same QT.
    """
    J,N,U=W0.shape; before=ap_evaluate(W0,mean,covariance,gt_second,offset)
    z=np.array([[np.vdot(mean[j,u],W0[j,:,u])/before['denominator'][u] for u in range(U)] for j in range(J)])
    W=[cp.Variable((N,U),complex=True) for _ in range(J)]; gamma=cp.Variable(); constraints=[]
    for u in range(U):
        denominator=offset[u]
        linear=0
        for j in range(J):
            linear+=2*cp.real(np.conj(z[j,u])*(np.conj(mean[j,u])@W[j][:,u]))
            for i in range(U):
                Q=covariance[j,u] if i==u else covariance[j,u]+np.outer(mean[j,u],np.conj(mean[j,u]))
                denominator+=cp.sum_squares(cp.abs(psd_factor(Q)@W[j][:,i]))
        constraints.append(gamma<=linear-np.sum(abs(z[:,u])**2)*denominator)
    for j in range(J):
        constraints.append(cp.sum_squares(cp.abs(W[j]))<=power_limit[j])
    for k in range(gt_second.shape[1]):
        constraints.append(sum(cp.sum_squares(cp.abs(psd_factor(gt_second[j,k])@W[j][:,i])) for j in range(J) for i in range(U))<=interference_limit[k])
    problem=cp.Problem(cp.Maximize(gamma),constraints); problem.solve(solver=solver,**(solver_options or {}))
    if problem.status not in ('optimal','optimal_inaccurate') or any(w.value is None for w in W):
        raise RuntimeError(f'AP QT subproblem: {problem.status}')
    value=np.stack([w.value for w in W]); after=ap_evaluate(value,mean,covariance,gt_second,offset)
    qt=np.sum(2*np.real(np.conj(z)*np.array([[np.vdot(mean[j,u],W0[j,:,u]) for u in range(U)] for j in range(J)])),axis=0)-np.sum(abs(z)**2,axis=0)*before['denominator']
    diagnostics=solver_diagnostics(problem)
    physical=max(0,float(np.max(after['satellite_power']/power_limit-1)),float(np.max(after['gt_interference']/interference_limit-1)))
    diagnostics['physical_normalized_constraint_max_violation']=physical
    diagnostics['constraint_max_relative_violation']=max(diagnostics['constraint_max_relative_violation'],physical)
    return value,{'solver_status':problem.status,'surrogate_minimum_sinr':float(gamma.value),
                  'solver_diagnostics':diagnostics,
                  'qt_bound_max_violation':float(max(0,gamma.value-np.min(after['sinr']))),
                  'qt_tightness_error':float(np.max(abs(qt-before['sinr']))),'before':before,'after':after}


def solver_diagnostics(problem):
    stats=problem.solver_stats
    out={'solver':stats.solver_name,'status':problem.status,'iterations':stats.num_iters,'solve_seconds':stats.solve_time}
    errors=[float(np.max(np.asarray(c.violation()))) for c in problem.constraints]
    relative=[]
    for constraint,error in zip(problem.constraints,errors):
        scale=max([float(np.max(abs(arg.value))) for arg in constraint.args if arg.value is not None]+[1.0])
        relative.append(error/scale)
    out.update(normalized_constraint_max_violation=max(errors,default=0.0),constraint_max_relative_violation=max(relative,default=0.0))
    return out
