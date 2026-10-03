"""Paper equations, not the old reduced MRT-position implementation.

CVXPY is only a backend for the paper's convex coordinate subproblems.
All tolerances, budgets, random inputs and equation interpretations are caller
supplied. Correlated-ZF Eqs.72/74 are deliberately not assigned a new formula.
"""
from __future__ import annotations
import numpy as np


def los(t, c):
    return np.exp(2j*np.pi/float(c["wavelength"])*(t@np.asarray(c["directions"]).T))


def mrt_statistics(t, c, antenna=None):
    n, m = len(t), len(c["beta"])
    beta, kap = np.asarray(c["beta"]), np.asarray(c["rician"])
    directions = np.asarray(c["directions"])
    wave = 2*np.pi/c["wavelength"]
    numerator = beta**2*(n*n+n*(2*kap+1)/(kap+1)**2)
    denominator = np.asarray(c["noise"])*n*beta.sum()/c["power"]
    gd = np.zeros((m,n,2)); psi = np.zeros(m)
    for u in range(m):
        bound = np.zeros((2,2))
        for v in range(m):
            if v == u:
                continue
            d = directions[u]-directions[v]
            e = np.exp(1j*wave*(t@d)); z = e.sum()
            q = beta[u]*beta[v]*kap[u]*kap[v]/((kap[u]+1)*(kap[v]+1))
            denominator[u] += q*abs(z)**2+beta[u]*beta[v]*n*(kap[u]+kap[v]+1)/((kap[u]+1)*(kap[v]+1))
            gd[u] += 2*q*np.real(np.conj(z)*1j*wave*e[:,None]*d)
            if antenna is not None:
                bound += q*abs(z-e[antenna])*abs(np.outer(d,d))
        if antenna is not None:
            interpretation = c["interpretations"]["mrt_curvature"]
            if interpretation == "equation_29a_max_eigenvalue":
                psi[u] = 2*wave**2*np.linalg.eigvalsh(bound)[-1]
            elif interpretation == "equation_29b_as_printed":
                radicand = (bound[0,0]-bound[1,1])**2-4*bound[0,1]**2
                if radicand < 0:
                    raise ValueError("Printed Eq.29b gives a negative radicand; author clarification required.")
                psi[u] = wave**2*(bound.trace()+np.sqrt(radicand))
            else:
                raise ValueError("Explicit MRT_CURVATURE interpretation is required.")
    weight = numerator/(np.log(2)*denominator*(denominator+numerator))
    rates = np.log2(1+numerator/denominator)
    gradient = -(weight[:,None,None]*gd).sum(axis=0)
    return float(rates.sum()), gradient, float(weight@psi), rates


def zf_statistics(t, c):
    h = los(t,c); n,m = h.shape
    if n <= m:
        raise ValueError("The paper ZF lower bound requires N>M.")
    kap, beta = np.asarray(c["rician"]), np.asarray(c["beta"])
    scale = np.sqrt(kap/(kap+1))
    sigma = np.diag(1/(kap+1))+h.conj().T@h*scale[:,None]*scale[None,:]/n
    inverse = np.linalg.solve(sigma,np.eye(m))
    eta = c["power"]*beta*(n-m)/(m*np.asarray(c["noise"]))
    rates = np.log2(1+eta/np.real(np.diag(inverse)))
    return float(rates.sum()), rates, sigma, eta


