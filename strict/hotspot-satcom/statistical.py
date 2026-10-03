"""Full finite-Rician statistics and the explicitly corrected original QT chain.

The printed full-rank covariance QoS is not a scalar SOC. The erratum applies
the manuscript's vector quadratic transform to QoS too; no LoS/instantaneous
replacement of the original average-SINR model is made. See STATISTICAL_ERRATUM.
"""
import numpy as np
import cvxpy as cp
from scipy.integrate import quad_vec
from core import solver_diagnostics,complex_squares
from termination import relative_stop,gradient_stop


def factor(Q):
    values,vectors=np.linalg.eigh((Q+Q.conj().T)/2)
    if values.min()<-1e-10*max(1,float(abs(values).max())):raise ValueError('Non-PSD channel moment')
    return np.sqrt(np.maximum(values,0))[:,None]*vectors.conj().T


def moments(inputs,phi,no_ris=False):
    dm,dv,G,gv,r,rv=(np.asarray(inputs[k]) for k in ('direct_mean','direct_variance','matrix_mean','matrix_variance','ground_mean','ground_variance'))
    U,N=dm.shape; M=G.shape[0]; phi=np.asarray(phi).reshape(M)
    if np.max(abs(abs(phi)-1))>1e-10:raise ValueError('Original unit-modulus phase required')
    means=dm.copy(); Q=np.zeros((U,N,N),complex); C=np.zeros_like(Q)
    for u in range(U):
        cov=np.diag(dv[u].astype(complex))
        if not no_ris:
            means[u]+=phi@(r[u,:,None]*G)
            cov+=np.einsum('m,mn,mp->np',rv[u],np.conj(G),G)
            cov+=np.diag(np.sum(gv*(abs(r[u])**2+rv[u])[:,None],axis=0))
        C[u]=cov;Q[u]=cov+np.outer(np.conj(means[u]),means[u])
    nm,nv=np.asarray(inputs['nhu_mean']),np.asarray(inputs['nhu_variance'])
    Psi=np.array([np.diag(nv[k])+np.outer(np.conj(nm[k]),nm[k]) for k in range(nm.shape[0])])
    return Q,Psi,means,C


def evaluate(Q,Psi,W,noise):
    allQ=np.concatenate((Q,Psi)); received=np.real(np.einsum('nj,unm,mj->uj',np.conj(W),allQ,W))
    desired=np.diag(received);den=np.sum(received,axis=1)-desired+noise
    if np.min(den)<=0:raise ValueError('Nonpositive statistical denominator')
    sinr=desired/den
    return {'sinr':sinr,'hu_sum_rate':float(np.sum(np.log2(1+sinr[:len(Q)]))),
            'total_power':float(np.sum(abs(W)**2)),'metric':'source_ratio_of_expected_powers_NOT_exact_ergodic_rate'}


def auxiliaries(Q,Psi,W,noise):
    allQ=np.concatenate((Q,Psi)); D=[factor(q) for q in allQ]
    received=np.array([np.sum(abs(d@W)**2,axis=0) for d in D]); desired=np.diag(received)
    den=np.sum(received,axis=1)-desired+noise
    z=np.array([d@W[:,j]/den[j] for j,d in enumerate(D)])
    return D,z,den


def qt_bounds(D,z,W,noise):
    J=W.shape[1];out=[]
    for j,d in enumerate(D):
        others=[i for i in range(J) if i!=j]
        den=float(np.sum(abs(d@W[:,others])**2)+noise)
        out.append(2*np.real(np.vdot(z[j],d@W[:,j]))-np.vdot(z[j],z[j]).real*den)
    return np.asarray(out)


