"""WORK same Eq39 candidate search: tighter exact supporting bound.

A floating FW relaxation ONLY chooses an SPD tangent matrix; it never prunes
or compares candidates. The final weights are quantized to an exactly feasible
dyadic hypersimplex, then ALL bound/certificate arithmetic is exact rational.
Any SPD tangent matrix gives the proved global upper plane, so solver-quality,
roundoff and premature chooser termination cannot invalidate the certificate.
"""
from fractions import Fraction as F
import numpy as np
from statistical_grid_exact import add,mul,conj,ZERO
from statistical_grid_exact_v5 import ExactStatisticalGrid as V5,full_inverse,exp_upper

class ExactStatisticalGrid(V5):
    def __init__(self,c,n,D,mode):
        super().__init__(c,n,D,mode)
        if mode=='ZF':
            self.numeric_terms=np.zeros((self.count,self.m,self.m),complex)
            for i in range(self.count):
                for u in range(self.m):
                    self.numeric_terms[i,u,u]=float(self.diagonal[i][u])
                    for v in range(u+1,self.m):
                        z=self.terms[u,v][i];self.numeric_terms[i,u,v]=complex(float(z[0]),float(z[1]));self.numeric_terms[i,v,u]=self.numeric_terms[i,u,v].conjugate()
            self.numeric_base=np.diag([float(x) for x in self.base]);self.numeric_eta=np.array([float(x) for x in self.eta])

    def choose_weights(self,indices,remaining,r):
        length=len(remaining);terms=self.numeric_terms[list(remaining)]
        fixed=self.numeric_base+self.numeric_terms[list(indices)].sum(axis=0) if indices else self.numeric_base.copy()
        w=np.full(length,r/length)
        def gradient(sigma):
            inv=np.linalg.inv((sigma+sigma.conj().T)/2);s=1/np.diag(inv).real
            weight=self.numeric_eta*s*s/(1+self.numeric_eta*s)
            return (inv*weight[None,:])@inv
        # This is a point chooser, not a numerical accuracy/convergence gate.
        for _ in range(12):
            sigma=fixed+np.einsum('i,ijk->jk',w,terms);g=gradient(sigma)
            score=np.einsum('jk,ikj->i',g,terms).real
            target=np.zeros(length);target[np.argsort(score)[-r:]]=1
            dw=target-w;delta=np.einsum('i,ijk->jk',dw,terms)
            if float(score@dw)<=0:break
            derivative=lambda a:float(np.trace(gradient(sigma+a*delta)@delta).real)
            if derivative(1)>=0:a=1.
            else:
                lo,hi=0.,1.
                for _ in range(32):
                    mid=(lo+hi)/2
                    if derivative(mid)>=0:lo=mid
                    else:hi=mid
                a=(lo+hi)/2
            w=(1-a)*w+a*target
        Q=1<<32;scaled=np.clip(w,0,1)*Q;counts=[int(np.floor(z)) for z in scaled]
        missing=r*Q-sum(counts)
        if missing>=0:
            order=np.argsort(scaled-np.array(counts))[::-1]
            while missing:
                for i in order:
                    if counts[i]<Q:counts[i]+=1;missing-=1
                    if not missing:break
        else:
            order=np.argsort(counts)[::-1]
            while missing:
                for i in order:
                    if counts[i]>0:counts[i]-=1;missing+=1
                    if not missing:break
        assert sum(counts)==r*Q and all(0<=x<=Q for x in counts)
        return [F(x,Q) for x in counts]

    def supporting_upper(self,indices,remaining):
        r=self.n-len(indices);m=self.m;weights=self.choose_weights(indices,remaining,r);partial=self.partial(indices)
        diag=[self.base[u]+sum(self.diagonal[i][u] for i in indices)+sum(w*self.diagonal[i][u] for w,i in zip(weights,remaining)) for u in range(m)]
        off={pair:(s[0]+sum(w*self.terms[pair][i][0] for w,i in zip(weights,remaining)),s[1]+sum(w*self.terms[pair][i][1] for w,i in zip(weights,remaining))) for pair,s in partial.items()}
        sigma=[[(diag[u],F(0)) if u==v else off[u,v] if u<v else conj(off[v,u]) for v in range(m)] for u in range(m)]
        inverse=full_inverse(sigma);schur=[1/inverse[u][u][0] for u in range(m)];product=F(1)
        for u in range(m):product*=1+self.eta[u]*schur[u]
        coefficient=[self.eta[u]*schur[u]**2/(1+self.eta[u]*schur[u]) for u in range(m)]
        grad=[]
        for u in range(m):
            row=[]
            for v in range(m):
                z=ZERO
                for j in range(m):
                    q=mul(inverse[u][j],inverse[j][v]);z=add(z,(coefficient[j]*q[0],coefficient[j]*q[1]))
                row.append(z)
            grad.append(row)
        scores=[]
        for i in remaining:
            value=sum(grad[u][u][0]*self.diagonal[i][u] for u in range(m))
            for u in range(m):
                for v in range(u+1,m):value+=2*mul(grad[u][v],conj(self.terms[u,v][i]))[0]
            scores.append(value)
        L=sum(sorted(scores,reverse=True)[:r])-sum(w*s for w,s in zip(weights,scores))
        assert L>=0  # Exact hypersimplex weights, not a floating optimiser flag.
        self.support_calls+=1
        return product*exp_upper(L)