def zf_surrogate(t, c, antenna):
    """Eqs.41-65, retaining the coordinate's Y/X rational identity."""
    h = los(t,c); n,m = h.shape
    kap = np.asarray(c["rician"])
    scale = np.diag(np.sqrt(kap/(kap+1)))
    g = h[antenna].conj()
    theta1 = h.conj().T@h-np.outer(g,g.conj())
    theta2 = np.diag(1/(kap+1))+scale@theta1@scale/n
    inv = np.linalg.solve(theta2,np.eye(m))
    y = n/m*np.eye(m)+scale@inv@scale
    dirs = np.asarray(c["directions"]); wave = 2*np.pi/c["wavelength"]
    chi, f0, grad, curvature, ratio, qrows = [], [], [], [], [], []
    a = float(np.real(g.conj()@y@g))
    for u in range(m):
        ell = (inv@scale)[u,:].conj()
        x = inv[u,u].real*y-np.outer(ell,ell.conj())
        b = float(np.real(g.conj()@x@g))
        lmax = np.linalg.eigvalsh(x)[-1]
        q = 2/b*(g.conj()@(y-a/b*(x-lmax*np.eye(m))))
        const = -a/b**2*(2*lmax*m-b)
        phase = wave*(dirs@t[antenna])-np.angle(q)
        f = float(np.sum(abs(q)*np.cos(phase)))
        dg = -wave*(abs(q)*np.sin(phase))@dirs
        bound = sum(abs(q[v])*abs(np.outer(dirs[v],dirs[v])) for v in range(m))
        xi = wave**2*np.linalg.eigvalsh(bound)[-1]
        chi.append(const); f0.append(f); grad.append(dg); curvature.append(xi)
        ratio.append(a/b); qrows.append(q)
    return {"chi":np.array(chi),"f0":np.array(f0),"gradient":np.array(grad),
            "curvature":np.array(curvature),"ratio":np.array(ratio),"q":np.array(qrows),"Y":y}


def coordinate_constraints(cp, x, t, c, antenna):
    lo,hi = np.asarray(c["region_lower"]),np.asarray(c["region_upper"])
    cons = [x>=lo, x<=hi]
    for v in range(len(t)):
        if v != antenna:
            d = t[antenna]-t[v]
            cons.append(2*d@(x-t[antenna])+d@d>=c["minimum_distance"]**2)
    return cons


def solve_coordinate(t, c, antenna, mode):
    import cvxpy as cp
    x = cp.Variable(2); delta = x-t[antenna]
    cons = coordinate_constraints(cp,x,t,c,antenna)
    if mode == "MRT":
        value, gradient, curvature, _ = mrt_statistics(t,c,antenna)
        objective = value+gradient[antenna]@delta-curvature/2*cp.sum_squares(delta)
    elif mode == "ZF":
        if c["interpretations"].get("zf_spacing") != "P5n_with_equation_30_spacing":
            raise ValueError("Explicit ZF_CROSS_REFERENCES interpretation required.")
        value,_,_,eta = zf_statistics(t,c)
        s = zf_surrogate(t,c,antenna)
        minor = s["chi"]+s["f0"]+s["gradient"]@delta-s["curvature"]/2*cp.sum_squares(delta)
        objective = cp.sum(cp.log(1+cp.multiply(eta,minor)))/np.log(2)
    else:
        raise ValueError(mode)
    problem = cp.Problem(cp.Maximize(objective),cons)
    spec = c["convex_solver"]
    problem.solve(solver=spec["name"], **spec["options"])
    if problem.status != "optimal":
        raise RuntimeError(f"{mode} coordinate {antenna}: solver status {problem.status}; no substitute update is applied.")
    candidate = np.asarray(x.value)
    trial = t.copy(); trial[antenna] = candidate
    actual = mrt_statistics(trial,c)[0] if mode == "MRT" else zf_statistics(trial,c)[0]
    lower = float(objective.value)
    tol = c["verification_tolerance"]
    if actual < lower-tol or actual < value-tol:
        raise RuntimeError(f"{mode}: source surrogate/update validation failed.")
    return trial, {"before":value,"after":actual,"surrogate":lower,"lower_bound_gap":actual-lower}


