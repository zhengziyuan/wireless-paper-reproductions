"""Source-bound complete1000-draw position evidence; never a full-figure claim."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from corrected_zf_position import evaluate_position,evaluator_fingerprint,position_evidence_complete
from execute_bank import atomic_json
from ma_metadata import fingerprint,implementation_fingerprint
from run import scenario


def validate(job_path,config_path,output_path):
    job_bytes=job_path.read_bytes();config_bytes=config_path.read_bytes()
    job=json.loads(job_bytes);config=json.loads(config_bytes)
    if config.get("geometry_realizations")!=100 or config.get("nlos_realizations_per_geometry")!=1000:
        raise ValueError("Complete configured100 geometry/1000 NLoS contract required")
    c,t=scenario(config,job["N"],job["M"],job["kappa"],job["power"],job["A"],job["geometry"])
    if "initial_positions" in job:t=np.asarray(job["initial_positions"],dtype=float)
    if "region_lower" in job:c["region_lower"]=job["region_lower"];c["region_upper"]=job["region_upper"]
    z=np.asarray(job["nlos_re"])+1j*np.asarray(job["nlos_im"])
    source_identity=evaluator_fingerprint()
    result=evaluate_position(t,c,z)
    if not position_evidence_complete(result,t,job["M"]):raise RuntimeError("Complete full-draw evidence gate failed")
    if source_identity!=evaluator_fingerprint():raise RuntimeError("Independent evaluator changed during validation")
    result.update(paper_id="two-timescale-ma",mode="full1000_position_evidence_not_full_figure",figure=job["figure"],
        evaluator_version="v3_segmented_same_Laplace_integral",evaluator_source_sha256=source_identity,
        input_fingerprint=fingerprint(config_bytes,job_bytes),
        input_job_sha256=hashlib.sha256(job_bytes).hexdigest(),input_config_sha256=hashlib.sha256(config_bytes).hexdigest(),
        unchanged_optimization_core_fingerprint=implementation_fingerprint(),
        validator_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        complete_position_evidence_passed=True,all_figure_geometries_or_trajectories_verified=False)
    output_path.parent.mkdir(parents=True,exist_ok=True);atomic_json(output_path,result)
    print(json.dumps({"N":job["N"],"M":job["M"],"complete_position_evidence_passed":True,
        "input_fingerprint":result["input_fingerprint"],"evaluator_source_sha256":source_identity,
        "models":{model:result["models"][model]["exact_original_model_Jensen"]["sum_rate"] for model in ["iid","correlated"]}}),flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--job",type=Path,required=True);p.add_argument("--config",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);args=p.parse_args();validate(args.job,args.config,args.output)
