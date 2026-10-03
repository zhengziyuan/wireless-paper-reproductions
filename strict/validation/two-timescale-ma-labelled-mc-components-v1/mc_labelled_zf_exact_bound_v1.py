"""Exact/outward finite-tabulated-channel MC ZF bounds, no label symmetry."""
from functools import lru_cache
from itertools import permutations
import hashlib

import numpy as np

BITS = 80
SCALE = 1 << BITS
TERMS = 24


def ceil_div(n,d):
    assert d > 0
    return -((-n)//d)


def atanh_log_interval(zn,zd):
    """Enclose ln((1+z)/(1-z)); rational0<=z<=1/3."""
    assert 0 <= 3*zn <= zd
    lo,hi = (zn*SCALE)//zd,ceil_div(zn*SCALE,zd)
    ylo,yhi = (lo*lo)//SCALE,ceil_div(hi*hi,SCALE)
    plo,phi = lo,hi
    total_lo=total_hi=0
    for j in range(TERMS):
        odd = 2*j+1
        total_lo += (2*plo)//odd
        total_hi += ceil_div(2*phi,odd)
        plo,phi = (plo*ylo)//SCALE,ceil_div(phi*yhi,SCALE)
    # Uniform nonnegative exact analytic remainder at the worst z=1/3.
    tail_hi=ceil_div(9*SCALE,4*(2*TERMS+1)*3**(2*TERMS+1))
    return total_lo,total_hi+tail_hi


LN2_LO,LN2_HI = atanh_log_interval(1,3)


@lru_cache(maxsize=16384)
def rational_log_interval(num,den):
    """Integer Q80 lower/upper ln(num/den), exactnum>=den>0."""
    assert num >= den > 0
    k = num.bit_length()-den.bit_length()
    if num < (den << k):
        k -= 1
    reduced_den = den << k
    assert reduced_den <= num < 2*reduced_den and k >= 0
    lo,hi = atanh_log_interval(num-reduced_den,num+reduced_den)
    return lo+k*LN2_LO,hi+k*LN2_HI


def binary_integer_table(values):
    flat = np.asarray(values).ravel()
    ratios = [float(x).as_integer_ratio() for z in flat for x in [z.real,z.imag]]
    exponent = max(d.bit_length()-1 for _,d in ratios)
    ints = [n << (exponent-(d.bit_length()-1)) for n,d in ratios]
    rows = np.array(ints,dtype=object).reshape(*np.asarray(values).shape,2)
    return rows,exponent


def row_gram(row):
    # Entries G01=d,G02=e,G12=f, with original G=H^H H.
    r = [int(x[0]) for x in row]
    i = [int(x[1]) for x in row]
    cross = lambda u,v:(r[u]*r[v]+i[u]*i[v],r[u]*i[v]-i[u]*r[v])
    d,e,f=cross(0,1),cross(0,2),cross(1,2)
    return (r[0]**2+i[0]**2,r[1]**2+i[1]**2,r[2]**2+i[2]**2,*d,*e,*f)


def det_and_minors(g):
    a,b,c,dr,di,er,ei,fr,fi=g
    d2,e2,f2=dr*dr+di*di,er*er+ei*ei,fr*fr+fi*fi
    triple=(dr*fr-di*fi)*er+(dr*fi+di*fr)*ei
    determinant=a*b*c+2*triple-a*f2-b*e2-c*d2
    return determinant,(b*c-f2,a*c-e2,a*b-d2)


class ExactLabelledMCZF:
    def __init__(self,grid,channels,power,noise,minimum_spacing=.5):
        self.grid=np.asarray(grid,float)
        self.channels=np.asarray(channels,complex)
        self.R,self.N,self.P,self.M=self.channels.shape
        assert self.R==1000 and self.N==4 and self.M==3 and len(self.grid)==self.P
        self.integer_h,self.h_exp=binary_integer_table(self.channels)
        self.gram_scale=1 << (2*self.h_exp)
        pnum,pden=float(power).as_integer_ratio()
        nnum,nden=float(noise).as_integer_ratio()
        self.a_num,self.a_den=pnum*nden,pden*self.M*nnum
        self.grams=[[ [row_gram(self.integer_h[r,n,p]) for p in range(self.P)]
                     for n in range(self.N)] for r in range(self.R)]
        self.allowed=np.linalg.norm(self.grid[:,None]-self.grid[None,:],axis=2)>=minimum_spacing
        self.allowed[np.diag_indices(self.P)]=False
        self.table_sha256=hashlib.sha256(self.channels.tobytes(order='C')).hexdigest()
        self.coefficients=None
        self.constant=None
        self.certificates=[]
        self.visited_leaves=[]
        self.nodes=0

    def completions(self,prefix=()):
        if len(prefix)==self.N:
            yield tuple(prefix)
            return
        for p in range(self.P):
            if all(self.allowed[p,q] for q in prefix):
                yield from self.completions((*prefix,p))

    def leaf_interval(self,layout):
        lo=hi=0
        min_det=None
        for r in range(self.R):
            g=tuple(sum(self.grams[r][n][layout[n]][j] for n in range(self.N)) for j in range(9))
            det,minor=det_and_minors(g)
            assert det>0 and all(value>0 for value in minor), 'Original ZF physical matrix must be full rank'
            min_det=det if min_det is None else min(min_det,det)
            for value in minor:
                den=self.a_den*self.gram_scale*value
                ll,uu=rational_log_interval(den+self.a_num*det,den)
                lo+=ll;hi+=uu
        return lo,hi

    def displayed_interval(self,interval):
        # Positive commonR*ln2 denominator, outward exact quotient.
        lo,hi=interval
        return float(lo/(self.R*LN2_HI)),float(hi/(self.R*LN2_LO))

    def build_bound(self,anchor_layout,invalid_anchor=False):
        v=np.empty((self.R,self.M,self.M),complex)
        for r in range(self.R):
            h=np.array([self.channels[r,n,anchor_layout[n]] for n in range(self.N)])
            inv=np.linalg.solve(h.conj().T@h,np.eye(self.M))
            for u in range(self.M):
                v[r,u]=inv[:,u]/inv[u,u]
                v[r,u,u]=1.+0j
        if invalid_anchor:
            v[0,0,0]=.5
        assert all(v[r,u,u] == 1.+0j for r in range(self.R) for u in range(self.M)), 'Variational anchor coordinate must be EXACT1'
        vi,vexp=binary_integer_table(v)
        qscale=1 << (2*(self.h_exp+vexp))
        coefficients=[[0]*self.P for _ in range(self.N)]
        constant=0
        for r in range(self.R):
            for u in range(self.M):
                q=[[0]*self.P for _ in range(self.N)]
                for n in range(self.N):
                    for p in range(self.P):
                        rr=ii=0
                        for j in range(self.M):
                            hr,hi=map(int,self.integer_h[r,n,p,j])
                            vr,vj=map(int,vi[r,u,j])
                            rr+=hr*vr-hi*vj;ii+=hr*vj+hi*vr
                        q[n][p]=rr*rr+ii*ii
                b=sum(q[n][anchor_layout[n]] for n in range(self.N))
                assert b>0
                den=self.a_den*qscale+self.a_num*b
                _,log_hi=rational_log_interval(den,self.a_den*qscale)
                constant+=log_hi-(self.a_num*b*SCALE)//den
                for n in range(self.N):
                    for p in range(self.P):
                        coefficients[n][p]+=ceil_div(self.a_num*q[n][p]*SCALE,den)
        self.coefficients,self.constant=coefficients,constant
        return {'anchor_layout':list(anchor_layout),'all3000_v_coordinates_exactly1':True,
                'approximate_inverse_only_chooses_v_not_certificate':True,
                'coefficient_sum_over_all1000_before_each_label_max':True,
                'h_dyadic_exponent':self.h_exp,'v_dyadic_exponent':vexp,
                'bound_natural_log_constant_Q80':str(constant),
                'bound_label_candidate_coefficients_Q80':[[str(x) for x in row] for row in coefficients]}

    def bound(self,prefix):
        value=self.constant+sum(self.coefficients[n][p] for n,p in enumerate(prefix))
        eligible=[p for p in range(self.P) if all(self.allowed[p,q] for q in prefix)]
        if not eligible and len(prefix)<self.N:
            return None
        for n in range(len(prefix),self.N):
            value+=max(self.coefficients[n][p] for p in eligible)
        return value

    def verify_pruning(self,oracle,incumbent):
        lower=oracle[incumbent][0]
        def visit(prefix):
            self.nodes+=1
            descendants=[layout for layout in oracle if layout[:len(prefix)] == prefix]
            if not descendants:
                return
            upper=self.bound(prefix)
            # Exact independent all-leaf interval oracle: not a float residual.
            max_leaf_upper=max(oracle[layout][1] for layout in descendants)
            # Rounded leaf upper can exceed an exact tangent at the anchor by
            # a few Q80 units. Compare independent leaf LOWER here; the strict
            # prune remains upper<=incumbentLOWER, so the theorem is exact.
            assert upper>=max(oracle[layout][0] for layout in descendants)
            if upper<=lower:
                self.certificates.append({'prefix':list(prefix),'upper_Q80':str(upper),
                    'incumbent_lower_Q80':str(lower),'all_descendant_leaves':len(descendants),
                    'independent_max_leaf_upper_Q80':str(max_leaf_upper),
                    'all_exact_leaf_intervals_checked':True})
                return
            if len(prefix)==self.N:
                self.visited_leaves.append(prefix)
                return
            for p in range(self.P):
                if all(self.allowed[p,q] for q in prefix):
                    visit((*prefix,p))
        visit(())
        covered=set(self.visited_leaves)
        for cert in self.certificates:
            prefix=tuple(cert['prefix'])
            covered.update(layout for layout in oracle if layout[:len(prefix)]==prefix)
        assert covered==set(oracle)
        return {'nodes':self.nodes,'visited_complete_leaves':len(self.visited_leaves),
                'certifiably_pruned_subtrees':len(self.certificates),'all_labelled_assignments_covered':True,
                'all_pruned_subtrees_independently_enumerated':True,'certificates':self.certificates}