def active_qt_update(Q,Psi,W0,noise,power,target,solver='CLARABEL',solver_options=None):
    """Same vector-QT objective, exact-QT erratum for full-rank NHU QoS."""
    U,N=Q.shape[:2];K=len(Psi);J=U+K;D,z,den=auxiliaries(Q,Psi,W0,noise)
    V=cp.Variable((N,J),complex=True);constraints=[complex_squares(V)<=1];bounds=[]
    for j,d in enumerate(D):
        others=[i for i in range(J) if i!=j];dz=d*np.sqrt(power/noise);az=z[j]*np.sqrt(noise)
        coefficient=np.linalg.norm(az)
        weighted=complex_squares(coefficient*(dz@V[:,others]))+coefficient**2
        lower=2*cp.real(np.conj(az)@(dz@V[:,j]))-weighted;bounds.append(lower)
        if j>=U:constraints.append(lower>=target[j-U])
    log_scale=1+evaluate(Q,Psi,W0,noise)['sinr'][:U]
    problem=cp.Problem(cp.Maximize(cp.sum(cp.log(cp.multiply(1/log_scale,1+cp.hstack(bounds[:U]))))/np.log(2)+np.sum(np.log2(log_scale))),constraints)
    attempts=[];controls=[dict(solver_options or {})]
    if solver=='CLARABEL':controls.extend([dict(solver_options or {},equilibrate_max_iter=50),dict(solver_options or {},static_regularization_constant=1e-12),dict(solver_options or {},equilibrate_max_iter=50,static_regularization_constant=1e-12)])
    last_error=None
    backend_controls=[(solver,c) for c in controls]
    if solver=='CLARABEL':backend_controls.append(('SCS',{'eps':1e-8,'max_iters':200000,'acceleration_lookback':10}))
    for backend,control in backend_controls:
        try:
            problem.solve(solver=backend,**control)
            if problem.status not in ('optimal','optimal_inaccurate') or V.value is None:raise cp.error.SolverError('Statistical QT status '+str(problem.status))
            trial=evaluate(Q,Psi,V.value*np.sqrt(power),noise);before_trial=evaluate(Q,Psi,W0,noise)
            primal=max(0,trial['total_power']/power-1,float(np.max(target-trial['sinr'][U:])))
            accepted=bool(primal<1e-5 and trial['hu_sum_rate']>=before_trial['hu_sum_rate']-1e-6)
            attempts.append({'backend':backend,'options':control,'status':problem.status,'physical_violation':primal,'accepted':accepted})
            if accepted:break
            last_error=cp.error.SolverError('Statistical QT physical/objective gate failed')
        except cp.error.SolverError as error:
            last_error=error;attempts.append({'backend':backend,'options':control,'error':str(error),'accepted':False})
    else:
        last_error.receipt={'block':'corrected_statistical_QT','same_problem_numerical_attempts':attempts}
        last_error.fixture={'Q':Q,'Psi':Psi,'W0':W0,'noise':noise,'power':power,'target':target}
        raise last_error
    if problem.status not in ('optimal','optimal_inaccurate') or V.value is None:raise RuntimeError('Corrected statistical QT '+str(problem.status))
    W=V.value*np.sqrt(power);before=evaluate(Q,Psi,W0,noise);after=evaluate(Q,Psi,W,noise)
    old=qt_bounds(D,z,W0,noise);new=qt_bounds(D,z,W,noise)
    diagnostics=solver_diagnostics(problem)
    diagnostics['same_problem_numerical_attempts']=attempts
    physical=max(0,after['total_power']/power-1,float(np.max(target-after['sinr'][U:])))
    diagnostics['constraint_max_relative_violation']=max(diagnostics['constraint_max_relative_violation'],physical)
    diagnostics['qt_bound_max_violation']=max(0,float(np.max(new-after['sinr'])))
    return W,{'before':before,'after':after,'solver_status':problem.status,'solver_diagnostics':diagnostics,
              'qt_tightness_error':float(np.max(abs(old-before['sinr']))),
              'qt_bound_max_violation':diagnostics['qt_bound_max_violation'],
              'qos_lower_bounds':new[U:],'qos_auxiliaries_are_exact_vector_QT':True}


def feasible_initialization(Q,Psi,means,nhu_means,noise,power,target,solver='CLARABEL',solver_options=None):
    """Conservative LoS lower bound ONLY to initialize the full covariance QT.

    Every resulting initializer is independently checked against full-Psi QoS.
    No LoS-only evaluation or production optimization is performed.
    """
    U,N=means.shape;K=len(Psi);J=U+K;V=cp.Variable((N,J),complex=True);constraints=[complex_squares(V)<=1]
    for k in range(K):
        j=U+k;others=[i for i in range(J) if i!=j];d=factor(Psi[k])*np.sqrt(power/noise)
        desired=nhu_means[k]@V[:,j]*np.sqrt(power/noise)
        field=d@V[:,others]
        constraints.extend([cp.imag(desired)==0,cp.norm(cp.hstack([cp.vec(cp.real(field),order='F'),cp.vec(cp.imag(field),order='F'),1]))<=cp.real(desired)/np.sqrt(target[k])])
    # Small, optimized HU initialization is a disclosed numerical start only.
    hu_terms=[cp.real(means[u]@V[:,u]) for u in range(U)]
    problem=cp.Problem(cp.Maximize(cp.sum(cp.hstack(hu_terms))),constraints)
    problem.solve(solver=solver,**(solver_options or {}))
    if problem.status not in ('optimal','optimal_inaccurate') or V.value is None:raise RuntimeError('Statistical feasible initializer: '+str(problem.status))
    W=V.value*np.sqrt(power);e=evaluate(Q,Psi,W,noise)
    if e['total_power']>power*(1+1e-5) or np.min(e['sinr'][U:]-target)<-1e-5:raise RuntimeError('Statistical initializer failed full-moment QoS')
    return W


