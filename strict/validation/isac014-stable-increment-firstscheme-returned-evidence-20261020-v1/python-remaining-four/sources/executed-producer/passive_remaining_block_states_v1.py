"""Copy actual returned tuple operands; never evaluate or change a return."""
import functools
import hashlib
import json
from pathlib import Path
import numpy as np

class PassiveRemainingBlockStates:
    def __init__(self,output,scheme,with_ris):
        self.output=Path(output);self.scheme=scheme;self.with_ris=with_ris
        self.arrays={};self.rows=[];self.errors=[];self.counts={}

    def wrap(self,name,fn):
        @functools.wraps(fn)
        def wrapped(*args,**kwargs):
            result=fn(*args,**kwargs)
            try:
                w,theta,r,c,iota=args[:5]
                if name=='update_w':w=result[0]
                elif name=='update_theta':theta=result[0]
                elif name=='update_rotation':r=result[0]
                else:raise ValueError('Only actual W/RCG/PGA returns')
                self.counts[name]=self.counts.get(name,0)+1
                prefix=f'{name}_{self.counts[name]:04d}';keys={}
                for key,value in [('W',w),('theta',theta),('r',r)]:
                    npzkey=prefix+'__'+key
                    self.arrays[npzkey]=np.array(value,copy=True);keys[key]=npzkey
                history=result[1]
                self.rows.append({'scheme':self.scheme,'method':name,'call':self.counts[name],
                    'fixed_iota':float(iota),'arrays':keys,
                    'actual_returned_flags':{k:history[k] for k in (
                        'applicable','converged','termination_reason','iterations','updates','iteration_budget',
                        'budget_exhausted','capped_unconverged','final_normalized_gradient_norm',
                        'final_projected_gradient_norm','gradient_tolerance','relative_step','relative_tolerance') if k in history},
                    'original_result_tuple_object_preserved':True})
            except Exception as error:
                self.errors.append({'method':name,'type':type(error).__name__,'message':str(error)})
            return result
        return wrapped

    def finish(self,result):
        p=self.output/'actual-returned-inner-block-states.npz'
        with p.open('xb') as stream:np.savez_compressed(stream,**self.arrays)
        hist=None if result is None else result['history'].get(self.scheme)
        expected=None if hist is None else len(hist['blocks'])
        expected_counts=None if expected is None else {'update_w':expected,'update_theta':expected if self.with_ris else 0,'update_rotation':expected}
        complete=None if expected_counts is None else not self.errors and all(self.counts.get(k,0)==v for k,v in expected_counts.items())
        value={'schema':'actual-passive-applicable-returned-block-state-single-scheme-v1','scheme':self.scheme,
            'with_RIS':self.with_ris,'rows':self.rows,'counts':self.counts,'expected_counts':expected_counts,
            'expected_completed_outer_blocks':expected,'capture_errors':self.errors,
            'all_completed_outer_blocks_have_applicable_saved_returns':complete,
            'failed_scheme_partial_actual_returns_retained':hist is None,
            'absent_NoRIS_RCG_returns_not_fabricated':True,'arrays_file':p.name,
            'arrays_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'no_model_gradient_MC_RNG_or_extra_trial_calls':True,'independent_scientific_PASS':False}
        with (self.output/'actual-returned-inner-block-states.json').open('x',encoding='utf8',newline='\n') as f:
            json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
        return value
