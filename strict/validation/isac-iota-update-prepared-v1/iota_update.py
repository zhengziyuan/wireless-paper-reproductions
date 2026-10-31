"""Small standalone ISAC iota update experiment; not a production solver.

Implements the exact Eq. (23) or the paper's explicitly requested epsilon
variant, and compares the *actual fixed-state* NMSE before and after. No claim
of monotonicity or source provenance is made. No channels or solvers run.
"""
import math

MAX_ITEMS = 4096

class InvalidArithmetic(ValueError):
    pass

def positive(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidArithmetic(field + '_not_real')
    try: value = float(value)
    except (OverflowError, ValueError): raise InvalidArithmetic(field + '_outside_binary64')
    if not math.isfinite(value) or value <= 0:
        raise InvalidArithmetic(field + '_not_finite_positive')
    return value

def product(a, b, field):
    value = a*b
    if not math.isfinite(value): raise InvalidArithmetic(field + '_overflow')
    if a != 0 and b != 0 and value == 0: raise InvalidArithmetic(field + '_underflow')
    return value

def divide(a, b, field):
    if not b > 0 or not math.isfinite(b): raise InvalidArithmetic(field + '_invalid_denominator')
    value = a/b
    if not math.isfinite(value): raise InvalidArithmetic(field + '_overflow')
    if a != 0 and value == 0: raise InvalidArithmetic(field + '_underflow')
    return value

def checked_sum(terms, field):
    try: result = math.fsum(terms)
    except OverflowError: raise InvalidArithmetic(field + '_overflow')
    if not math.isfinite(result): raise InvalidArithmetic(field + '_overflow')
    return result

def vector(values, field):
    if not isinstance(values, (tuple, list)) or not 1 <= len(values) <= MAX_ITEMS:
        raise InvalidArithmetic(field + '_invalid_length')
    result=[]
    for item in values:
        if isinstance(item, bool) or not isinstance(item, (int,float)):
            raise InvalidArithmetic(field + '_not_real')
        try: item=float(item)
        except (OverflowError,ValueError): raise InvalidArithmetic(field + '_outside_binary64')
        if not math.isfinite(item) or item < 0: raise InvalidArithmetic(field + '_negative_or_nonfinite')
        result.append(item)
    return result

def calc_nmse(p, desired, iota, energy):
    # Algebraically Eq. (22), dividing first avoids squaring iota.
    residual=[]
    for a,b in zip(p,desired):
        r=divide(a,iota,'p_over_iota')-b
        if not math.isfinite(r): raise InvalidArithmetic('residual_overflow')
        residual.append(product(r,r,'residual_square'))
    return divide(checked_sum(residual,'residual_sum'),energy,'nmse')

def analyze(p, desired, *, previous_iota, mode, epsilon=None, epsilon_source=None):
    """Return bounded explicit result; invalid arithmetic becomes a failure record.

    previous_iota is required so comparisons refer to a real fixed state. A
    source label is user-supplied metadata, not provenance verification. Exact
    mode accepts no epsilon; safeguarded mode requires positive finite epsilon.
    """
    result={'schema':'isac-iota-fixed-state-helper-v1','mode':mode,'status':'failed',
            'source_provenance_verified':False,'full_scientific_acceptance':False,
            'numeric_precision':'binary64; comparison can hide changes below rounding precision'}
    try:
        if mode not in ('exact','safeguarded'):raise InvalidArithmetic('unknown_mode')
        if mode=='exact' and (epsilon is not None or epsilon_source is not None):raise InvalidArithmetic('exact_disallows_epsilon')
        if mode=='safeguarded':
            epsilon=positive(epsilon,'epsilon')
            if not isinstance(epsilon_source,str) or not epsilon_source.strip() or len(epsilon_source)>512:raise InvalidArithmetic('epsilon_source_required')
            result['epsilon']=epsilon;result['epsilon_source']=epsilon_source
        previous_iota=positive(previous_iota,'previous_iota')
        p=vector(p,'pattern');desired=vector(desired,'desired')
        if len(p)!=len(desired):raise InvalidArithmetic('length_mismatch')
        c=checked_sum((product(v,v,'pattern_square') for v in p),'pattern_energy')
        d=checked_sum((product(a,b,'overlap_product') for a,b in zip(p,desired)),'overlap')
        e=checked_sum((product(v,v,'desired_square') for v in desired),'desired_energy')
        if c<=0:raise InvalidArithmetic('zero_pattern_energy')
        if e<=0:raise InvalidArithmetic('zero_desired_energy')
        if mode=='exact' and d<=0:raise InvalidArithmetic('exact_zero_overlap_no_finite_minimizer')
        denom=d if mode=='exact' else d+epsilon
        if not math.isfinite(denom) or denom<=0:raise InvalidArithmetic('update_denominator_overflow_or_nonpositive')
        if mode=='safeguarded':result['epsilon_addition_rounded_away']=(denom==d)
        new_iota=positive(divide(c,denom,'iota'),'new_iota')
        old_nmse=calc_nmse(p,desired,previous_iota,e)
        new_nmse=calc_nmse(p,desired,new_iota,e)
        result.update(status='ok',pattern_energy=c,overlap=d,desired_energy=e,previous_iota=previous_iota,
                      new_iota=new_iota,nmse_before=old_nmse,nmse_after=new_nmse,
                      observed_change=('increased' if new_nmse>old_nmse else 'decreased' if new_nmse<old_nmse else 'equal'),
                      interpretation='fixed saved state only; no AO monotonicity or convergence claim')
    except (InvalidArithmetic, OverflowError, ZeroDivisionError) as exc:
        result['reason']=str(exc) or type(exc).__name__
    return result