def optimize(initial, c, mode):
    t = np.asarray(initial,dtype=float).copy()
    value = mrt_statistics(t,c)[0] if mode == "MRT" else zf_statistics(t,c)[0]
    history = [value]; positions=[t.tolist()]; coordinates = []; converged = False
    for sweep in range(c["maximum_AO_iterations"]):
        for n in range(len(t)):
            t, record = solve_coordinate(t,c,n,mode)
            record.update({"sweep":sweep,"antenna":n}); coordinates.append(record)
        value = mrt_statistics(t,c)[0] if mode == "MRT" else zf_statistics(t,c)[0]
        history.append(value)
        positions.append(t.tolist())
        if (history[-1]-history[-2])/abs(history[-2]) < c["fractional_increase_threshold"]:
            converged = True; break
    return t,{"objective":history,"positions":positions,"coordinate_updates":coordinates,"converged":converged,
             "termination":"fractional_increase" if converged else "configured_iteration_cap"}


def spatial_covariance(t, c):
    from scipy.special import j0
    distances = np.linalg.norm(t[:,None]-t[None,:],axis=2)
    return j0(2*np.pi*distances/c["wavelength"])


def correlated_mrt(t,c):
    """Only the dimensionally defined Eq.69, evaluated at supplied positions."""
    h=los(t,c); n,m=h.shape; s=spatial_covariance(t,c)
    beta,kap=np.asarray(c["beta"]),np.asarray(c["rician"])
    q=np.real(np.sum(h.conj()*(s@h),axis=0)); trace=float(np.trace(s@s))
    numerator=beta**2*(n*n+(2*kap*q+trace)/(kap+1)**2)
    denominator=np.asarray(c["noise"])*n*beta.sum()/c["power"]
    gram=abs(h.conj().T@h)**2
    for u in range(m):
        for v in range(m):
            if u!=v:
                denominator[u]+=beta[u]*beta[v]*(kap[u]*kap[v]*gram[u,v]+kap[u]*q[u]+kap[v]*q[v]+trace)/((kap[u]+1)*(kap[v]+1))
    return float(np.log2(1+numerator/denominator).sum())


def correlated_zf_bound(t,c):
    raise NotImplementedError("Printed Eqs.72/74 multiply MxM and NxN matrices; an author-approved formula is required. No replacement is implemented.")


def instantaneous(t,c,nlos,mode,correlated=False):
    nlos=np.asarray(nlos,dtype=complex)
    beta,kap=np.asarray(c["beta"]),np.asarray(c["rician"])
    hb=los(t,c); n,m=hb.shape
    if correlated:
        s=spatial_covariance(t,c); val,vec=np.linalg.eigh(s)
        if val.min() < -c["verification_tolerance"]:
            raise ValueError("Bessel covariance not PSD within specified tolerance.")
        # Spectral square root is precisely S^(1/2) in Eq.68, not a new model.
        root=(vec*np.sqrt(np.maximum(val,0)))@vec.T
        nlos=np.einsum("ab,sbc->sac",root,nlos)
    rates=[]; powers=[]; leakage=[]
    for sample in nlos:
        h=hb*np.sqrt(beta*kap/(kap+1))+sample*np.sqrt(beta/(kap+1))
        if mode=="MRT":
            w=h*np.sqrt(c["power"]/np.sum(abs(h)**2))
        elif mode=="ZF":
            v=h@np.linalg.solve(h.conj().T@h,np.eye(m))
            w=v/np.linalg.norm(v,axis=0)*np.sqrt(c["power"]/m)
        else:
            raise ValueError(mode)
        hw=h.conj().T@w; gain=abs(hw)**2; signal=np.diag(gain)
        rates.append(float(np.log2(1+signal/(gain.sum(axis=1)-signal+np.asarray(c["noise"]))).sum()))
        powers.append(float(np.sum(abs(w)**2)))
        leakage.append(float(np.max(abs(hw-np.diag(np.diag(hw))))))
    return {"sample_sum_rates":rates,"mean_sum_rate":float(np.mean(rates)),"powers":powers,"off_diagonal_amplitude":leakage}


