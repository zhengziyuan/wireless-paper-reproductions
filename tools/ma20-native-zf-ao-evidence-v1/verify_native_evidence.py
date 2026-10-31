"""Replay saved MATLAB ZF and conditional Python donor; no optimizer/MC run.

Checks are binary64 and conditioned on reconstructed single-coordinate
order and the current Python model. They are not interval certificates.
"""
import argparse
import base64
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys


def need(ok, message):
    if not ok: raise ValueError(message)


class Bytes:
    def __init__(self, raw): self.raw = raw
    def read_bytes(self): return self.raw


def check_record(rec, before, after, previous_after, first, tolerance, sweep_end):
    vals=(rec['before'], rec['after'], rec['surrogate'], rec['lower_bound_gap'])
    need(all(type(v) in (int,float) and math.isfinite(v) for v in vals), 'finite record')
    if first: need(math.isclose(before['sweep_start'],rec['before'],rel_tol=1e-12,abs_tol=1e-12), 'initial objective')
    if previous_after is not None:
        need(math.isclose(previous_after,rec['before'],rel_tol=1e-12,abs_tol=1e-12), 'objective continuity')
    need(math.isclose(rec['lower_bound_gap'],rec['after']-rec['surrogate'],rel_tol=1e-12,abs_tol=1e-12), 'minorant gap')
    need(rec['solver_status']=='certified_global_2d' and rec['original_subproblem_unchanged'] is True, 'solver record')
    need(rec['after']>=rec['surrogate']-tolerance and rec['after']>=rec['before']-tolerance, 'source acceptance')
    cert=rec['certificate'];bounds=[cert[k] for k in ('maximum_normalized_constraint_violation',
        'normalized_constraint_tolerance','global_objective_gap_upper_bound','global_objective_gap_tolerance')]
    need(all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in bounds), 'finite certificate values')
    need(bounds[0]<=bounds[1] and bounds[2]<=bounds[3], 'saved certificate limits')
    if sweep_end: need(math.isclose(after['sweep_start'],rec['after'],rel_tol=1e-12,abs_tol=1e-12), 'sweep objective')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--repo',type=Path,required=True);args=ap.parse_args();repo=args.repo.resolve()
    with gzip.open(args.bundle,'rb') as f: raw=f.read(2*1024*1024+1)
    need(len(raw)<=2*1024*1024,'bundle cap');bundle=json.loads(raw)
    need(bundle.get('schema')=='MA20_NATIVE_ZF_SEVEN_SEGMENTS_EVIDENCE_V1','bundle schema')
    for name,pin in bundle['python_source_sha256'].items():
        source=(repo/'strict/two-timescale-ma'/name).read_bytes()
        need(len(source)<=131072 and hashlib.sha256(source).hexdigest()==pin,'Python source pin')
    sys.path.insert(0,str(repo/'strict/two-timescale-ma'));import numpy as np
    import core,run
    from read_native_events import read_segment
    job=bundle['job_theory_only'];config=bundle['config'];donor=bundle['python_zf_history']
    need(job['N']==6 and job['M']==5 and config['maximum_AO_iterations']==10000,'original budget')
    model,initial=run.scenario(config,job['N'],job['M'],job['kappa'],job['power'],job['A'],job['geometry'])
    model['region_lower']=job['region_lower'];model['region_upper']=job['region_upper']
    threshold=config['fractional_increase_threshold'];tol=config['verification_tolerance']
    pypos=np.asarray(donor['positions'],dtype=float);pyobj=np.asarray(donor['objective'],dtype=float)
    pyrecords=donor['coordinate_updates']
    need(pypos.shape==(34,6,2) and pyobj.shape==(34,) and len(pyrecords)==198,'donor history shape')
    need(np.all(np.isfinite(pypos)) and np.all(np.isfinite(pyobj)),'finite donor')
    need(np.array_equal(pypos[0],np.asarray(initial)) and donor['converged'] is True
         and donor['termination']=='fractional_increase','donor initial and stop labels')
    failed=bundle['first_attempt_failure'];fst=failed['stage']
    need(fst['reason']=='monitor_error' and failed['committed_events']==0
         and failed['scientific_acceptance'] is False,'first zero-event failure')
    need(len(bundle['segments'])==7,'seven segments')
    previous=None;events=[];peak=0
    for index,segment in enumerate(bundle['segments'],1):
        need(segment['segment']==index,'segment ordering');term=segment['terminal'];stage=term['stage']
        need(term['failure'] is None and stage['reason']=='natural_exit' and stage['returncode']==0
             and stage['errors']==[] and term['scientific_acceptance'] is False,'native terminal')
        need(term.get('ending_edge_identity_verified') is True,'held-input edge check')
        peak=max(peak,int(stage['peak_bytes']))
        data=base64.b64decode(segment['events_base64'],validate=True)
        decoded=read_segment(Bytes(data),previous,threshold)
        need(not decoded['partial_tail_preserved'] and decoded['committed_events']==term['committed_events'], 'complete event stream')
        if previous is None:
            need(np.array_equal(np.asarray(decoded['first_state']['t']),np.asarray(initial)), 'native initial')
        need(decoded['last_state']==segment['summary']['state'], 'segment checkpoint')
        previous=decoded['last_state'];events.extend(json.loads(line) for line in data.splitlines())
    need(len(events)==198 and previous['done'] and previous['sweep']==33, 'native termination')
    previous_after=None;stops=[];negative=0;min_spacing=float('inf');min_margin=float('inf')
    max_pos=0.;max_cross_obj=0.;max_native_formula=0.;last_sweep=0
    for i,event in enumerate(events):
        before,after,rec=event['input'],event['output'],event['record']
        sweep,antenna=divmod(i,6);pyrec=pyrecords[i]
        need(pyrec['sweep']==sweep and pyrec['antenna']==antenna,'donor recorded order')
        # Donor stores sweep boundaries, so intermediate positions require
        # the documented single-coordinate-in-order reconstruction.
        pyafter=pypos[sweep].copy();pyafter[:antenna+1]=pypos[sweep+1,:antenna+1]
        x=np.asarray(after['t'],dtype=float);max_pos=max(max_pos,float(np.max(np.abs(x-pyafter))))
        max_cross_obj=max(max_cross_obj,abs(float(rec['before'])-float(pyrec['before'])),
                          abs(float(rec['after'])-float(pyrec['after'])))
        for state,key in ((before,'before'),(after,'after')):
            val=float(core.zf_statistics(np.asarray(state['t']),model)[0]);saved=float(rec[key])
            need(math.isfinite(val) and math.isfinite(saved),'finite formula result')
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
    need(stops==[33] and negative==0,'native first stop or negative increment')
    need(np.all(pyobj[:-1]!=0),'donor stop denominator')
    donor_rel=(pyobj[1:]-pyobj[:-1])/np.abs(pyobj[:-1])
    need(np.all(np.isfinite(donor_rel)) and np.all(donor_rel>=0)
         and np.flatnonzero(donor_rel<threshold).tolist()==[32],'donor first stop')
    need(min_spacing>=.5-tol and min_margin>=-tol,'saved geometric feasibility')
    need(max_pos<=1e-9 and max_cross_obj<=1e-9 and max_native_formula<=1e-9,'binary64 comparison')
    print(json.dumps({'native_segments':7,'native_updates':198,'sweeps':last_sweep,'first_stop':stops[0],
        'negative_sweep_changes':negative,'max_position_difference':max_pos,'max_cross_objective_difference':max_cross_obj,
        'max_python_formula_difference':max_native_formula,'minimum_spacing':min_spacing,'minimum_box_margin':min_margin,
        'peak_guard_observed_bytes':peak,'donor_intermediate_positions_reconstructed':True,
        'historical_producer_reauthenticated':False,'optimizer_rerun':False,'full_figure_or_paper_pass':False},separators=(',',':')))


if __name__=='__main__':main()
