"""New production hoist versus byte-preserved original, full W stops/states.

Not an all500-job run. Includes nonzero-RIS scalar-gradient probes on an
additional unchanged original input so a zero reflected derivative is not
misrepresented as a nontrivial test.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
import core
from diagnose_fixed_channel_cache import scalar_utility,SCHEMES
from isac_metadata import implementation_fingerprint,fingerprint
from execute_bank import atomic_json


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def main(snapshot,bank,output):
    manifest=json.loads((snapshot/"snapshot-manifest.json").read_text());old=module("preserved_isac_core",snapshot/"numeric-source"/"core.py")
    oldmeta=module("preserved_isac_metadata",snapshot/"numeric-source"/"isac_metadata.py")
    if oldmeta.implementation_fingerprint()!=manifest["original_implementation_fingerprint"]:raise ValueError("Preserved original code/runtime identity mismatch")
    for entry in manifest["snapshotted_files"]:
        p=snapshot/entry["snapshot_relative"]
        if hashlib.sha256(p.read_bytes()).hexdigest()!=entry["sha256"]:raise ValueError("Immutable old source/evidence changed")
    scene_bytes=(bank/"jobs"/"case-000-mc-000.json").read_bytes();config_bytes=(bank/"run_config.json").read_bytes();c=json.loads(scene_bytes)
    source=json.loads((bank/"case-000-mc-000-python.json").read_text())
    if not oldmeta.complete(source,fingerprint(config_bytes,scene_bytes)):raise ValueError("Actual preserved full six-scheme source result required")
    runs={};checks=[];began=time.perf_counter()
    for name in SCHEMES:
        cfg=copy.deepcopy(c);group="no_RIS" if "No-RIS" in name else "with_RIS"
        if group=="no_RIS":cfg["br_gain_re"]=[0.]*len(c["br_gain_re"]);cfg["br_gain_im"]=[0.]*len(c["br_gain_im"])
        saved=source["metrics"][name];w=np.asarray(saved["w_re"])+1j*np.asarray(saved["w_im"]);theta=np.asarray(saved["theta_re"])+1j*np.asarray(saved["theta_im"]);r=np.asarray(saved["rotation"])
        om,og=old.evaluate(w,theta,r,cfg,None,True);nm,ng=core.evaluate(w,theta,r,cfg,None,True)
        bundle=core.channels(theta,r,cfg);cm,cg=core.evaluate(w,theta,r,cfg,None,True,_fixed_channel_bundle=bundle)
        for key in om:
            if not np.array_equal(om[key],nm[key]) or not np.array_equal(om[key],cm[key]):raise RuntimeError("Original/cached/default physical metrics differ")
        if not all(np.array_equal(a,b) and np.array_equal(a,d) for a,b,d in zip(og,ng,cg)):raise RuntimeError("Original/cached/default gradients differ")
        if group not in runs:
            wi,ti,ri=old.initialize(cfg);iota=old.evaluate(wi,ti,ri,cfg)["iota"]
            clock=time.perf_counter();ow,oh=old.update_w(wi.copy(),ti,ri,cfg,iota);os=time.perf_counter()-clock
            clock=time.perf_counter();nw,nh=core.update_w(wi.copy(),ti,ri,cfg,iota);ns=time.perf_counter()-clock
            if not np.array_equal(ow,nw) or oh!=nh:raise RuntimeError("Original full W prefix/state/QCQP/stop gates changed")
            runs[group]={"original_W_budget":cfg["W_solver"]["maximum_iterations"],"iterations":oh["iterations"],"converged":oh["converged"],
                "objective":oh["objective"],"all_objectives_states_QCQP_and_stop_gates_bitwise_equal":True,
                "original_seconds":os,"new_production_seconds":ns,"speedup":os/ns}
        if runs[group]["objective"]!=source["history"][name]["blocks"][0]["W"]["objective"]:raise RuntimeError("Preserved actual full W history does not match")
        checks.append({"scheme":name,"original_saved_final_metrics_and_all_gradients_bitwise_equal":True,
            "full_original_initial_W_prefix_and_stops_bitwise_equal":True,"W_group":group})
        print(json.dumps({"scheme":name,"production_equivalence_verified":True,"speedup":runs[group]["speedup"]}),flush=True)
    # An ORIGINAL exported scene with active BS-RIS geometry at the original
    # zero angles. It is not a different/reduced channel or an optimized figure.
    active=None;active_path=None
    for path in sorted((bank/"jobs").glob("case-000-mc-*.json")):
        cfg=json.loads(path.read_text())
        if any(np.asarray(b)[2]>0 and np.asarray(r)[2]>0 for b,r in zip(cfg["br_directions"],cfg["rb_directions"])):
            active=cfg;active_path=path;break
    if active is None:raise ValueError("No active original scene available for nonzero-RIS gradient oracle")
    rng=np.random.default_rng(24604);active_checks=[]
    for name in SCHEMES:
        cfg=copy.deepcopy(active)
        if "No-RIS" in name:cfg["br_gain_re"]=[0.]*len(cfg["br_gain_re"]);cfg["br_gain_im"]=[0.]*len(cfg["br_gain_im"])
        w,theta,r=old.initialize(cfg);theta=np.exp(1j*rng.uniform(-np.pi,np.pi,len(theta)))
        w=(rng.normal(size=w.shape)+1j*rng.normal(size=w.shape));w*=np.sqrt(cfg["power"])/np.linalg.norm(w)
        om,og=old.evaluate(w,theta,r,cfg,None,True);cm,cg=core.evaluate(w,theta,r,cfg,None,True,_fixed_channel_bundle=core.channels(theta,r,cfg))
        if not all(np.array_equal(om[k],cm[k]) for k in om) or not all(np.array_equal(a,b) for a,b in zip(og,cg)):raise RuntimeError("Active original-scene cache arithmetic differs")
        dw=(rng.normal(size=w.shape)+1j*rng.normal(size=w.shape));dw/=np.linalg.norm(dw);phase=rng.normal(size=len(theta));phase/=np.linalg.norm(phase);dr=rng.normal(size=6);dr/=np.linalg.norm(dr)
        eps=1e-6;iota=om["iota"]
        fd=[(scalar_utility(w+eps*dw,theta,r,cfg,iota)-scalar_utility(w-eps*dw,theta,r,cfg,iota))/(2*eps),
            (scalar_utility(w,theta*np.exp(1j*eps*phase),r,cfg,iota)-scalar_utility(w,theta*np.exp(-1j*eps*phase),r,cfg,iota))/(2*eps),
            (scalar_utility(w,theta,r+eps*dr,cfg,iota)-scalar_utility(w,theta,r-eps*dr,cfg,iota))/(2*eps)]
        analytical=[float(np.real(np.vdot(og[0],dw))),float(np.real(np.vdot(og[1],1j*theta*phase))),float(og[2]@dr)]
        errors=[abs(a-b)/max(1,abs(a),abs(b)) for a,b in zip(analytical,fd)]
        if max(errors)>1e-5:raise RuntimeError("Nonzero-link independent scalar gradient oracle failed")
        norm=float(np.linalg.norm(og[1]));expected="No-RIS" not in name
        if expected and norm<=1e-10:raise RuntimeError("RIS-present active gradient unexpectedly trivial")
        active_checks.append({"scheme":name,"original_full4_36_66_geometry_preserved":True,"RIS_gradient_norm":norm,
            "RIS_gradient_expected_nonzero":expected,"original_and_cached_gradients_bitwise_equal":True,
            "scalar_directional_gradient_relative_errors_W_RIS_rotation":errors,
            "probe_is_feasible_diagnostic_state_not_an_optimized_figure_result":True})
    result={"paper_id":"rotatable-isac","scope":"new_production_fixed_channel_hoist_vs_immutable_original_full_dimension_test_not_full_bank",
        "original_implementation_fingerprint":oldmeta.implementation_fingerprint(),"new_implementation_fingerprint":implementation_fingerprint(),
        "all_six_saved_scheme_states_and_full_W_runs_verified":True,"source_scene_sha256":hashlib.sha256(scene_bytes).hexdigest(),
        "active_original_input_filename":active_path.name,"active_original_input_sha256":hashlib.sha256(active_path.read_bytes()).hexdigest(),
        "full_original_W_runs":runs,"scheme_checks":checks,"active_link_scalar_gradient_checks":active_checks,
        "new_full500_job_bank_or_figures_completed":False,"elapsed_seconds":time.perf_counter()-began}
    output.parent.mkdir(parents=True,exist_ok=True);atomic_json(output,result);print(json.dumps({"all_six_schemes_verified":True,"new_implementation_fingerprint":result["new_implementation_fingerprint"]}))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--snapshot",type=Path,required=True);p.add_argument("--bank",type=Path,required=True);p.add_argument("--output",type=Path,required=True);args=p.parse_args();main(args.snapshot,args.bank,args.output)
