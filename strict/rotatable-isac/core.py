"""Rotation-aware model and the paper QT/MM, RCG, and PGA/BB algorithms.

No projected-gradient W replacement, phase-ascent replacement or PR+ restart.
Printed BB and an explicitly recorded ascent-sign correction are selectable.
"""
from __future__ import annotations
import numpy as np


def rotation(r):
    x,y,z=r;cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
    rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    dx=np.array([[0,0,0],[0,-sx,-cx],[0,cx,-sx]]);dy=np.array([[-sy,0,cy],[0,0,0],[-cy,0,-sy]])
    dz=np.array([[-sz,-cz,0],[cz,-sz,0],[0,0,0]])
    return rx@ry@rz,[dx@ry@rz,rx@dy@rz,rx@ry@dz]


def response(coords,center,direction,r,c):
    q,dq=rotation(r);cosine=float(q[:,2]@direction)
    positions=np.asarray(coords)@q.T+center;wave=2*np.pi/c["wavelength"]
    steering=np.exp(1j*wave*(positions@direction))
    if cosine<=0: return np.zeros(len(coords),complex),np.zeros((len(coords),3),complex)
    b=c["directivity_exponent"];amp=np.sqrt(c["maximum_gain"])*cosine**(b/2)
    a=amp*steering;da=np.empty((len(coords),3),complex)
    for d in range(3):
        damp=np.sqrt(c["maximum_gain"])*(b/2)*cosine**(b/2-1)*(dq[d][:,2]@direction)
        dphase=wave*(np.asarray(coords)@dq[d].T@direction)
        da[:,d]=steering*(damp+1j*amp*dphase)
    return a,da


def channels(theta,r,c):
    cb,cr=np.asarray(c["bs_coordinates"]),np.asarray(c["ris_coordinates"])
    ob,orr=np.asarray(c["bs_center"]),np.asarray(c["ris_center"])
    m,n=len(cb),len(cr);k=len(c["noise"]);a=len(c["bt_directions"]);links=k+a
    h=np.zeros((m,links),complex);g=np.zeros((n,links),complex)
    dh=np.zeros((m,links,6),complex);dg=np.zeros((n,links,6),complex)
    for u in range(k):
        for p in range(len(c["bu_directions"][u])):
            v,dv=response(cb,ob,np.asarray(c["bu_directions"][u][p]),r[:3],c)
            gain=complex(c["bu_gain_re"][u][p],c["bu_gain_im"][u][p]);h[:,u]+=gain*v;dh[:,u,:3]+=gain*dv
            v,dv=response(cr,orr,np.asarray(c["ru_directions"][u][p]),r[3:],c)
            gain=complex(c["ru_gain_re"][u][p],c["ru_gain_im"][u][p]);g[:,u]+=gain*v;dg[:,u,3:]+=gain*dv
    for v in range(a):
        h[:,k+v],dh[:,k+v,:3]=response(cb,ob,np.asarray(c["bt_directions"][v]),r[:3],c)
        g[:,k+v],dg[:,k+v,3:]=response(cr,orr,np.asarray(c["rt_directions"][v]),r[3:],c)
    bridge=np.zeros((m,n),complex);db=np.zeros((m,n,6),complex)
    for p in range(len(c["br_directions"])):
        ab,dab=response(cb,ob,np.asarray(c["br_directions"][p]),r[:3],c)
        ar,dar=response(cr,orr,np.asarray(c["rb_directions"][p]),r[3:],c)
        gain=complex(c["br_gain_re"][p],c["br_gain_im"][p])
        bridge+=gain*np.outer(ab,ar.conj())
        for d in range(3):
            db[:,:,d]+=gain*np.outer(dab[:,d],ar.conj())
            db[:,:,d+3]+=gain*np.outer(ab,dar[:,d].conj())
    f=h+bridge@(theta[:,None]*g)
    jac=np.empty((m,links,6),complex)
    for d in range(6):
        jac[:,:,d]=dh[:,:,d]+db[:,:,d]@(theta[:,None]*g)+bridge@(theta[:,None]*dg[:,:,d])
    return f,jac,bridge,g


