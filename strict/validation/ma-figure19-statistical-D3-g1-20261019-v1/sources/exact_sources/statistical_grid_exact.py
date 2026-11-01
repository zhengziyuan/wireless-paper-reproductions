"""WORK-only exact rational discrete Eq13/39 branch-and-bound prototype.

Not the undisclosed historical brute-force protocol; never used by live banks.
Floating-point trig inputs are frozen once, then all search/certificate arithmetic
is exact Fraction arithmetic. Comparing products(1+SINR) exactly is equivalent
to comparing sums of log2(1+SINR), without a numerical log tolerance.
"""
from fractions import Fraction as F
from itertools import combinations
from math import log2
import numpy as np


def frac(x):return F(float(x))
def add(a,b):return a[0]+b[0],a[1]+b[1]
def neg(a):return -a[0],-a[1]
def mul(a,b):return a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]
def conj(a):return a[0],-a[1]
def div(a,b):
    d=b[0]*b[0]+b[1]*b[1]
    return ((a[0]*b[0]+a[1]*b[1])/d,(a[1]*b[0]-a[0]*b[1])/d)
def norm2(a):return a[0]*a[0]+a[1]*a[1]
ZERO=(F(0),F(0))


def inverse_diagonal(matrix):
    """Exact complex Gauss–Jordan; scalar rational oracle, not LAPACK."""
    m=len(matrix)
    a=[[matrix[i][j] for j in range(m)]+[(F(int(i==j)),F(0)) for j in range(m)] for i in range(m)]
    for k in range(m):
        pivot=next(i for i in range(k,m) if norm2(a[i][k])>0)
        a[k],a[pivot]=a[pivot],a[k]
        p=a[k][k];a[k]=[div(v,p) for v in a[k]]
        for i in range(m):
            if i!=k:
                q=a[i][k];a[i]=[add(v,neg(mul(q,w))) for v,w in zip(a[i],a[k])]
    result=[a[i][m+i] for i in range(m)]
    assert all(v[1]==0 and v[0]>0 for v in result)
    return [v[0] for v in result]


