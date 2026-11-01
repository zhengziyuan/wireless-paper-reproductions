"""MP formulas for three saved MA prestates only; no source solver import.

Two declared operand layers: exact captured binary64 physical fields, or
source-literal geometry evaluated at high precision. Neither is a historical
producer-operand recovery. Non-LoS samples/MC are unnecessary for Eq13/37 SCA.
"""
import mpmath as mp


def exact(x):
    n,d=float(x).as_integer_ratio()
    return mp.mpf(n)/d


def dot(a,b):
    assert len(a)==len(b)
    return mp.fsum(x*y for x,y in zip(a,b))


def largest2(B):
    return (B[0][0]+B[1][1]+mp.sqrt((B[0][0]-B[1][1])**2+4*B[0][1]*B[1][0]))/2


def inputs(c,t,antenna):
    directions=[[exact(x) for x in row] for row in c['directions']]
    return {'t':[[exact(x) for x in row] for row in t], 'directions':directions,
            'beta':[exact(x) for x in c['beta']], 'kap':[exact(x) for x in c['rician']],
            'noise':[exact(x) for x in c['noise']], 'power':exact(c['power']),
            'wave':2*mp.pi/exact(c['wavelength']), 'antenna':antenna}


def source_literal_geometry(common_job,c,t,antenna):
    p=inputs(c,t,antenna)
    geom=common_job['geometry']
    el,az=geom['elevation'],geom['azimuth']
    p['directions']=[[mp.cos(exact(e))*mp.sin(exact(a)),mp.sin(exact(e))] for e,a in zip(el,az)]
    # Literal 1e-4 and -2.8 are promoted from their actual source binary64
    # values. No undisclosed decimal-exponent/propagation-model correction.
    p['beta']=[exact(1e-4)*mp.power(exact(d),exact(-2.8)) for d in geom['distances_m']]
    return p


def los(p):
    return mp.matrix([[mp.exp(mp.j*p['wave']*dot(t,d)) for d in p['directions']] for t in p['t']])


def full_Gram_value_gradient(p,mode):
    """Differentiate the statistical objective through full H^H H.

    This is independent of the coefficient construction below; no finite
    difference/new position is generated.
    """
    n,m=len(p['t']),len(p['beta']);H=los(p);gram=H.H*H
    beta,kap,noise,power=p['beta'],p['kap'],p['noise'],p['power']
    if mode=='MRT':
        numerator=[beta[u]**2*(n*n+n*(2*kap[u]+1)/(kap[u]+1)**2) for u in range(m)]
        scale=[[mp.mpf(0) if u==v else beta[u]*beta[v]*kap[u]*kap[v]/((kap[u]+1)*(kap[v]+1)) for v in range(m)] for u in range(m)]
        den=[noise[u]*n*mp.fsum(beta)/power+mp.fsum(scale[u][v]*abs(gram[u,v])**2+
             beta[u]*beta[v]*n*(kap[u]+kap[v]+1)/((kap[u]+1)*(kap[v]+1)) for v in range(m) if u!=v) for u in range(m)]
        value=mp.fsum(mp.log1p(a/b) for a,b in zip(numerator,den))/mp.log(2)
    else:
        assert n>m
        S=mp.diag([mp.sqrt(k/(k+1)) for k in kap])
        Sigma=mp.diag([1/(k+1) for k in kap])+S*gram*S/n
        V=Sigma**-1
        eta=[power*beta[u]*(n-m)/(m*noise[u]) for u in range(m)]
        diagonals=[mp.re(V[u,u]) for u in range(m)]
        value=mp.fsum(mp.log1p(e/d) for e,d in zip(eta,diagonals))/mp.log(2)
    gradients=[];a=p['antenna']
    for axis in range(2):
        h=[H[a,u] for u in range(m)]
        dh=[mp.j*p['wave']*p['directions'][u][axis]*h[u] for u in range(m)]
        dgram=mp.matrix([[mp.conj(dh[u])*h[v]+mp.conj(h[u])*dh[v] for v in range(m)] for u in range(m)])
        if mode=='MRT':
            dden=[mp.fsum(2*scale[u][v]*mp.re(mp.conj(gram[u,v])*dgram[u,v]) for v in range(m)) for u in range(m)]
            g=-mp.fsum(numerator[u]*dden[u]/(mp.log(2)*den[u]*(den[u]+numerator[u])) for u in range(m))
        else:
            dV=-V*(S*dgram*S/n)*V
            g=-mp.fsum(eta[u]*mp.re(dV[u,u])/(mp.log(2)*diagonals[u]*(diagonals[u]+eta[u])) for u in range(m))
        gradients.append(g)
    return value,gradients