def evaluate(w,theta,r,c,iota=None,gradients=False):
    field,jac,bridge,g=channels(theta,r,c);k=len(c["noise"])
    fc,fs=field[:,:k],field[:,k:];y=fc.conj().T@w;z=fs.conj().T@w
    total=np.sum(abs(y)**2,axis=1)+c["noise"];signal=abs(y[np.arange(k),np.arange(k)])**2
    interference=total-signal;rate=float(np.log2(total/interference).sum());p=np.sum(abs(z)**2,axis=1)
    pd=np.asarray(c["desired_pattern"]);energy=float(pd@pd)
    if iota is None:
        overlap=float(pd@p)
        if overlap<=c["iota_denominator_epsilon"]:
            raise ValueError("Exact iota* is undefined at this zero-overlap pattern; no fabricated sensing score is returned.")
        iota=float(p@p/overlap)
    denominator=iota*iota*energy;residual=p-iota*pd;nmse=float(residual@residual/denominator)
    result={"utility":rate-c["rho"]*nmse,"rate":rate,"nmse":nmse,"iota":iota,"pattern":p,"sinr":signal/interference}
    if not gradients:return result
    coeff=np.repeat((1/total-1/interference)[:,None],w.shape[1],axis=1)
    coeff[np.arange(k),np.arange(k)]+=1/interference
    gw=2*fc@(coeff*y)/np.log(2)-4*c["rho"]*fs@(residual[:,None]*z)/denominator
    bw=bridge.conj().T@w
    gt=np.zeros(len(theta),complex)
    for u in range(k):gt+=2*g[:,u].conj()*(bw@(coeff[u]*y[u].conj()))/np.log(2)
    for v in range(len(pd)):gt-=4*c["rho"]*residual[v]/denominator*g[:,k+v].conj()*(bw@z[v].conj())
    gr=np.zeros(6)
    for d in range(6):
        dy=jac[:,:k,d].conj().T@w;dz=jac[:,k:,d].conj().T@w
        dtotal=2*np.real(np.sum(y.conj()*dy,axis=1));dsignal=2*np.real(y[np.arange(k),np.arange(k)].conj()*dy[np.arange(k),np.arange(k)])
        drate=np.sum(dtotal/total-(dtotal-dsignal)/interference)/np.log(2)
        dp=2*np.real(np.sum(z.conj()*dz,axis=1));gr[d]=drate-2*c["rho"]*residual@dp/denominator
    return result,(gw,gt,gr)


def update_w(w,theta,r,c,iota):
    """Algorithm 1: original LDT/QT + sensing MM QCQP + scalar dual bisection."""
    f,_,_,_=channels(theta,r,c);k=len(c["noise"]);fc,fs=f[:,:k],f[:,k:]
    m=len(w);pd=np.asarray(c["desired_pattern"]);den=iota*iota*float(pd@pd)
    norms=np.sum(abs(fs)**2,axis=0)
    lip=12*c["power"]*norms**2+4*iota*pd*norms
    spec=c["W_solver"];history=[evaluate(w,theta,r,c,iota)["utility"]];records=[]
    converged=False;reason="maximum_iterations_without_criterion_stop";relative_objective=relative_step=None
    for _ in range(spec["maximum_iterations"]):
        y=fc.conj().T@w;total=np.sum(abs(y)**2,axis=1)+c["noise"]
        signal=abs(y[np.arange(k),np.arange(k)])**2;mu=signal/(total-signal);eta=y[np.arange(k),np.arange(k)]/total
        q=(fc*((1+mu)*abs(eta)**2)[None,:])@fc.conj().T/np.log(2)
        p=np.zeros_like(w);p[:,:k]=fc*((1+mu)*eta)[None,:]/np.log(2)
        z=fs.conj().T@w;pattern=np.sum(abs(z)**2,axis=1)
        ga=4*fs@((pattern-iota*pd)[:,None]*z)
        q+=c["rho"]*lip.sum()/(2*den)*np.eye(m)
        p+=c["rho"]/(2*den)*(lip.sum()*w-ga)
        val,vec=np.linalg.eigh(q);projected=vec.conj().T@p;row=np.sum(abs(projected)**2,axis=1)
        if val.min()<=0:raise ValueError("QCQP Q is not positive definite; rho=0 singular case requires explicit source handling.")
        def power(nu):return float(np.sum(row/(val+nu)**2))
        nu=0.;bisects=0
        if power(0)>c["power"]:
            lo,hi=0.,1.
            while power(hi)>c["power"]:hi*=2
            while hi-lo>spec["bisection_tolerance"]*max(1,hi):
                mid=(lo+hi)/2
                if power(mid)>c["power"]:lo=mid
                else:hi=mid
                bisects+=1
            nu=hi
        new=vec@(projected/(val+nu)[:,None]);value=evaluate(new,theta,r,c,iota)["utility"]
        if value<history[-1]-c["verification_tolerance"]:raise RuntimeError("QT/MM actual objective decreased.")
        rel=np.linalg.norm(new-w)/max(np.linalg.norm(w),np.finfo(float).tiny)
        relative_step=float(rel)
        records.append({"nu":nu,"bisection_steps":bisects,"stationarity_residual":float(np.linalg.norm((q+nu*np.eye(m))@new-p)),"power":float(np.sum(abs(new)**2))})
        w=new;history.append(value)
        relative_objective=float((history[-1]-history[-2])/max(abs(history[-2]),np.finfo(float).tiny))
        if relative_objective<spec["relative_tolerance"] or rel<spec["relative_tolerance"]:
            converged=True;reason="relative_objective_tolerance" if relative_objective<spec["relative_tolerance"] else "relative_step_tolerance";break
    return w,{"objective":history,"QCQP":records,"converged":converged,"termination_reason":reason,
              "iterations":len(records),"iteration_budget":spec["maximum_iterations"],"budget_exhausted":len(records)>=spec["maximum_iterations"],
              "capped_unconverged":not converged,"relative_objective_improvement":relative_objective,"relative_step":relative_step,"relative_tolerance":spec["relative_tolerance"]}


