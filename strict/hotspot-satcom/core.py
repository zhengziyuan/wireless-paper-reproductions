"""Actual QT/SOCP, SDP/randomization and original two-stage RGD/QT blocks.

No ZF precoder is used as the optimization algorithm. Final TWC full-text
conformance remains an explicit gate; thesis-equivalent blocks are not final proof.
"""
from __future__ import annotations
import numpy as np
import cvxpy as cp
import time
from termination import relative_stop,gradient_stop


def solver_diagnostics(problem):
    stats=problem.solver_stats; info={'solver':stats.solver_name,'status':problem.status,
                                     'iterations':stats.num_iters,'solve_seconds':stats.solve_time}
    extra=stats.extra_stats
    if isinstance(extra,dict) and isinstance(extra.get('info'),dict):
        raw=extra['info']
        for name in ('res_pri','res_dual','gap','pobj','dobj'):
            if name in raw and np.isfinite(raw[name]): info[name]=float(raw[name])
    violations=[float(np.max(np.asarray(c.violation()))) for c in problem.constraints]
    relative=[]
    for constraint,error in zip(problem.constraints,violations):
        magnitude=max([float(np.max(abs(arg.value))) for arg in constraint.args if arg.value is not None]+[1.0])
        relative.append(error/magnitude)
    info['normalized_constraint_max_violation']=max(violations,default=0.0)
    info['constraint_max_relative_violation']=max(relative,default=0.0)
    return info


def effective_rows(direct_hu,cascade,phi):
    return np.asarray(direct_hu)+np.einsum('m,umn->un',phi,cascade)


def evaluate(hu,nhu,W,noise):
    C=np.vstack((hu,nhu)); received=abs(C@W)**2
    desired=np.diag(received); denominator=np.sum(received,axis=1)-desired+noise
    sinr=desired/denominator
    return {'sinr':sinr,'hu_sum_rate':float(np.sum(np.log2(1+sinr[:hu.shape[0]]))),
            'total_power':float(np.sum(abs(W)**2))}


def qt_parameters(hu,W,noise):
    received=hu@W; U=hu.shape[0]
    den=np.sum(abs(received)**2,axis=1)-abs(received[np.arange(U),np.arange(U)])**2+noise
    return received[np.arange(U),np.arange(U)]/den


def active_qt_update(hu,nhu,W0,noise,total_power,nhu_target,solver='CLARABEL',solver_options=None,a=None):
    """Genuine complex QT sum-log objective + exact NHU SOC QoS constraints."""
    U,N=hu.shape; K=nhu.shape[0]; J=U+K
    if a is None:
        a=qt_parameters(hu,W0,noise)
    # Exact variable/noise normalization: physical W=sqrt(P)*V.
    # lambda' = |a*sqrt(noise)|^2 * lambda/noise is the weighted interference
    # epigraph. This eliminates a large lambda multiplied by a tiny |a|^2;
    # it is the identical QT feasible set/objective (also when a=0).
    # SINRs/objective/QoS are unchanged; this is numerical conditioning only.
    W=cp.Variable((N,J),complex=True); lam=cp.Variable(U); gamma=cp.Variable(U)
    scale=np.sqrt(total_power/noise); hs=hu*scale; ns=nhu*scale; az=a*np.sqrt(noise)
    constraints=[cp.sum_squares(cp.abs(W))<=1]
    for u in range(U):
        interferers=[j for j in range(J) if j!=u]
        constraints.append(cp.sum_squares(cp.abs(np.conj(az[u])*(hs[u]@W[:,interferers])))+abs(az[u])**2<=lam[u])
        constraints.append(gamma[u]<=2*cp.real(np.conj(az[u])*(hs[u]@W[:,u]))-lam[u])
    for k in range(K):
        index=U+k; interferers=[j for j in range(J) if j!=index]
        desired=ns[k]@W[:,index]
        constraints.append(cp.imag(desired)==0)
        constraints.append(cp.norm(cp.hstack([ns[k]@W[:,interferers],1.0]))<=cp.real(desired)/np.sqrt(nhu_target[k]))
    problem=cp.Problem(cp.Maximize(cp.sum(cp.log1p(gamma))/np.log(2)),constraints)
    try:
        problem.solve(solver=solver,**(solver_options or {}))
    except cp.error.SolverError as error:
        error.receipt={'block':'active_QT','backend':solver,'solver_options':solver_options,
                       'before':evaluate(hu,nhu,W0,noise),'auxiliary_magnitudes':abs(a),
                       'scaled_hu_row_norms':np.linalg.norm(hs,axis=1)}
        error.fixture={'hu':hu,'nhu':nhu,'W0':W0,'noise':noise,'power':total_power,'target':nhu_target,'a':a}
        raise
    if problem.status not in ('optimal','optimal_inaccurate') or W.value is None:
        raise RuntimeError(f'Hotspot QT/SOCP: {problem.status}')
    value=W.value*np.sqrt(total_power); after=evaluate(hu,nhu,value,noise); before=evaluate(hu,nhu,W0,noise)
    received=hu@W0; den=np.sum(abs(received)**2,axis=1)-abs(received[np.arange(U),np.arange(U)])**2+noise
    qt=2*np.real(np.conj(a)*received[np.arange(U),np.arange(U)])-abs(a)**2*den
    return value,{'solver_status':problem.status,'surrogate_rate':float(problem.value),
                  'solver_diagnostics':dict(solver_diagnostics(problem),epigraph_scaling='lambda_prime_equals_abs_a_squared_times_physical_interference'),
                  'qt_bound_max_violation':float(max(0,np.max(gamma.value-after['sinr'][:U]))),
                  'qt_tightness_error':float(np.max(abs(qt-before['sinr'][:U]))),'before':before,'after':after},a


