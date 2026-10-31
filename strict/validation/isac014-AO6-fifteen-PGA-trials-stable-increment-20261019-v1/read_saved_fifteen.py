"""Portable saved15 inspection and optional same-input binary64 replay.

No MP oracle, optimizer, line search, step choice, MC or RNG is called. Replay
evaluates the unchanged arithmetic provider only at the fifteen saved r1 values.
"""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,struct,sys,traceback

def digest(raw):return hashlib.sha256(raw).hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def same(a,b):return a.dtype==b.dtype and a.shape==b.shape and a.tobytes(order='F')==b.tobytes(order='F')
def floatbits(v):return struct.pack('>d',float(v))
def main(args):
    root=Path(__file__).resolve().parent;out=args.output_dir.resolve()
    need(out!=root and root not in out.parents and not out.exists(),'Fresh outside-public output required')
    out.mkdir(parents=True)
    report=dict(schema='portable-only-actual-AO6-fifteen-saved-trials-v1',errors=[],trials=[],
        fresh_MP_or_optimizer_line_search_newtrial_MC_RNG_calls=0,
        existing_MP_results_inspected_not_recomputed=True,
        full_trajectory_strict_stationarity_native_reference_or_paper_PASS=False)
    expected={};before={};code=1
    try:
        manifest_raw=(root/'input-manifest.json').read_bytes();manifest=json.loads(manifest_raw)
        expected={p:v['SHA256'] for p,v in manifest['files'].items()};expected['input-manifest.json']=digest(manifest_raw)
        blobs={p:(root/p).read_bytes() for p in expected};before={p:digest(v) for p,v in blobs.items()}
        need(before==expected,'Frozen mathematical input/code manifest differs')
        for p,row in manifest['files'].items():need(len(blobs[p])==row['bytes'],'Frozen byte length differs')
        def data(p):return json.loads(gzip.decompress(blobs[p])) if p.endswith('.gz') else json.loads(blobs[p])
        binding=data('inputs/fixed-input-bindings.json');meta=data('inputs/captured-prefix-and-fifteen.json.gz')
        scene=data('inputs/original-scenario.json');mp=data('inputs/actual-MP80-MP100.json.gz')
        stable=data('inputs/actual-stable-fifteen-versus-MP.json.gz')
        need(meta['diagnostic_capture_pass'] is True and meta['all6_original_blocks_scalar_history_IEEE64_equal'] is True
             and meta['source_and_input_interval_closed'] is True and meta['actual_error'] is None,'Original passive capture not closed')
        need(meta['array_SHA256']==digest(blobs['inputs/actual-operands.npz'])==binding['original_operands_NPZ_SHA256'],'Exact original NPZ identity differs')
        need(mp['source_input_interval_closed'] is True and mp['crossprecision_pass'] is True and stable['source_input_interval_closed'] is True,'Original MP/stable source closure unavailable')
        need(mp['source_and_inputs_before'][binding['logical_original_NPZ_source_key']]==meta['array_SHA256'],'MP report not bound to this actual NPZ')
        need(stable['MP80_MP100_closed_report']['SHA256']==binding['original_MP_report_SHA256'],'Stable report not bound to same MP80/100 report')
        need(len(meta['actual_trials'])==15 and stable['actual_trial_count']==15,'Exactly fifteen actual trials required')
        import numpy as np
        import io
        with np.load(io.BytesIO(blobs['inputs/actual-operands.npz']),allow_pickle=False) as z:arrays={key:z[key] for key in z.files}
        inventory=binding['original_NPZ_NPY_header_inventory']
        need(set(arrays)==set(inventory),'Actual array key set differs')
        for key,a in arrays.items():
            v=inventory[key];need(a.dtype.str==v['dtype_descriptor'] and list(a.shape)==v['shape'],'Actual dtype/shape differs')
            need(bool(a.flags.f_contiguous) if v['fortran_order'] else bool(a.flags.c_contiguous),'Original stored memory-order schema differs')
            need(a.dtype.kind in 'fc' and bool(np.isfinite(a).all()),'Nonfinite or unsupported actual operand')
        ctx=meta['actual_context'];inc=meta['incumbent_actual_evaluation']
        w=arrays[ctx['w']];theta=arrays[ctx['theta']];r0=arrays[ctx['r']];iota=ctx['iota']
        need(same(w,arrays[inc['w']]) and same(theta,arrays[inc['theta']]) and same(r0,arrays[inc['r']]),'Actual incumbent arrays differ')
        truth=mp['precision_lanes']['100']['trials'];old=stable['trials']
        need(len(truth)==len(old)==15,'Existing actual trial reports differ')
        core=candidate=None
        if args.replay_stable:
            core=load(root/'sources/core_original_case014_v1.py','_original_response_provider_no_optimizer')
            candidate=load(root/'sources/stable_rotation_increment_v1.py','_unchanged_saved_increment_provider')
        for t,q,s in zip(meta['actual_trials'],truth,old):
            need(t['index']==q['index']==s['index'],'Actual trial order differs')
            ev=t['actual_evaluation'];need(same(w,arrays[ev['w']]) and same(theta,arrays[ev['theta']])
                and floatbits(ev['iota'])==floatbits(iota),'W/theta/iota changed across actual pair')
            need(same(r0+arrays[t['delta']],arrays[ev['r']]),'Saved actual trial not represented original displacement')
            row=dict(index=t['index'],original_branch=t['actual_original_decision'],actual_endpoint_and_fixed_input_identity=True,
                existing_MP100_fullphysical_increment=q['physical_increment'],
                existing_MP100_fullphysical_margin=q['fullphysical_margin_source_gradient'],
                existing_fullphysical_false_rejection=q['original_false_rejection_fullphysical'],
                existing_frozen_channel_false_rejection=q['original_false_rejection_frozen_channel'],
                existing_stable_absolute_error=s['absolute_increment_error'],
                existing_stable_relative_error=s['relative_increment_error'],binary64_candidate_replayed=False)
            if args.replay_stable:
                result=candidate.utility_increment(core,w,theta,r0,arrays[ev['r']],scene,iota)
                fields={'utility_increment':'stable_increment','rate_increment':'stable_rate_increment','nmse_increment':'stable_nmse_increment'}
                need(all(floatbits(result[a])==floatbits(s[b]) for a,b in fields.items()),'Candidate binary64 outputs differ from actual saved15 comparison')
                row.update(binary64_candidate_replayed=True,all_three_candidate_scalar_IEEE64_values_exact=True,
                           existing_MP100_decision=s['MP100_accepts_same_Armijo'],existing_stable_decision=s['stable_accepts_same_Armijo'])
            report['trials'].append(row)
        report.update(actual_trial_count=15,original_rejected=sum(t['actual_original_decision']!='accepted_original_branch' for t in meta['actual_trials']),
            original_accepted=sum(t['actual_original_decision']=='accepted_original_branch' for t in meta['actual_trials']),
            existing_fullphysical_false_rejections=sum(q['original_false_rejection_fullphysical'] for q in truth),
            existing_frozen_channel_false_rejections=sum(q['original_false_rejection_frozen_channel'] for q in truth),
            existing_stable15_matches_MP100=stable['all_fifteen_candidate_Armijo_decisions_match_existing_MP100'],
            existing_maximum_absolute_increment_error=stable['maximum_absolute_increment_error'],
            existing_maximum_relative_increment_error=stable['maximum_relative_increment_error'],
            existing_strict_fullphysical_PG_pass=mp['fullphysics_strict_PG_pass'],
            existing_fullphysical_projected_gradient_norm=mp['precision_lanes']['100']['fullphysical_projected_gradient_norm'],
            all_actual_arrays_dtype_shape_order_and_original_NPZ_bits_bound=True,
            original_reports_source_bound_and_actual_fifteen_input_identity_pass=True,
            all_fifteen_binary64_candidate_values_reproduced=(True if args.replay_stable else None))
        code=0
    except BaseException as error:report['errors'].append(dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
    finally:
        after={}
        for p in expected:
            try:after[p]=digest((root/p).read_bytes())
            except OSError as error:report['errors'].append(dict(source=p,type=type(error).__name__,message=str(error)))
        report.update(source_input_before=before,source_input_after=after,source_input_interval_closed=bool(expected) and before==after==expected)
        if not report['source_input_interval_closed']:code=1
        report['actual_reader_exit_code']=code
        report['scope']='Only captured actual15 input/unchanged binary64 arithmetic versus stored closed MP results. No new MP oracle or trajectory convergence.'
        (out/'ACTUAL_PORTABLE_FIXED_FIFTEEN_INPUT_AND_BINARY64_REPLAY_V1.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(exit_code=code,actual_trial_count=len(report['trials']),binary64_replay=bool(args.replay_stable),fresh_MP_calls=0,full_trajectory_PASS=False)))
    return code
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--replay-stable',action='store_true')
    raise SystemExit(main(p.parse_args()))