def power_qcqp(q,b,power,tolerance):
    """Exact KKT diagonal QCQP, including the inactive power constraint."""
    def at(nu):
        denom=q+nu
        out=np.zeros_like(b)
        nonzero=denom>0
        out[nonzero]=b[nonzero]/denom[nonzero]
        if np.any(abs(b[~nonzero])>tolerance):
            return None
        return out
    answer=at(0)
    if answer is not None and np.sum(abs(answer)**2)<=power:
        return answer
    lo,hi=0.0,1.0
    while np.sum(abs(at(hi))**2)>power:
        hi*=2
    while hi-lo>tolerance*max(1,hi):
        mid=(lo+hi)/2
        if np.sum(abs(at(mid))**2)>power: lo=mid
        else: hi=mid
    return at(hi)


def channel_rate(h,w,noise):
    z=h.conj().T@w; power=abs(z)**2; signal=np.diag(power)
    return float(np.log2(1+signal/(power.sum(axis=1)-signal+noise)).sum())


def fixed_array_benchmark(h,c,kind):
    """The five-scheme benchmark objectives; QT does not imply global optimality."""
    noise=np.asarray(c["noise"]); h=h/np.sqrt(noise)[None,:]
    n,m=h.shape; p=c["power"]; spec=c["benchmark_solver"]
    if kind=="FPA-ZF":
        v=h@np.linalg.solve(h.conj().T@h,np.eye(m)); v/=np.linalg.norm(v,axis=0)
        gain=abs(np.diag(h.conj().T@v))**2; cost=1/gain
        lo,hi=0.,p+max(cost)
        while hi-lo>spec["bisection_tolerance"]:
            mid=(lo+hi)/2
            if np.maximum(mid-cost,0).sum()>p: hi=mid
            else: lo=mid
        w=v*np.sqrt(np.maximum(lo-cost,0))[None,:]
        return channel_rate(h,w,np.ones(m)),{"iterations":0,"converged":True}
    v=h/np.linalg.norm(h,axis=0)
    w=v*np.sqrt(p/m); history=[channel_rate(h,w,np.ones(m))]
    converged=False
    for _ in range(spec["maximum_iterations"]):
        z=h.conj().T@w; total=np.sum(abs(z)**2,axis=1)+1
        signal=abs(np.diag(z))**2; mu=signal/(total-signal); eta=np.diag(z)/total
        if kind=="FPA-MRT":
            hv=h.conj().T@v
            q=np.sum(((1+mu)*abs(eta)**2)[:,None]*abs(hv)**2,axis=0)/np.log(2)
            b=(1+mu)*np.real(np.conj(eta)*np.diag(hv))/np.log(2)
            amp=power_qcqp(q,b,p,spec["bisection_tolerance"])
            w=v*amp[None,:]
        elif kind=="FPA-OPT":
            q=(h*((1+mu)*abs(eta)**2)[None,:])@h.conj().T/np.log(2)
            b=h*((1+mu)*eta)[None,:]/np.log(2)
            val,vec=np.linalg.eigh(q); projected=vec.conj().T@b
            row_energy=np.sum(abs(projected)**2,axis=1)
            scale=max(float(val.max()),1)
            if val.min() < -spec["spectral_zero_tolerance"]*scale:
                raise RuntimeError("QT QCQP matrix failed its PSD identity.")
            # Only negative roundoff is clipped: small positive eigenvalues are
            # retained. Discarding them can incorrectly remove range(Q) modes.
            val[val<0]=0
            rownorm=np.sqrt(row_energy)
            diagonal=power_qcqp(val,rownorm,p,spec["bisection_tolerance"])
            denominator=np.divide(rownorm,diagonal,out=np.ones_like(rownorm),where=diagonal>0)
            w=vec@(projected/denominator[:,None])
        else:
            raise ValueError(kind)
        history.append(channel_rate(h,w,np.ones(m)))
        if history[-1]<history[-2]-c["verification_tolerance"]:
            raise RuntimeError("Fixed-array QT benchmark decreased its actual sum rate.")
        if (history[-1]-history[-2])/abs(history[-2])<spec["fractional_tolerance"]:
            converged=True; break
    return history[-1],{"iterations":len(history)-1,"converged":converged,"objective":history}
