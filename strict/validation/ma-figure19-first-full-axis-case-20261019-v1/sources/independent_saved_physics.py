"""Exact independent physical-reference definition excerpts; no optimizers."""
import numpy as np

def rates_batch(h, w, noise):
    gain = abs(h.conj().transpose(0,2,1) @ w)**2
    signal = np.diagonal(gain, axis1=1, axis2=2)
    return np.log2(1+signal/(gain.sum(axis=2)-signal+noise)).sum(axis=1)


def geometry_functions(job,cfg):
    n,m=job['N'],job['M']; power,kap=job['power'],job['kappa'];geom=job['geometry']
    el,az=np.array(geom['elevation']),np.array(geom['azimuth'])
    directions=np.c_[np.cos(el)*np.sin(az),np.sin(el)]
    beta=1e-4*np.array(geom['distances_m'])**-2.8;noise=np.full(m,1e-11)
    nr,nc=cfg['antenna_factorization'][str(n)]
    initial=np.array([[x,y]for x in(np.arange(nr)-(nr-1)/2)/2 for y in(np.arange(nc)-(nc-1)/2)/2])
    lower,upper=-np.array([nr,nc])*job['A']/2,np.array([nr,nc])*job['A']/2
    draws=np.array(job['nlos_re'])+1j*np.array(job['nlos_im'])
    def channel(t):
        return np.exp(2j*np.pi*(t@directions.T))[None,:,:]*np.sqrt(beta*kap/(kap+1))[None,None,:]+draws*np.sqrt(beta/(kap+1))[None,None,:]
    def design(t,mode):
        H=np.exp(2j*np.pi*(t@directions.T))
        if mode=='zf':
            sigma=np.eye(m)/(kap+1)+kap/(kap+1)*(H.conj().T@H)/n
            eta=power*beta*(n-m)/(m*noise)
            return float(np.log2(1+eta/np.real(np.diag(np.linalg.solve(sigma,np.eye(m))))).sum())
        numerator=beta**2*(n*n+n*(2*kap+1)/(kap+1)**2)
        denominator=noise*n*beta.sum()/power
        for u in range(m):
            for v in range(m):
                if u!=v:
                    inner=np.sum(np.exp(2j*np.pi*(t@(directions[u]-directions[v]))))
                    denominator[u]+=beta[u]*beta[v]*(kap*kap*abs(inner)**2+n*(2*kap+1))/(kap+1)**2
        return float(np.log2(1+numerator/denominator).sum())
    return initial,lower,upper,draws,noise,channel,design


def ma_rates(h,power,noise,mode):
    if mode=='mrt':
        w=h*np.sqrt(power/np.sum(abs(h)**2,axis=(1,2)))[:,None,None]
    else:
        count,n,m=h.shape;q,r=np.linalg.qr(h,mode='reduced')
        v=q@np.linalg.solve(r.conj().transpose(0,2,1),np.broadcast_to(np.eye(m),(count,m,m)))
        w=v/np.linalg.norm(v,axis=1)[:,None,:]*np.sqrt(power/m)
    return rates_batch(h,w,noise),np.sum(abs(w)**2,axis=(1,2))

