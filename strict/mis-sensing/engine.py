"""Strict MIS equations and product-manifold solvers; NumPy only.
No scheduling elimination, phase-only surrogate, incumbent replacement or hidden cap.
Rank-one G_k factorization is algebraically exact, not a changed sensing model.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

BLOCKS = ("phi", "theta", "X", "eta")

def inner(a, b):
    return float(np.real(np.vdot(a, b)))

def simplex(y):
    z = np.sort(y, axis=1)[:, ::-1]
    cs = np.cumsum(z, axis=1) - 1
    j = np.arange(1, y.shape[1]+1)
    active = z-cs/j > 0
    r = np.sum(active, axis=1)-1
    tau = cs[np.arange(y.shape[0]), r]/(r+1)
    return np.maximum(y-tau[:, None], 0)

def project(z, g):
    out = {}
    for b in g:
        if b in ("phi", "theta"):
            out[b] = g[b]-np.real(g[b]*np.conj(z[b]))*z[b]
        elif b == "X":
            out[b] = g[b]-np.mean(g[b], axis=1, keepdims=True)
        else:
            out[b] = g[b]
    return out

def retract(z, d, alpha):
    out = {b: np.array(z[b], copy=True) for b in z}
    for b in d:
        v = z[b]+alpha*d[b]
        if b in ("phi", "theta"):
            out[b] = v/np.abs(v)
        elif b == "X":
            out[b] = simplex(v)
        else:
            out[b] = v
    return out

def norm(g):
    return np.sqrt(sum(inner(x, x) for x in g.values()))

def projected_kkt_norm(z,g):
    """Euclidean simplex projection may hit its boundary; row-mean norm then
    includes a normal component and is not a KKT residual. Report both.
    """
    residual=dict(g)
    residual["X"]=z["X"]-simplex(z["X"]-g["X"])
    return norm(residual)

def self_excluded_sum(values,targets):
    """Sum every other echo explicitly, without total-minus-wanted cancellation.

    The same helper also sums signed exact echo increments. No interferer is
    removed, and no metric, physical normalization or search direction changes.
    """
    rows=np.arange(values.shape[0])
    return np.stack([np.sum(values[rows!=k],axis=0) for k in range(targets)])

class Model:
    def __init__(self, config):
        self.config = config
        mr, mc = config["ms1"]
        nr, nc = config["ms2"]
        self.M, self.N = mr*mc, nr*nc
        if nr == 0 or nc == 0:
            self.indices = np.empty((1, 0), dtype=int)
        else:
            if nr>mr or nc>mc:
                raise ValueError("MS2 must fit inside MS1")
            self.indices = np.array([[ (r+i)*mc+c+j for i in range(nr) for j in range(nc)]
                                     for r in range(mr-nr+1) for c in range(mc-nc+1)])
        self.U = len(self.indices)
        coords = np.array([[r, c] for r in range(mr) for c in range(mc)])
        az = np.deg2rad(config["azimuth_deg"])
        el = np.deg2rad(config["elevation_deg"])
        direction = np.column_stack((np.sin(el)*np.cos(az), np.sin(el)*np.sin(az)))
        self.c = np.exp(2j*np.pi*config["spacing_over_wavelength"]*(direction@coords.T))
        incidence = config["incidence_direction_cosines"]
        self.c *= np.exp(2j*np.pi*config["spacing_over_wavelength"]*(coords@incidence))[None,:]
        self.K = len(az)
        self.beta = np.broadcast_to(config.get("echo_beta_squared", 1), (len(az),)).copy()
        self.targets = config.get("number_of_targets", self.K)

    def fields(self, z):
        bar = np.ones((self.U, self.M), dtype=complex)
        for u, ix in enumerate(self.indices):
            bar[u, ix] = z["theta"]
        v = bar*z["phi"][None,:]
        q = self.c@v.T
        a = np.abs(q)**2
        return bar, v, q, a

    def metric(self, z, objective, derivative_weight=None, *, prepared_fields=None):
        # An explicit bundle only reuses the identical forward calculation;
        # no field, opponent, echo or derivative is approximated or removed.
        bar, v, q, a = self.fields(z) if prepared_fields is None else prepared_fields
        if objective == "communications":
            gamma = self.config["reference_snr"]*a
            echo_coeff = None
        else:
            S = self.beta[:,None]*a*a
            if objective == "sinr":
                noise = np.asarray(self.config["noise_over_power"])
                D = self_excluded_sum(S,self.targets)+noise
                gamma = S[:self.targets]/D
                if derivative_weight is not None:
                    W = derivative_weight
                    weighted_interference=W*S[:self.targets]/(D*D)
                    echo_coeff=np.empty_like(S)
                    for k in range(self.K):
                        if k<self.targets:
                            others=np.arange(self.targets)!=k
                            echo_coeff[k]=W[k]/D[k]-np.sum(weighted_interference[others],axis=0)
                        else:
                            echo_coeff[k]=-np.sum(weighted_interference,axis=0)
            elif objective == "pslr":
                mu = self.config["pslr_mu"]
                eps = self.config["pslr_epsilon"]
                gamma = np.empty((self.targets,self.U))
                echo_coeff = np.zeros_like(S) if derivative_weight is not None else None
                for k, opponents in enumerate(self.config["pslr_opponents"]):
                    ix = np.array(opponents, dtype=int)
                    ratios = S[k][None,:]/(S[ix]+eps)
                    mn = np.min(ratios, axis=0)
                    ex = np.exp(-(ratios-mn)/mu)
                    pi = ex/np.sum(ex,axis=0)
                    gamma[k] = mn-mu*np.log(np.sum(ex,axis=0))
                    if derivative_weight is not None:
                        wpi = derivative_weight[k][None,:]*pi
                        echo_coeff[k] += np.sum(wpi/(S[ix]+eps),axis=0)
                        echo_coeff[ix] -= wpi*S[k][None,:]/(S[ix]+eps)**2
            else:
                raise ValueError(objective)
        if derivative_weight is None:
            return gamma
        if objective == "communications":
            aq = 2*self.config["reference_snr"]*derivative_weight*q
        else:
            aq = 4*echo_coeff*self.beta[:,None]*a*q
        gv = np.conj(self.c).T@aq
        grad_phi = np.sum(np.conj(bar.T)*gv,axis=1)
        grad_theta = np.zeros(self.N,dtype=complex)
        for u, ix in enumerate(self.indices):
            grad_theta += np.conj(z["phi"][ix])*gv[ix,u]
        return gamma, grad_phi, grad_theta

    def communication_objective(self, z, mu, convention):
        gamma = self.metric(z,"communications")
        g = np.sum(z["X"]*gamma,axis=1)
        mn = np.min(g)
        ex = np.exp(-(g-mn)/mu)
        weights = ex/np.sum(ex)
        f = mn-mu*np.log(np.sum(ex))
        _, gp, gt = self.metric(z,"communications",weights[:,None]*z["X"])
        sign = -1 if convention == "maximize_negative_softmin" else 1
        if convention not in ("maximize_negative_softmin","literal_paper_descent_of_f"):
            raise ValueError("Explicit resolution of source sign contradiction required")
        eu = {"phi":sign*gp,"theta":sign*gt,"X":sign*weights[:,None]*gamma}
        return sign*f, eu, {"softmin":f,"min_relaxed_snr":float(np.min(g))}

    def augmented(self,z,lam,rho,objective):
        prepared=self.fields(z)
        gamma = self.metric(z,objective,prepared_fields=prepared)
        q = float(z["eta"])-np.sum(z["X"]*gamma,axis=1)
        chi = np.maximum(0,lam+rho*q)
        value = -float(z["eta"])+np.sum(chi*chi)/(2*rho)
        _, gp, gt = self.metric(z,objective,-chi[:,None]*z["X"],prepared_fields=prepared)
        eu = {"phi":gp,"theta":gt,"X":-chi[:,None]*gamma,
              "eta":np.asarray(-1+np.sum(chi))}
        return float(value),eu,{"q":q,"gamma":gamma}

    def constrained_kkt_certificate(self,z,lam,objective,stationarity_tolerance,feasibility_tolerance):
        """Independent residuals of the ORIGINAL constrained relaxed problem.

        This uses final multipliers directly, not ALM chi, objective change or
        an early-stop flag. Numerical tolerances are reported, never silently
        replaced by a test bound. Binary recovery is certified separately.
        """
        lam=np.asarray(lam)
        prepared=self.fields(z)
        gamma=self.metric(z,objective,prepared_fields=prepared)
        residual=float(z["eta"])-np.sum(z["X"]*gamma,axis=1)
        _,gp,gt=self.metric(z,objective,-lam[:,None]*z["X"],prepared_fields=prepared)
        eg={"phi":gp,"theta":gt,"X":-lam[:,None]*gamma,"eta":np.asarray(-1+np.sum(lam))}
        stationarity=float(projected_kkt_norm(z,project(z,eg)))
        primal=float(max(0,np.max(residual)))
        dual=float(max(0,-np.min(lam)))
        complementarity=float(np.max(np.abs(lam*residual)))
        phase=max((float(np.max(np.abs(np.abs(z[b])-1))) if z[b].size else 0.) for b in ("phi","theta"))
        simplex_error=float(max(np.max(np.abs(np.sum(z["X"],axis=1)-1)),max(0,-np.min(z["X"]))))
        feasible_storage=max(phase,simplex_error)<=32*np.finfo(float).eps
        verified=stationarity<stationarity_tolerance and primal<=feasibility_tolerance and dual<=feasibility_tolerance and complementarity<=feasibility_tolerance and feasible_storage
        return {"scope":("original_P2.1_SINR_relaxed_constrained_projected_KKT_not_global_optimality" if objective=="sinr" else "original_P3.1_finite_mu_epsilon_regularized_PSLR_relaxed_projected_KKT_not_unsmoothed_or_global_optimality"),
            "stationarity_norm":stationarity,"stationarity_tolerance":float(stationarity_tolerance),
            "maximum_positive_primal_residual":primal,"maximum_negative_dual_residual":dual,
            "maximum_absolute_complementarity":complementarity,"feasibility_tolerance":float(feasibility_tolerance),
            "maximum_phase_modulus_error":phase,"maximum_simplex_storage_error":simplex_error,
            "original_problem_kkt_verified":bool(verified)}

    def echo_increment(self,base,candidate,*,unit_circle=False,prepared_base=None):
        """Same complete quartic echoes, using exact field cross terms.

        The direct positive endpoint is returned separately: subtracting echo
        plus increment may cancel at a near-zero PSLR opponent denominator.
        """
        oldbar,_,q,a=self.fields(base) if prepared_base is None else prepared_base
        if unit_circle:
            # Exact circular points, not the sub-ULP radial storage error of
            # complex normalization. See the independent normalized Decimal
            # tests; the plain endpoint identity remains the default above.
            def circle_delta(first,last):
                if first.size and (np.max(np.abs(np.abs(first)-1))>32*np.finfo(float).eps or np.max(np.abs(np.abs(last)-1))>32*np.finfo(float).eps):
                    raise ValueError("Unit-circle increments require feasible phase endpoints")
                angle=np.angle(last*np.conj(first))
                return first*(-2*np.sin(angle/2)**2+1j*np.sin(angle))
            dphi=circle_delta(base["phi"],candidate["phi"])
            dtheta=circle_delta(base["theta"],candidate["theta"])
            dbar=np.zeros_like(oldbar)
            for u,ix in enumerate(self.indices):dbar[u,ix]=dtheta
            dv=oldbar*dphi[None,:]+dbar*(base["phi"]+dphi)[None,:]
        else:
            newbar=np.ones_like(oldbar)
            for u,ix in enumerate(self.indices):newbar[u,ix]=candidate["theta"]
            dv=oldbar*(candidate["phi"]-base["phi"])[None,:]+(newbar-oldbar)*candidate["phi"][None,:]
        dq=self.c@dv.T
        da=2*np.real(np.conj(q)*dq)+np.abs(dq)**2
        echo=self.beta[:,None]*a*a
        decho=self.beta[:,None]*(2*a*da+da*da)
        newecho=self.beta[:,None]*np.abs(q+dq)**4
        return echo,decho,newecho

    def sinr_alm_difference(self,base,candidate,lam,rho,*,unit_circle=False,prepared_base=None):
        """Exact SINR ALM increment; no Armijo slack or stopping changes."""
        echo,decho,newecho=self.echo_increment(base,candidate,unit_circle=unit_circle,prepared_base=prepared_base)
        denominator=self_excluded_sum(echo,self.targets)+self.config["noise_over_power"]
        dd=self_excluded_sum(decho,self.targets)
        newdenominator=self_excluded_sum(newecho,self.targets)+self.config["noise_over_power"]
        gamma=echo[:self.targets]/denominator
        dgamma=(decho[:self.targets]-gamma*dd)/newdenominator
        deta=float(candidate["eta"]-base["eta"])
        residual=float(base["eta"])-np.sum(base["X"]*gamma,axis=1)
        dresidual=deta-np.sum((candidate["X"]-base["X"])*gamma+candidate["X"]*dgamma,axis=1)
        raw=np.asarray(lam)+rho*residual; draw=rho*dresidual
        chi=np.maximum(0,raw)
        dchi=np.where(raw>0,np.where(raw+draw>0,draw,-raw),np.maximum(0,raw+draw))
        return float(-deta+np.sum(dchi*(2*chi+dchi))/(2*rho))

    def pslr_alm_difference(self,base,candidate,lam,rho,*,unit_circle=False,prepared_base=None):
        """Exact original finite-mu/epsilon LSE + ALM increment, all opponents.

        log1p/expm1 are algebraic evaluation identities, not Taylor or surrogate
        objectives. Large newly dominant opponents use direct positive echoes
        to survive old probability underflow and avoid cancelled denominators.
        """
        echo,decho,newecho=self.echo_increment(base,candidate,unit_circle=unit_circle,prepared_base=prepared_base)
        mu,epsilon=self.config["pslr_mu"],self.config["pslr_epsilon"]
        gamma=np.empty((self.targets,self.U));dgamma=np.empty_like(gamma)
        for k,opponents in enumerate(self.config["pslr_opponents"]):
            ix=np.asarray(opponents,dtype=int)
            ratios=echo[k][None,:]/(echo[ix]+epsilon)
            minimum=np.min(ratios,axis=0)
            gamma[k]=minimum-mu*np.log(np.sum(np.exp(-(ratios-minimum)/mu),axis=0))
            dratios=(decho[k][None,:]-ratios*decho[ix])/(newecho[ix]+epsilon)
            newratios=newecho[k][None,:]/(newecho[ix]+epsilon)
            dgamma[k]=softmin_increment(ratios,dratios,newratios,mu)
        deta=float(candidate["eta"]-base["eta"])
        residual=float(base["eta"])-np.sum(base["X"]*gamma,axis=1)
        dresidual=deta-np.sum((candidate["X"]-base["X"])*gamma+candidate["X"]*dgamma,axis=1)
        raw=np.asarray(lam)+rho*residual;draw=rho*dresidual;chi=np.maximum(0,raw)
        dchi=np.where(raw>0,np.where(raw+draw>0,draw,-raw),np.maximum(0,raw+draw))
        return float(-deta+np.sum(dchi*(2*chi+dchi))/(2*rho))


def softmin_increment(old,change,new,mu):
    """Exact opponent soft-min increment; opponent x position arrays."""
    minimum=np.min(old,axis=0)
    ex=np.exp(-(old-minimum)/mu);normalizer=np.sum(ex,axis=0)
    probability=ex/normalizer;t=-change/mu;small=np.abs(t)<=.5
    b=-(new-minimum)/mu-np.log(normalizer)
    ordinary=np.max(np.where(small,-np.inf,b),axis=0)<500
    increments=np.zeros_like(old)
    increments[small]=(probability*np.expm1(np.where(small,t,0)))[small]
    with np.errstate(over="ignore",invalid="ignore"):
        large_change=np.exp(np.where(small,-np.inf,b))-probability
    increments[~small]=large_change[~small]
    total=np.sum(increments,axis=0)
    ordinary&=np.isfinite(total)&(total>-.5)
    answer=np.empty(old.shape[1]);answer[ordinary]=-mu*np.log1p(total[ordinary])
    if np.any(~ordinary):
        trial=new[:,~ordinary];trial_min=np.min(trial,axis=0)
        answer[~ordinary]=trial_min-minimum[~ordinary]-mu*(np.log(np.sum(np.exp(-(trial-trial_min)/mu),axis=0))-np.log(normalizer[~ordinary]))
    return answer

def objective_increment(evaluate,base,candidate,f):
    difference=getattr(evaluate,"stable_difference",None)
    return difference(base,candidate) if difference is not None else evaluate(candidate)[0]-f

def block_backtracking(z,g,raw_d,evaluate,f,options):
    """Published distinct block step sizes; joint-coupling check is disclosed.
    Raw PR coefficients/directions are not clipped. A projected non-descent block
    alone can restart; a boundary-normal block with exactly zero motion is inactive.
    """
    guard=options.get("non_descent_policy","literal_printed")=="documented_non_descent_restart"
    d={b:np.array(v,copy=True) for b,v in raw_d.items()}
    alphas={}; backtracks={}; restarts={}; raw_actual={}; inactive={};raw_slopes={};restart_reasons={}
    for b in g:
        alpha=options.get("initial_steps",{}).get(b,options["initial_step"])
        if inner(g[b],g[b])==0:
            alphas[b]=0.;backtracks[b]=0;inactive[b]=True;raw_actual[b]=0.;restarts[b]=False;raw_slopes[b]=0.;restart_reasons[b]=[]
            continue
        probe=retract(z,{b:d[b]},alpha)
        delta=probe[b]-z[b]
        raw_actual[b]=float(inner(g[b],delta))
        raw_slopes[b]=float(inner(g[b],d[b]));restart_reasons[b]=[]
        restarts[b]=False
        if guard and (raw_slopes[b]>=0 or raw_actual[b]>=0) and inner(g[b],g[b])>0:
            restart_reasons[b]=(["raw_non_descent"] if raw_slopes[b]>=0 else [])+(["projected_non_descent"] if raw_actual[b]>=0 else [])
            d[b]=-g[b]
            restarts[b]=True
            probe=retract(z,{b:d[b]},alpha); delta=probe[b]-z[b]
        if inner(delta,delta)==0:
            alphas[b]=0.; backtracks[b]=0; inactive[b]=True
            continue
        inactive[b]=False
        raw_slope=inner(g[b],d[b]); accepted=False
        exhaustion_restart=guard and options.get("exhausted_direction_policy")=="documented_block_restart"
        for attempt in range(2 if exhaustion_restart else 1):
            for ls in range(options["max_backtracks"]):
                candidate=retract(z,{b:d[b]},alpha)
                actual_slope=inner(g[b],candidate[b]-z[b])
                predicted=actual_slope if guard else alpha*raw_slope
                change=objective_increment(evaluate,z,candidate,f)
                if np.isfinite(change) and predicted<0 and change<=options["armijo_constant"]*predicted:
                    accepted=True; break
                alpha*=options["backtrack_factor"]
            if accepted or attempt==1 or not exhaustion_restart: break
            # Keep the original PR coefficient in history. Retry only this
            # exhausted block with minus its current gradient, never a new solver.
            d[b]=-g[b]; raw_slope=-inner(g[b],g[b])
            restarts[b]=True;restart_reasons[b].append("backtracking_exhausted")
            alpha=options.get("initial_steps",{}).get(b,options["initial_step"])
        alphas[b]=float(alpha); backtracks[b]=ls+attempt*options["max_backtracks"]
        if not accepted:
            info={"block_step_sizes":alphas,"block_backtracks":backtracks,"block_non_descent_restarts":restarts,
                  "block_raw_direction_slopes":raw_slopes,"block_restart_reasons":restart_reasons,
                  "raw_projected_displacement_slopes":raw_actual,"inactive_projected_blocks":inactive,
                  "non_descent_restart":any(restarts.values())}
            return z,d,info,"block_line_search_exhausted_"+b
    info={"block_step_sizes":alphas,"block_backtracks":backtracks,"block_non_descent_restarts":restarts,
          "block_raw_direction_slopes":raw_slopes,"block_restart_reasons":restart_reasons,
          "raw_projected_displacement_slopes":raw_actual,
          "raw_projected_displacement_slope":float(sum(raw_actual.values())),
          "inactive_projected_blocks":inactive,"non_descent_restart":any(restarts.values())}
    if not any(a>0 for a in alphas.values()):
        reason="gradient_tolerance" if projected_kkt_norm(z,g)<options["gradient_tolerance"] else "zero_projected_PR_direction"
        return z,d,info,reason
    scaled={b:alphas[b]*d[b] for b in d}
    coupling=1.; accepted=False
    for ls in range(options["max_backtracks"]):
        candidate=retract(z,scaled,coupling)
        actual=sum(inner(g[b],candidate[b]-z[b]) for b in g)
        predicted=actual if guard else coupling*sum(alphas[b]*inner(g[b],d[b]) for b in g)
        change=objective_increment(evaluate,z,candidate,f)
        if np.isfinite(change) and predicted<0 and change<=options["armijo_constant"]*predicted:
            accepted=True;break
        coupling*=options["backtrack_factor"]
    info.update(coupling_scale=float(coupling),coupling_backtracks=ls,
                accepted_displacement_slope=float(actual))
    return candidate if accepted else z,d,info,None if accepted else "coupling_line_search_exhausted"

def rcg(z, evaluate, options):
    """Per-block raw Polak-Ribiere coefficients; exact stated transport/retraction.
    Original distinct block step sizes are production; common-alpha is diagnostic.
    The source omits constants/coupling, so a recorded joint Armijo scaling checks
    the combined independently-backtracked block steps.
    No PR+ clipping is applied. Optional documented non-descent restart records
    the original coefficients and raw direction slope before restarting.
    """
    if options["line_search_policy"]=="corrected_product_pr_wolfe":
        from solver_erratum import corrected_product_rcg
        return corrected_product_rcg(z,evaluate,options)
    if options["line_search_policy"] not in ("common_product_armijo","original_per_block_backtracking"):
        raise ValueError("Select original per-block backtracking or diagnostic common-product Armijo")
    oldg = oldd = None
    history = []
    reason = "iteration_cap"
    for it in range(options["max_iterations"]):
        f, eg, detail = evaluate(z)
        g = project(z,eg)
        guard=options.get("non_descent_policy","literal_printed")=="documented_non_descent_restart"
        kkt=projected_kkt_norm(z,g)
        history.append({"iteration":it,"objective":float(f),"gradient_norm":float(norm(g)),"projected_kkt_norm":float(kkt)})
        stopping_norm=kkt if guard else norm(g)
        if it>0 and stopping_norm<options["gradient_tolerance"]:
            reason="gradient_tolerance"
            break
        d = {}; betas={}
        if oldd is not None:
            transported=project(z,oldd)
        for b in g:
            denominator = inner(oldg[b],oldg[b]) if oldg is not None else 0
            beta = inner(g[b],g[b]-oldg[b])/denominator if denominator>0 else 0
            betas[b]=float(beta)
            d[b]=-g[b]+beta*transported[b] if oldg is not None else -g[b]
        slope=sum(inner(g[b],d[b]) for b in g)
        history[-1]["raw_pr_beta"]=betas
        history[-1]["raw_pr_slope"]=float(slope)
        history[-1]["non_descent_restart"]=False
        if options["line_search_policy"]=="original_per_block_backtracking":
            candidate,d,info,exit_reason=block_backtracking(z,g,d,evaluate,f,options)
            history[-1].update(info)
            if exit_reason is not None:
                reason=exit_reason
                break
            oldg,oldd=g,d
            z=candidate
            continue
        probe=retract(z,d,options["initial_step"])
        actual_slope=sum(inner(g[b],probe[b]-z[b]) for b in g)
        history[-1]["raw_projected_displacement_slope"]=float(actual_slope)
        non_descent=actual_slope>=0 if guard else slope>=0
        if non_descent:
            if guard and norm(g)>0:
                d={b:-g[b] for b in g}
                slope=-sum(inner(g[b],g[b]) for b in g)
                history[-1]["non_descent_restart"]=True
            else:
                reason="non_descent_raw_PR_direction"
                break
        alpha=options["initial_step"]
        accepted=False
        for ls in range(options["max_backtracks"]):
            candidate=retract(z,d,alpha)
            change=objective_increment(evaluate,z,candidate,f)
            feasible_slope=sum(inner(g[b],candidate[b]-z[b]) for b in g)
            predicted=feasible_slope if guard else alpha*slope
            if np.isfinite(change) and predicted<0 and change<=options["armijo_constant"]*predicted:
                accepted=True
                break
            alpha*=options["backtrack_factor"]
        if not accepted:
            reason="line_search_exhausted"
            break
        oldg,oldd=g,d
        z=candidate
    f,eg,detail=evaluate(z)
    rg=project(z,eg)
    return z,history,{"reason":reason,"objective":float(f),"gradient_norm":float(norm(rg)),
                      "projected_kkt_norm":float(projected_kkt_norm(z,rg)),
                      "stationarity_measure":"projected_simplex_KKT" if options.get("non_descent_policy","literal_printed")=="documented_non_descent_restart" else "printed_rowmean_gradient"}

def communication_solve(model,z,options):
    """Original mu-halving continuation; no max-SNR incumbent inside a start."""
    mu=options["initial_mu"]
    history=[]
    while mu>=options["terminal_mu"]:
        z,h,stop=rcg(z,lambda x:model.communication_objective(x,mu,options["objective_convention"]),options["rcg"])
        history.append({"mu":mu,"inner":h,"stop":stop})
        mu*=0.5
    gamma=model.metric(z,"communications")
    binary=np.zeros_like(z["X"])
    binary[np.arange(model.K),np.argmax(z["X"],axis=1)]=1
    return z,history,{"min_relaxed_snr":float(np.min(np.sum(z["X"]*gamma,axis=1))),
                     "min_binary_snr":float(np.min(np.sum(binary*gamma,axis=1))),
                     "binary_schedule":binary.tolist()}

def sensing_solve(model,z,options,objective="sinr"):
    """Final-source RALM: old multipliers in iota, exact conditional penalty."""
    rho=options["rho_initial"]
    lam=np.broadcast_to(options["lambda_initial"],(model.targets,)).astype(float).copy()
    eps=options["epsilon_initial"]
    factor=(options["epsilon_min"]/eps)**(1/options["outer_iterations"])
    oldiota=None
    history=[]
    for outer in range(options["outer_iterations"]):
        oldz={b:np.array(v,copy=True) for b,v in z.items()}
        inner_options=dict(options["rcg"],gradient_tolerance=eps)
        def evaluate(x): return model.augmented(x,lam,rho,objective)
        difference=inner_options.get("objective_difference")
        stable_modes=("exact_sinr_increment","exact_unit_circle_sinr_increment","exact_sensing_increment","exact_unit_circle_sensing_increment")
        if difference in stable_modes and (objective=="sinr" or difference in ("exact_sensing_increment","exact_unit_circle_sensing_increment")):
            unit_circle=difference.startswith("exact_unit_circle")
            cache={}
            def stable_difference(base,trial):
                # The solver does not mutate current iterates in place. Copies
                # still guard reuse if a caller changes a phase array in place.
                if cache.get("state") is not base or not np.array_equal(cache["phi"],base["phi"]) or not np.array_equal(cache["theta"],base["theta"]):
                    cache.update(state=base,phi=base["phi"].copy(),theta=base["theta"].copy(),fields=model.fields(base))
                method=model.sinr_alm_difference if objective=="sinr" else model.pslr_alm_difference
                return method(base,trial,lam,rho,unit_circle=unit_circle,prepared_base=cache["fields"])
            evaluate.stable_difference=stable_difference
        z,h,stop=rcg(z,evaluate,inner_options)
        q=model.augmented(z,lam,rho,objective)[2]["q"]
        iota=np.maximum(q,-lam/rho)
        newlam=np.clip(lam+rho*q,options["lambda_min"],options["lambda_max"])
        newrho=rho if outer==0 or np.max(iota)<=options["iota_progress_ratio"]*np.max(oldiota) else rho*options["rho_factor"]
        step=np.sqrt(sum(inner(z[b]-oldz[b],z[b]-oldz[b]) for b in z))
        neweps=options["epsilon_min"] if outer+1==options["outer_iterations"] else max(options["epsilon_min"],factor*eps)
        history.append({"outer_iteration":outer+1,"rho_used":rho,"rho_next":newrho,
                        "epsilon_used":eps,"epsilon_next":neweps,"eta":float(z["eta"]),"lambda":newlam.tolist(),
                        "q":q.tolist(),"iota":iota.tolist(),"step":float(step),"inner":h,"stop":stop})
        stepstop=step<=options["minimum_step"]
        epsstop=neweps<=options["epsilon_min"]
        logic=options["outer_stopping_logic"]
        if logic not in ("algorithm_OR","numerical_text_AND"):
            raise ValueError("Select stated source stopping interpretation explicitly")
        lam,rho,eps,oldiota=newlam,newrho,neweps,iota
        if (stepstop or epsstop) if logic=="algorithm_OR" else (stepstop and epsstop):
            break
    gamma=model.metric(z,objective)
    binary=np.zeros_like(z["X"])
    binary[np.arange(model.targets),np.argmax(z["X"],axis=1)]=1
    q=float(z["eta"])-np.sum(z["X"]*gamma,axis=1)
    metrics={"eta":float(z["eta"]),"min_relaxed_metric":float(np.min(np.sum(z["X"]*gamma,axis=1))),
             "min_binary_metric":float(np.min(np.sum(binary*gamma,axis=1))),
             "maximum_constraint":float(np.max(q)),"multipliers":lam.tolist(),"penalty":rho,
             "binary_schedule":binary.tolist()}
    return z,history,metrics

def closed_form(model):
    """Same-reference Section VI chirps in the positive-field convention.

    Eq(61) uses a negative array exponent with +A/-A chirps. Model.fields
    uses a positive exponent, so conjugate BOTH chirps, not just one layer.
    This preserves every finite one-padded array power; see dedicated tests.
    """
    mr,mc=model.config["ms1"]; nr,nc=model.config["ms2"]
    ur,uc=mr-nr+1,mc-nc+1
    if min(ur,uc)<=1:
        raise ValueError("Published closed-form A is singular when Ur or Uc equals one")
    # Coordinates in wavelengths make A dimensionless without changing phases.
    d=model.config["spacing_over_wavelength"]
    A=np.pi/d*max(1/(ur-1),1/(uc-1))
    r,c=np.meshgrid(np.arange(mr),np.arange(mc),indexing="ij")
    rn,cn=np.meshgrid(np.arange(nr),np.arange(nc),indexing="ij")
    return {"phi":np.exp(-1j*A*d*d*(r*r+c*c)).ravel(),
            "theta":np.exp(1j*A*d*d*(rn*rn+cn*cn)).ravel(),
            "X":np.ones((model.targets,model.U))/model.U,"eta":np.asarray(0.)}

def check_gradient(z,evaluate,h=1e-6):
    g=project(z,evaluate(z)[1])
    errors={}
    for b in g:
        d={k:np.zeros_like(v) for k,v in g.items()}
        if b in ("phi","theta"):
            d[b]=1j*z[b]*np.cos(np.arange(np.size(z[b]))+0.3)
        elif b=="X":
            raw=np.cos(np.arange(z[b].size).reshape(z[b].shape)+.4)
            d[b]=raw-np.mean(raw,axis=1,keepdims=True)
        else:
            d[b]=np.asarray(.31)
        fd=(evaluate(retract(z,d,h))[0]-evaluate(retract(z,d,-h))[0])/(2*h)
        ana=inner(g[b],d[b])
        errors[b]=float(abs(fd-ana)/max(1,abs(fd),abs(ana)))
    return errors

def serialize(z):
    return {b:({"real":np.real(v).tolist(),"imag":np.imag(v).tolist()} if np.iscomplexobj(v)
               else np.asarray(v).tolist()) for b,v in z.items()}
