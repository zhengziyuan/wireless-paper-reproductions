"""Passive scalar observation of the actual original RCG line search only."""
from pathlib import Path
import json

class PassiveRCGSeedTrace:
    def __init__(self,source):
        self.source=str(Path(source));self.lines=Path(source).read_text().splitlines()
        self.blocks=[];self.active={}
    def trace(self,frame,event,arg):
        if frame.f_code.co_filename!=self.source or frame.f_code.co_name!='update_theta':return None
        key=id(frame);v=frame.f_locals
        if event=='call':
            row=dict(block=len(self.blocks),iterations=[],actual_original_function_returned=False)
            self.blocks.append(row);self.active[key]=row
        elif event=='line':
            row=self.active[key];line=self.lines[frame.f_lineno-1].strip()
            if line.startswith('for _ in range(spec["maximum_backtracks"])'):
                it=int(v['iteration'])
                if len(row['iterations'])<=it:
                    row['iterations'].append(dict(iteration=it,initial_trial_seed=float(v['alpha']),accepted_alpha=None,actual_trials=0,utility=float(v['metric']['utility']),gradient_norm=float(v['checked_gradient'])))
            if line.startswith('if value>='):
                record=row['iterations'][int(v['iteration'])];record['actual_trials']+=1
                if v['value']>=v['metric']['utility']+v['spec']['armijo']*v['alpha']*v['slope']:
                    record.update(accepted_alpha=float(v['alpha']),accepted_utility=float(v['value']))
        elif event=='return':
            row=self.active.pop(key)
            if arg is not None:
                row.update(actual_original_function_returned=True,returned_flags={k:arg[1][k] for k in ('converged','termination_reason','iterations','updates','iteration_budget','final_normalized_gradient_norm','gradient_tolerance')})
        return self.trace
    def finish(self,output):
        report=dict(schema='actual-case014-original-RCG-growing-seed-passive-line-search-scalars-v1',blocks=self.blocks,unreturned_observed_frames=len(self.active),
            actual_seed_policy='Each block initial_step1; subsequent seed=2*previous accepted alpha, unchanged original Armijo/backtracking.',
            no_objective_gradient_RNG_or_trial_evaluation_by_observer=True,full_convergence_or_paper_PASS=False)
        with (Path(output)/'passive-RCG-actual-seeds-and-accepted-steps.json').open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
        return report
