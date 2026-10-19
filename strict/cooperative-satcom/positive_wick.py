"""Isolated original conditional-Gaussian formulas, non-subtractive MR own/cross terms.

NumPy binary64, no solver/RNG/phase normalization/clipping.
math.fsum changes reduction precision only, not the source mathematical metric.
"""
import math
import numpy as np

def total(values):return math.fsum(float(x) for x in values)
def n2(value):return total((np.abs(value)**2).reshape(-1))
def realdot(a,b):return float(np.vdot(a,b).real)


def moments(data,phi):
    J,U,N=data['d_mean'].shape;M=phi.shape[1]
    if phi.shape!=(U,M) or data['G_mean'].shape!=(J,U,N,M):raise ValueError('Complete channel dimensions required')
    if np.max(np.abs(np.abs(phi)-1))>1e-10:raise ValueError('Source near-unit stored phase domain required')
    mean=np.zeros((J,U,N),complex);C=np.zeros((J,U,N,N),complex);Q=np.zeros_like(C)
    A=np.zeros((J,U,N,M),complex);Cb=np.zeros_like(C);Ev=np.zeros((J,U));power=np.zeros((J,U))
    own=np.zeros((J,U));fourth=np.zeros((J,U));offset=np.zeros(U)
    for j in range(J):
        for u in range(U):
            rv=float(data['r_var'][u]);dv=float(data['d_var'][j,u]);gv=float(data['G_var'][j,u])
            if min(rv,dv,gv)<0:raise ValueError('No negative source variance or silent clipping')
            a=data['G_mean'][j,u]*phi[u][None,:];r=data['r_mean'][u]
            mu=data['d_mean'][j,u]+a@r
            f=n2(a);r2=n2(r);m2=n2(mu);er2=r2+M*rv;er4=er2**2+M*rv**2+2*rv*r2
            ev=dv+gv*er2;cb=rv*a@a.conj().T;cov=cb+ev*np.eye(N)
            eb2=m2+rv*f;ev2=dv**2+2*dv*gv*er2+gv**2*er4
            wick=n2(r[:,None]*mu.conj()[None,:]+rv*a.conj().T)+M*rv*m2+rv*r2*f+M*rv**2*f
            t=a.conj().T@a+N*gv*np.eye(M)
            ownvar=total((rv**2*n2(t),2*rv*n2(a.conj().T@mu+N*gv*r),N*ev2,2*dv*eb2,2*gv*wick))
            q=eb2+N*ev
            A[j,u]=a;mean[j,u]=mu;Cb[j,u]=cb;C[j,u]=cov;Q[j,u]=cov+np.outer(mu,mu.conj())
            Ev[j,u]=ev;power[j,u]=q;own[j,u]=ownvar;fourth[j,u]=q*q+ownvar
    for u in range(U):
        r=data['r_mean'][u];rv=float(data['r_var'][u])
        geoA=data['geo_G_mean'][u]*phi[u]
        gm=data['geo_d_mean'][u]+np.sum(geoA*r)
        offset[u]=total((1,float(data['geo_d_var'][u]),float(data['geo_G_var'][u])*(n2(r)+M*rv),rv*n2(geoA),abs(gm)**2))
    return dict(mean=mean,C=C,Q=Q,A=A,Cb=Cb,Ev=Ev,tts_power=power,tts_own=own,fourth=fourth,offset=offset)


