"""Numerically structured form of ONE original positive-alpha QCQP.

No optimizer loop, new model, jitter, eigenvalue clipping or tolerance change.
Only the supplied captured fixed subproblem is validated. The communication
right-hand side is kept factored, rather than projecting a rounded large P.
"""
import numpy as np

def solve_fixed_original_qcqp(w,fc,mu,eta,lip,ga,den,rho,power,bisection_tolerance):
    w=np.asarray(w);fc=np.asarray(fc);mu=np.asarray(mu);eta=np.asarray(eta);lip=np.asarray(lip);ga=np.asarray(ga)
    m,k=fc.shape
    if w.shape[0]!=m or ga.shape!=w.shape or not k<=m or w.shape[1]<k:raise ValueError('Validated layout requires K<=M and original padded W')
    if not den>0 or not rho>0 or not power>0 or not bisection_tolerance>0:raise ValueError('Positive original denominator/rho/power/tolerance required')
    if np.any(mu<0) or not all(np.all(np.isfinite(x)) for x in (w,fc,mu,eta,lip,ga)):raise ValueError('Only finite original nonnegative-mu case supported here')
    alpha=rho*float(np.sum(lip))/(2*den);beta=rho/(2*den)
    if not alpha>0:raise ValueError('Only original strictly-positive alpha is validated; no repair is introduced')
    log2=np.log(2.0);root=np.sqrt(1+mu)/np.sqrt(log2);magnitude=np.abs(eta)
    scale=root*magnitude
    gamma=np.zeros_like(eta,dtype=complex);active=magnitude!=0
    gamma[active]=root[active]*(eta[active]/magnitude[active])
    factor=fc*scale[None,:]
    left,singular,right_h=np.linalg.svd(factor,full_matrices=True)
    sigma2=np.r_[singular**2,np.zeros(m-k)]
    comm_coordinates=np.zeros_like(w)
    comm_coordinates[:k,:k]=(singular[:,None]*right_h)*gamma[None,:]
    projected_w=left.conj().T@w;projected_ga=left.conj().T@ga
    sensing_coordinates=alpha*projected_w-beta*projected_ga
    coordinates=comm_coordinates+sensing_coordinates
    row=np.sum(abs(coordinates)**2,axis=1)
    diagonal=alpha+sigma2
    def transmit(nu):return float(np.sum(row/(diagonal+nu)**2))
    nu=0.;bisects=0;doublings=0;lo=hi=None
    if transmit(0)>power:
        lo,hi=0.,1.
        while transmit(hi)>power:hi*=2;doublings+=1
        while hi-lo>bisection_tolerance*max(1,hi):
            middle=(lo+hi)/2
            if transmit(middle)>power:lo=middle
            else:hi=middle
            bisects+=1
        nu=hi
    solution=left@(coordinates/(diagonal+nu)[:,None])
    reconstructed_comm=np.zeros_like(w);reconstructed_comm[:,:k]=factor*gamma[None,:]
    reconstructed_sensing=alpha*w-beta*ga
    return solution,dict(alpha=alpha,beta=beta,nu=nu,bisection_steps=bisects,bracket_doublings=doublings,bracket_lo=lo,bracket_hi=hi,
        power_from_basis=transmit(nu),actual_binary64_power=float(np.sum(abs(solution)**2)),original_power_cap=power,bisection_tolerance=bisection_tolerance,
        factor=factor,left=left,singular=singular,right_h=right_h,gamma=gamma,comm_coordinates=comm_coordinates,sensing_coordinates=sensing_coordinates,
        total_coordinates=coordinates,original_positive_diagonal=diagonal,reconstructed_communication_P=reconstructed_comm,reconstructed_sensing_P=reconstructed_sensing,
        no_actual_bad_Q_or_assembled_communication_P_used=True,exact_zero_eta_branch_only=True,no_rank_threshold_clamp_jitter_or_eigh=True)
