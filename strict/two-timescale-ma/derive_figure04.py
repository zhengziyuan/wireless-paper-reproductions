"""Full Fig4 from an exactly source-matched, completed full Fig3 bank.

Fig3 already runs BOTH original independent MRT/ZF position optimizers and
all5 benchmarks. Fig4 differs only in which accepted trajectory's MC history
is evaluated. Reuse that executed ZF trajectory, then freshly evaluate EVERY
accepted position with the SAME complete1000 NLoS draws. No reduced bank.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from core import instantaneous
from execute_bank import atomic_json
from figures import cases,make_job
from ma_metadata import bank_complete,complete,fingerprint,implementation_fingerprint
from render_figures import terminal_hold_mean,render
from run import scenario


def job_bytes(case,config,realization):
    return (json.dumps(make_job(case,config,realization),separators=(",",":"))+"\n").encode("utf-8")


def verify_source(bank):
    config_bytes=(bank/"run_config.json").read_bytes();config=json.loads(config_bytes)
    manifest_bytes=(bank/"manifest.json").read_bytes();manifest=json.loads(manifest_bytes)
    plan=json.loads((bank/"plan.json").read_text())
    source_cases=cases(config,3);target_cases=cases(config,4)
    if (plan.get("figure")!=3 or plan.get("cases")!=source_cases or manifest.get("expected_jobs")!=200
        or config.get("geometry_realizations")!=100 or config.get("nlos_realizations_per_geometry")!=1000
        or not bank_complete(bank/"jobs",manifest,config_bytes)):
        raise ValueError("Exact original completed2-case full200-job Fig3 bank required")
    for source,target in zip(source_cases,target_cases):
        if {k:v for k,v in source.items() if k!="figure"}!={k:v for k,v in target.items() if k!="figure"}:
            raise ValueError("Source/target original scenario contracts differ")
    records=[];missing=[];invalid=[]
    for entry in manifest["files"]:
        input_bytes=(bank/"jobs"/entry["filename"]).read_bytes();index=entry["case_index"];r=entry["realization"]
        if input_bytes!=job_bytes(source_cases[index],config,r):
            raise ValueError("Source exported inputs do not exactly regenerate from their original immutable configuration")
        target_bytes=job_bytes(target_cases[index],config,r)
        source_job=json.loads(input_bytes);target_job=json.loads(target_bytes)
        if {k:v for k,v in source_job.items() if k!="figure"}!={k:v for k,v in target_job.items() if k!="figure"}:
            raise ValueError("All positions, geometry and1000 random draws must be exactly identical")
        result_path=bank/(Path(entry["filename"]).stem+"-python.json")
        if not result_path.exists():missing.append(result_path.name);continue
        try:result_bytes=result_path.read_bytes();result=json.loads(result_bytes)
        except (OSError,ValueError):invalid.append(result_path.name);continue
        if not complete(result,entry["input_fingerprint"],source_job,config):invalid.append(result_path.name);continue
        records.append((entry,source_job,result,result_bytes,target_bytes))
    ready=not missing and not invalid and len(records)==200
    receipt={"paper_id":"two-timescale-ma","figure":4,"source_figure":3,"full_execution_verified":ready,
        "derivation":"source-matched full Fig3 bank's independently optimized ZF trajectory plus fresh full1000 MC history",
        "source_full_geometry_jobs_required":200,"source_full_geometry_jobs_verified":len(records),
        "geometries_per_kappa":100,"nlos_per_geometry":1000,"input_bank_complete":True,
        "source_and_target_scenario_parameters_exactly_equal_except_figure_metadata":True,
        "all200_generated_job_inputs_match_original_immutable_config":True,
        "missing_source_results":missing,"invalid_or_nonconverged_source_results":invalid,
        "source_manifest_sha256":hashlib.sha256(manifest_bytes).hexdigest(),
        "source_config_sha256":hashlib.sha256(config_bytes).hexdigest(),
        "source_implementation_fingerprint":implementation_fingerprint(),
        "fresh_position_optimization_rerun":False,"original_ZF_algorithm_was_executed_for_all200_source_jobs":ready,
        "original_curve_closeness_verified":False}
    return receipt,config,config_bytes,source_cases,records


def derive(bank,output):
    output.mkdir(parents=True,exist_ok=True);receipt,config,config_bytes,source_cases,records=verify_source(bank)
    atomic_json(output/"source-readiness.json",receipt)
    if not receipt["full_execution_verified"]:return {"source_bank_ready":False,"figure_rendered":False,"verified_jobs":len(records)}
    began=time.perf_counter();engine_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    # The scalar history evaluator is fingerprinted through core.py and run.py;
    # this adapter's hash additionally binds the source-to-target derivation.
    by_case=[[] for _ in source_cases]
    for entry,job,result,result_bytes,target_bytes in records:
        path=output/(Path(entry["filename"]).stem+"-derived-figure04.json")
        source_hash=hashlib.sha256(result_bytes).hexdigest();positions=result["history"]["zf"]["positions"]
        target_input=fingerprint(config_bytes,target_bytes);cached=None
        if path.exists():
            try:cached=json.loads(path.read_text())
            except (OSError,ValueError):pass
        if (not cached or cached.get("source_result_sha256")!=source_hash or cached.get("derivation_source_sha256")!=engine_sha256
            or cached.get("target_input_fingerprint")!=target_input or len(cached.get("actual_full1000_MC_history",[]))!=len(positions)
            or not all(np.isfinite(cached.get("actual_full1000_MC_history",[])))):
            c,_=scenario(config,job["N"],job["M"],job["kappa"],job["power"],job["A"],job["geometry"])
            nlos=np.asarray(job["nlos_re"])+1j*np.asarray(job["nlos_im"])
            if nlos.shape!=(1000,6,5):raise ValueError("Original complete1000x6x5 ZF draw bank required")
            actual=[instantaneous(np.asarray(position),c,nlos,"ZF")["mean_sum_rate"] for position in positions]
            cached={"paper_id":"two-timescale-ma","figure":4,"source_figure":3,"case_index":entry["case_index"],
                "realization":entry["realization"],"kappa":job["kappa"],"source_input_fingerprint":entry["input_fingerprint"],
                "target_input_fingerprint":target_input,"source_result_sha256":source_hash,"derivation_source_sha256":engine_sha256,
                "source_implementation_fingerprint":implementation_fingerprint(),"original_ZF_accepted_positions_exactly_reused":True,
                "accepted_position_count":len(positions),"all1000_identical_NLoS_draws_freshly_evaluated_at_each_position":True,
                "nlos_per_position":1000,"actual_full1000_MC_history":actual,
                "statistical_objective_history":result["history"]["zf"]["objective"],
                "all_source_coordinate_certificates_prevalidated":True,"original_curve_closeness_verified":False}
            atomic_json(path,cached)
        by_case[entry["case_index"]].append(cached)
        print(json.dumps({"source_figure":3,"derived_figure":4,"completed_derivation_jobs":sum(map(len,by_case)),"required_jobs":200}),flush=True)
    if not all(len(items)==100 for items in by_case):raise RuntimeError("All100 source geometries per kappa required")
    series=[]
    for case,items in zip(source_cases,by_case):
        for key,label in [("statistical_objective_history","ZF original statistical bound"),("actual_full1000_MC_history","ZF actual MC sum rate")]:
            curve=terminal_hold_mean([item[key] for item in items])
            series.append({"label":f'{label}; kappa={case["kappa"]}',"x":list(range(len(curve))),"y":curve.tolist()})
    data={**receipt,"data_kind":"independent_simulation_curves","source_artifact":"Convergence_ZF.eps",
        "full_execution_verified":True,"fresh_full1000_ZF_MC_history_derivation_complete":True,
        "derivation_source_sha256":engine_sha256,"elapsed_derivation_seconds":time.perf_counter()-began,
        "x_name":"AO_sweep_index","x_unit":"iterations","y_name":"rate","y_unit":"bps/Hz","series":series,
        "aggregation":"all100 geometries at each kappa, all1000 identical draws at each accepted ZF position; explicit final-state hold for unequal lengths"}
    atomic_json(output/"ma-figure-04.json",data);render(data,output/"ma-figure-04")
    return {"source_bank_ready":True,"figure_rendered":True,"verified_jobs":200,"source_figure":3,"derived_figure":4}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source-bank",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args();print(json.dumps(derive(args.source_bank,args.output_dir)),flush=True)