def evaluate_mr(data,phi,p,mu,limit,tts):
    terms=moments(data,phi);mean,C,Q,A,Cb,Ev=(terms[k] for k in ('mean','C','Q','A','Cb','Ev'))
    J,U,N=mean.shape;M=phi.shape[1];K=len(limit)
    if p.shape!=(J,U) or mu<=0 or not np.all(np.isfinite(p)) or np.any(p<0):raise ValueError('Original positive smoothing/nonnegative full powers required')
    gt=(data['gt_second']+data['gt_second'].conj().swapaxes(-1,-2))/2
    power=terms['tts_power'] if tts else np.sum(abs(mean)**2,axis=2)
    signal=power**2;cross=np.zeros((J,U,U));own=np.zeros((J,U));leak=np.zeros((J,U,K))
    for j in range(J):
        for u in range(U):
            rv=float(data['r_var'][u]);m=mean[j,u];a=A[j,u];f=n2(a)
            own[j,u]=terms['tts_own'][j,u] if tts else total((rv*n2(a.conj().T@m),Ev[j,u]*n2(m)))
            for i in range(U):
                if i==u:cross[j,u,i]=signal[j,u]+own[j,u];continue
                mi=mean[j,i];ai=A[j,i];rvi=float(data['r_var'][i])
                value=total((rv*n2(a.conj().T@mi),Ev[j,u]*n2(mi),abs(np.vdot(m,mi))**2))
                if tts:
                    value=total((value,rvi*n2(ai.conj().T@m),Ev[j,i]*n2(m),
                        rv*rvi*n2(a.conj().T@ai),rv*Ev[j,i]*f,rvi*Ev[j,u]*n2(ai),N*Ev[j,u]*Ev[j,i]))
                cross[j,u,i]=value
            for k in range(K):
                leak[j,u,k]=realdot(m,gt[j,k]@m)+(float(np.trace(gt[j,k]@C[j,u]).real) if tts else 0)
    numerator=np.sum(p*signal,axis=0)
    denominator=np.array([total([terms['offset'][u]]+[p[j,u]*own[j,u] for j in range(J)]+
        [p[j,i]*cross[j,u,i] for j in range(J) for i in range(U) if i!=u]) for u in range(U)])
    if not np.all(np.isfinite(denominator)) or min(denominator)<=0:raise ValueError('Original positive denominator required')
    sinr=numerator/denominator;minimum=np.min(sinr);ex=np.exp(-(sinr-minimum)/mu);weights=ex/np.sum(ex)
    residual=np.einsum('ju,juk->k',p,leak)-limit
    value=float(minimum-mu*np.log(np.sum(ex))-np.sum(residual**2))
    theta=np.zeros((U,M));dn_all=np.zeros((U,M,U));dd_all=np.zeros_like(dn_all)
    ds_all=np.zeros_like(dn_all);penalty=np.zeros((U,M))
    for v in range(U):
        for coordinate in range(M):
            dns=[[] for _ in range(U)];dds=[[] for _ in range(U)];dls=[[] for _ in range(K)]
            gm=data['geo_d_mean'][v]+np.sum(data['geo_G_mean'][v]*phi[v]*data['r_mean'][v])
            dg=1j*phi[v,coordinate]*data['geo_G_mean'][v,coordinate]*data['r_mean'][v,coordinate]
            dds[v].append(2*float((np.conj(gm)*dg).real))
            for j in range(J):
                mv=mean[j,v];d=1j*phi[v,coordinate]*data['G_mean'][j,v,:,coordinate]*data['r_mean'][v,coordinate]
                dp=2*realdot(mv,d);dns[v].append(p[j,v]*2*power[j,v]*dp)
                if tts:
                    ar=A[j,v]@data['r_mean'][v]
                    own_der=total((4*realdot(mv,Cb[j,v]@d),2*Ev[j,v]*dp,
                        4*(N+1)*float(data['G_var'][j,v])*float(data['r_var'][v])*(realdot(d,mv)+realdot(ar,d))))
                else:own_der=2*realdot(d,C[j,v]@mv)
                dds[v].append(p[j,v]*own_der)
                for u in range(U):
                    for i in range(U):
                        if i==u:continue
                        c=np.vdot(mean[j,u],mean[j,i]);db=0.
                        if u==v:
                            db+=2*float((np.conj(c)*np.vdot(d,mean[j,i])).real)
                            if tts:db+=2*realdot(d,C[j,i]@mv)
                        if i==v:
                            db+=2*realdot(d,C[j,u]@mv)+2*float((np.conj(c)*np.vdot(mean[j,u],d)).real)
                        dds[u].append(p[j,i]*db)
                for k in range(K):dls[k].append(p[j,v]*2*realdot(d,gt[j,k]@mv))
            dn=np.array([total(row) for row in dns]);dd=np.array([total(row) for row in dds])
            ds=(dn*denominator-numerator*dd)/denominator**2
            pen=2*total(residual[k]*total(dls[k]) for k in range(K))
            theta[v,coordinate]=total(weights[u]*ds[u] for u in range(U))-pen
            dn_all[v,coordinate]=dn;dd_all[v,coordinate]=dd;ds_all[v,coordinate]=ds;penalty[v,coordinate]=pen
    return dict(criterion=value,gradient=1j*phi*theta,theta_gradient=theta,numerator=numerator,
        denominator=denominator,sinr=sinr,weights=weights,residual=residual,signal=signal,cross=cross,
        own_interference=own,power=power,leakage=leak,dnumerator=dn_all,ddenominator=dd_all,
        dsinr=ds_all,penalty_theta=penalty,**terms)


def evaluate_ap(data,phi,W):
    """Original AP individual-user SINR/angular derivative, no MR softmin."""
    terms=moments(data,phi);mean,C,Q=(terms[k] for k in ('mean','C','Q'))
    J,U,N=mean.shape;M=phi.shape[1]
    if W.shape!=(J,N,U):raise ValueError('Full original AP precoder required')
    num=np.zeros(U);den=terms['offset'].copy();theta=np.zeros((U,M))
    for u in range(U):
        for j in range(J):
            num[u]+=abs(np.vdot(mean[j,u],W[j,:,u]))**2
            for i in range(U):den[u]+=realdot(W[j,:,i],(C[j,u] if i==u else Q[j,u])@W[j,:,i])
        for coordinate in range(M):
            gm=data['geo_d_mean'][u]+np.sum(data['geo_G_mean'][u]*phi[u]*data['r_mean'][u])
            dg=1j*phi[u,coordinate]*data['geo_G_mean'][u,coordinate]*data['r_mean'][u,coordinate]
            dn=0.;dd=2*float((np.conj(gm)*dg).real)
            for j in range(J):
                d=1j*phi[u,coordinate]*data['G_mean'][j,u,:,coordinate]*data['r_mean'][u,coordinate]
                a=np.vdot(mean[j,u],W[j,:,u]);da=np.vdot(d,W[j,:,u]);dn+=2*float((np.conj(a)*da).real)
                for i in range(U):
                    if i!=u:dd+=2*float((np.conj(np.vdot(mean[j,u],W[j,:,i]))*np.vdot(d,W[j,:,i])).real)
            theta[u,coordinate]=(dn*den[u]-num[u]*dd)/den[u]**2
    return dict(criterion=num/den,gradient=1j*phi*theta,theta_gradient=theta,numerator=num,
                denominator=den,sinr=num/den,weights=None,**terms)
