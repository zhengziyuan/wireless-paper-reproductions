"""Independent N>M exact frozen-operand values, safe uppers and clique counts.

No original model, inverse, supporting-weight chooser, search or RNG is loaded.
The caller supplies the separately frozen binary64 primitive vectors. ZF uses
determinants/cofactors. Its Schur upper uses lambda_max(C)<=min(trace(C),Gersh).
The supporting tangent is evaluated at any explicitly supplied valid dyadic
hypersimplex point, never by rerunning an original chooser.
"""
from fractions import Fraction as F
from functools import lru_cache
import itertools
import math

def need(v,s):
    if not v:raise ValueError(s)

def constants(p,n,m,mode,k):
    beta=list(map(k.q,p['beta']));kap=list(map(k.q,p['rician']));noise=list(map(k.q,p['noise']));power=k.q(p['power'])
    need(n>m>=2 and len(beta)==len(kap)==len(noise)==m and all(x>0 for x in beta+noise) and all(x>=0 for x in kap) and power>0,'Physical rational constants')
    if mode=='MRT':
        return dict(desired=[beta[u]**2*(n*n+n*(2*kap[u]+1)/(kap[u]+1)**2) for u in range(m)],
            offset=[noise[u]*n*sum(beta)/power+sum(beta[u]*beta[v]*n*(kap[u]+kap[v]+1)/((kap[u]+1)*(kap[v]+1)) for v in range(m) if v!=u) for u in range(m)],
            coefficient={(u,v):beta[u]*beta[v]*kap[u]*kap[v]/((kap[u]+1)*(kap[v]+1)) for u in range(m) for v in range(m) if u!=v})
    need(mode=='ZF','MRT/ZF only')
    return dict(offset=[1/(x+1) for x in kap],eta=[power*beta[u]*(n-m)/(m*noise[u]) for u in range(m)])

def operands(p,mode,np,k):
    n=int(p['N']);D=int(p['D']);m=len(p['beta']);P=D*D
    need(n>m>=2 and p['mode']==mode,'Dimensions/mode')
    grid=np.asarray(p['grid']);need(grid.shape==(P,2) and grid.dtype==np.dtype('float64') and np.isfinite(grid).all(),'Grid schema')
    c=constants(p,n,m,mode,k);terms={};diagonal=None
    if mode=='MRT':
        h=np.asarray(p['pair_phasors']);need(h.shape==(P,math.comb(m,2)) and h.dtype==np.dtype('complex128') and np.isfinite(h).all(),'Pair phasors')
        for j,(u,v) in enumerate(itertools.combinations(range(m),2)):
            z=[(k.q(x.real),k.q(x.imag)) for x in h[:,j]];terms[u,v]=z;terms[v,u]=[k.zconj(x) for x in z]
    else:
        h=np.asarray(p['LOS_phasors']);s=np.asarray(p['binary64_sqrt_scale']).reshape(-1)
        need(h.shape==(P,m) and h.dtype==np.dtype('complex128') and s.shape==(m,) and s.dtype==np.dtype('float64') and np.isfinite(h).all() and np.isfinite(s).all(),'ZF phasors/scales')
        weighted=[[(k.q(z.real)*k.q(s[u]),k.q(z.imag)*k.q(s[u])) for u,z in enumerate(row)] for row in h]
        diagonal=[[k.znorm(row[u])/n for u in range(m)] for row in weighted]
        for u,v in itertools.combinations(range(m),2):
            z=[k.zmul(k.zconj(row[u]),row[v]) for row in weighted];terms[u,v]=[(x[0]/n,x[1]/n) for x in z]
    return dict(c,grid=grid,spacing=k.q(p['minimum_distance']),terms=terms,diagonal=diagonal,n=n,m=m)

DIRECTIONS=((1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1))
def lower_projection(z,prefix,remaining,r):
    s=(sum(z[i][0] for i in prefix),sum(z[i][1] for i in prefix))
    return max(max(F(0),a*s[0]+b*s[1]+sum(sorted(a*z[i][0]+b*z[i][1] for i in remaining)[:r]))**2/(a*a+b*b) for a,b in DIRECTIONS)

def base_upper(o,prefix,remaining,mode,k,b):
    n=o['n'];m=o['m'];r=n-len(prefix);need(0<r<=len(remaining),'Incomplete eligible prefix')
    low={pair:lower_projection(z,prefix,remaining,r) for pair,z in o['terms'].items()};result=F(1)
    if mode=='MRT':
        for u in range(m):
            den=o['offset'][u]+sum(o['coefficient'][u,v]*low[u,v] for v in range(m) if v!=u)
            need(den>0,'Positive exact MRT bound denominator');result*=1+o['desired'][u]/den
        return result
    diag=[o['offset'][u]+sum(o['diagonal'][i][u] for i in prefix)+sum(sorted((o['diagonal'][i][u] for i in remaining),reverse=True)[:r]) for u in range(m)]
    norms={pair:b.independent_norm_upper(z,prefix,remaining,r,k) for pair,z in o['terms'].items()}
    for u in range(m):
        others=[v for v in range(m) if v!=u]
        trace=sum(diag[v] for v in others)
        gersh=max(diag[v]+sum(norms[min(v,w),max(v,w)] for w in others if w!=v) for v in others)
        eigen_upper=min(trace,gersh);need(eigen_upper>0,'Positive principal Gram eigen upper (no tolerance clamp)')
        off_lower=sum(low[min(u,v),max(u,v)] for v in others)
        schur=max(F(0),diag[u]-off_lower/eigen_upper)
        result*=1+o['eta'][u]*schur
    return result

