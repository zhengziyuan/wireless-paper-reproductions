"""Finite sorted root of the SAME Euclidean closed-simplex tangent cone.

Mandatory coordinates are exactly stored X>0. Optional coordinates are
constrained nonnegative. Uncertain rows use exact binary Fraction membership
and round each exact projected component once. No support cutoff, pruning,
metric, conjugate-gradient direction, or stationarity threshold is changed.
"""
from __future__ import annotations
from fractions import Fraction
import math
import numpy as np

def exact_binary_row(direction, mandatory):
    y=[Fraction(float(value)) for value in direction]
    free=[i for i,take in enumerate(mandatory) if take]
    if not free:raise ValueError('A valid row simplex must have a positive coordinate')
    optional=sorted((i for i,take in enumerate(mandatory) if not take),key=lambda i:y[i],reverse=True)
    total=sum(y[i] for i in free)
    for count in range(len(optional)+1):
        if count:total+=y[optional[count-1]]
        denominator=len(free)+count
        previous_ok=count==0 or denominator*y[optional[count-1]]>total
        next_ok=count==len(optional) or total>=denominator*y[optional[count]]
        if previous_ok and next_ok:
            threshold=total/denominator
            answer=[v-threshold if mandatory[i] else max(v-threshold,Fraction(0)) for i,v in enumerate(y)]
            assert sum(answer)==0
            return answer,threshold,count
    raise ArithmeticError('Exact monotone cone root could not be bracketed')

def sorted_row(direction,mandatory):
    direction=np.asarray(direction,dtype=float);mandatory=np.asarray(mandatory,dtype=bool)
    if not np.all(np.isfinite(direction)):raise ValueError('Finite raw cone direction required')
    free=np.flatnonzero(mandatory)
    if not len(free):raise ValueError('A valid row simplex must have a positive coordinate')
    if np.all(direction==direction[free[0]]):
        return np.zeros_like(direction),dict(method='exact_constant_row',mandatory_count=len(free),optional_active_count=0)
    centered=direction-direction[free[0]]
    optional=sorted(np.flatnonzero(~mandatory),key=lambda i:centered[i],reverse=True)
    chosen=list(free);threshold=math.fsum(float(centered[i]) for i in chosen)/len(chosen);count=0
    for index in optional:
        if centered[index]<=threshold:break
        chosen.append(index);count+=1
        threshold=math.fsum(float(centered[i]) for i in chosen)/len(chosen)
    previous_ok=count==0 or centered[optional[count-1]]>threshold
    next_ok=count==len(optional) or threshold>=centered[optional[count]]
    bound=16*np.finfo(float).eps*max(float(np.max(np.abs(centered))),np.finfo(float).tiny)
    uncertain=any(abs(float(centered[i]-threshold))<=bound for i in optional)
    if not previous_ok or not next_ok or uncertain:
        exact,tau,count=exact_binary_row(direction,mandatory)
        return np.asarray([float(v) for v in exact]),dict(method='exact_binary_fraction_row_only',
            mandatory_count=len(free),optional_active_count=count,
            raw_threshold_fraction=[str(tau.numerator),str(tau.denominator)],
            roundoff_guard_only_not_support_or_stopping_tolerance=float(bound))
    return np.where(mandatory,centered-threshold,np.maximum(centered-threshold,0)),dict(
        method='finite_sorted_centered_fsum',mandatory_count=len(free),optional_active_count=count,
        roundoff_guard_only_not_support_or_stopping_tolerance=float(bound))

def project_rows(X,direction):
    out=np.empty_like(direction,dtype=float)
    for row,(y,x) in enumerate(zip(direction,X)):out[row]=sorted_row(y,x>0)[0]
    return out
