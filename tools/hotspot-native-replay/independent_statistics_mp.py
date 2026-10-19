"""Independent full finite-Rician/statistical vector-QT fixed-input formulas.

No numerical package is imported here. The future caller supplies an MP context.
This module never initializes a design, generates a channel, or optimizes W/phi.
Ordinary row channels and the literal P transpose are retained throughout.
"""
import math


def number(mp,value):
    if hasattr(value,'item'):value=value.item()
    if type(value) is complex:return mp.mpc(number(mp,value.real),number(mp,value.imag))
    if type(value) is int:return mp.mpf(value)
    if type(value) is float:
        if not math.isfinite(value):raise ValueError('Nonfinite literal double input')
        n,d=value.as_integer_ratio();return mp.mpf(n)/d
    raise ValueError('Only actual integer/binary64 real/complex inputs are promoted')


def matrix(mp,value):
    shape=tuple(value.shape)
    if len(shape)!=2:raise ValueError('A complete original two-dimensional matrix is required')
    return mp.matrix([[number(mp,value[i,j]) for j in range(shape[1])] for i in range(shape[0])])


def filled_matrix(mp,rows,cols,element):
    """Populate every entry explicitly; mpmath ignores a third constructor arg."""
    result=mp.matrix(rows,cols)
    for i in range(rows):
        for j in range(cols):result[i,j]=element(i,j)
    return result


def row(mp,value,count):
    if tuple(value.shape)!=(1,count):raise ValueError('Literal original row-vector dimensions required')
    return [number(mp,value[0,i]) for i in range(count)]


def sumsq(mp,value):return mp.fsum(abs(z)**2 for z in value)
def real(mp,value):return mp.re(value)


def input_matrices(mp,x):
    names=('direct_mean','direct_variance','matrix_mean','matrix_variance','ground_mean','ground_variance','nhu_mean','nhu_variance')
    result={name:matrix(mp,x[name]) for name in names}
    for name in ('direct_variance','matrix_variance','ground_variance','nhu_variance'):
        if any(mp.im(v)!=0 or v<0 for v in result[name]):raise ValueError('Every literal physical variance must be real/nonnegative')
    return result


def moments(mp,x,phi,no_ris=False):
    dm,dv,G,gv,r,rv,nm,nv=[x[k] for k in ('direct_mean','direct_variance','matrix_mean','matrix_variance','ground_mean','ground_variance','nhu_mean','nhu_variance')]
    U,N,M,K=dm.rows,dm.cols,G.rows,nm.rows
    if G.cols!=N or r.rows!=U or r.cols!=M or len(phi)!=M or nm.cols!=N:raise ValueError('No reduced moment model')
    mu=dm.copy();Q=[];covariances=[]
    for u in range(U):
        C=mp.matrix(N,N)
        for n in range(N):
            C[n,n]=dv[u,n]
            if not no_ris:
                mu[u,n]+=mp.fsum(phi[m]*r[u,m]*G[m,n] for m in range(M))
                C[n,n]+=mp.fsum(gv[m,n]*(abs(r[u,m])**2+rv[u,m]) for m in range(M))
            for j in range(N):
                if not no_ris:C[n,j]+=mp.fsum(mp.conj(G[m,n])*rv[u,m]*G[m,j] for m in range(M))
        covariances.append(C)
        Q.append(C+filled_matrix(mp,N,N,lambda n,j:mp.conj(mu[u,n])*mu[u,j]))
    Psi=[]
    for k in range(K):
        Psi.append(filled_matrix(mp,N,N,lambda n,j:(nv[k,n] if n==j else 0)+mp.conj(nm[k,n])*nm[k,j]))
    return Q,Psi,mu,covariances


def evaluate(mp,Q,Psi,W,noise):
    mats=Q+Psi;J=W.cols
    if len(mats)!=J or W.rows!=mats[0].rows or noise<=0:raise ValueError('Full positive-noise expected-power metric required')
    received=mp.matrix(J,J)
    for u,q in enumerate(mats):
        product=q*W
        for stream in range(J):received[u,stream]=real(mp,mp.fsum(mp.conj(W[n,stream])*product[n,stream] for n in range(W.rows)))
    sinr=[]
    for u in range(J):
        denominator=mp.fsum(received[u,j] for j in range(J) if j!=u)+noise
        if denominator<=0:raise ValueError('Nonpositive original denominator')
        sinr.append(received[u,u]/denominator)
    rates=[mp.log1p(s)/mp.log(2) for s in sinr]
    return dict(received=received,sinr=sinr,rates=rates,hu_sum_rate=mp.fsum(rates[:len(Q)]),power=sumsq(mp,W))


