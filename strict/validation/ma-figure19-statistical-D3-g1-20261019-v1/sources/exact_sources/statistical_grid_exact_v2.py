"""WORK v2: tighter certified ZF Schur bound; original v1 proof kept immutable."""
from fractions import Fraction as F
from math import isqrt
from statistical_grid_exact import ExactStatisticalGrid as V1,norm2


def sqrt_upper(q):
    """Exact rational ceiling at2^-64; no floating-point sqrt in certificate."""
    if q<0:raise ValueError('Nonnegative squared norm required')
    scale=1<<64
    scaled=(q.numerator*scale*scale+q.denominator-1)//q.denominator
    root=isqrt(scaled)
    if root*root<scaled:root+=1
    value=F(root,scale)
    assert value*value>=q
    return value


class ExactStatisticalGrid(V1):
    def upper_norm(self,pair,s,remaining,r):
        """Exact coordinate rectangle and triangle relaxations of same completions."""
        bounds=[]
        for d in range(2):
            values=sorted(self.terms[pair][i][d] for i in remaining)
            lo=s[d]+sum(values[:r]);hi=s[d]+sum(values[-r:]) if r else s[d]
            bounds.append(max(lo*lo,hi*hi))
        rectangle=sqrt_upper(sum(bounds))
        triangle=sqrt_upper(norm2(s))+sum(sorted((sqrt_upper(norm2(self.terms[pair][i])) for i in remaining),reverse=True)[:r])
        return min(rectangle,triangle)

    def upper(self,indices,remaining):
        if self.mode=='MRT':return super().upper(indices,remaining)
        r=self.n-len(indices);sums=self.partial(indices);product=F(1)
        lower={pair:self.lower_norm_squared(pair,s,remaining,r) for pair,s in sums.items()}
        upper={pair:self.upper_norm(pair,s,remaining,r) for pair,s in sums.items()}
        diag=[self.base[u]+sum(self.diagonal[i][u] for i in indices)+
              sum(sorted((self.diagonal[i][u] for i in remaining),reverse=True)[:r]) for u in range(self.m)]
        for u in range(self.m):
            other=[v for v in range(self.m) if v!=u]
            trace=sum(diag[v] for v in other)
            gersh=max(diag[v]+sum(upper[min(v,w),max(v,w)] for w in other if w!=v) for v in other)
            eigen_upper=min(trace,gersh)
            schur_upper=diag[u]-sum(lower[min(u,v),max(u,v)] for v in other)/eigen_upper
            # Negative bound can only occur in a completion-free subtree. No
            # feasible PSD completion has a negative Schur complement.
            schur_upper=max(F(0),schur_upper)
            product*=1+self.eta[u]*schur_upper
        return product
