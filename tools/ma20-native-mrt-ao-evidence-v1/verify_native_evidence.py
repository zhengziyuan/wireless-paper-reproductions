"""Review eight saved MATLAB MRT segments; never run an optimizer or MC.

The prior Python bundle is a separate published artifact. Numerical checks
are binary64 evaluations and are not interval or historical identity proofs.
"""
import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

def need(ok,message):
    if not ok:raise ValueError(message)

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

class Bytes:
    def __init__(self,value):self.value=value
    def read_bytes(self):return self.value

def check_record(rec,before,after,previous_after,first,tolerance,sweep_end):
    vals=(rec['before'],rec['after'],rec['surrogate'],rec['lower_bound_gap'])
    need(all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in vals),'finite record')
    if first:need(math.isclose(before['sweep_start'],rec['before'],rel_tol=1e-12,abs_tol=1e-12),'initial objective binding')
    if previous_after is not None:
        need(math.isclose(previous_after,rec['before'],rel_tol=1e-12,abs_tol=1e-12),'coordinate objective continuity')
    need(math.isclose(rec['lower_bound_gap'],rec['after']-rec['surrogate'],rel_tol=1e-12,abs_tol=1e-12),'saved surrogate gap')
    need(rec['solver_status']=='certified_global_2d' and rec['original_subproblem_unchanged'] is True,'native coordinate record')
    need(rec['after']>=rec['surrogate']-tolerance and rec['after']>=rec['before']-tolerance,'record acceptance')
    cert=rec['certificate'];bounds=[cert[k] for k in ('maximum_normalized_constraint_violation',
        'normalized_constraint_tolerance','global_objective_gap_upper_bound','global_objective_gap_tolerance')]
    need(all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in bounds),'finite nonnegative saved certificate bounds')
    need(cert['maximum_normalized_constraint_violation']<=cert['normalized_constraint_tolerance']
        and cert['global_objective_gap_upper_bound']<=cert['global_objective_gap_tolerance'],'saved certificate bounds')
    if sweep_end:need(math.isclose(after['sweep_start'],rec['after'],rel_tol=1e-12,abs_tol=1e-12),
                      'sweep boundary objective binding')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--repo',type=Path,required=True);args=ap.parse_args();repo=args.repo.resolve()
    with gzip.open(args.bundle,'rb') as stream:raw=stream.read(2*1024*1024+1)
    need(len(raw)<=2*1024*1024,'bundle cap');bundle=json.loads(raw)
    need(bundle.get('schema')=='MA20_NATIVE_MRT_EIGHT_SEGMENTS_EVIDENCE_V1','bundle schema')
    python_dir=repo/'tools/ma20-mrt-recovered-evidence-v1'
    with gzip.open(python_dir/'recorded_ao_bundle.json.gz','rb') as stream:python_bundle=json.load(stream)
    for name,pin in bundle['python_source_sha256'].items():
        source=(repo/'strict/two-timescale-ma'/name).read_bytes()
        need(len(source)<=131072 and hashlib.sha256(source).hexdigest()==pin,'Python source binding')
    sys.path.insert(0,str(repo/'strict/two-timescale-ma'));import numpy as np
    import core,run
    pyreader=load_module(python_dir/'replay_bundle.py','_native_evidence_python_reader')
    reader=load_module(Path(__file__).with_name('read_native_events.py'),'_native_evidence_event_reader')
    init=python_bundle['first_start'];epoch=init['epoch_SHA256']
    rows1,digest=pyreader.read_frames(base64.b64decode(python_bundle['first_frames_base64'],validate=True),
        epoch,init['next_sequence'],init['previous_SHA256'])
    rows2,_=pyreader.read_frames(base64.b64decode(python_bundle['second_frames_base64'],validate=True),
        epoch,len(rows1),digest)
    pyrows=rows1+rows2;need(len(pyrows)==234,'Python frame count')
    job=python_bundle['job_theory_only'];config=python_bundle['config']
    need(bundle['job_theory_only']==job and bundle['config']==config,'theory inputs')
    model,initial=run.scenario(config,job['N'],job['M'],job['kappa'],job['power'],job['A'],job['geometry'])
    model['region_lower']=job['region_lower'];model['region_upper']=job['region_upper']
    threshold=config['fractional_increase_threshold'];tol=config['verification_tolerance']
    need(job['N']==6 and job['M']==5 and config['maximum_AO_iterations']==10000,'original dimensions/budget')
    previous=None;all_events=[];stops=[];negative=0;min_spacing=float('inf');min_margin=float('inf')
    max_pos=0.;max_cross_obj=0.;max_native_formula=0.;last_sweep=0
    need(len(bundle['segments'])==8,'eight segments')
    for index,segment in enumerate(bundle['segments'],1):
        need(segment['segment']==index,'segment order');term=segment['terminal'];stage=term['stage']
        need(term['failure'] is None and stage['reason']=='natural_exit' and stage['returncode']==0
            and stage['errors']==[] and term['scientific_acceptance'] is False,'guard terminal')
        raw_events=base64.b64decode(segment['events_base64'],validate=True)
        decoded=reader.read_segment(Bytes(raw_events),previous,threshold)
        need(not decoded['partial_tail_preserved'] and decoded['committed_events']==term['committed_events'],
            'complete event stream')
        if previous is None:
            need(np.array_equal(np.asarray(decoded['first_state']['t']),np.asarray(initial)), 'initial layout')
        need(decoded['last_state']==segment['summary']['state'],'segment checkpoint')
        previous=decoded['last_state'];all_events.extend(json.loads(line) for line in raw_events.splitlines())
    need(len(all_events)==234 and previous['done'] and previous['sweep']==39,'native stop state')
    previous_after=None
    for i,(event,pyrow) in enumerate(zip(all_events,pyrows)):
        before,after,rec=event['input'],event['output'],event['record']
        x=np.asarray(after['t'],dtype=float);y=np.asarray(pyrow['state']['positions'],dtype=float)
        max_pos=max(max_pos,float(np.max(np.abs(x-y))))
        pyrec=pyrow['event']['record']
        max_cross_obj=max(max_cross_obj,abs(float(rec['before'])-float(pyrec['before'])),
                          abs(float(rec['after'])-float(pyrec['after'])))
        for state,key in ((before,'before'),(after,'after')):
            val=float(core.mrt_statistics(np.asarray(state['t']),model)[0]);saved=float(rec[key])
            need(math.isfinite(val) and math.isfinite(saved),'finite independently evaluated objective')
            max_native_formula=max(max_native_formula,abs(val-saved))
            pos=np.asarray(state['t']);delta=pos[:,None,:]-pos[None,:,:]
            distance=np.sqrt(np.sum(delta*delta,axis=2));distance+=np.eye(6)*1e9
            min_spacing=min(min_spacing,float(np.min(distance)))
            lo=np.asarray(job['region_lower']);hi=np.asarray(job['region_upper'])
            min_margin=min(min_margin,float(np.min(pos-lo)),float(np.min(hi-pos)))
        check_record(rec,before,after,previous_after,i==0,tol,event['sweep_relative_change']!=[])
        previous_after=rec['after']
        if event['sweep_relative_change']!=[]:
            last_sweep+=1;relative=float(event['sweep_relative_change']);negative+=int(relative<0)
            if relative<threshold:stops.append(last_sweep)
    need(stops==[39] and negative==0,'first stop or negative changes')
    need(min_spacing>=.5-tol and min_margin>=-tol,'saved geometric feasibility at tolerance')
    need(max_pos<=1e-10 and max_cross_obj<=1e-10 and max_native_formula<=1e-10,'binary64 comparison')
    print(json.dumps({'native_segments':8,'native_updates':234,'sweeps':last_sweep,'first_stop':stops[0],
        'negative_sweep_changes':negative,'max_position_difference':max_pos,'max_cross_objective_difference':max_cross_obj,
        'max_python_formula_difference':max_native_formula,'minimum_spacing':min_spacing,'minimum_box_margin':min_margin,
        'historical_producer_reauthenticated':False,'optimizer_rerun':False,'full_figure_or_paper_pass':False},separators=(',',':')))

if __name__=='__main__':main()
