"""Exact original-model Jensen expectation on an executed iid-ZF trajectory.

The source's undefined Eq74 is not silently replaced in existing receipts.
This creates a separate, explicitly corrected-bound artifact and checks the
complete original1000-draw input and every original trajectory position.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from corrected_zf_position import evaluate_position,evaluator_fingerprint,position_evidence_complete
from execute_bank import atomic_json
from ma_metadata import fingerprint,implemented_complete
from run import scenario


def evaluate(job,executed,config,expected,position_cache=None):
    if not job.get("correlated") or job.get("figure") not in [14,16]:
        raise ValueError("Source-correlated ZF figures14/16 only")
    if not implemented_complete(executed,expected,job,config):
        raise ValueError("Complete original executed trajectory and all1000 input draws required")
    c,_=scenario(config,job["N"],job["M"],job["kappa"],job["power"],job["A"],job["geometry"])
    nlos=np.asarray(job["nlos_re"])+1j*np.asarray(job["nlos_im"])
    positions=executed["history"]["zf"]["positions"];records=[];source_hash=evaluator_fingerprint()
    for index,p in enumerate(positions):
        position_hash=hashlib.sha256(expected.encode()+source_hash.encode()+np.asarray(p,dtype="<f8").tobytes()).hexdigest()
        path=Path(position_cache)/f"position-{index:04d}.json" if position_cache is not None else None
        record=None
        if path is not None and path.exists():
            try:
                candidate=json.loads(path.read_text())
                if candidate.get("position_evidence_fingerprint")==position_hash and position_evidence_complete(candidate,p,job["M"]):record=candidate
            except (OSError,ValueError):pass
        if record is None:
            record=evaluate_position(np.asarray(p),c,nlos)
            record.update(accepted_position_index=index,position_evidence_fingerprint=position_hash,evaluator_source_sha256=source_hash)
            if path is not None:path.parent.mkdir(parents=True,exist_ok=True);atomic_json(path,record)
        records.append(record)
    for model,old in [("iid",executed["history"]["zf"]["instantaneous_MC_mean"]),
                      ("correlated",executed["metrics"]["correlated_extension"]["ZF_correlated_MC_history"])]:
        fresh=[r["models"][model]["actual_full1000_MC"]["mean_sum_rate"] for r in records]
        if not np.allclose(fresh,old,rtol=1e-9,atol=1e-9):raise RuntimeError("Fresh full1000 MC does not match unchanged source trajectory evidence")
    bound_records=[r["models"]["correlated"]["exact_original_model_Jensen"] for r in records]
    return {"paper_id":"two-timescale-ma","figure":job["figure"],"scope":"corrected_original_model_Jensen_bound_not_printed_Eq75",
        "input_fingerprint":expected,"original_trajectory_implementation_fingerprint":executed["implementation_fingerprint"],
        "trajectory":"unchanged_original_iid_Algorithm2","same_original_positions":True,
        "outer_expectation_samples_per_position":1000,"trajectory_positions_evaluated":len(records),
        "sum_rate_history":[r["sum_rate"] for r in bound_records],
        "maximum_quadrature_error_history":[r["maximum_quadrature_error"] for r in bound_records],
        "inverse_moment_standard_error_history":[r["inverse_moment_standard_error"] for r in bound_records],
        "histories":{model:{
            "MC_mean":[r["models"][model]["actual_full1000_MC"]["mean_sum_rate"] for r in records],
            "exact_population_Jensen_plugin":[r["models"][model]["exact_original_model_Jensen"]["sum_rate"] for r in records],
            "MC_minus_Jensen_plugin":[r["models"][model]["MC_minus_population_Jensen_plugin"] for r in records],
            "MC_standard_error":[r["models"][model]["MC_standard_error_within_geometry"] for r in records],
            "Jensen_outer_MC_standard_error_delta_method":[r["models"][model]["population_Jensen_rate_outer_MC_standard_error_delta_method"] for r in records],
            "Jensen_quadrature_rate_error_estimate_first_order":[r["models"][model]["population_Jensen_rate_quadrature_error_estimate_first_order"] for r in records]}
            for model in ["iid","correlated"]},
        "accepted_positions":positions,"corrected_evaluator_source_sha256":source_hash,
        "all_positions_full1000_MC_match_unchanged_source_receipt":True,
        "records":records,"modified_channel_or_Wishart_approximation":False,
        "printed_Eq74_closed_form_recovered":False,"original_curve_closeness_verified":False,
        "finite_ensemble_bound_guaranteed":False,
        "theoretical_population_Jensen_bound_valid":True}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--job",type=Path,required=True);p.add_argument("--run-result",type=Path,required=True)
    p.add_argument("--config",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--position-cache",type=Path);args=p.parse_args()
    began=time.perf_counter();config_bytes=args.config.read_bytes();job_bytes=args.job.read_bytes()
    result=evaluate(json.loads(job_bytes),json.loads(args.run_result.read_text()),json.loads(config_bytes),fingerprint(config_bytes,job_bytes),args.position_cache)
    result["elapsed_seconds"]=time.perf_counter()-began
    args.output.parent.mkdir(parents=True,exist_ok=True);atomic_json(args.output,result)
    print(json.dumps({k:result[k] for k in ["scope","trajectory_positions_evaluated","outer_expectation_samples_per_position","printed_Eq74_closed_form_recovered","elapsed_seconds"]}))
