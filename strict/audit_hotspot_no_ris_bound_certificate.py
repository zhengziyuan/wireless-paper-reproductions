"""Verify the public CURRENT-model NoRIS upper-bound witness exactly.

Built-in Fraction arithmetic checks every Hermitian LDL pivot for the
published binary64 matrices/constants, not floating-point eigenvalue signs.
It does not recover author inputs or certify original-figure reproduction.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random
import time


def zadd(a,b):return (a[0]+b[0],a[1]+b[1])
def zsub(a,b):return (a[0]-b[0],a[1]-b[1])
def zmul(a,b):return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def zconj(a):return (a[0],-a[1])
def scale(a,b):return (a[0]*b,a[1]*b)
def mag2(a):return a[0]*a[0]+a[1]*a[1]


def decode_exact(value):
    raw=[[(F(float(re)),F(float(im))) for re,im in zip(rrow,irow)]
         for rrow,irow in zip(value['real'],value['imag'])]
    # The executed metric is real(w^H Q w), exactly w^H H w for
    # H=(Q+Q^H)/2. Do this algebra in exact fractions, retaining every
    # raw entry; do not silently discard a small antisymmetric component.
    return [[scale(zadd(raw[i][j],zconj(raw[j][i])),F(1,2))
             for j in range(len(raw))] for i in range(len(raw))]


def exact_hermitian_positive_definite(matrix):
    n=len(matrix);assert n==16 and all(len(r)==n for r in matrix)
    assert all(matrix[i][j]==zconj(matrix[j][i]) for i in range(n) for j in range(n))
    L=[[(F(0),F(0)) for _ in range(n)] for _ in range(n)];D=[];receipts=[]
    for j in range(n):
        assert matrix[j][j][1]==0
        pivot=matrix[j][j][0]-sum((D[k]*mag2(L[j][k]) for k in range(j)),F(0))
        if pivot<=0:raise ValueError('Nonpositive exact rational Hermitian LDL pivot')
        D.append(pivot);L[j][j]=(F(1),F(0))
        for i in range(j+1,n):
            numerator=matrix[i][j]
            for k in range(j):numerator=zsub(numerator,scale(zmul(L[i][k],zconj(L[j][k])),D[k]))
            L[i][j]=scale(numerator,1/pivot)
        digest=hashlib.sha256((str(pivot.numerator)+'/'+str(pivot.denominator)).encode('ascii')).hexdigest()
        receipts.append(dict(pivot_index=j,exact_sign_positive=True,
            approximate_pivot_for_readability=float(pivot),numerator_bits=pivot.numerator.bit_length(),
            denominator_bits=pivot.denominator.bit_length(),exact_rational_pivot_sha256=digest))
    return dict(all16_exact_rational_LDL_pivots_positive=True,pivots=receipts)


def pair_merge_checks(lower,upper):
    """Independently expand pair-merge cross products at1000 rational cases."""
    assert 0<lower<=upper<=2*lower
    rng=random.Random(3309957)
    for _ in range(1000):
        a,b,rest=(F(rng.randint(0,10000),rng.randint(1,10000)) for _ in range(3))
        S=a+b+rest;C=1+lower*rest
        cross=(C+upper*(a+b))*(C+lower*b)*(C+lower*a)-C*(C+lower*b+upper*a)*(C+lower*a+upper*b)
        factored=upper*a*b*(C*(2*lower-upper)+lower*lower*(a+b))
        assert cross==factored and factored>=0 and C>0
    return dict(exact_rational_cases=1000,cross_product_equals_factored_polynomial=True,
        all_pair_merge_differences_nonnegative=True,seed=3309957,
        identity='RHS-LHS=u*a*b*[C*(2*l-u)+l^2*(a+b)], C=1+l*(S-a-b)>0')


def verify(path):
    start=time.perf_counter();raw=json.loads(Path(path).read_text(encoding='utf-8'))
    constants=raw['certificate_constants'];lower=F(constants['lower']);upper=F(constants['upper']);lam=F(constants['lambda_upper'])
    assert constants['power_w']==100 and constants['normalized_noise_variance']==1
    Q0=decode_exact(raw['matrix_witness']['Q0']);cases=[]
    for u,q in enumerate(raw['matrix_witness']['HU_Q']):
        Q=decode_exact(q)
        below=[[zsub(Q[i][j],scale(Q0[i][j],lower)) for j in range(16)] for i in range(16)]
        above=[[zsub(scale(Q0[i][j],upper),Q[i][j]) for j in range(16)] for i in range(16)]
        cases.append(dict(HU_index=u+1,Q_minus_lowerQ0=exact_hermitian_positive_definite(below),
            upperQ0_minus_Q=exact_hermitian_positive_definite(above)))
    spectral=[[zsub((lam if i==j else F(0),F(0)),Q0[i][j]) for j in range(16)] for i in range(16)]
    eigenBound=exact_hermitian_positive_definite(spectral)
    pair=pair_merge_checks(lower,upper)
    result=dict(scope='exact_rational_verification_of_CURRENT_binary64_NoRIS_moment_witness_NOT_author_inputs_or_original_Elog',
        all_passed=len(cases)==6 and all(c['Q_minus_lowerQ0']['all16_exact_rational_LDL_pivots_positive'] and c['upperQ0_minus_Q']['all16_exact_rational_LDL_pivots_positive'] for c in cases),
        case_count=6,Hermitian_dimension=16,exact_LDL_matrix_count=13,actual_matrix_certificates=cases,
        lambdaI_minus_Q0=eigenBound,pair_merge_lemma_checks=pair,
        matrix_contract='Exact Hermitian part H=(Q+Q^H)/2 of every raw published binary64 Q; real(w^H Q w)=w^H H w without dropping small entries or relaxing a tolerance.',
        input_certificate_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        executed_verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),elapsed_seconds=time.perf_counter()-start,
        no_optimizer_run=True,unchanged_original_thresholds=True,
        historical_author_input_recovery_claimed=False,full_reproduction_pass=False)
    assert result['all_passed'] and eigenBound['all16_exact_rational_LDL_pivots_positive']
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();receipt=verify(args.input);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ('all_passed','exact_LDL_matrix_count','elapsed_seconds')}),flush=True)
