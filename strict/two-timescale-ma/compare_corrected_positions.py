"""Independent paired full1000 position comparison, not full-bank closure."""
import argparse
import json
from pathlib import Path
import numpy as np
from execute_bank import atomic_json


def compare(py,mat):
    n=len(py["positions"]);checks={};details={};roundoff=64*np.finfo(float).eps
    def numerical(name,p,q):
        p=np.asarray(p,dtype=float);q=np.asarray(q,dtype=float)
        valid=p.shape==q.shape and np.all(np.isfinite(p)) and np.all(np.isfinite(q))
        checks[name]=bool(valid and np.allclose(p,q,rtol=1e-9,atol=1e-10))
        details[name]={"shape":list(p.shape),"maximum_absolute_difference":float(np.max(abs(p-q))) if valid else None,
                       "rtol":1e-9,"atol":1e-10}
    numerical("unchanged_original_positions",py["positions"],mat["positions"])
    numerical("original_iid_design_objective",py["original_iid_Algorithm2_statistical_design_objective"],mat["original_iid_Algorithm2_statistical_design_objective"])
    for model in ["iid","correlated"]:
        p=py["models"][model];q=mat["models"][model];pb=p["exact_original_model_Jensen"];qb=q["exact_original_model_Jensen"]
        for key in ["sample_sum_rates","powers","off_diagonal_amplitude","mean_sum_rate"]:
            numerical(model+"_MC_"+key,np.ravel(p["actual_full1000_MC"][key]),np.ravel(q["actual_full1000_MC"][key]))
        for key in ["direct_MC_inverse_diagonal_samples","direct_MC_inverse_diagonal_mean","direct_MC_inverse_diagonal_standard_error"]:
            numerical(model+"_"+key,p[key],q[key])
        for key in ["sum_rate","per_user_rates","mean_inverse_normalized_Gram_diagonal","inverse_moment_standard_error"]:
            numerical(model+"_Jensen_"+key,np.ravel(pb[key]),np.ravel(qb[key]))
        pc=np.asarray(pb["conditional_inverse_moment_samples"]);qc=np.asarray(qb["conditional_inverse_moment_samples"])
        numerical(model+"_all5000_conditional_moments_fixed_tolerance",pc,qc)
        error=np.asarray(pb["conditional_quadrature_error_samples"])+np.asarray(qb["conditional_quadrature_error_samples"])
        envelope=error+roundoff*np.maximum(1,np.maximum(abs(pc),abs(qc)))
        checks[model+"_all5000_conditional_moments_combined_reported_error_estimate"]=bool(pc.shape==(1000,5) and np.all(abs(pc-qc)<=envelope))
        details[model+"_conditional_error_envelope"]={"maximum_actual_absolute_difference":float(abs(pc-qc).max()),
            "maximum_combined_reported_quadrature_error_estimate":float(error.max()),
            "fixed_tolerance_failure_count":int(np.count_nonzero(~np.isclose(pc,qc,rtol=1e-9,atol=1e-10))),
            "outside_reported_error_estimate_count":int(np.count_nonzero(abs(pc-qc)>envelope)),
            "numerical_error_estimates_are_not_interval_proofs":True}
        for key in ["MC_standard_error_within_geometry","MC_minus_population_Jensen_plugin","population_Jensen_rate_outer_MC_standard_error_delta_method"]:
            numerical(model+"_"+key,p[key],q[key])
        checks[model+"_full1000_identity_checks_in_both_languages"]=bool(p["all1000_times_M_Schur_identities_pass"] and q["all1000_times_M_Schur_identities_pass"]
            and p["all1000_ZF_beamformer_rate_identities_pass"] and q["all1000_ZF_beamformer_rate_identities_pass"])
    return {"paper_id":"two-timescale-ma","scope":"paired_full1000_initial_position_evidence_not_full_figure", "N":n,"M":5,
        "checks":checks,"details":details,"all_fixed_tolerance_checks_passed":all(v for k,v in checks.items() if "combined_reported_error_estimate" not in k),
        "all_model_metric_and_reported_error_estimate_checks_passed":all(v for k,v in checks.items() if "fixed_tolerance" not in k),
        "all_figure_geometries_or_trajectories_verified":False,"historical_figure_recovery_claimed":False}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--python",type=Path,required=True);p.add_argument("--matlab",type=Path,required=True);p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    result=compare(json.loads(args.python.read_text()),json.loads(args.matlab.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);atomic_json(args.output,result)
    print(json.dumps({k:result[k] for k in ["N","M","all_fixed_tolerance_checks_passed","all_model_metric_and_reported_error_estimate_checks_passed","all_figure_geometries_or_trajectories_verified"]}))