class ExactStatisticalGrid:
    def __init__(self,c,n,D,mode):
        if mode not in ['MRT','ZF']:raise ValueError(mode)
        self.c=c;self.n=n;self.m=len(c['beta']);self.D=D;self.mode=mode
        if n<=self.m:raise ValueError('Original ZF design requires N>M')
        self.grid=np.array([[x,y] for x in np.linspace(c['region_lower'][0],c['region_upper'][0],D)
                            for y in np.linspace(c['region_lower'][1],c['region_upper'][1],D)])
        self.points=[tuple(map(frac,p)) for p in self.grid];self.count=len(self.grid)
        spacing=frac(c['minimum_distance'])**2
        self.compatible=[[sum((self.points[i][d]-self.points[j][d])**2 for d in range(2))>=spacing
                          for j in range(self.count)] for i in range(self.count)]
        beta=list(map(frac,c['beta']));kap=list(map(frac,c['rician']));noise=list(map(frac,c['noise']));power=frac(c['power'])
        self.directions=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
        self.terms={};self.diagonal=None
        if mode=='MRT':
            self.numerator=[beta[u]**2*(n*n+F(n)*(2*kap[u]+1)/(kap[u]+1)**2) for u in range(self.m)]
            self.base=[noise[u]*n*sum(beta)/power for u in range(self.m)]
            self.coefficient={}
            wave=2*np.pi/c['wavelength'];directions=np.asarray(c['directions'])
            for u in range(self.m):
                for v in range(self.m):
                    if u==v:continue
                    phase=np.exp(1j*wave*(self.grid@(directions[u]-directions[v])))
                    self.terms[u,v]=[(frac(z.real),frac(z.imag)) for z in phase]
                    self.coefficient[u,v]=beta[u]*beta[v]*kap[u]*kap[v]/((kap[u]+1)*(kap[v]+1))
                    self.base[u]+=beta[u]*beta[v]*n*(kap[u]+kap[v]+1)/((kap[u]+1)*(kap[v]+1))
        else:
            h=np.exp(2j*np.pi/c['wavelength']*(self.grid@np.asarray(c['directions']).T))
            scale=[frac(x) for x in np.sqrt(np.asarray(c['rician'])/(np.asarray(c['rician'])+1))]
            weighted=[[(frac(z.real)*scale[u],frac(z.imag)*scale[u]) for u,z in enumerate(row)] for row in h]
            self.base=[F(1)/(k+1) for k in kap]
            self.diagonal=[[norm2(row[u])/n for u in range(self.m)] for row in weighted]
            self.eta=[power*beta[u]*(n-self.m)/(self.m*noise[u]) for u in range(self.m)]
            for u in range(self.m):
                for v in range(u+1,self.m):
                    self.terms[u,v]=[(z[0]/n,z[1]/n) for z in [mul(conj(row[u]),row[v]) for row in weighted]]
        self.projections={pair:[[x*z[0]+y*z[1] for z in terms] for x,y in self.directions]
                          for pair,terms in self.terms.items()}
        self.best=None;self.winner=None;self.nodes=0;self.leaves=0;self.certificates=[];self.infeasible=0

    def partial(self,indices):
        return {pair:tuple(sum(self.terms[pair][i][d] for i in indices) for d in range(2)) for pair in self.terms}

    def lower_norm_squared(self,pair,s,remaining,r):
        """Every completion's projection >=partial +r smallest eligible terms.

        Repeats and spacing among future points are relaxed, never added. For
        integer direction q, |z|^2 >=max(0,q.z)^2/|q|^2 exactly (Cauchy–Schwarz).
        """
        lower=F(0)
        for k,(x,y) in enumerate(self.directions):
            minimum=x*s[0]+y*s[1]+sum(sorted(self.projections[pair][k][i] for i in remaining)[:r])
            if minimum>0:lower=max(lower,minimum*minimum/F(x*x+y*y))
        return lower

    def value(self,indices):
        sums=self.partial(indices);product=F(1)
        if self.mode=='MRT':
            for u in range(self.m):
                den=self.base[u]+sum(self.coefficient[u,v]*norm2(sums[u,v]) for v in range(self.m) if v!=u)
                product*=1+self.numerator[u]/den
        else:
            diag=[self.base[u]+sum(self.diagonal[i][u] for i in indices) for u in range(self.m)]
            sigma=[[(diag[u],F(0)) if u==v else sums[u,v] if u<v else conj(sums[v,u]) for v in range(self.m)] for u in range(self.m)]
            inverse=inverse_diagonal(sigma)
            for u in range(self.m):product*=1+self.eta[u]/inverse[u]
        return product

    def upper(self,indices,remaining):
        r=self.n-len(indices);sums=self.partial(indices);product=F(1)
        lower={pair:self.lower_norm_squared(pair,s,remaining,r) for pair,s in sums.items()}
        if self.mode=='MRT':
            for u in range(self.m):
                den=self.base[u]+sum(self.coefficient[u,v]*lower[u,v] for v in range(self.m) if v!=u)
                product*=1+self.numerator[u]/den
        else:
            # Every future diagonal sum <=r largest eligible diagonal terms.
            diag=[self.base[u]+sum(self.diagonal[i][u] for i in indices)+
                  sum(sorted((self.diagonal[i][u] for i in remaining),reverse=True)[:r]) for u in range(self.m)]
            for u in range(self.m):
                trace_other=sum(diag[v] for v in range(self.m) if v!=u)
                # C positive definite: C^-1 >= I/tr(C) >= I/trace_upper.
                schur_upper=diag[u]-sum(lower[min(u,v),max(u,v)] for v in range(self.m) if v!=u)/trace_other
                assert schur_upper>=0
                product*=1+self.eta[u]*schur_upper
        return product

    def completions(self,indices,remaining):
        for tail in combinations(remaining,self.n-len(indices)):
            whole=tuple(indices)+tail
            if all(self.compatible[i][j] for i,j in combinations(whole,2)):yield whole

    def exhaustive(self):
        best=None;winner=None;count=0
        for whole in self.completions((),range(self.count)):
            value=self.value(whole);count+=1
            if best is None or value>best:best,winner=value,whole
        return best,winner,count

    def search(self,verify_every_pruned_subtree=False):
        def visit(indices,remaining):
            self.nodes+=1;r=self.n-len(indices)
            if len(remaining)<r:self.infeasible+=1;return
            if r==0:
                value=self.value(indices);self.leaves+=1
                if self.best is None or value>self.best:self.best,self.winner=value,indices
                return
            upper=self.upper(indices,remaining)
            if self.best is not None and upper<=self.best:
                maximum=None;count=0
                if verify_every_pruned_subtree:
                    for whole in self.completions(indices,remaining):
                        value=self.value(whole);count+=1
                        maximum=value if maximum is None else max(maximum,value)
                    assert maximum is None or upper>=maximum
                self.certificates.append({'prefix':list(indices),'eligible':list(remaining),
                    'exact_upper_numerator':str(upper.numerator),'exact_upper_denominator':str(upper.denominator),
                    'incumbent_numerator':str(self.best.numerator),'incumbent_denominator':str(self.best.denominator),
                    'independent_all_completions_checked':verify_every_pruned_subtree,'completions_checked':count})
                return
            for k,point in enumerate(remaining):
                future=tuple(i for i in remaining[k+1:] if self.compatible[point][i])
                visit(indices+(point,),future)
        visit((),tuple(range(self.count)))
        if self.winner is None:raise ValueError('No complete feasible grid geometry')
        return self.best,self.winner

    def display_rate(self,value):
        # Display only; never used for optimization/certificate comparisons.
        return log2(value.numerator)-log2(value.denominator)
