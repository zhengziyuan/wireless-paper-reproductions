"""Copy original W/RCG/PGA returned states; no model/gradient/RNG calls."""
from pathlib import Path
import functools,hashlib,json
import numpy as np
class PassiveReturnedBlockStates:
    def __init__(self,output):
        self.output=Path(output);self.arrays={};self.rows=[];self.errors=[];self.counts={}
    def wrap(self,name,fn):
        @functools.wraps(fn)
        def wrapped(*args,**kwargs):
            result=fn(*args,**kwargs)
            try:
                # Exact unchanged original tuple object is returned after copying.
                w,theta,r,c,iota=args[:5]
                if name=='update_w':w=result[0]
                elif name=='update_theta':theta=result[0]
                elif name=='update_rotation':r=result[0]
                else:raise ValueError('Only three inner methods are eligible')
                self.counts[name]=self.counts.get(name,0)+1
                prefix=f'{name}_{self.counts[name]:03d}';keys={}
                for key,value in [('W',w),('theta',theta),('r',r)]:
                    npzkey=prefix+'__'+key;self.arrays[npzkey]=np.array(value,copy=True);keys[key]=npzkey
                history=result[1]
                self.rows.append({'method':name,'call':self.counts[name],'fixed_iota':float(iota),'arrays':keys,
                    'actual_returned_flags':{k:history[k]for k in ('applicable','converged','termination_reason','iterations','updates','iteration_budget','budget_exhausted','capped_unconverged')if k in history},
                    'original_result_tuple_object_preserved':True})
            except Exception as error:
                self.errors.append({'method':name,'type':type(error).__name__,'message':str(error)})
            return result
        return wrapped
    def finish(self,result):
        p=self.output/'actual-returned-inner-block-states.npz'
        with p.open('xb')as stream:np.savez_compressed(stream,**self.arrays)
        expected=None if result is None else len(result['history']['Rot-BS & Rot-RIS']['blocks'])
        complete=expected is not None and not self.errors and all(self.counts.get(k,0)==expected for k in ('update_w','update_theta','update_rotation'))
        value={'schema':'actual-passive-every-returned-inner-block-state-v1','rows':self.rows,'counts':self.counts,'expected_completed_outer_blocks':expected,
            'capture_errors':self.errors,'all_completed_blocks_have_three_saved_returned_states':complete,'arrays_file':p.name,
            'arrays_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'no_model_gradient_MC_RNG_or_extra_trial_calls':True,'scientific_PASS':False}
        with(self.output/'actual-returned-inner-block-states.json').open('x',encoding='utf8',newline='\n')as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
        return value
