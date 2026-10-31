"""Reuse only four actually closed calls of the stopped Fig19 g1 prefix."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,pickle,struct
def _base():
 p=Path(__file__).with_name('relevant_input_original_component_reuse_v1.py')
 s=importlib.util.spec_from_file_location('_MA_reuse_projection',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def load_ma_components_from_return_prefix(target_job,target_cfg,donor_record):
 """No original optimize/instantaneous call is executed; no tape is rebound."""
 h=_base();job=h.read_bound_json(donor_record['job']);cfg=h.read_bound_json(donor_record['config'])
 h.need(h.compare(job,cfg,target_job,target_cfg,'MA')['equal'],'Correct original geometry/region/MA/input controls required')
 binding=h.read_bound_json(donor_record['case_binding'])
 h.need(binding['input_fingerprint']==donor_record['input_fingerprint'],'Original full-cfg input identity')
 h.need(binding['original_runtime_implementation_fingerprint']==h.EXPECTED_PYTHON_IMPLEMENTATION,'Original source/runtime epoch')
 # Compile only the exact pure input-construction function, never import solver.
 source_identity=donor_record['scenario_source'];source=Path(source_identity['path']).read_bytes()
 h.need(hashlib.sha256(source).hexdigest()==source_identity['SHA256'],'Original run.py source bytes')
 text=source.decode();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='scenario')
 block=''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
 h.need(hashlib.sha256(block.encode()).hexdigest()==donor_record['scenario_definition_SHA256'],'Exact original pure input constructor')
 import numpy as np
 ns=dict(copy=copy,np=np);exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact-original-scenario-input-constructor>','exec'),ns)
 c,t=ns['scenario'](cfg,job['N'],job['M'],job['kappa'],job['power'],job['A'],job['geometry'])
 if 'region_lower' in job:c['region_lower']=job['region_lower'];c['region_upper']=job['region_upper']
 if 'initial_positions' in job:t=np.asarray(job['initial_positions'])
 nlos=np.asarray(job['nlos_re'])+1j*np.asarray(job['nlos_im'])
 actual_frames=[];p=Path(donor_record['tape']['path'])
 with p.open('rb') as stream:
  for i,expected in enumerate(donor_record['first_four_actual_return_frames']):
   stream.seek(expected['frame_offset']);header=stream.read(40)
   h.need(len(header)==40 and struct.unpack('>Q',header[:8])[0]==expected['body_bytes'],'Closed selected frame header')
   body=stream.read(expected['body_bytes'])
   h.need(hashlib.sha256(body).digest()==header[8:] and hashlib.sha256(body).hexdigest()==expected['body_SHA256'],'Closed selected original frame SHA before trusted local decoding')
   f=pickle.loads(body) # Only this source-bound, immutable local original tape.
   h.need(f['identity']==expected['identity'] and f['kind']=='original_return','Actual selected original returned call')
   if i<2:args=(t,c,'MRT' if i==0 else 'ZF')
   else:args=(actual_frames[i-2]['return'][0],c,nlos,'MRT' if i==2 else 'ZF')
   argsha=hashlib.sha256(pickle.dumps((args,{}),protocol=5)).hexdigest()
   h.need(argsha==f['identity']['exact_argument_pickle_SHA256'],'Exact original actual callable arguments/ordering before component reuse')
   h.need(f['identity']['ordinal']==i and f['identity']['name']==('optimize' if i<2 else 'instantaneous'),'Original first four call roles')
   actual_frames.append(f)
 payload={}
 for i,mode in enumerate(('mrt','zf')):
  pos,hist=actual_frames[i]['return'];perf=actual_frames[i+2]['return']
  h.need(type(hist['converged']) is bool and len(perf['sample_sum_rates'])==1000,'Complete original state/stop/performance return')
  payload[mode]=dict(positions=pos,realized_positions=pos.copy(),history=hist,actual_full1000_performance=perf)
 receipt=dict(schema='actual-only-four-closed-original-calls-component-adoption-v1',
   source_prefix_inventory=donor_record['inventory'],original_case_binding=donor_record['case_binding'],
   reused_actual_first_four_argument_SHA256=[f['identity']['exact_argument_pickle_SHA256'] for f in actual_frames],
   actual_all_four_saved_return_frames_and_exact_original_arguments_pass=True,
   original_whole_configuration_tape_not_rebound=True,old_MC_brute_search_not_statistical_optimum=True,
   complete_original_case_or_grid_claimed=False,original_failed_stop_flags_preserved=True,
   actual_new_optimizations_MC_rate_computations_RNG_calls=0,
   pure_original_scenario_data_constructor_only_called=True,
   original_performance_returns_not_recomputed=True)
 return payload,receipt
