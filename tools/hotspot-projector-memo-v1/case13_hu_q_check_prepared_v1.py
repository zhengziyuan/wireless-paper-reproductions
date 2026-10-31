"""Disabled saved-point HU reconstruction and rate comparison for Case 13.

All matrix and beam arithmetic treats the stored binary64 values as exact
rationals. The final logarithm is evaluated in binary64; this is not an
interval-certified transcendental result. Historical source content and the
whole event snapshot are not reauthenticated by this calculation.
"""
import math
from fractions import Fraction

REAL_SCIENCE_ENABLED=False
N,M,J=16,25,16
ORDINALS=(1327666,1327713,1327755,1327778,1327876,1327926,1327964,1328004)

def need(x,message):
    if x is not True: raise ValueError(message)

def add(a,b): return (a[0]+b[0],a[1]+b[1])
def mul(a,b): return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def scale(a,s): return (a[0]*s,a[1]*s)

def real_values(desc,shape,decoder):
    values=decoder.decode_array(desc,shape)
    need(all(z[1]==0 for z in values),'expected real saved array')
    return [z[0] for z in values]

def build_covariance(dm,dv,G,gv,ground,rv,decoder):
    zero=Fraction(0);out=[]
    for row in range(N):
        line=[]
        for col in range(N):
            z=(dv[row] if row==col else zero,zero)
            for m in range(M):
                z=add(z,scale(decoder.product_conj_left(G[m+M*row],G[m+M*col]),rv[m]))
                if row==col:
                    z=add(z,(gv[m+M*row]*(decoder.abs2(ground[m])+rv[m]),zero))
            line.append(z)
        out.append(line)
    return out

def build_q(dm,G,ground,phi,cov,decoder):
    means=[]
    for n in range(N):
        z=dm[n]
        for m in range(M): z=add(z,mul(mul(phi[m],ground[m]),G[m+M*n]))
        means.append(z)
    return [[add(cov[r][c],decoder.product_conj_left(means[r],means[c]))
             for c in range(N)] for r in range(N)]

def exact_rate(matrix,cols,noise,decoder):
    gains=[decoder.gain_saved(matrix,w) for w in cols]
    den=noise+sum(gains[1:],Fraction(0))
    need(den>0 and gains[0]>=0,'positive denominator and nonnegative desired power')
    sinr=gains[0]/den
    try:
        sinr_binary64=float(sinr)
    except OverflowError as exc:
        raise ValueError('exact SINR overflows binary64 logarithm input') from exc
    need(math.isfinite(sinr_binary64) and not (sinr>0 and sinr_binary64==0.0),
         'exact positive SINR must not overflow or underflow binary64')
    rate=math.log1p(sinr_binary64)/math.log(2.0)
    need(math.isfinite(rate) and not (sinr>0 and rate==0.0),
         'finite, non-underflowed binary64 logarithm')
    return sinr,rate

