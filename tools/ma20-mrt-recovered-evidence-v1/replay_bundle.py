"""Replay the supplied saved MRT AO trajectory without rerunning any solver.

This reads the small portable bundle and the repository's source; no random
channel bank is included or generated. It is not a full paper acceptance test.
"""
import argparse
import base64
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

def need(x,msg):
    if not x:raise ValueError(msg)

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')

def same_number(a,b):
    need(not isinstance(a,bool) and not isinstance(b,bool) and
         isinstance(a,(int,float)) and isinstance(b,(int,float)) and
         math.isfinite(a) and math.isfinite(b),'finite non-boolean number')
    return struct.pack('>d',float(a))==struct.pack('>d',float(b))

def check_transition(before,after,event,model,core,np):
    """Recheck source-order and stop conditions without calling its solver."""
    required={'schema','mode','sweep','antenna','updates','positions','last_value','done','converged'}
    need(type(before) is dict and type(after) is dict and set(before)==required and set(after)==required and
         before['schema']=='ma-original-optimize-coordinate-state-v1' and after['schema']==before['schema'],
         'state fields and schema')
    for state in (before,after):
        positions=state['positions']
        need(type(positions) is list and len(positions)==6 and
             all(type(row) is list and len(row)==2 and all(not isinstance(x,bool) and
                 isinstance(x,(int,float)) and math.isfinite(x) for x in row) for row in positions) and
             type(state['sweep']) is int and type(state['antenna']) is int and type(state['updates']) is int and
             type(state['done']) is bool and type(state['converged']) is bool and
             not isinstance(state['last_value'],bool) and isinstance(state['last_value'],(int,float)) and
             math.isfinite(state['last_value']), 'finite positions and cursor types')
    n=len(before['positions']);antenna=before['antenna'];sweep=before['sweep']
    cap=model['maximum_AO_iterations'];need(type(cap) is int and 0<=sweep<cap and 0<=antenna<n,'cursor range')
    need(before['mode']=='MRT' and after['mode']=='MRT' and before['done'] is False and
         before['updates']==sweep*n+antenna,'predecessor cursor')
    need(type(event) is dict and set(event) in ({'kind','record','positions'},{'kind','record','positions','sweep_objective'}) and
         event['kind']=='coordinate' and type(event['record']) is dict and event['record']['sweep']==sweep and
         event['record']['antenna']==antenna and canonical(event['positions'])==canonical(after['positions']),
         'event order and positions')
    for i in range(n):
        if i!=antenna:need(canonical(before['positions'][i])==canonical(after['positions'][i]),'unchanged coordinates')
    rec=event['record'];old=core.mrt_statistics(np.asarray(before['positions']),model)[0]
    new=core.mrt_statistics(np.asarray(after['positions']),model)[0]
    tolerance=model.get('verification_tolerance');surrogate=rec.get('surrogate')
    need(not isinstance(tolerance,bool) and isinstance(tolerance,(int,float)) and math.isfinite(tolerance) and
         tolerance>=0 and not isinstance(surrogate,bool) and isinstance(surrogate,(int,float)) and
         math.isfinite(surrogate),'finite source acceptance tolerance and surrogate')
    need(same_number(old,rec['before']) and same_number(new,rec['after']) and
         new>=surrogate-tolerance and new>=old-tolerance,'source objective and acceptance')
    sweep_end=antenna==n-1;ns=sweep+1 if sweep_end else sweep;ni=0 if sweep_end else antenna+1
    conv=(new-before['last_value'])/abs(before['last_value'])<model['fractional_increase_threshold'] if sweep_end else False
    last=new if sweep_end else before['last_value'];done=conv or ns==model['maximum_AO_iterations']
    need((('sweep_objective' in event)==sweep_end) and
         (not sweep_end or same_number(event['sweep_objective'],new)) and
         after['sweep']==ns and after['antenna']==ni and after['updates']==before['updates']+1 and
         after['done'] is bool(done) and after['converged'] is bool(conv) and
         same_number(after['last_value'],last),'source stopping rule')