def tangent(theta,v):return v-np.real(v*theta.conj())*theta


def update_theta(w,theta,r,c,iota):
    spec=c["RCG_solver"];history=[];coefficients=[];restarts=[];oldg=oldd=None
    converged=False;reason="maximum_iterations_without_criterion_stop";checked_gradient=None
    for iteration in range(spec["maximum_iterations"]):
        metric,(_,ambient,_)=evaluate(w,theta,r,c,iota,True);g=tangent(theta,ambient);history.append(metric["utility"])
        checked_gradient=float(np.linalg.norm(g)/np.sqrt(len(theta)))
        if checked_gradient<=spec["gradient_tolerance"]:
            converged=True;reason="gradient_tolerance";break
        beta=0. if oldg is None else float(np.real(np.vdot(g,g-tangent(theta,oldg)))/np.real(np.vdot(oldg,oldg)))
        direction=g if oldg is None else g+beta*tangent(theta,oldd)
        slope=float(np.real(np.vdot(g,direction)));coefficients.append(beta)
        if slope<=0:
            if spec["mode"]=="documented_non_ascent_restart":
                restarts.append({"iteration":iteration,"reason":"non_ascent_direction","raw_PR":beta,"raw_slope":slope})
                direction=g;slope=float(np.real(np.vdot(g,g)))
            else:
                raise RuntimeError("Printed untruncated PR direction is not ascent. Literal diagnostic mode does not restart.")
        alpha=spec["initial_step"];accepted=False
        for _ in range(spec["maximum_backtracks"]):
            trial=theta+alpha*direction;trial/=abs(trial)
            value=evaluate(w,trial,r,c,iota)["utility"]
            if value>=metric["utility"]+spec["armijo"]*alpha*slope:
                oldg,oldd=g,direction;theta=trial;accepted=True;break
            alpha*=spec["backtrack_factor"]
        if not accepted:raise RuntimeError("Printed RCG Armijo line search failed; no substitute solver.")
    final_metric,(_,final_ambient,_)=evaluate(w,theta,r,c,iota,True)
    return theta,{"objective":history,"PR_coefficients":coefficients,"restarts":restarts,"mode":spec["mode"],"final_objective":final_metric["utility"],
                  "applicable":True,"converged":converged,"termination_reason":reason,"iterations":len(history),"updates":len(coefficients),
                  "iteration_budget":spec["maximum_iterations"],"budget_exhausted":len(history)>=spec["maximum_iterations"],"capped_unconverged":not converged,
                  "last_checked_normalized_gradient_norm":checked_gradient,"final_normalized_gradient_norm":float(np.linalg.norm(tangent(theta,final_ambient))/np.sqrt(len(theta))),
                  "gradient_tolerance":spec["gradient_tolerance"]}


