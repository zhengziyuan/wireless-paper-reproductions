"""Exact stable increments of the ORIGINAL finite-Rician phase objectives.

On the unit circle covariance terms are phase independent. These identities
include all finite-Rician fourth moments, GEO offsets and the full squared
constraint penalty. They change numerical evaluation, not the objective.
"""
import numpy as np
from scipy.special import logsumexp
from models import channel_moments,mr_components


def square_increment(x,dx):
    return 2*np.real(np.conj(x)*dx)+abs(dx)**2


def quadratic_increment(x,dx,Q):
    return float(2*np.vdot(x,Q@dx).real+np.vdot(dx,Q@dx).real)


def mean_changes(data,old,new):
    changes=np.einsum('junm,um->jun',data['G_mean'],data['r_mean']*(new-old))
    geo=data['geo_d_mean']+np.sum(data['geo_G_mean']*old*data['r_mean'],axis=1)
    dgeo=np.sum(data['geo_G_mean']*(new-old)*data['r_mean'],axis=1)
    return changes,square_increment(geo,dgeo)


def ap_increment(data,old,new,W):
    mean,C,_,_,offset=channel_moments(data,old);dm,doffset=mean_changes(data,old,new)
    J,U,N=mean.shape;numerator=np.zeros(U);denominator=offset.copy();dn=np.zeros(U);dd=doffset.copy()
    for u in range(U):
        for j in range(J):
            projected=np.conj(mean[j,u])@W[j];dprojected=np.conj(dm[j,u])@W[j]
            increments=square_increment(projected,dprojected)
            numerator[u]+=abs(projected[u])**2;dn[u]+=increments[u]
            denominator[u]+=sum(np.vdot(W[j,:,i],C[j,u]@W[j,:,i]).real for i in range(U))
            denominator[u]+=np.sum(abs(projected)**2)-abs(projected[u])**2
            dd[u]+=np.sum(increments)-increments[u]
    return (dn*denominator-numerator*dd)/(denominator*(denominator+dd))


def mr_increment(data,old,new,p,smoothing,limit,tts=False):
    s,b,power,l,offset,mean,Q,fourth=mr_components(data,old,tts);dm,doffset=mean_changes(data,old,new)
    J,U,N=mean.shape;M=old.shape[1];dQ=np.zeros_like(Q);ds=np.zeros_like(s);db=np.zeros_like(b);dl=np.zeros_like(l)
    _,C,_,_,_=channel_moments(data,old)
    for j in range(J):
        dfourth=np.zeros(U)
        for u in range(U):
            m=mean[j,u];d=dm[j,u];dp=float(np.sum(square_increment(m,d)))
            dQ[j,u]=np.outer(m,np.conj(d))+np.outer(d,np.conj(m))+np.outer(d,np.conj(d))
            ds[j,u]=2*power[j,u]*dp+dp*dp
            if tts:
                G=data['G_mean'][j,u];r=data['r_mean'][u];rv=data['r_var'][u]
                Cb=rv*(G@G.conj().T);er2=np.vdot(r,r).real+M*rv;eb2=np.vdot(m,m).real+np.trace(Cb).real
                deb4=2*eb2*dp+dp*dp+2*quadratic_increment(m,d,Cb)
                ar=m-data['d_mean'][j,u]
                der2b2=er2*dp+2*rv*np.real(np.vdot(ar,d)+np.vdot(d,m)+np.vdot(d,d))
                dfourth[u]=deb4+2*(N+1)*(data['d_var'][j,u]*dp+data['G_var'][j,u]*der2b2)
            for k in range(l.shape[2]):dl[j,u,k]=quadratic_increment(m,d,data['gt_second'][j,k])
        for u in range(U):
            for i in range(U):
                if tts:
                    db[j,u,i]=dfourth[u] if i==u else np.trace(dQ[j,u]@Q[j,i]+Q[j,u]@dQ[j,i]+dQ[j,u]@dQ[j,i]).real
                else:
                    a=np.vdot(mean[j,u],mean[j,i]);da=np.vdot(mean[j,u],dm[j,i])+np.vdot(dm[j,u],mean[j,i])+np.vdot(dm[j,u],dm[j,i])
                    db[j,u,i]=square_increment(a,da)+quadratic_increment(mean[j,i],dm[j,i],C[j,u])
    numerator=np.sum(p*s,axis=0);denominator=offset+np.einsum('ji,jui->u',p,b)-numerator
    dn=np.sum(p*ds,axis=0);dd=doffset+np.einsum('ji,jui->u',p,db)-dn
    dsinr=(dn*denominator-numerator*dd)/(denominator*(denominator+dd));sinr=numerator/denominator
    centered=-(sinr-np.min(sinr))/smoothing;log_weights=centered-logsumexp(centered);weights=np.exp(log_weights);t=-dsinr/smoothing
    # log1p/expm1 prevents cancellation for near-stationary directions. The
    # centered logsumexp branch is the same exact expression for large steps.
    soft_increment=-smoothing*(np.log1p(weights@np.expm1(t)) if np.max(abs(t))<50 else logsumexp(log_weights+t))
    residual=np.einsum('ju,juk->k',p,l)-limit;dleak=np.einsum('ju,juk->k',p,dl)
    return float(soft_increment-np.sum(2*residual*dleak+dleak*dleak))