def matrix_at(o,prefix,remaining,weights,k):
    m=o['m'];a=[[k.Z0 for _ in range(m)] for _ in range(m)]
    for u in range(m):a[u][u]=(o['offset'][u]+sum(o['diagonal'][i][u] for i in prefix)+sum(w*o['diagonal'][i][u] for w,i in zip(weights,remaining)),F(0))
    for u,v in itertools.combinations(range(m),2):
        z=[o['terms'][u,v][i] for i in prefix]
        z.extend((w*o['terms'][u,v][i][0],w*o['terms'][u,v][i][1]) for w,i in zip(weights,remaining))
        a[u][v]=k.zsum(z);a[v][u]=k.zconj(a[u][v])
    return a

def supporting_tangent_upper(o,prefix,remaining,counts,k,b):
    n=o['n'];m=o['m'];r=n-len(prefix);Q=1<<32
    need(len(counts)==len(remaining) and all(type(x) is int and 0<=x<=Q for x in counts) and sum(counts)==r*Q,'Valid explicit dyadic hypersimplex point')
    weights=[F(x,Q) for x in counts];a=matrix_at(o,prefix,remaining,weights,k)
    for j in range(1,m):k.real_positive_det([row[:j] for row in a[:j]])
    det=k.real_positive_det(a)
    inverse=[]
    for i in range(m):
        row=[]
        for j in range(m):
            z=k.determinant([[a[v][w] for w in range(m) if w!=i] for v in range(m) if v!=j]);sign=(-1)**(i+j)
            row.append((sign*z[0]/det,sign*z[1]/det))
        inverse.append(row)
    schur=[];point_product=F(1)
    for u in range(m):
        need(inverse[u][u][1]==0 and inverse[u][u][0]>0,'Positive exact inverse diagonal')
        schur.append(1/inverse[u][u][0]);point_product*=1+o['eta'][u]*schur[-1]
    alpha=[o['eta'][u]*schur[u]**2/(1+o['eta'][u]*schur[u]) for u in range(m)]
    gradient=[]
    for u in range(m):
        row=[]
        for v in range(m):
            z=[k.zmul(inverse[u][j],inverse[j][v]) for j in range(m)]
            row.append((sum(alpha[j]*z[j][0] for j in range(m)),sum(alpha[j]*z[j][1] for j in range(m))))
        gradient.append(row)
    scores=[]
    for i in remaining:
        score=sum(gradient[u][u][0]*o['diagonal'][i][u] for u in range(m))
        for u,v in itertools.combinations(range(m),2):score+=2*k.zmul(gradient[u][v],k.zconj(o['terms'][u,v][i]))[0]
        scores.append(score)
    increment=sum(sorted(scores,reverse=True)[:r])-sum(w*s for w,s in zip(weights,scores))
    need(increment>=0,'Exact linear relaxation increment nonnegative')
    return point_product*b.independent_exp_ceiling(increment)

class CliqueCounter:
    """Ascending compatible-set DP. r=0, impossible and complete graph exact.

    LRU capacity bounds storage, never the number of mathematical operations.
    No objective is evaluated inside a counted safe subtree.
    """
    def __init__(self,compatible):
        self.P=len(compatible);self.adj=[]
        for i,row in enumerate(compatible):
            need(len(row)==self.P and not row[i],'No repeated grid vertices')
            self.adj.append(sum(1<<j for j,v in enumerate(row) if v))
        need(all(compatible[i][j]==compatible[j][i] for i in range(self.P) for j in range(self.P)),'Symmetric exact compatibility')
        self.all=(1<<self.P)-1
        self.count=lru_cache(maxsize=4096)(self._count)
        self.edges=lru_cache(maxsize=4096)(self._edges)
    def _edges(self,mask):
        count=0
        while mask:
            bit=mask&-mask;mask^=bit;count+=(mask&self.adj[bit.bit_length()-1]).bit_count()
        return count
    def _count(self,mask,r):
        size=mask.bit_count()
        if size<r:return 0
        if r==0:return 1
        if r==1:return size
        edge=self.edges(mask)
        if r==2:return edge
        if edge==math.comb(size,2):return math.comb(size,r)
        total=0
        while mask:
            bit=mask&-mask;mask^=bit;v=bit.bit_length()-1;total+=self.count(mask&self.adj[v],r-1)
        return total
    @staticmethod
    def indices(mask):
        out=[]
        while mask:
            bit=mask&-mask;mask^=bit;out.append(bit.bit_length()-1)
        return tuple(out)

def compatible_matrix(o,k):
    grid=[[k.q(x) for x in row] for row in o['grid']];P=len(grid)
    return [[i!=j and sum((grid[i][a]-grid[j][a])**2 for a in range(2))>=o['spacing']**2 for j in range(P)] for i in range(P)]

def equal_dyadic_counts(r,length):
    need(0<=r<=length,'Hypersimplex mass')
    value,remainder=divmod(r*(1<<32),length)
    return [value+(i<remainder) for i in range(length)]