def update_rotation(w,theta,r,c,iota,lower,upper):
    spec=c["PGA_solver"];oldr=oldg=None;history=[];bb=[];steps=[]
    converged=False;reason="maximum_iterations_without_criterion_stop";checked_gradient=relative_step=None
    for _ in range(spec["maximum_iterations"]):
        metric,(_,_,g)=evaluate(w,theta,r,c,iota,True);history.append(metric["utility"])
        residual=g.copy();residual[r<=lower]=np.maximum(0,g[r<=lower]);residual[r>=upper]=np.minimum(0,g[r>=upper])
        # A fixed coordinate is not a free KKT component.
        residual[np.asarray(lower)==np.asarray(upper)]=0
        checked_gradient=float(np.linalg.norm(residual))
        if checked_gradient<=spec["gradient_tolerance"]:
            converged=True;reason="projected_gradient_tolerance";break
        alpha=spec["initial_step"]
        if oldr is not None:
            s=r-oldr;den=float(s@(g-oldg))
            if spec["BB_interpretation"]=="ascent_sign_correction":den=-den
            elif spec["BB_interpretation"]!="as_printed":raise ValueError("Unknown BB interpretation.")
            raw=float(s@s/den) if den!=0 else float("inf")
            alpha=float(np.clip(raw,spec["minimum_step"],spec["maximum_step"]))
            bb.append({"raw":None if not np.isfinite(raw) else raw,"clipped":alpha,"denominator":den})
        accepted=False
        for _ in range(spec["maximum_backtracks"]):
            delta=np.clip(r+alpha*g,lower,upper)-r
            value=evaluate(w,theta,r+delta,c,iota)["utility"]
            if value>=metric["utility"]+spec["armijo"]*float(g@delta):
                oldr,oldg=r.copy(),g.copy();r=r+delta;accepted=True;steps.append(alpha);break
            alpha*=spec["backtrack_factor"]
        if not accepted:raise RuntimeError("Paper PGA Armijo search failed.")
        relative_step=float(np.linalg.norm(r-oldr)/max(1,np.linalg.norm(oldr)))
        if relative_step<=spec["relative_tolerance"]:
            converged=True;reason="relative_step_tolerance";break
    final_metric,(_,_,final_g)=evaluate(w,theta,r,c,iota,True)
    residual=final_g.copy();residual[r<=lower]=np.maximum(0,final_g[r<=lower]);residual[r>=upper]=np.minimum(0,final_g[r>=upper]);residual[np.asarray(lower)==np.asarray(upper)]=0
    return r,{"objective":history,"BB":bb,"steps":steps,"final_objective":final_metric["utility"],"converged":converged,"termination_reason":reason,
              "iterations":len(history),"updates":len(steps),"iteration_budget":spec["maximum_iterations"],"budget_exhausted":len(history)>=spec["maximum_iterations"],
              "capped_unconverged":not converged,"last_checked_projected_gradient_norm":checked_gradient,"final_projected_gradient_norm":float(np.linalg.norm(residual)),
              "gradient_tolerance":spec["gradient_tolerance"],"relative_step":relative_step,"relative_tolerance":spec["relative_tolerance"]}


def initialize(c):
    theta=np.ones(len(c["ris_coordinates"]),complex);r=np.asarray(c["initial_angles"],float)
    f,_,_,_=channels(theta,r,c);k=len(c["noise"]);m=len(c["bs_coordinates"])
    fc=f[:,:k];v=fc@np.linalg.pinv(fc.conj().T@fc,rcond=c["initial_pseudoinverse_tolerance"])
    # Feasible ZF initialization on communication columns, plus sensing identity.
    w=np.c_[v,np.eye(m)*c["initial_sensing_amplitude"]]
    w*=np.sqrt(c["power"])/np.linalg.norm(w)
    return w,theta,r


def optimize(c,lower,upper,with_ris=True):
    w,theta,r=initialize(c);hist=[];blocks=[];converged=False;relative_objective=None
    for iteration in range(c["AO_solver"]["maximum_iterations"]):
        metric=evaluate(w,theta,r,c);iota=metric["iota"]
        if not hist:hist.append(metric["utility"])
        w,hw=update_w(w,theta,r,c,iota)
        ht={"applicable":False,"converged":True,"capped_unconverged":False,"termination_reason":"not_applicable_no_RIS","iterations":0,"iteration_budget":0,"budget_exhausted":False}
        if with_ris:theta,ht=update_theta(w,theta,r,c,iota)
        r,hr=update_rotation(w,theta,r,c,iota,np.asarray(lower),np.asarray(upper))
        new=evaluate(w,theta,r,c);hist.append(new["utility"])
        if hist[-1]<hist[-2]-c["verification_tolerance"]:raise RuntimeError("AO exact-iota utility decreased.")
        blocks.append({"iota":iota,"W":hw,"RIS":ht,"rotation":hr})
        relative_objective=float((hist[-1]-hist[-2])/max(abs(hist[-2]),np.finfo(float).tiny))
        if relative_objective<c["AO_solver"]["relative_tolerance"]:
            converged=True;break
    inner_all=bool(blocks and all(block[key]["converged"] for block in blocks for key in ["W","RIS","rotation"]))
    return w,theta,r,{"utility":hist,"blocks":blocks,"converged":converged,"inner_all_converged":inner_all,"full_converged":converged and inner_all,
                     "iterations":len(blocks),"iteration_budget":c["AO_solver"]["maximum_iterations"],"budget_exhausted":len(blocks)>=c["AO_solver"]["maximum_iterations"],
                     "termination_reason":"relative_objective_tolerance" if converged else "maximum_iterations_without_criterion_stop",
                     "relative_objective_improvement":relative_objective,"relative_tolerance":c["AO_solver"]["relative_tolerance"]}