def read_frames(raw,epoch,seq,prev):
    need(len(raw)<=700*1024+8232 and raw[:8]==b'MAAOJ1\0\0','frame bound or magic')
    at=8;result=[]
    while at<len(raw):
        need(len(raw)-at>=40,'partial frame header')
        size=struct.unpack('>Q',raw[at:at+8])[0];digest=raw[at+8:at+40];at+=40
        need(size<=8192 and len(raw)-at>=size,'partial frame payload')
        body=raw[at:at+size];at+=size;need(hashlib.sha256(body).digest()==digest,'frame digest')
        row=json.loads(body)
        need(type(row) is dict and set(row)=={'schema','epoch_SHA256','sequence','previous_SHA256','state','event'}
             and canonical(row)==body and row.get('schema')=='MA_AO_COORDINATE_FRAME_V1' and row.get('epoch_SHA256')==epoch and
             row.get('sequence')==seq and row.get('previous_SHA256')==prev,'frame chain')
        result.append(row);prev=digest.hex();seq+=1
    return result,prev

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--repo',type=Path,required=True);a=ap.parse_args();repo=a.repo.resolve()
    with gzip.open(a.bundle,'rb') as f:raw=f.read(2*1024*1024+1)
    need(len(raw)<=2*1024*1024,'bundle bound');b=json.loads(raw)
    need(b.get('schema')=='MA20_D3G0_MRT_RECOVERED_PORTABLE_EVIDENCE_V1','bundle schema')
    for name in ('core.py','run.py'):
        path=repo/'strict/two-timescale-ma'/name
        with path.open('rb') as f:source=f.read(131073)
        need(len(source)<=131072 and hashlib.sha256(source).hexdigest()==b['source_sha256'][name],
             'source differs from the recorded first-segment binding')
    sys.path.insert(0,str(repo/'strict/two-timescale-ma'))
    import numpy as np
    import core,run
    j,cfg=b['job_theory_only'],b['config'];model,initial=run.scenario(cfg,j['N'],j['M'],j['kappa'],j['power'],j['A'],j['geometry'])
    model['region_lower']=j['region_lower'];model['region_upper']=j['region_upper']
    el=np.asarray(j['geometry']['elevation']);az=np.asarray(j['geometry']['azimuth'])
    directions=np.column_stack((np.cos(el)*np.sin(az),np.sin(el)))
    beta=1e-4*np.asarray(j['geometry']['distances_m'])**-2.8;noise=1e-11;n=j['N'];m=j['M'];kap=j['kappa']
    def independent_eq13(t):
        numerator=beta**2*(n*n+n*(2*kap+1)/(kap+1)**2)
        denominator=np.full(m,noise*n*beta.sum()/j['power'])
        for u in range(m):
            for v in range(m):
                if u==v:continue
                phasor=np.exp(2j*np.pi*(t@(directions[u]-directions[v])))
                denominator[u]+=beta[u]*beta[v]*(kap*kap*abs(np.sum(phasor))**2+n*(2*kap+1))/(kap+1)**2
        return float(np.log2(1+numerator/denominator).sum())
    start,second,cp,binding=b['first_start'],b['second_start'],b['second_checkpoint'],b['binding']
    epoch=hashlib.sha256(canonical(binding)).hexdigest();initial_value=core.mrt_statistics(initial,model)[0]
    s0={'schema':'ma-original-optimize-coordinate-state-v1','mode':'MRT','sweep':0,'antenna':0,'updates':0,
        'positions':initial.tolist(),'last_value':initial_value,'done':False,'converged':False}
    e0={'kind':'initial','objective':initial_value,'positions':initial.tolist()}
    need(canonical(s0)==canonical(start['state']) and canonical(e0)==canonical(start['original_initial_event'])
         and start['epoch_SHA256']==epoch,'initial state')
    old,old_chain=read_frames(base64.b64decode(b['first_frames_base64'],validate=True),epoch,0,epoch)
    need(len(old)==151 and second['next_sequence']==151 and second['previous_SHA256']==old_chain and
         canonical(second['state'])==canonical(old[-1]['state']),'old prefix')
    new,last=read_frames(base64.b64decode(b['second_frames_base64'],validate=True),epoch,151,old_chain)
    need(len(new)==83 and cp['events']==83 and cp['next_sequence']==234 and cp['last_SHA256']==last and
         canonical(cp['state'])==canonical(new[-1]['state']),'successor')
    claim=b['second_claim'];need(claim['predecessor_sequence']==151 and claim['predecessor_chain']==old_chain and claim['successor_step']==2,'claim')
    need(b['first_terminal']['terminal_reason']=='guard_failure' and b['second_terminal']['guard_success'] is True and
         b['second_terminal']['terminal_reason']=='natural_exit','terminal facts')
    lo=np.asarray(j['region_lower']);hi=np.asarray(j['region_upper']);state=s0;maxerr=0.;deltas=[];sweeps=[e0['objective']]
    def geometry(t):
        dist=np.linalg.norm(t[:,None,:]-t[None,:,:],axis=2)
        return float(dist[np.triu_indices(len(t),1)].min()),max(float(np.maximum(lo-t,0).max()),float(np.maximum(t-hi,0).max()))
    minspace,maxbox=geometry(initial)
    for f in old+new:
        event=f['event'];after=f['state'];record=event['record'];check_transition(state,after,event,model,core,np)
        before=np.asarray(state['positions']);positions=np.asarray(after['positions'])
        maxerr=max(maxerr,abs(independent_eq13(before)-record['before']),abs(independent_eq13(positions)-record['after']))
        sp,box=geometry(positions);minspace=min(minspace,sp);maxbox=max(maxbox,box)
        deltas.append(record['after']-record['before'])
        if 'sweep_objective' in event:sweeps.append(event['sweep_objective'])
        state=after
    ratios=[(v-u)/abs(u) for u,v in zip(sweeps,sweeps[1:])];threshold=cfg['fractional_increase_threshold']
    trigger=[i+1 for i,value in enumerate(ratios) if value<threshold]
    need(len(sweeps)==40 and trigger==[39] and state['done'] is True and state['converged'] is True,'stopping')
    need(maxerr<=1e-9 and minspace>=.5-1e-9 and maxbox<=1e-9,'numerical scope')
    print(json.dumps({'first_frames':len(old),'second_frames':len(new),'updates':state['updates'],'sweeps':state['sweep'],
       'first_stop_sweep':trigger[0],'last_fractional_increase':ratios[-1],'threshold':threshold,
       'initial_objective':sweeps[0],'final_objective':sweeps[-1],
       'independent_max_abs_objective_difference':maxerr,'minimum_saved_spacing':minspace,
       'maximum_saved_box_violation':maxbox,'minimum_coordinate_objective_delta':min(deltas),
       'strict_negative_coordinate_deltas':sum(x<0 for x in deltas),'comparison_tolerance':1e-9,
       'coordinate_solver_replayed':False,'old_guard_failure_retained':True,
       'bank_contents_included':False,'full_monte_carlo_run':False,'matlab_full_search':False,
       'reference_agreement':False,'full_paper_pass':False},separators=(',',':'),allow_nan=False))

if __name__=='__main__':main()