def qt_loop(hu,nhu,W0,noise,power,target,max_iterations,relative_tolerance,solver='CLARABEL',solver_options=None,diagnostics=None,status=None):
    W=W0.copy(); history=[evaluate(hu,nhu,W,noise)['hu_sum_rate']]
    for _ in range(max_iterations):
        candidate,info,_=active_qt_update(hu,nhu,W,noise,power,target,solver,solver_options)
        if diagnostics is not None: diagnostics.append(dict(info['solver_diagnostics'],qt_bound_max_violation=info['qt_bound_max_violation']))
        value=info['after']['hu_sum_rate']
        if value < history[-1]-1e-6:
            error=RuntimeError('QT update decreased exact objective beyond solver tolerance')
            error.receipt={'block':'QT','attempted_iteration':len(history),
                           'retained_history':history,'attempted_value':value,
                           'decrease':history[-1]-value,'active_update':info,
                           'solver_diagnostics':diagnostics or []}
            raise error
        W=candidate; history.append(value)
        if (history[-1]-history[-2])/max(abs(history[-2]),1e-12)<relative_tolerance:
            break
    if status is not None: status.update(relative_stop(history,max_iterations,relative_tolerance))
    return W,history


def phase_surrogate(direct,cascade,phi,W,a,noise):
    hu=effective_rows(direct,cascade,phi); received=hu@W; U=hu.shape[0]
    den=np.sum(abs(received)**2,axis=1)-abs(received[np.arange(U),np.arange(U)])**2+noise
    q=2*np.real(np.conj(a)*received[np.arange(U),np.arange(U)])-abs(a)**2*den
    if np.any(1+q<=0):
        return -np.inf
    return float(np.sum(np.log2(1+q)))