def compute(hu,all_ao,first,final,decoder):
    need(REAL_SCIENCE_ENABLED,'reviewed external guard admission required')
    need(hu.get('schema')=='CASE13_HU_INPUTS_IDENTITY_V1' and
         hu.get('historical_chunk_content_reverified') is False and
         hu.get('whole_event_atomic_snapshot_verified') is False,'conditional HU source')
    event=hu['event'];ctx=event['context']
    need(event['action']=='design_context' and event['ordinal']==1327098 and
         ctx['case_id']==13 and ctx['U']==1 and ctx['beta']==20 and ctx['geometry_id']==12013,
         'fixed HU design identity')
    x=event['fields']['x'];need(set(x)=={'direct_mean','direct_variance','matrix_mean',
         'matrix_variance','ground_mean','ground_variance'},'six moment inputs')
    dec=decoder.decode_array
    dm=dec(x['direct_mean'],[1,N]);dv=real_values(x['direct_variance'],[1,N],decoder)
    G=dec(x['matrix_mean'],[M,N]);gv=real_values(x['matrix_variance'],[M,N],decoder)
    ground=dec(x['ground_mean'],[1,M]);rv=real_values(x['ground_variance'],[1,M],decoder)
    need(all(z>=0 for z in dv+gv+rv),'nonnegative saved variances')
    need(all_ao.get('schema')=='CASE13_ALL_AO_IDENTITY_COMPACT_FIELDS_V1' and
         all_ao.get('historical_chunk_content_reverified') is False and
         all_ao.get('whole_event_atomic_snapshot_verified') is False,'conditional AO source')
    events=all_ao['events'];arrays=all_ao['arrays'];finals=final['events']
    need([e['ordinal'] for e in events]==list(ORDINALS) and
         [e['ordinal'] for e in finals]==[1327779,1328005] and
         first['ordinal']==ORDINALS[0] and first['context']==events[0]['context'], 'fixed AO/final identities')
    cov=build_covariance(dm,dv,G,gv,ground,rv,decoder)
    records=[]
    for ix,e in enumerate(events):
        start=ix//4;ec=e['context'];fc=finals[start]['context']
        need(ec['case_id']==fc['case_id']==13 and ec['geometry_id']==fc['geometry_id']==12013 and
             ec['start_id']==fc['start_id']==start and ec['scheme']==fc['scheme']=='AO' and
             ec['U']==fc['U']==1 and ec['beta']==fc['beta']==20,'AO/final context')
        f=first['fields'] if ix==0 else e['fields'];phi=dec(f['phi'],[1,M]);w=dec(f['W'],[N,J])
        columns=[[w[row+N*j] for row in range(N)] for j in range(J)]
        noise=real_values(finals[start]['fields']['noise'],[1,1],decoder)[0];need(noise>0,'positive noise')
        ref=e['fields']['Q']['array_ref'];need(type(ref) is int and 0<=ref<len(arrays),'saved Q ref')
        q=dec(arrays[ref],[1,N,N]);saved=[[q[r+N*c] for c in range(N)] for r in range(N)]
        rebuilt=build_q(dm,G,ground,phi,cov,decoder)
        maxdiff=Fraction(0);eq=0
        for r in range(N):
            for c in range(N):
                a,b=rebuilt[r][c],saved[r][c];eq+=int(a==b)
                maxdiff=max(maxdiff,abs(a[0]-b[0]),abs(a[1]-b[1]))
        sr,rate_saved=exact_rate(saved,columns,noise,decoder)
        rr,rate_rebuilt=exact_rate(rebuilt,columns,noise,decoder)
        v=real_values(f['evaluation']['hu_sum_rate'],[1,1],decoder)[0]
        saved_sinr=real_values(e['fields']['evaluation']['sinr'],[J,1],decoder)[0]
        records.append(dict(ordinal=e['ordinal'],start_id=start,
          max_abs_Q_component_difference=decoder.ratio(maxdiff),
          exactly_equal_complex_Q_entries=eq,
          rate_from_rebuilt_Q_binary64=repr(rate_rebuilt),rate_from_saved_Q_binary64=repr(rate_saved),
          saved_rate_binary64=repr(float(v)),saved_Q_rate_minus_recorded=repr(rate_saved-float(v)),
          rebuilt_Q_rate_minus_recorded=repr(rate_rebuilt-float(v)),
          exact_saved_Q_sinr_minus_recorded=decoder.ratio(sr-saved_sinr),
          exact_rebuilt_Q_sinr=decoder.ratio(rr)))
    return dict(schema='CASE13_HU_Q_CHECK_V1',records=records,
      arithmetic='exact rational Q and SINR from stored binary64; logarithm computed in binary64',
      saved_final_noise_assumed_for_all_four_iterations_of_each_start=True,
      historical_chunk_content_reverified=False,whole_event_atomic_snapshot_verified=False,
      saved_inputs_historical_content_freshly_authenticated=False,
      no_quadrature_or_physical_units_certificate=True,
      full_paper_pass=False,not_full_convergence_matlab_or_reference_validation=True,
      scope='one HU, eight saved AO points; source moments and stored Q share historical origin')
