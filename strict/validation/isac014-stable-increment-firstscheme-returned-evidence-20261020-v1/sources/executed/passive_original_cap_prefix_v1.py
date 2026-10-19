"""Observe the previous first500 boundary without interrupting the new run."""
from pathlib import Path
import json
from passive_RCG_seed_trace_v1 import PassiveRCGSeedTrace

class PassiveCapBoundaryTrace(PassiveRCGSeedTrace):
    def __init__(self,source):
        super().__init__(source);self.rotation_calls=0;self.first_rotation_frame=None;self.prefix=[]
    def trace(self,frame,event,arg):
        if frame.f_code.co_filename==self.source and frame.f_code.co_name=='update_rotation':
            if event=='call':
                self.rotation_calls+=1
                if self.rotation_calls==1:self.first_rotation_frame=id(frame)
            if id(frame)!=self.first_rotation_frame:return None
            if event=='line':
                line=self.lines[frame.f_lineno-1].strip();v=frame.f_locals
                if line.startswith('if checked_gradient<='):
                    iteration=len(v['history'])-1
                    if iteration in (0,499,500):
                        self.prefix.append(dict(actual_outer_zero_based=0,inner_iteration_zero_based=iteration,
                            utility=float(v['metric']['utility']),checked_projected_gradient_norm=float(v['checked_gradient']),
                            relative_step_from_previous_accepted=v.get('relative_step'),iota=float(v['iota'])))
            elif event=='return':self.first_rotation_frame=None
            return self.trace
        return super().trace(frame,event,arg)
    def finish(self,output):
        result=super().finish(output)
        value=dict(schema='actual-first-PGA-previous-cap500-boundary-passive-scalars-v1',
            rows=self.prefix,rotation_calls=self.rotation_calls,source_arithmetic_and_all_returns_unchanged=True,
            no_extra_model_gradient_trial_or_rng_evaluation=True)
        with (Path(output)/'passive-first-PGA-original500-boundary.json').open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
        return result