def mrt(p):
    n,m=len(p['t']),len(p['beta']);a=p['antenna']
    beta,kap,wave=p['beta'],p['kap'],p['wave']
    numerator=[beta[u]**2*(n*n+n*(2*kap[u]+1)/(kap[u]+1)**2) for u in range(m)]
    den=[p['noise'][u]*n*mp.fsum(beta)/p['power'] for u in range(m)]
    derivative=[[mp.mpf(0),mp.mpf(0)] for _ in range(m)];psi=[]
    for u in range(m):
        B=[[mp.mpf(0),mp.mpf(0)] for _ in range(2)]
        for v in range(m):
            if u==v:continue
            direction=[p['directions'][u][j]-p['directions'][v][j] for j in range(2)]
            phase=[mp.exp(mp.j*wave*dot(t,direction)) for t in p['t']]
            z=mp.fsum(phase)
            q=beta[u]*beta[v]*kap[u]*kap[v]/((kap[u]+1)*(kap[v]+1))
            den[u]+=q*abs(z)**2+beta[u]*beta[v]*n*(kap[u]+kap[v]+1)/((kap[u]+1)*(kap[v]+1))
            for j in range(2):derivative[u][j]+=2*q*mp.re(mp.conj(z)*mp.j*wave*phase[a])*direction[j]
            other_sum=mp.fsum(phase[k] for k in range(n) if k!=a)
            for j in range(2):
                for k in range(2):B[j][k]+=q*abs(other_sum)*abs(direction[j]*direction[k])
        psi.append(2*wave**2*largest2(B))
    weights=[numerator[u]/(mp.log(2)*den[u]*(den[u]+numerator[u])) for u in range(m)]
    g=[-mp.fsum(weights[u]*derivative[u][j] for u in range(m)) for j in range(2)]
    q=dot(weights,psi)
    value=mp.fsum(mp.log1p(numerator[u]/den[u]) for u in range(m))/mp.log(2)
    direct_value,direct_gradient=full_Gram_value_gradient(p,'MRT')
    return {'coefficients':{'g':g,'q':q},'value':value,'tangent':g,
            'direct_value':direct_value,'direct_gradient':direct_gradient,
            'intermediates':{'numerator':numerator,'denominator':den,'weight':weights,'psi':psi}}


def zf(p):
    n,m=len(p['t']),len(p['beta']);a=p['antenna'];H=los(p)
    kap=p['kap'];S=mp.diag([mp.sqrt(k/(k+1)) for k in kap])
    # Explicit other-row Gram avoids the source subtractive full Gram-minus-row
    # construction, while retaining exactly the same mathematical Theta2.
    others=mp.matrix([[H[k,u] for u in range(m)] for k in range(n) if k!=a])
    Theta2=mp.diag([1/(k+1) for k in kap])+S*(others.H*others)*S/n
    inverse=Theta2**-1;Y=mp.eye(m)*(mp.mpf(n)/m)+S*inverse*S
    g=mp.matrix([mp.conj(H[a,u]) for u in range(m)])
    a0=mp.re((g.H*Y*g)[0]);wave=p['wave']
    eta=[p['power']*p['beta'][u]*(n-m)/(m*p['noise'][u]) for u in range(m)]
    base=[];gradient=[];curvature=[];user=[]
    for u in range(m):
        row=inverse*S;ell=mp.matrix([mp.conj(row[u,v]) for v in range(m)])
        X=mp.re(inverse[u,u])*Y-ell*ell.H
        b0=mp.re((g.H*X*g)[0]);assert b0>0
        eigenvalues=mp.eighe(X,eigvals_only=True);largest=eigenvalues[m-1]
        q=(2/b0)*(g.H*(Y-a0/b0*(X-largest*mp.eye(m))))
        qu=[q[0,v] for v in range(m)]
        G=[-wave*mp.fsum(mp.im(mp.conj(qu[v])*H[a,v])*p['directions'][v][j] for v in range(m)) for j in range(2)]
        B=[[mp.fsum(abs(qu[v])*abs(p['directions'][v][j]*p['directions'][v][k]) for v in range(m)) for k in range(2)] for j in range(2)]
        xi=wave**2*largest2(B);ratio=a0/b0
        base.append(ratio+1/eta[u]);gradient.append(G);curvature.append(xi)
        user.append({'H':H,'Theta2':Theta2,'inverse':inverse,'Y':Y,'a':a0,'X':X,'b':b0,
                     'lmax':largest,'q':qu,'ratio':ratio,
                     'X_antiHermitian_Fnorm':mp.norm(X-X.H)})
    direct_value,direct_gradient=full_Gram_value_gradient(p,'ZF')
    tangent=[mp.fsum(gradient[u][j]/base[u] for u in range(m))/mp.log(2) for j in range(2)]
    return {'coefficients':{'a':base,'G':gradient,'q':curvature},'value':direct_value,'tangent':tangent,
            'direct_value':direct_value,'direct_gradient':direct_gradient,'user_intermediates':user}


def reference(p,mode):
    return mrt(p) if mode=='MRT' else zf(p)