def phase_sdr_update(direct,cascade,phi0,W,a,noise,normal_draws,solver='CLARABEL',solver_options=None):
    """Actual lifted unit-diagonal complex SDP + supplied Gaussian randomization.

    normal_draws contains shared CN(0,I) samples (M+1,Lrand), not solver data.
    No hidden count/seed change. The current feasible phase is also retained as
    an incumbent to handle non-tight SDR/randomization without false monotonicity.
    """
    U,M,N=cascade.shape; J=W.shape[1]
    normals=np.asarray(normal_draws,complex)
    if normals.ndim!=2 or normals.shape[0]!=M+1 or normals.shape[1]<1:
        raise ValueError('Supply shared Gaussian draws with shape (M+1,Lrand)')
    V=cp.Variable((M+1,M+1),hermitian=True); constraints=[V>>0,cp.diag(V)==1]
    terms=[]
    for u in range(U):
        b=np.conj(a[u])*(cascade[u]@W[:,u])
        L=np.zeros((M+1,M+1),complex); L[:M,M]=b/2; L[M,:M]=np.conj(b)/2
        q=2*np.real(np.conj(a[u])*(direct[u]@W[:,u]))+2*cp.real(cp.trace(L@V))-abs(a[u])**2*noise
        for j in range(J):
            if j!=u:
                column=np.r_[cascade[u]@W[:,j],direct[u]@W[:,j]]
                Q=np.outer(column,np.conj(column))
                q-=abs(a[u])**2*cp.real(cp.trace(Q@V))
        terms.append(cp.log1p(q)/np.log(2))
    problem=cp.Problem(cp.Maximize(cp.sum(cp.hstack(terms))),constraints)
    try:
        problem.solve(solver=solver,**(solver_options or {}))
    except cp.error.SolverError as error:
        error.receipt={'block':'phase_SDP','backend':solver,'solver_options':solver_options,
                       'before_exact_rate':evaluate(effective_rows(direct,cascade,phi0),np.empty((0,N)),W,noise)['hu_sum_rate'],
                       'incumbent_surrogate':phase_surrogate(direct,cascade,phi0,W,a,noise)}
        error.fixture={'direct':direct,'cascade':cascade,'phi0':phi0,'W':W,'a':a,'noise':noise,'normal_draws':normal_draws}
        raise
    if problem.status not in ('optimal','optimal_inaccurate') or V.value is None:
        raise RuntimeError(f'Phase SDP: {problem.status}')
    relaxation=(V.value+V.value.conj().T)/2
    values,vectors=np.linalg.eigh(relaxation)
    if np.min(values)<-1e-5:
        error=RuntimeError('SDP returned non-PSD matrix beyond numerical tolerance')
        error.receipt={'block':'phase_SDP','smallest_sdp_eigenvalue':float(np.min(values)),
                       'sdp_eigenvalues':values,'diagonal_error':float(np.max(abs(np.diag(relaxation)-1))),
                       'solver_diagnostics':solver_diagnostics(problem)}
        raise error
    # Principal Hermitian square root eliminates eigenvector phase/order gauges
    # so paired MATLAB/Python normal draws address the same random directions.
    factor=(vectors*np.sqrt(np.maximum(values,0))[None,:])@vectors.conj().T
    samples=factor@normals
    best=phi0.copy(); best_value=phase_surrogate(direct,cascade,best,W,a,noise)
    for sample in samples.T:
        if abs(sample[-1])<1e-14:
            continue
        phase=np.conj(sample[:-1]/sample[-1]); phase/=abs(phase)
        value=phase_surrogate(direct,cascade,phase,W,a,noise)
        if value>best_value:
            best,best_value=phase,value
    diag=solver_diagnostics(problem)
    diag['sdr_bound_max_violation']=float(max(0,best_value-problem.value))
    return best,{'solver_status':problem.status,'sdr_upper_bound':float(problem.value),
                 'solver_diagnostics':diag,
                 'rounded_surrogate':best_value,'unit_modulus_error':float(np.max(abs(abs(best)-1))),
                 'diagonal_error':float(np.max(abs(np.diag(relaxation)-1))),
                 'smallest_sdp_eigenvalue':float(np.min(values)),'randomization_count':int(normals.shape[1])}