def qt_values(mp,D,z,W,noise):
    J=W.cols
    if len(D)!=J or z.rows!=J or z.cols!=W.rows:raise ValueError('Every original vector auxiliary is required')
    result=[];denominators=[];products=[]
    for j in range(J):
        product=D[j]*W
        denominator=noise+mp.fsum(abs(product[n,k])**2 for n in range(W.rows) for k in range(J) if k!=j)
        normz=mp.fsum(abs(z[j,n])**2 for n in range(W.rows))
        result.append(2*real(mp,mp.fsum(mp.conj(z[j,n])*product[n,j] for n in range(W.rows)))-normz*denominator)
        denominators.append(denominator);products.append(product)
    return result,denominators,products


def rate_gradient(mp,x,phi,W,noise):
    Q,_,mu,_=moments(mp,x,phi);U,N,M=x['direct_mean'].rows,x['direct_mean'].cols,len(phi)
    J=W.cols;received=mp.matrix(U,J)
    for u in range(U):
        product=Q[u]*W
        for j in range(J):received[u,j]=real(mp,mp.fsum(mp.conj(W[n,j])*product[n,j] for n in range(N)))
    total=[noise+mp.fsum(received[u,j] for j in range(J)) for u in range(U)]
    den=[total[u]-received[u,u] for u in range(U)]
    if min(den)<=0:raise ValueError('Full original rate denominator positive')
    projection=mu*W;theta=[]
    for m in range(M):
        dmu=filled_matrix(mp,U,N,lambda u,n:1j*phi[m]*x['ground_mean'][u,m]*x['matrix_mean'][m,n])
        dprojection=dmu*W;derivative=filled_matrix(mp,U,J,lambda u,j:2*real(mp,mp.conj(projection[u,j])*dprojection[u,j]))
        value=mp.fsum((mp.fsum(derivative[u,j] for j in range(J))/total[u]
                      -(mp.fsum(derivative[u,j] for j in range(J))-derivative[u,u])/den[u]) for u in range(U))/mp.log(2)
        theta.append(value)
    return mp.fsum(mp.log(total[u]/den[u])/mp.log(2) for u in range(U)),[1j*phi[m]*theta[m] for m in range(M)]


def pair_value_derivative(mp,x,A,B,u,v,dA=None):
    dm,dv,G,gv,r,rv=[x[k] for k in ('direct_mean','direct_variance','matrix_mean','matrix_variance','ground_mean','ground_variance')]
    du=dm[u,:].T;dvect=dm[v,:].T;ru=r[u,:].T;rr=r[v,:].T;vu=rv[u,:].T;vv=rv[v,:].T
    bu=du+A*ru;bv=dvect+A*rr
    eu=filled_matrix(mp,A.rows,1,lambda n,k:dv[u,n]+mp.fsum(gv[m,n]*(abs(ru[m])**2+vu[m]) for m in range(A.cols)))
    ev=filled_matrix(mp,A.rows,1,lambda n,k:dv[v,n]+mp.fsum(gv[m,n]*(abs(rr[m])**2+vv[m]) for m in range(A.cols)))
    ebu=filled_matrix(mp,A.rows,1,lambda n,k:abs(bu[n])**2+mp.fsum(abs(A[n,m])**2*vu[m] for m in range(A.cols)))
    ebv=filled_matrix(mp,A.rows,1,lambda n,k:abs(bv[n])**2+mp.fsum(abs(A[n,m])**2*vv[m] for m in range(A.cols)))
    b=du.H*A+ru.H*B;c=A.H*dvect+B*rr;t=(du.H*dvect+du.H*A*rr+ru.H*A.H*dvect+ru.H*B*rr)[0]
    value=abs(t)**2+mp.fsum(vv[m]*abs(b[m])**2+vu[m]*abs(c[m])**2 for m in range(A.cols))
    value+=mp.fsum(vu[i]*vv[j]*abs(B[i,j])**2 for i in range(A.cols) for j in range(A.cols))
    value+=(ebu.T*ev+ebv.T*eu+eu.T*ev)[0]
    if dA is None:return real(mp,value),None
    dB=dA.H*A+A.H*dA;db=du.H*dA+ru.H*dB;dc=dA.H*dvect+dB*rr
    dt=(du.H*dA*rr+ru.H*dA.H*dvect+ru.H*dB*rr)[0]
    debu=filled_matrix(mp,A.rows,1,lambda n,k:2*real(mp,mp.conj(bu[n])*(dA*ru)[n])
        +mp.fsum(2*real(mp,mp.conj(A[n,m])*dA[n,m])*vu[m] for m in range(A.cols)))
    debv=filled_matrix(mp,A.rows,1,lambda n,k:2*real(mp,mp.conj(bv[n])*(dA*rr)[n])
        +mp.fsum(2*real(mp,mp.conj(A[n,m])*dA[n,m])*vv[m] for m in range(A.cols)))
    change=2*real(mp,(mp.conj(t)*dt
        +mp.fsum(vv[m]*mp.conj(b[m])*db[m]+vu[m]*mp.conj(c[m])*dc[m] for m in range(A.cols))
        +mp.fsum(vu[i]*vv[j]*mp.conj(B[i,j])*dB[i,j] for i in range(A.cols) for j in range(A.cols))))
    change+=(debu.T*ev+debv.T*eu)[0]
    return real(mp,value),real(mp,change)


