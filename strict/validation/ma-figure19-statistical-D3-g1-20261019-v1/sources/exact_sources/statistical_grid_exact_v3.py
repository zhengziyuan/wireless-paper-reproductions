"""WORK exact fraction-free determinant evaluator, SAME finite Eq39 contract.

This does not change bounds/search/symmetry, or the frozen production core.
Schur reciprocal-inverse diagonals equal det(Sigma)/det(Sigma without user).
All determinants are exact Gaussian-integer Bareiss eliminations after one
common integer scaling. Every division is verified exact, never rounded.
"""
from fractions import Fraction as F
from math import lcm
from statistical_grid_exact_v2 import ExactStatisticalGrid as V2

def imul(a,b):return a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]
def isub(a,b):return a[0]-b[0],a[1]-b[1]
def idiv_exact(a,b):
    den=b[0]*b[0]+b[1]*b[1]
    nr=a[0]*b[0]+a[1]*b[1];ni=a[1]*b[0]-a[0]*b[1]
    assert den>0 and nr%den==0 and ni%den==0
    return nr//den,ni//den

def determinant_spd_integer(matrix):
    """No pivot exchange: every leading principal pivot of SPD is positive."""
    if len(matrix)==0:return 1
    a=[row[:] for row in matrix];previous=(1,0)
    for k in range(len(a)-1):
        pivot=a[k][k]
        assert pivot[1]==0 and pivot[0]>0
        for i in range(k+1,len(a)):
            for j in range(k+1,len(a)):
                a[i][j]=idiv_exact(isub(imul(a[i][j],pivot),imul(a[i][k],a[k][j])),previous)
        previous=pivot
    result=a[-1][-1]
    assert result[1]==0 and result[0]>0
    return result[0]

class ExactStatisticalGrid(V2):
    def __init__(self,c,n,D,mode):
        super().__init__(c,n,D,mode)
        if mode!='ZF':return
        den=1
        for value in self.base:den=lcm(den,value.denominator)
        for row in self.diagonal:
            for value in row:den=lcm(den,value.denominator)
        for terms in self.terms.values():
            for pair in terms:
                for value in pair:den=lcm(den,value.denominator)
        self.integer_scale=den
        def integer(value):
            assert den%value.denominator==0
            return value.numerator*(den//value.denominator)
        self.integer_base=[integer(x) for x in self.base]
        self.integer_diagonal=[[integer(x) for x in row] for row in self.diagonal]
        self.integer_terms={pair:[(integer(z[0]),integer(z[1])) for z in terms]
                            for pair,terms in self.terms.items()}

    def value(self,indices):
        if self.mode!='ZF':return super().value(indices)
        sums={pair:(sum(terms[i][0] for i in indices),sum(terms[i][1] for i in indices))
              for pair,terms in self.integer_terms.items()}
        diag=[self.integer_base[u]+sum(self.integer_diagonal[i][u] for i in indices)
              for u in range(self.m)]
        a=[[(diag[u],0) if u==v else sums[u,v] if u<v else
             (sums[v,u][0],-sums[v,u][1]) for v in range(self.m)] for u in range(self.m)]
        det=determinant_spd_integer(a);product=F(1)
        for u in range(self.m):
            minor=[[a[v][w] for w in range(self.m) if w!=u] for v in range(self.m) if v!=u]
            minor_det=determinant_spd_integer(minor)
            schur=F(det,self.integer_scale*minor_det)
            product*=1+self.eta[u]*schur
        return product
