"""Conservative event-chain reader for the prepared MATLAB MRT driver.

Not a scientific verifier or an execution admission. The caller must bind the
first input, sources, process identities and a single writer separately.
"""
from __future__ import annotations
import json
import math
from pathlib import Path

CAP=64*1024
STATE_KEYS={'schema','t','sweep','antenna','sweep_start','updates','done',
            'original_converged_flag','termination'}


def state_ok(state):
    if not isinstance(state,dict) or set(state)!=STATE_KEYS: return False
    if state['schema']!='MA20_NATIVE_MRT_SEGMENT_STATE_V1': return False
    sweep,antenna,updates=state['sweep'],state['antenna'],state['updates']
    if any(type(x) is not int for x in (sweep,antenna,updates)): return False
    if not (0<=sweep<=10000 and 0<=antenna<6 and updates==sweep*6+antenna): return False
    if any(type(state[k]) is not bool for k in ('done','original_converged_flag')): return False
    if sweep==10000 and not state['done']: return False
    if type(state['termination']) is not str: return False
    v=state['sweep_start']
    if type(v) not in (int,float) or not math.isfinite(v): return False
    t=state['t']
    return (isinstance(t,list) and len(t)==6 and all(isinstance(row,list) and len(row)==2
            and all(type(x) in (int,float) and math.isfinite(x) for x in row) for row in t))


def read_segment(path: Path, expected_start=None, fractional_threshold=None):
    if type(fractional_threshold) not in (int,float) or not math.isfinite(fractional_threshold):
        raise ValueError('finite original threshold required')
    raw=path.read_bytes()
    if len(raw)>CAP: raise ValueError('segment exceeds configured bound')
    # A partial last line is retained for inspection and never treated as a
    # committed coordinate. Previous complete lines remain available.
    complete=raw.rfind(b'\n')+1
    tail=raw[complete:]
    lines=raw[:complete].splitlines()
    if not lines: raise ValueError('no complete committed event')
    previous=expected_start;count=0
    for line in lines:
        event=json.loads(line)
        if not isinstance(event,dict) or set(event)!={'schema','input','record','output','sweep_relative_change'}:
            raise ValueError('unexpected event fields')
        before,after=event['input'],event['output']
        if event['schema']!='MA20_NATIVE_MRT_COORDINATE_EVENT_V1' or not state_ok(before) or not state_ok(after):
            raise ValueError('invalid state or event schema')
        if previous is not None and before!=previous: raise ValueError('state chain discontinuity')
        if before['done'] or after['updates']!=before['updates']+1: raise ValueError('invalid update counter')
        if before['original_converged_flag'] or before['termination']!='pending':
            raise ValueError('invalid pre-update stopping state')
        coord=before['antenna'];expected_sweep=before['sweep']+(coord==5)
        if after['sweep']!=expected_sweep or after['antenna']!=(coord+1)%6:
            raise ValueError('invalid coordinate cursor')
        if any(before['t'][i]!=after['t'][i] for i in range(6) if i!=coord):
            raise ValueError('other coordinates changed')
        relative=event['sweep_relative_change']
        if coord!=5:
            if (relative!=[] or after['sweep_start']!=before['sweep_start'] or after['done']
                    or after['original_converged_flag'] or after['termination']!='pending'):
                raise ValueError('invalid intermediate sweep state')
        else:
            if before['sweep_start']==0 or type(relative) not in (int,float) or not math.isfinite(relative):
                raise ValueError('undefined or non-finite fractional change')
            recomputed=(after['sweep_start']-before['sweep_start'])/abs(before['sweep_start'])
            if not math.isclose(relative,recomputed,rel_tol=1e-12,abs_tol=1e-15):
                raise ValueError('fractional change mismatch')
            if (relative<fractional_threshold)!=(recomputed<fractional_threshold):
                raise ValueError('rounded value changes original stop decision')
            converged=relative<fractional_threshold
            reached_cap=after['sweep']==10000
            expected_done=converged or reached_cap
            expected_reason='fractional_increase' if converged else ('configured_iteration_cap' if reached_cap else 'pending')
            if (after['done']!=expected_done or after['original_converged_flag']!=converged
                    or after['termination']!=expected_reason):
                raise ValueError('original stopping state mismatch')
        rec=event['record']
        if not isinstance(rec,dict) or rec.get('sweep')!=before['sweep'] or rec.get('antenna')!=coord:
            raise ValueError('record does not match coordinate')
        previous=after;count+=1
    first=json.loads(lines[0])['input']
    return {'committed_events':count,'first_state':first,'last_state':previous,'partial_tail_bytes':len(tail),
            'partial_tail_preserved':bool(tail),'scientific_pass':False}
