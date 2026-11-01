"""PREPARED arithmetic candidate: the same fixed-W/theta/iota utility difference.

No optimizer, step selection, threshold, regularizer, or stop rule. No acceptance
decision is made here. The caller supplies an ACTUAL incumbent/trial pair. This
has not yet been validated against captured original trials or used in a run.

All identities are in real/complex arithmetic. Actual source inputs remain
binary64, as in the original model. Back-hemisphere crossings retain the same
piecewise response; they receive no floor or smoothing.
"""
import numpy as np


def _rotation_factors(r):
    x,y,z=r
    cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
    return (np.array([[1.,0.,0.],[0.,cx,-sx],[0.,sx,cx]]),
            np.array([[cy,0.,sy],[0.,1.,0.],[-sy,0.,cy]]),
            np.array([[cz,-sz,0.],[sz,cz,0.],[0.,0.,1.]]))


def rotation_increment(r0,r1):
    """Q1-Q0 without subtracting two nearly equal rotation matrices."""
    old=_rotation_factors(r0)
    # r1-r0 is the represented actual displacement, not alpha*g before clipping.
    half=(np.asarray(r1)-np.asarray(r0))/2.
    middle=np.asarray(r0)+half
    dc=-2.*np.sin(middle)*np.sin(half)
    ds=2.*np.cos(middle)*np.sin(half)
    dx=np.array([[0.,0.,0.],[0.,dc[0],-ds[0]],[0.,ds[0],dc[0]]])
    dy=np.array([[dc[1],0.,ds[1]],[0.,0.,0.],[-ds[1],0.,dc[1]]])
    dz=np.array([[dc[2],-ds[2],0.],[ds[2],dc[2],0.],[0.,0.,0.]])
    x,y,z=old
    return dx@y@z+(x+dx)@dy@z+(x+dx)@(y+dy)@dz


def response_increment(core,coords,center,direction,r0,r1,c):
    """Return the original a0 and algebraic da=a1-a0 with stable trig changes."""
    coords,center,direction=np.asarray(coords),np.asarray(center),np.asarray(direction)
    a0,_=core.response(coords,center,direction,r0,c)
    q0,_=core.rotation(r0)
    dq=rotation_increment(r0,r1)
    cosine0=float(q0[:,2]@direction)
    dcosine=float(dq[:,2]@direction)
    cosine1=cosine0+dcosine
    q1,_=core.rotation(r1)
    cosine1_original=float(q1[:,2]@direction)
    # Retain the actual original trial hemisphere branch. At a represented
    # boundary, a sign disagreement in the incremental formula also falls
    # back to the literal original responses; no floor or smoothing is added.
    if cosine0<=0. or cosine1_original<=0. or cosine1<=0.:
        a1,_=core.response(coords,center,direction,r1,c)
        return a0,a1-a0
    exponent=c['directivity_exponent']/2.
    amp0=np.sqrt(c['maximum_gain'])*cosine0**exponent
    damp=amp0*np.expm1(exponent*np.log1p(dcosine/cosine0))
    wave=2.*np.pi/c['wavelength']
    phase0=wave*((coords@q0.T+center)@direction)
    dphase=wave*(coords@dq.T@direction)
    # exp(i*dphase)-1, retaining its quadratic real component near zero.
    phase_increment=-2.*np.sin(dphase/2.)**2+1j*np.sin(dphase)
    da=np.exp(1j*phase0)*(damp+(amp0+damp)*phase_increment)
    return a0,da


def field_increment(core,theta,r0,r1,c,fixed_base=None):
    """Delta of the full original direct+RIS field; fixed theta is unchanged."""
    r0,r1=np.asarray(r0),np.asarray(r1)
    base=core.channel_base(r0,c) if fixed_base is None else fixed_base
    h,g,_,_,bridge,_=base
    dh,dg,db=np.zeros_like(h),np.zeros_like(g),np.zeros_like(bridge)
    cb,cr=np.asarray(c['bs_coordinates']),np.asarray(c['ris_coordinates'])
    ob,orr=np.asarray(c['bs_center']),np.asarray(c['ris_center'])
    k=len(c['noise'])
    for u in range(k):
        for p in range(len(c['bu_directions'][u])):
            _,da=response_increment(core,cb,ob,c['bu_directions'][u][p],r0[:3],r1[:3],c)
            dh[:,u]+=complex(c['bu_gain_re'][u][p],c['bu_gain_im'][u][p])*da
            _,da=response_increment(core,cr,orr,c['ru_directions'][u][p],r0[3:],r1[3:],c)
            dg[:,u]+=complex(c['ru_gain_re'][u][p],c['ru_gain_im'][u][p])*da
    for v in range(len(c['bt_directions'])):
        _,dh[:,k+v]=response_increment(core,cb,ob,c['bt_directions'][v],r0[:3],r1[:3],c)
        _,dg[:,k+v]=response_increment(core,cr,orr,c['rt_directions'][v],r0[3:],r1[3:],c)
    for p in range(len(c['br_directions'])):
        ab,dab=response_increment(core,cb,ob,c['br_directions'][p],r0[:3],r1[:3],c)
        ar,dar=response_increment(core,cr,orr,c['rb_directions'][p],r0[3:],r1[3:],c)
        gain=complex(c['br_gain_re'][p],c['br_gain_im'][p])
        db+=gain*(np.outer(dab,ar.conj())+np.outer(ab+dab,dar.conj()))
    f0=h+bridge@(theta[:,None]*g)
    df=dh+db@(theta[:,None]*g)+(bridge+db)@(theta[:,None]*dg)
    return f0,df


def utility_increment(core,w,theta,r0,r1,c,iota,fixed_base=None):
    """Same R(r1)-R(r0)-rho*(NMSE(r1)-NMSE(r0)), with fixed iota.

    log(T1/I1)-log(T0/I0) = log1p((dS*I0-S0*dI)/(T0*I1)).
    Squared pattern residual difference = dp*(2*(p0-iota*pd)+dp).
    This arithmetic provider deliberately returns no accepted/converged flag.
    """
    f0,df=field_increment(core,theta,r0,r1,c,fixed_base)
    k=len(c['noise'])
    y0,dy=f0[:,:k].conj().T@w,df[:,:k].conj().T@w
    z0,dz=f0[:,k:].conj().T@w,df[:,k:].conj().T@w
    ypower=abs(y0)**2
    dypower=2.*np.real(y0.conj()*dy)+abs(dy)**2
    mask=np.ones(ypower.shape,dtype=bool);mask[np.arange(k),np.arange(k)]=False
    s0=ypower[np.arange(k),np.arange(k)]
    ds=dypower[np.arange(k),np.arange(k)]
    i0=np.asarray(c['noise'])+np.sum(np.where(mask,ypower,0.),axis=1)
    di=np.sum(np.where(mask,dypower,0.),axis=1)
    t0=s0+i0
    drate=float(np.log1p((ds*i0-s0*di)/(t0*(i0+di))).sum()/np.log(2.))
    p0=np.sum(abs(z0)**2,axis=1)
    dp=np.sum(2.*np.real(z0.conj()*dz)+abs(dz)**2,axis=1)
    pd=np.asarray(c['desired_pattern'])
    dnmse=float(dp@(2.*(p0-iota*pd)+dp)/(iota*iota*float(pd@pd)))
    return {'utility_increment':drate-c['rho']*dnmse,'rate_increment':drate,
            'nmse_increment':dnmse,'incumbent_field':f0,'field_increment':df}