def criterion_gradient(mp,x,phi,P):
    Q,_,mu,_=moments(mp,x,phi);G=x['matrix_mean'];gv=x['matrix_variance'];U=len(Q);N=G.cols;M=G.rows
    A=filled_matrix(mp,N,M,lambda n,m:G[m,n]*phi[m]);B=A.H*A+mp.diag([mp.fsum(gv[m,n] for n in range(N)) for m in range(M)])
    value=mp.fsum(real(mp,mp.fsum((Q[u]*P)[n,n] for n in range(N))) for u in range(U))
    value-=mp.fsum(pair_value_derivative(mp,x,A,B,u,v)[0] for u in range(U) for v in range(u))
    theta=[]
    for m in range(M):
        dA=filled_matrix(mp,N,M,lambda n,j:1j*phi[m]*G[m,n] if j==m else 0)
        derivative=mp.fsum(2*real(mp,(mu[u,:].T.H*P.T*dA*x['ground_mean'][u,:].T)[0]) for u in range(U))
        derivative-=mp.fsum(pair_value_derivative(mp,x,A,B,u,v,dA)[1] for u in range(U) for v in range(u))
        theta.append(derivative)
    return value,[1j*phi[m]*theta[m] for m in range(M)]


def instantaneous(mp,hu,nhu,W,noise):
    H=filled_matrix(mp,hu.rows+nhu.rows,hu.cols,lambda u,n:hu[u,n] if u<hu.rows else nhu[u-hu.rows,n])
    product=H*W;J=W.cols
    sinr=[abs(product[u,u])**2/(noise+mp.fsum(abs(product[u,j])**2 for j in range(J) if j!=u)) for u in range(J)]
    rates=[mp.log1p(s)/mp.log(2) for s in sinr]
    return dict(received=filled_matrix(mp,J,J,lambda u,j:abs(product[u,j])**2),sinr=sinr,rates=rates,
                hu_sum_rate=mp.fsum(rates[:hu.rows]),power=sumsq(mp,W),
                leakage=max(abs(product[u,j]) for u in range(J) for j in range(J) if j!=u))


def projector_square(mp,x):
    """All finite-CN normalized NHU projector entries, not mean outer products.

    Each upper-triangle entry is independently integrated on the exact original
    t=s/(1-s) interval. Hermitian partners are mathematical conjugates, not
    removed dimensions. Integral accuracy is additionally compared at MP80 and
    MP100 by the caller; this is not a rigorous interval certificate.
    """
    nm,nv=x['nhu_mean'],x['nhu_variance'];K,N=nm.rows,nm.cols;projectors=[]
    if K<=0 or N!=16:raise ValueError('Complete original nonempty NHU/feed model')
    for k in range(K):
        scale=mp.fsum(abs(nm[k,n])**2+nv[k,n] for n in range(N))
        if scale<=0:raise ValueError('A nonzero full finite-CN channel is required')
        m=[mp.conj(nm[k,n])/mp.sqrt(scale) for n in range(N)]
        v=[nv[k,n]/scale for n in range(N)]
        if any(a<=0 for a in v):raise ValueError('No LoS-only replacement or erased finite variance')
        P=mp.matrix(N,N)
        for i in range(N):
            for j in range(i,N):
                def integrand(s):
                    if s==1:return mp.mpf(0)
                    t=s/(1-s);iv=[1/(1+t*a) for a in v]
                    lap=mp.exp(-mp.fsum(mp.log1p(t*a) for a in v)
                        -t*mp.fsum(abs(m[n])**2*iv[n] for n in range(N)))
                    entry=m[i]*mp.conj(m[j])*iv[i]*iv[j]
                    if i==j:entry+=v[i]*iv[i]
                    return lap*entry/(1-s)**2
                P[i,j]=mp.quad(integrand,[0,mp.mpf('0.5'),mp.mpf('0.9'),mp.mpf('0.99'),1])
                P[j,i]=mp.conj(P[i,j])
        projectors.append(P)
    square=mp.eye(N)
    for p in projectors:square-=p
    for k in range(K):
        for j in range(K):
            if k!=j:square+=projectors[k]*projectors[j]
    return (square+square.H)/2,projectors