def qt_loop(Q,Psi,W0,noise,power,target,settings):
    W=W0.copy();history=[evaluate(Q,Psi,W,noise)['hu_sum_rate']];records=[]
    for _ in range(settings['qt_max_iterations']):
        candidate,info=active_qt_update(Q,Psi,W,noise,power,target,settings['solver'],settings['solver_options'])
        value=info['after']['hu_sum_rate'];records.append(dict(info['solver_diagnostics'],qt_bound_max_violation=info['qt_bound_max_violation']))
        if value<history[-1]-1e-6:raise RuntimeError('Corrected statistical QT exact objective decreased')
        W=candidate;history.append(value)
        if (history[-1]-history[-2])/max(abs(history[-2]),1e-12)<settings['relative_tolerance']:break
    return W,history,relative_stop(history,settings['qt_max_iterations'],settings['relative_tolerance']),records


def rate_value_gradient(inputs,phi,W,noise):
    Q,Psi,mean,C=moments(inputs,phi);U=len(Q);J=W.shape[1];G=inputs['matrix_mean'];r=inputs['ground_mean']
    received=np.real(np.einsum('nj,unm,mj->uj',np.conj(W),Q,W));total=np.sum(received,axis=1)+noise
    desired=received[np.arange(U),np.arange(U)];den=total-desired
    value=float(np.sum(np.log2(total/den)));grad=np.zeros(len(phi))
    projection=mean@W
    for m in range(len(phi)):
        dm=1j*phi[m]*r[:,m,None]*G[m];dr=2*np.real(np.conj(projection)*(dm@W));dt=np.sum(dr,axis=1)
        dd=dt-dr[np.arange(U),np.arange(U)]
        grad[m]=np.sum(dt/total-dd/den)/np.log(2)
    return value,1j*np.asarray(phi)*grad


def normalized_projector(mean,variance):
    """Exact E[h h^H/||h||²], finite-Rician diagonal covariance, no ratio swap."""
    m=np.asarray(mean,complex);v=np.asarray(variance,float);scale=float(np.sum(abs(m)**2+v));m=m/np.sqrt(scale);v=v/scale
    if np.max(v)==0:return np.outer(m,np.conj(m))/np.vdot(m,m).real
    def integrand(s):
        if s>=1:return np.zeros((len(m),len(m)),complex)
        t=s/(1-s);inv=1/(1+t*v);lap=np.exp(-np.sum(np.log1p(t*v))-t*np.sum(abs(m)**2*inv))
        return lap*(np.diag(v*inv)+np.outer(m*inv,np.conj(m*inv)))/(1-s)**2
    P,error=quad_vec(integrand,0,1,epsabs=1e-11,epsrel=1e-11)
    if abs(np.trace(P).real-1)>1e-8:raise RuntimeError('Normalized projector quadrature did not converge')
    return (P+P.conj().T)/2


def expected_projector_square(inputs):
    projectors=[normalized_projector(np.conj(m),v) for m,v in zip(inputs['nhu_mean'],inputs['nhu_variance'])]
    N=len(projectors[0]);B=np.eye(N,dtype=complex)-sum(projectors)
    for k,P in enumerate(projectors):
        for j,R in enumerate(projectors):
            if k!=j:B+=P@R
    return (B+B.conj().T)/2


def pair_moment(inputs,phi,u,v,derivative=None):
    """Exact shared-satellite-RIS fourth moment, by conditional Gaussian identity."""
    d=np.asarray(inputs['direct_mean']);dv=np.asarray(inputs['direct_variance']);G=np.asarray(inputs['matrix_mean']);gv=np.asarray(inputs['matrix_variance'])
    r=np.asarray(inputs['ground_mean']);rv=np.asarray(inputs['ground_variance']);A=G.T*np.asarray(phi)[None,:]
    B=A.conj().T@A+np.diag(np.sum(gv,axis=1));mu,mv=r[u],r[v];vu,vv=rv[u],rv[v]
    bu=d[u]+A@mu;bv=d[v]+A@mv
    eu=dv[u]+gv.T@(abs(mu)**2+vu);ev=dv[v]+gv.T@(abs(mv)**2+vv)
    eb_u=abs(bu)**2+abs(A)**2@vu;eb_v=abs(bv)**2+abs(A)**2@vv
    b=np.conj(d[u])@A+np.conj(mu)@B;c=A.conj().T@d[v]+B@mv
    t=np.vdot(d[u],d[v])+np.conj(d[u])@A@mv+np.conj(mu)@A.conj().T@d[v]+np.conj(mu)@B@mv
    value=float(abs(t)**2+np.sum(vv*abs(b)**2)+np.sum(vu*abs(c)**2)+np.sum(vu[:,None]*vv[None,:]*abs(B)**2)+eb_u@ev+eb_v@eu+eu@ev)
    if derivative is None:return value
    dA=derivative;dB=dA.conj().T@A+A.conj().T@dA
    db=np.conj(d[u])@dA+np.conj(mu)@dB;dc=dA.conj().T@d[v]+dB@mv
    dt=np.conj(d[u])@dA@mv+np.conj(mu)@dA.conj().T@d[v]+np.conj(mu)@dB@mv
    debu=2*np.real(np.conj(bu)*(dA@mu))+2*np.real(np.conj(A)*dA)@vu
    debv=2*np.real(np.conj(bv)*(dA@mv))+2*np.real(np.conj(A)*dA)@vv
    change=float(2*np.real(np.conj(t)*dt+np.sum(vv*np.conj(b)*db)+np.sum(vu*np.conj(c)*dc)+np.sum(vu[:,None]*vv[None,:]*np.conj(B)*dB))+debu@ev+debv@eu)
    return value,change


