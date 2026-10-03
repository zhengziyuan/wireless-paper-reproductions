"""Author/thesis finite-Rician model with analytical circle derivatives.

Each LU has its own RIS; channels for different LUs are independent. The same
ground channel is shared across satellites for a given LU. Monte Carlo samples
retain that dependence. Geometry and unreported gains are configured, never
hidden empirical curve-fitting factors.
"""
import numpy as np
from core import rician_effective_moments, statistical_mr_coefficients, tts_mr_coefficients


def channel_moments(data,phi,no_ris=False):
    J,U,N=data['d_mean'].shape
    mean=np.zeros((J,U,N),complex); cov=np.zeros((J,U,N,N),complex)
    second=np.zeros_like(cov); fourth=np.zeros((J,U)); offset=np.ones(U)
    for u in range(U):
        for j in range(J):
            if no_ris:
                q=rician_effective_moments(data['d_mean'][j,u],data['d_var'][j,u],
                    data['G_mean'][j,u]*0,0,data['r_mean'][u],data['r_var'][u],phi[u])
            else:
                q=rician_effective_moments(data['d_mean'][j,u],data['d_var'][j,u],
                    data['G_mean'][j,u],data['G_var'][j,u],data['r_mean'][u],data['r_var'][u],phi[u])
            mean[j,u]=q['mean']; cov[j,u]=q['covariance']; second[j,u]=q['second']; fourth[j,u]=q['norm_fourth']
        g=rician_effective_moments(np.array([data['geo_d_mean'][u]]),data['geo_d_var'][u],
                data['geo_G_mean'][u][None,:]*(0 if no_ris else 1),data['geo_G_var'][u]*(0 if no_ris else 1),
                data['r_mean'][u],data['r_var'][u],phi[u])
        offset[u]+=g['second'][0,0].real
    return mean,cov,second,fourth,offset


def moment_direction(data,phi,mean,u,m):
    """Exact d/dtheta[u,m] first/second/norm-fourth moments, not finite differences."""
    J,U,N=mean.shape; dm=np.zeros_like(mean); dQ=np.zeros((J,U,N,N),complex); dfourth=np.zeros((J,U))
    for j in range(J):
        G=data['G_mean'][j,u]; r=data['r_mean'][u]; rv=data['r_var'][u]
        mu=mean[j,u]; d=1j*phi[u,m]*G[:,m]*r[m]; dm[j,u]=d
        dQ[j,u]=np.outer(d,np.conj(mu))+np.outer(mu,np.conj(d))
        Cb=rv*G@G.conj().T; er2=np.vdot(r,r).real+r.size*rv
        eb2=np.vdot(mu,mu).real+np.trace(Cb).real; deb2=2*np.vdot(mu,d).real
        deb4=2*eb2*deb2+4*np.vdot(mu,Cb@d).real
        ar=mu-data['d_mean'][j,u]
        der2b2=er2*deb2+2*rv*np.real(np.vdot(d,mu)+np.vdot(ar,d))
        devb2=data['d_var'][j,u]*deb2+data['G_var'][j,u]*der2b2
        dfourth[j,u]=deb4+2*(N+1)*devb2
    geo_mean=data['geo_d_mean'][u]+np.sum(data['geo_G_mean'][u]*phi[u]*data['r_mean'][u])
    dgeo=1j*phi[u,m]*data['geo_G_mean'][u,m]*data['r_mean'][u,m]
    doffset=np.zeros(U); doffset[u]=2*np.real(np.conj(geo_mean)*dgeo)
    return dm,dQ,dfourth,doffset


def mr_components(data,phi,tts=False,no_ris=False):
    mean,cov,Q,fourth,offset=channel_moments(data,phi,no_ris)
    coef=tts_mr_coefficients(Q,fourth,data['gt_second']) if tts else statistical_mr_coefficients(mean,Q,data['gt_second'])
    return (*coef,offset,mean,Q,fourth)


