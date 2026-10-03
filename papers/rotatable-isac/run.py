"""Independent rotation-aware ISAC model and disclosed AO projected-ascent variant.

Implements arXiv:2512.20987 Eqs.2-24. Does not pretend to implement its
QT/MM precoder or Riemannian conjugate-gradient phase subsolvers.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np


def rotation(r):
    x,y,z = r
    cx,sx,cy,sy,cz,sz = np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
    rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    dx=np.array([[0,0,0],[0,-sx,-cx],[0,cx,-sx]])
    dy=np.array([[-sy,0,cy],[0,0,0],[-cy,0,-sy]])
    dz=np.array([[-sz,-cz,0],[cz,-sz,0],[0,0,0]])
    return rx@ry@rz, [dx@ry@rz,rx@dy@rz,rx@ry@dz]


def response(coords, center, direction, r, f):
    """sqrt(G) times steering, plus exact derivatives of Euler angles."""
    q,dq=rotation(r)
    normal=q[:,2]
    cosine=float(normal@direction)
    positions=np.asarray(coords)@q.T+center
    wave=2*np.pi/f["wavelength"]
    steering=np.exp(1j*wave*(positions@direction))
    if cosine<=0:
        return np.zeros(len(coords),complex),np.zeros((len(coords),3),complex)
    b=f["directivity_exponent"]
    amplitude=np.sqrt(f["maximum_gain"])*cosine**(b/2)
    a=amplitude*steering
    da=np.empty((len(coords),3),complex)
    for i in range(3):
        dcos=dq[i][:,2]@direction
        damp=np.sqrt(f["maximum_gain"])*(b/2)*cosine**(b/2-1)*dcos
        dphase=wave*(np.asarray(coords)@dq[i].T@direction)
        da[:,i]=steering*(damp+1j*amplitude*dphase)
    return a,da


def channels(phases, angles, f):
    cb,cr=np.asarray(f["bs_coordinates"]),np.asarray(f["ris_coordinates"])
    ob,orr=np.asarray(f["bs_center"]),np.asarray(f["ris_center"])
    m,n=len(cb),len(cr)
    users,len_a=len(f["bu_directions"]),len(f["bt_directions"])
    links=users+len_a
    rb,rr=angles[:3],angles[3:]
    h=np.zeros((m,links),complex); g=np.zeros((n,links),complex)
    dh=np.zeros((m,links,6),complex); dg=np.zeros((n,links,6),complex)
    for k in range(users):
        for p in range(len(f["bu_directions"][k])):
            a,da=response(cb,ob,np.asarray(f["bu_directions"][k][p]),rb,f)
            gain=complex(f["bu_gain_re"][k][p],f["bu_gain_im"][k][p])
            h[:,k]+=gain*a; dh[:,k,:3]+=gain*da
            a,da=response(cr,orr,np.asarray(f["ru_directions"][k][p]),rr,f)
            gain=complex(f["ru_gain_re"][k][p],f["ru_gain_im"][k][p])
            g[:,k]+=gain*a; dg[:,k,3:]+=gain*da
    for a in range(len_a):
        h[:,users+a],dh[:,users+a,:3]=response(cb,ob,np.asarray(f["bt_directions"][a]),rb,f)
        g[:,users+a],dg[:,users+a,3:]=response(cr,orr,np.asarray(f["rt_directions"][a]),rr,f)
    bridge=np.zeros((m,n),complex); db=np.zeros((m,n,6),complex)
    for p in range(len(f["br_directions"])):
        ab,dab=response(cb,ob,np.asarray(f["br_directions"][p]),rb,f)
        ar,dar=response(cr,orr,np.asarray(f["rb_directions"][p]),rr,f)
        gain=complex(f["br_gain_re"][p],f["br_gain_im"][p])
        bridge+=gain*np.outer(ab,np.conj(ar))
        for d in range(3):
            db[:,:,d]+=gain*np.outer(dab[:,d],np.conj(ar))
            db[:,:,3+d]+=gain*np.outer(ab,np.conj(dar[:,d]))
    theta=np.exp(1j*phases)
    x=h+bridge@(theta[:,None]*g)
    derivatives=np.zeros((m,links,n+6),complex)
    for d in range(n):
        derivatives[:,:,d]=bridge[:,d,None]*(1j*theta[d]*g[d,None,:])
    for d in range(6):
        derivatives[:,:,n+d]=dh[:,:,d]+db[:,:,d]@(theta[:,None]*g)+bridge@(theta[:,None]*dg[:,:,d])
    return x,derivatives


def unpack(x,f):
    m=len(f["bs_coordinates"]); n=len(f["ris_coordinates"])
    s=len(f["bu_directions"])+m; count=m*s
    w=(x[:count]+1j*x[count:2*count]).reshape((m,s),order="F")
    return w,x[2*count:2*count+n],x[-6:]


def evaluate(x,f,iota=None,need_gradient=True):
    w,phases,angles=unpack(x,f)
    field,df=channels(phases,angles,f)
    users=len(f["noise"])
    fc,fs=field[:,:users],field[:,users:]
    y=fc.conj().T@w; z=fs.conj().T@w
    total=np.sum(abs(y)**2,axis=1)+f["noise"]
    signal=abs(y[np.arange(users),np.arange(users)])**2
    interference=total-signal
    sinr=signal/interference
    rate=float(np.log2(total/interference).sum())
    p=np.sum(abs(z)**2,axis=1)
    pd=np.asarray(f["desired_pattern"]); energy=float(pd@pd)
    if iota is None:
        iota=float(p@p/(pd@p))
    residual=p-iota*pd
    nmse=float(residual@residual/(iota*iota*energy))
    utility=rate-f["rho"]*nmse
    metrics={"utility":utility,"rate":rate,"nmse":nmse,"iota":iota,"sinr":sinr,"pattern":p}
    if not need_gradient:
        return metrics,None
    coeff=np.repeat((1/total-1/interference)[:,None],w.shape[1],axis=1)
    coeff[np.arange(users),np.arange(users)]+=1/interference
    gw=2*fc@(coeff*y)/np.log(2)-4*f["rho"]*fs@(residual[:,None]*z)/(iota*iota*energy)
    gd=np.zeros(df.shape[2])
    for d in range(df.shape[2]):
        dy=df[:,:users,d].conj().T@w
        dz=df[:,users:,d].conj().T@w
        dtotal=2*np.real(np.sum(np.conj(y)*dy,axis=1))
        dsignal=2*np.real(np.conj(y[np.arange(users),np.arange(users)])*dy[np.arange(users),np.arange(users)])
        drate=np.sum(dtotal/total-(dtotal-dsignal)/interference)/np.log(2)
        dp=2*np.real(np.sum(np.conj(z)*dz,axis=1))
        gd[d]=drate-f["rho"]*2*residual@dp/(iota*iota*energy)
    grad=np.concatenate([gw.real.ravel(order="F"),gw.imag.ravel(order="F"),gd])
    return metrics,grad


def initial_vector(f):
    w=np.asarray(f["initial_w_re"])+1j*np.asarray(f["initial_w_im"])
    w=w/np.linalg.norm(w)*np.sqrt(f["power"])
    return np.r_[w.real.ravel(order="F"),w.imag.ravel(order="F"),f["initial_phases"],f["initial_bs_angles"],f["initial_ris_angles"]]


def optimize(x0,f,rotations):
    x=x0.copy(); m=len(f["bs_coordinates"]); users=len(f["noise"]); count=m*(users+m)
    n=len(f["ris_coordinates"])
    angle_center=x0[-6:].copy()
    indices=[np.arange(2*count),np.arange(2*count,2*count+n)]
    steps=[0.15,0.35]
    if rotations:
        indices.append(np.arange(2*count+n,len(x)))
        steps.append(0.15)
    history=[evaluate(x,f)[0]["utility"]]
    for _ in range(f["outer_iterations"]):
        iota=evaluate(x,f)[0]["iota"]
        for block,step in zip(indices,steps):
            for _ in range(f["inner_steps"]):
                metrics,grad=evaluate(x,f,iota)
                direction=grad[block]/max(1,float(np.linalg.norm(grad[block])))
                alpha=step
                for _ in range(28):
                    trial=x.copy(); trial[block]+=alpha*direction
                    if block[0]==0:
                        norm=float(np.linalg.norm(trial[:2*count]))
                        if norm>np.sqrt(f["power"]):
                            trial[:2*count]*=np.sqrt(f["power"])/norm
                    elif block[0]==2*count+n:
                        trial[-6:]=np.clip(trial[-6:],angle_center-f["rotation_half_width"],angle_center+f["rotation_half_width"])
                    delta=trial-x
                    slope=float(grad@delta)
                    new=evaluate(trial,f,iota,False)[0]["utility"]
                    if slope>=-1e-15 and new>=metrics["utility"]+1e-4*slope-1e-13:
                        x=trial
                        break
                    alpha*=0.5
        history.append(evaluate(x,f)[0]["utility"])
    return x,history


def summarize(x,f):
    metric,_=evaluate(x,f)
    w,phases,angles=unpack(x,f)
    return {"utility":metric["utility"],"sum_rate":metric["rate"],"nmse":metric["nmse"],
        "iota":metric["iota"],"sinr":metric["sinr"].tolist(),"beampattern":metric["pattern"].tolist(),
        "w_re":w.real.tolist(),"w_im":w.imag.tolist(),"phases":phases.tolist(),"angles":angles.tolist()}


def run():
    f=json.loads(Path(__file__).with_name("fixture.json").read_text())
    x0=initial_vector(f)
    base,hb=optimize(x0,f,False)
    joint,hj=optimize(x0,f,True)
    metric,grad=evaluate(x0,f)
    iota=metric["iota"]
    numerical=np.zeros(len(x0))
    for d in range(len(x0)):
        p,m=x0.copy(),x0.copy();p[d]+=1e-6;m[d]-=1e-6
        numerical[d]=(evaluate(p,f,iota,False)[0]["utility"]-evaluate(m,f,iota,False)[0]["utility"])/2e-6
    w,phases,angles=unpack(joint,f)
    final=evaluate(joint,f)[0]
    pd=np.asarray(f["desired_pattern"]);pattern=final["pattern"]
    identity=abs(final["nmse"]-(1-(pd@pattern)**2/((pattern@pattern)*(pd@pd))))
    reduced=abs(final["utility"]-(final["rate"]-f["rho"]*final["nmse"]))
    center=x0[-6:]
    directions=[]
    for name in ["bu_directions","ru_directions","br_directions","rb_directions","bt_directions","rt_directions"]:
        directions.extend(np.asarray(f[name]).reshape(-1,3))
    unit_error=float(np.max(abs(np.linalg.norm(directions,axis=1)-1)))
    checks={"gradient_max_error":float(np.max(abs(grad-numerical))),
        "gradient_pass":bool(np.max(abs(grad-numerical))<1e-7),
        "power":float(np.sum(abs(w)**2)),"power_feasible":bool(np.sum(abs(w)**2)<=f["power"]+1e-10),
        "unit_modulus_max_error":float(np.max(abs(abs(np.exp(1j*phases))-1))),
        "rotation_feasible":bool(np.all(abs(angles-center)<=f["rotation_half_width"]+1e-10)),
        "joint_objective_monotone":bool(np.min(np.diff(hj))>=-1e-10),
        "fixed_objective_monotone":bool(np.min(np.diff(hb))>=-1e-10),
        "nmse_identity_error":float(identity),"utility_identity_error":float(reduced),
        "direction_unit_norm_max_error":unit_error,"finite":bool(np.all(np.isfinite(joint)))}
    assert checks["gradient_pass"] and checks["power_feasible"] and checks["rotation_feasible"]
    assert checks["joint_objective_monotone"] and checks["fixed_objective_monotone"]
    assert identity<1e-12 and reduced<1e-12 and unit_error<1e-12
    return {"paper_id":"rotatable-isac","metrics":{"initial":summarize(x0,f),"fixed_arrays":summarize(base,f),"joint_rotations":summarize(joint,f)},
        "checks":checks,"history":{"fixed_arrays_utility":hb,"joint_rotations_utility":hj}}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();result=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"paper_id":result["paper_id"],"checks":result["checks"]}))
