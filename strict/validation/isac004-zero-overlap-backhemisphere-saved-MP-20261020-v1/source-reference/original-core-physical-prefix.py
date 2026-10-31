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


def channel_base(r,c):
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
    return h,g,dh,dg,bridge,db


def channels(theta,r,c,_fixed_rotation_base=None):
    h,g,dh,dg,bridge,db=channel_base(r,c) if _fixed_rotation_base is None else _fixed_rotation_base
    m,links=h.shape
    f=h+bridge@(theta[:,None]*g)
    jac=np.empty((m,links,6),complex)
    for d in range(6):
        jac[:,:,d]=dh[:,:,d]+db[:,:,d]@(theta[:,None]*g)+bridge@(theta[:,None]*dg[:,:,d])
    return f,jac,bridge,g


def evaluate(w,theta,r,c,iota=None,gradients=False,_fixed_channel_bundle=None,_fixed_rotation_base=None):
    # Only a W block passes this bundle: theta/r/c are fixed for that block.
    # The original metric/gradient arithmetic below is unchanged.
    field,jac,bridge,g=channels(theta,r,c,_fixed_rotation_base) if _fixed_channel_bundle is None else _fixed_channel_bundle
    k=len(c["noise"])
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