def mr_phase_value_gradient(data,phi,p,mu,limit,tts=False):
    s,b,power,l,offset,mean,Q,fourth=mr_components(data,phi,tts)
    J,U=p.shape; M=phi.shape[1]
    numerator=np.sum(p*s,axis=0); denominator=offset.copy()
    for u in range(U): denominator[u]+=np.sum(p*b[:,u,:])-numerator[u]
    sinr=numerator/denominator
    minimum=np.min(sinr); exp=np.exp(-(sinr-minimum)/mu); weights=exp/np.sum(exp)
    leakage=np.einsum('ju,juk->k',p,l); residual=leakage-limit
    value=float(minimum-mu*np.log(np.sum(exp))-np.sum(residual**2))
    gradtheta=np.zeros_like(phi.real)
    for v in range(U):
        for m in range(M):
            dm,dQ,df,do=moment_direction(data,phi,mean,v,m)
            ds=np.zeros((J,U)); db=np.zeros((J,U,U)); dl=np.zeros_like(l)
            for j in range(J):
                for u in range(U):
                    if tts:
                        dp=np.trace(dQ[j,u]).real; ds[j,u]=2*power[j,u]*dp
                        for i in range(U):
                            db[j,u,i]=df[j,u] if i==u else np.trace(dQ[j,u]@Q[j,i]+Q[j,u]@dQ[j,i]).real
                        for k in range(l.shape[2]): dl[j,u,k]=np.trace(data['gt_second'][j,k]@dQ[j,u]).real
                    else:
                        dp=2*np.vdot(mean[j,u],dm[j,u]).real; ds[j,u]=2*power[j,u]*dp
                        for i in range(U):
                            db[j,u,i]=2*np.vdot(dm[j,i],Q[j,u]@mean[j,i]).real+np.vdot(mean[j,i],dQ[j,u]@mean[j,i]).real
                        for k in range(l.shape[2]): dl[j,u,k]=2*np.vdot(dm[j,u],data['gt_second'][j,k]@mean[j,u]).real
            dn=np.sum(p*ds,axis=0); dd=do.copy()
            for u in range(U): dd[u]+=np.sum(p*db[:,u,:])-dn[u]
            dsnr=(dn*denominator-numerator*dd)/denominator**2
            dleak=np.einsum('ju,juk->k',p,dl)
            gradtheta[v,m]=weights@dsnr-2*residual@dleak
    return value,1j*phi*gradtheta


def ap_phase_value_gradient(data,phi,W):
    mean,C,Q,_,offset=channel_moments(data,phi); J,U,N=mean.shape; M=phi.shape[1]
    numerator=np.zeros(U); den=offset.copy()
    for u in range(U):
        for j in range(J):
            numerator[u]+=abs(np.vdot(mean[j,u],W[j,:,u]))**2
            for i in range(U): den[u]+=np.vdot(W[j,:,i],(C[j,u] if i==u else Q[j,u])@W[j,:,i]).real
    sinr=numerator/den; gtheta=np.zeros((U,M))
    # Each RIS affects only its own LU SINR; optimizing all U independently
    # preserves the minimum objective, exactly the author Algorithm 1 RMO stage.
    for u in range(U):
        for m in range(M):
            dm,dQ,_,do=moment_direction(data,phi,mean,u,m); dn=0; dd=do[u]
            for j in range(J):
                a=np.vdot(mean[j,u],W[j,:,u]); da=np.vdot(dm[j,u],W[j,:,u])
                dn+=2*np.real(np.conj(a)*da)
                for i in range(U):
                    if i!=u: dd+=np.vdot(W[j,:,i],dQ[j,u]@W[j,:,i]).real
            gtheta[u,m]=(dn*den[u]-numerator[u]*dd)/den[u]**2
    return sinr,1j*phi*gtheta


def sample_effective(data,phi,rng):
    """Shared r[u] across satellites, independent G[j,u], no pure-LoS fallback."""
    cn=lambda shape:(rng.standard_normal(shape)+1j*rng.standard_normal(shape))/np.sqrt(2)
    J,U,N=data['d_mean'].shape; out=np.zeros((J,U,N),complex)
    for u in range(U):
        r=data['r_mean'][u]+np.sqrt(data['r_var'][u])*cn(data['r_mean'][u].shape)
        for j in range(J):
            G=data['G_mean'][j,u]+np.sqrt(data['G_var'][j,u])*cn(data['G_mean'][j,u].shape)
            d=data['d_mean'][j,u]+np.sqrt(data['d_var'][j,u])*cn((N,))
            out[j,u]=d+G@(phi[u]*r)
    return out
