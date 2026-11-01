"""WORK v5: same concave-matrix bound with upward argument ceiling for SAME Eq39 grid.

Not production, not the undisclosed historical search objective, and never a
permutation reduction of fixed per-antenna Monte Carlo draws. Candidate values
and spacing retain the exact v3 frozen-binary64-input rational contract.
"""
from fractions import Fraction as F
from statistical_grid_exact import add,mul,conj,div,neg,ZERO
from statistical_grid_exact_v3 import ExactStatisticalGrid as V3

def full_inverse(matrix):
    m=len(matrix)
    a=[[matrix[i][j] for j in range(m)]+[(F(int(i==j)),F(0)) for j in range(m)] for i in range(m)]
    for k in range(m):
        # SPD has positive nonzero leading Schur pivots: no pivot approximation.
        p=a[k][k];assert p[1]==0 and p[0]>0
        a[k]=[div(z,p) for z in a[k]]
        for i in range(m):
            if i==k:continue
            q=a[i][k];a[i]=[add(z,neg(mul(q,v))) for z,v in zip(a[i],a[k])]
    return [row[m:] for row in a]

def ceil_dyadic(value,bits=128):
    scale=1<<bits;return F((value.numerator*scale+value.denominator-1)//value.denominator,scale)

def exp_upper(value):
    """Rigorous rational exp ceiling, Taylor/geometric remainder + squaring.

    For t<=1/2 the tail after degree40 is bounded by
    next_term/(1-t/42). Every dyadic rounding is upward, and every subsequent
    square is monotone on nonnegative values. No float/MP number is a gate.
    """
    assert value>=0
    if value==0:return F(1)
    scale_count=0;t=value
    while t>F(1,2):t/=2;scale_count+=1
    t=ceil_dyadic(t)  # Monotone exp: rigorous upward argument rounding.
    assert t<=F(1,2)
    term=F(1);partial=term
    for k in range(1,41):term*=t/k;partial+=term
    next_term=term*t/41;upper=ceil_dyadic(partial+next_term/(1-t/42))
    for _ in range(scale_count):upper=ceil_dyadic(upper*upper)
    return upper

class ExactStatisticalGrid(V3):
    def __init__(self,c,n,D,mode):
        super().__init__(c,n,D,mode);self.support_calls=0;self.support_improved=0

    def supporting_upper(self,indices,remaining):
        r=self.n-len(indices);m=self.m;length=len(remaining)
        assert r>0 and length>=r
        partial=self.partial(indices)
        diag=[self.base[u]+sum(self.diagonal[i][u] for i in indices)+F(r,length)*sum(self.diagonal[i][u] for i in remaining) for u in range(m)]
        off={pair:(s[0]+F(r,length)*sum(self.terms[pair][i][0] for i in remaining),s[1]+F(r,length)*sum(self.terms[pair][i][1] for i in remaining)) for pair,s in partial.items()}
        sigma=[[(diag[u],F(0)) if u==v else off[u,v] if u<v else conj(off[v,u]) for v in range(m)] for u in range(m)]
        inverse=full_inverse(sigma);schur=[1/inverse[u][u][0] for u in range(m)]
        product=F(1)
        for u in range(m):product*=1+self.eta[u]*schur[u]
        weights=[self.eta[u]*schur[u]**2/(1+self.eta[u]*schur[u]) for u in range(m)]
        grad=[]
        for u in range(m):
            row=[]
            for v in range(m):
                z=ZERO
                for j in range(m):
                    q=mul(inverse[u][j],inverse[j][v]);z=add(z,(weights[j]*q[0],weights[j]*q[1]))
                row.append(z)
            grad.append(row)
        scores=[]
        for i in remaining:
            value=sum(grad[u][u][0]*self.diagonal[i][u] for u in range(m))
            for u in range(m):
                for v in range(u+1,m):value+=2*mul(grad[u][v],conj(self.terms[u,v][i]))[0]
            scores.append(value)
        linear_increment=sum(sorted(scores,reverse=True)[:r])-F(r,length)*sum(scores)
        assert linear_increment>=0
        self.support_calls+=1
        return product*exp_upper(linear_increment)

    def upper(self,indices,remaining):
        previous=super().upper(indices,remaining)
        # Single-row subtrees are cheap integer determinant leaves already;
        # this guard is an optional bound computation, never an exclusion.
        if self.mode!='ZF' or self.n-len(indices)<2:return previous
        candidate=self.supporting_upper(indices,remaining)
        if candidate<previous:self.support_improved+=1
        return min(previous,candidate)