def ao(direct,cascade,nhu,phi0,W0,noise,power,target,normal_draws,max_iterations,relative_tolerance,
       solver='CLARABEL',solver_options=None,diagnostics=None,status=None,budget_endpoints=None):
    """Original instantaneous AO/QT/SDR structure; shared draws per AO iteration."""
    W=W0.copy(); phi=phi0.copy(); hu=effective_rows(direct,cascade,phi)
    history=[evaluate(hu,nhu,W,noise)['hu_sum_rate']]
    if len(normal_draws)<max_iterations:
        raise ValueError('Provide fixed Gaussian draws for every allowed AO iteration')
    for iteration in range(max_iterations):
        a=qt_parameters(hu,W,noise)
        try:
            W,active,_=active_qt_update(hu,nhu,W,noise,power,target,solver,solver_options,a)
        except (RuntimeError,cp.error.SolverError) as error:
            error.receipt={'block':'AO_active_subproblem','attempted_iteration':iteration+1,
                           'retained_history':history,'active_failure':getattr(error,'receipt',None),
                           'solver_diagnostics':diagnostics or []}
            raise
        # Algorithm 3-1 updates the quadratic parameter again after active W.
        a=qt_parameters(hu,W,noise)
        phase_clock=time.perf_counter()
        try:
            phi,phase=phase_sdr_update(direct,cascade,phi,W,a,noise,normal_draws[iteration],solver,solver_options)
        except (RuntimeError,cp.error.SolverError) as error:
            error.receipt={'block':'AO_phase_subproblem','attempted_iteration':iteration+1,
                           'retained_history':history,'active_update':active,
                           'phase_failure':getattr(error,'receipt',None),'solver_diagnostics':diagnostics or []}
            raise
        phase['solver_diagnostics']['phase_cpu_seconds']=time.perf_counter()-phase_clock
        if diagnostics is not None: diagnostics.append({'active':dict(active['solver_diagnostics'],qt_bound_max_violation=active['qt_bound_max_violation']),
                                                       'phase':phase['solver_diagnostics']})
        hu=effective_rows(direct,cascade,phi); value=evaluate(hu,nhu,W,noise)['hu_sum_rate']
        if value<history[-1]-1e-5:
            error=RuntimeError('AO objective decrease beyond solver accuracy')
            error.receipt={'block':'AO','attempted_iteration':iteration+1,
                           'retained_history':history,'attempted_value':value,
                           'decrease':history[-1]-value,'active_update':active,
                           'phase_update':phase,'solver_diagnostics':diagnostics or []}
            raise error
        history.append(value)
        if budget_endpoints is not None and iteration+1 in (20,100):
            budget_endpoints[str(iteration+1)]={'evaluation':evaluate(hu,nhu,W,noise),
                'executed_outer_iterations':iteration+1,'requested_outer_budget':iteration+1,
                'interpretation':'reported_fixed_budget_endpoint_NOT_stationarity_claim',
                'solver_diagnostics':list(diagnostics or [])}
        if (history[-1]-history[-2])/max(abs(history[-2]),1e-12)<relative_tolerance:
            break
    if status is not None: status.update(relative_stop(history,max_iterations,relative_tolerance))
    if budget_endpoints is not None:
        for budget in (20,100):
            if str(budget) not in budget_endpoints and len(history)-1<budget and relative_stop(history,max_iterations,relative_tolerance)['converged']:
                budget_endpoints[str(budget)]={'evaluation':evaluate(hu,nhu,W,noise),
                    'executed_outer_iterations':len(history)-1,'requested_outer_budget':budget,
                    'interpretation':'original_relative_stop_reached_before_reported_budget_NO_trace_padding',
                    'solver_diagnostics':list(diagnostics or [])}
    return phi,W,history


def criterion_gradient(direct,cascade,nhu,phi):
    c=effective_rows(direct,cascade,phi); N=c.shape[1]; A=np.eye(N,dtype=complex)
    for row in nhu:
        h=np.conj(row); A-=np.outer(h,np.conj(h))/np.vdot(h,h).real
    ca=c@A; f2=np.sum(abs(ca)**2); f3=0.0
    for u in range(c.shape[0]):
        for v in range(u):
            f3+=abs(c[u]@np.conj(c[v]))**2
    gradient=np.zeros(phi.size)
    for m in range(phi.size):
        dc=1j*phi[m]*cascade[:,m,:]; d2=2*np.real(np.sum(np.conj(ca)*(dc@A))); d3=0
        for u in range(c.shape[0]):
            for v in range(u):
                t=c[u]@np.conj(c[v]); dt=dc[u]@np.conj(c[v])+c[u]@np.conj(dc[v])
                d3+=2*np.real(np.conj(t)*dt)
        gradient[m]=d2-d3
    return float(f2-f3),1j*phi*gradient


