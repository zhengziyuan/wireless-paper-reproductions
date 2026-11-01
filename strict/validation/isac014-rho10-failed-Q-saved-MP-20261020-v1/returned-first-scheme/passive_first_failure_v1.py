"""One passive exception snapshot; never retries or changes scientific operands."""
import functools
import json
import math
from pathlib import Path
import sys
import traceback
import numpy as np

ARRAY_NAMES = frozenset(('w','theta','r','q','p','y','total','signal','interference','mu','eta','lip','ga','z','pattern','fc','fs','f','norms','pd','new','val','vec','projected','row','lower','upper','g','direction','trial'))
SCALAR_NAMES = ('iota','den','nu','bisects','iteration','_','value','slope','alpha','relative_objective','relative_step')

def number(value):
    if isinstance(value, (bool, int, np.integer)):return int(value) if not isinstance(value,bool) else value
    if isinstance(value, (float,np.floating)):
        return float(value) if math.isfinite(float(value)) else {'nonfinite_repr':repr(float(value))}
    return None

class PassiveFirstFailure:
    def __init__(self, output):
        self.output=Path(output);self.first=None;self.errors=[];self.methods={}

    def wrap(self, name, function):
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            self.methods[name]=self.methods.get(name,0)+1
            try:return function(*args, **kwargs)
            except Exception as error:
                if self.first is None:
                    try:self.capture(name,error,error.__traceback__)
                    except Exception as observer_error:
                        self.errors.append({'type':type(observer_error).__name__,'message':str(observer_error),'stage':'passive_capture'})
                        # Mark attempted: no retry of a failed observer or scientific call.
                        self.first={'scientific_exception_type':type(error).__name__,'scientific_exception_message':str(error),'capture_failed':True}
                raise
        return wrapped

    def capture(self, method, error, tb):
        scheme=None;frame=sys._getframe()
        while frame is not None:
            if frame.f_code.co_name=='run_scenario' and 'name' in frame.f_locals:
                scheme=frame.f_locals['name'];break
            frame=frame.f_back
        arrays={};frames=[];index=0
        while tb is not None:
            frame=tb.tb_frame;local=frame.f_locals;fn=frame.f_code.co_name
            if fn!='wrapped':
                prefix=f'f{index}_{fn}';entry={'function':fn,'line':tb.tb_lineno,'source_name':Path(frame.f_code.co_filename).name,'arrays':[],'scalars':{}}
                for name in sorted(ARRAY_NAMES):
                    value=local.get(name)
                    if isinstance(value,np.ndarray) and value.dtype.kind in 'biufc':
                        key=f'{prefix}_{name}';arrays[key]=np.array(value,copy=True);entry['arrays'].append(key)
                for name in SCALAR_NAMES:
                    value=number(local.get(name))
                    if value is not None:entry['scalars'][name]=value
                information=local.get('structured_info')
                if isinstance(information,dict):
                    entry['structured_solver_scalars']={name:number(value) for name,value in information.items() if number(value) is not None}
                    for name,value in information.items():
                        if isinstance(value,np.ndarray) and value.dtype.kind in 'biufc':
                            key=f'{prefix}_structured_{name}';arrays[key]=np.array(value,copy=True);entry['arrays'].append(key)
                frames.append(entry);index+=1
            tb=tb.tb_next
        npz=self.output/'first-real-failure-operands.npz'
        with npz.open('xb') as stream:np.savez_compressed(stream,**arrays)
        self.first={'scheme':scheme,'method':method,'scientific_exception_type':type(error).__name__,'scientific_exception_message':str(error),'frames':frames,'array_file':npz.name,'array_count':len(arrays),'passive_existing_traceback_only':True,'no_retry_no_frame_local_assignment':True,'assembled_q_p_are_old_binary64_diagnostics_not_theoretical_reference':True}

    def finish(self):
        value={'schema':'PASSIVE_ONE_FIRST_REAL_EXCEPTION_AND_METHOD_COUNTS_V1','first_failure':self.first,'method_calls':self.methods,'observer_errors':self.errors,'no_optimizer_call_by_observer':True,'no_RNG_or_sampling':True}
        with (self.output/'passive-first-failure-and-methods.json').open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
        return value
