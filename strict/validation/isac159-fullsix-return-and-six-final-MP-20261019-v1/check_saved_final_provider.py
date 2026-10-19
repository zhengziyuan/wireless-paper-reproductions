"""Portable first use of the actual saved-state provider, not a new optimization."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from equivalent_runtime_case159_v1 import load_core
HERE=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError('Preserve prior checks')
 m=json.loads((HERE/'SOURCE_MANIFEST_V1.json').read_bytes())
 before={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in m['source_SHA256']}
 assert before==m['source_SHA256']
 fixture=json.loads((HERE/'six-final-state-fixture.json').read_bytes());scene=json.loads((HERE/'original-scenario.json').read_bytes())
 assert len(fixture['metrics'])==6 and fixture['original_full_converged']==4 and fixture['actual_entry_exit_code']==2
 model=load_core();rows=[]
 for name,state in fixture['metrics'].items():
  own=copy.deepcopy(scene)
  if 'No-RIS' in name:
   own['br_gain_re']=[0.]*len(own['br_gain_re']);own['br_gain_im']=[0.]*len(own['br_gain_im'])
  w=np.asarray(state['w_re'])+1j*np.asarray(state['w_im']);theta=np.asarray(state['theta_re'])+1j*np.asarray(state['theta_im'])
  got=model.evaluate(w,theta,np.asarray(state['rotation']),own)
  fields={}
  for key in ('utility','rate','nmse','iota','sinr','pattern'):
   x=np.asarray(got[key]);y=np.asarray(state[key]);assert x.shape==y.shape
   err=abs(x-y);bound=scene['verification_tolerance']+(1e-10*abs(y) if key in ('iota','sinr') else 0)
   fields[key]={'maximum_absolute_error':float(np.max(err)),'pass':bool(np.all(err<=bound))}
  rows.append({'scheme':name,'fields':fields,'pass':all(v['pass'] for v in fields.values())})
 after={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in m['source_SHA256']}
 result={'rows':rows,'source_interval_unchanged':before==after,'all_six_saved_provider_comparisons_pass':before==after and all(x['pass'] for x in rows),'original_execution_exit':2,'original_full_converged':4,'optimization_MC_MP_calls':0,'new_independent_physics_dual_or_convergence_PASS':False}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'all_six_saved_provider_comparisons_pass':result['all_six_saved_provider_comparisons_pass']}))
 return 0 if result['all_six_saved_provider_comparisons_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