def criterion_value_gradient(inputs,phi,projector_square):
    Q,_,mean,_=moments(inputs,phi);U=len(Q);G=inputs['matrix_mean'];r=inputs['ground_mean']
    f5=float(np.real(np.einsum('unm,mn->',Q,projector_square)))
    A=G.T*np.asarray(phi)[None,:];T=A.conj().T@A;gv=inputs['matrix_variance'];B=T+np.diag(np.sum(gv,axis=1))
    # Exact all-coordinate derivatives. dT has only its selected row/column,
    # so no repeated matrix multiplication is necessary inside the RGD loop.
    grad=np.zeros(len(phi));f6=0.0
    for u in range(U):
        grad+=2*np.real(1j*r[u]*(np.conj(mean[u])@projector_square.T@A))
        for v in range(u):
            du,dv=inputs['direct_mean'][u],inputs['direct_mean'][v];mu,mv=r[u],r[v];vu,vv=inputs['ground_variance'][u],inputs['ground_variance'][v]
            bu,bv=du+A@mu,dv+A@mv;eu=inputs['direct_variance'][u]+gv.T@(abs(mu)**2+vu);ev=inputs['direct_variance'][v]+gv.T@(abs(mv)**2+vv)
            eb_u=abs(bu)**2+abs(A)**2@vu;eb_v=abs(bv)**2+abs(A)**2@vv
            b=np.conj(du)@A+np.conj(mu)@B;c=A.conj().T@dv+B@mv
            t=np.vdot(du,dv)+np.conj(du)@A@mv+np.conj(mu)@A.conj().T@dv+np.conj(mu)@B@mv
            f6+=float(abs(t)**2+np.sum(vv*abs(b)**2)+np.sum(vu*abs(c)**2)+np.sum(vu[:,None]*vv[None,:]*abs(B)**2)+eb_u@ev+eb_v@eu+eu@ev)
            bt=np.conj(du)@A+np.conj(mu)@T;ct=A.conj().T@dv+T@mv
            db=1j*np.diag(bt)-1j*np.conj(mu)[:,None]*T
            dc=1j*mv[:,None]*T.T-1j*np.diag(ct)
            dt=1j*(bt*mv-np.conj(mu)*ct)
            dBsum=1j*vv*np.sum(vu[:,None]*np.conj(B)*T,axis=0)-1j*vu*np.sum(vv[None,:]*np.conj(B)*T,axis=1)
            change=2*np.real(np.conj(t)*dt+db@(vv*np.conj(b))+dc@(vu*np.conj(c))+dBsum
                             +1j*mu*((np.conj(bu)*ev)@A)+1j*mv*((np.conj(bv)*eu)@A))
            grad-=change
    return float(f5-f6),1j*np.asarray(phi)*grad


def phase_rgd(phi,value_gradient,settings):
    phi=np.asarray(phi).copy();value,g=value_gradient(phi);history=[value]
    for _ in range(settings['rgd_max_iterations']):
        norm2=float(np.vdot(g,g).real)
        if np.sqrt(norm2)<=settings['gradient_tolerance']:break
        # Original RGD direction/retraction/Armijo; a unit initial tangent
        # displacement is the disclosed unreported stepsize control. No tiny
        # gradient is mistaken for convergence and no tolerance is relaxed.
        alpha=1.0/np.sqrt(norm2)
        for _ in range(60):
            trialphi=phi+alpha*g;trialphi/=abs(trialphi);trial,trialg=value_gradient(trialphi)
            if trial-value>=1e-4*alpha*norm2:break
            alpha/=2
        else:raise RuntimeError('Statistical original RGD Armijo search failed')
        phi,value,g=trialphi,trial,trialg;history.append(value)
    return phi,history,gradient_stop(np.linalg.norm(g),len(history)-1,settings['rgd_max_iterations'],settings['gradient_tolerance'])


def printed_soc_update(*args,**kwargs):
    raise RuntimeError('Original printed Eq3-46 is not equivalent to full-rank Eq3-41 QoS; select explicit corrected_QT_erratum, never a silent substitute.')