def transport(vector,point):
    return vector-np.real(vector*np.conj(point))*point


def phase_rcg(direct,cascade,nhu,phi,max_iterations,gradient_tolerance,status=None):
    """Explicit PR+ diagnostic only; never used by the formal two-stage method."""
    return _phase_optimizer(direct,cascade,nhu,phi,max_iterations,gradient_tolerance,status,True,False)


def phase_rgd(direct,cascade,nhu,phi,max_iterations,gradient_tolerance,status=None,literal_sign=False):
    """Author Algorithm 3-2 RGD: minimize -F, hence direction +grad(F).

    Eq3-36 maximizes F=f2-f3 while the prose prints -grad(F). literal_sign=True
    is an explicit diagnostic minimizing F, not the formal paper objective.
    """
    return _phase_optimizer(direct,cascade,nhu,phi,max_iterations,gradient_tolerance,status,False,literal_sign)


def _phase_optimizer(direct,cascade,nhu,phi,max_iterations,gradient_tolerance,status,conjugate,literal_sign):
    sign=-1.0 if literal_sign else 1.0
    phi=phi.copy(); value,g=criterion_gradient(direct,cascade,nhu,phi); direction=sign*g.copy(); history=[value]
    for _ in range(max_iterations):
        norm2=np.vdot(g,g).real
        if np.sqrt(norm2)<=gradient_tolerance:
            break
        if not conjugate:direction=sign*g.copy()
        slope=np.vdot(sign*g,direction).real
        if slope<=0:
            direction=g.copy(); slope=norm2
        alpha=1.0
        for _ in range(50):
            candidate=phi+alpha*direction; candidate/=abs(candidate)
            trial,newg=criterion_gradient(direct,cascade,nhu,candidate)
            if sign*(trial-value)>=1e-4*alpha*slope:
                break
            alpha*=0.5
        else:
            raise RuntimeError('RGD/explicit diagnostic line search failed; no substitute algorithm used')
        if conjugate:
            oldg=transport(g,candidate); olddir=transport(direction,candidate)
            beta=max(0.0,np.vdot(newg,newg-oldg).real/norm2)
            direction=newg+beta*olddir
        phi=candidate; value=trial; g=newg; history.append(value)
    if status is not None:
        status.update(gradient_stop(np.linalg.norm(g),len(history)-1,max_iterations,gradient_tolerance))
        status.update(phase_method='PR_plus_RCG_diagnostic_NOT_paper_method' if conjugate else ('literal_negative_grad_F_diagnostic_NOT_argmax_F' if literal_sign else 'author_Algorithm_3-2_RGD_minimize_negative_F'),
                      printed_sign_interpretation='literal_diagnostic' if literal_sign else 'argmax_F_equivalent_minimize_negative_F')
    return phi,history


def two_stage(direct,cascade,nhu,phi0,W0,noise,power,target,rgd_iterations,gradient_tolerance,
              qt_iterations,qt_tolerance,solver='CLARABEL',solver_options=None):
    phase_stop={}; qt_stop={}
    phase_clock=time.perf_counter()
    phi,phase_history=phase_rgd(direct,cascade,nhu,phi0,rgd_iterations,gradient_tolerance,phase_stop)
    phase_seconds=time.perf_counter()-phase_clock
    diagnostics=[]
    W,rate_history=qt_loop(effective_rows(direct,cascade,phi),nhu,W0,noise,power,target,
                           qt_iterations,qt_tolerance,solver,solver_options,diagnostics,qt_stop)
    return phi,W,{'phase_criterion':phase_history,'qt_rate':rate_history,'solver_diagnostics':diagnostics,
                 'phase_method':'author_Algorithm_3-2_RGD_minimize_negative_F',
                 'phase_cpu_seconds':phase_seconds,
                 'termination':{'phase':phase_stop,'QT':qt_stop}}
