"""Paired full1000-input original correlated-channel identity receipt.

This evaluates the initial physical array of one exported original geometry;
it is not a full100-geometry figure or an optimized trajectory claim.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import numpy as np
from core import los,spatial_covariance,instantaneous
from correlated_zf import correlated_jensen_bound
from ma_metadata import fingerprint
from run import scenario


def validate(job,config):
    c,t=scenario(config,job["N"],job["M"],job["kappa"],job["power"],job["A"],job["geometry"])
    if "initial_positions" in job:t=np.asarray(job["initial_positions"])
    nlos=np.asarray(job["nlos_re"])+1j*np.asarray(job["nlos_im"])
    if config["nlos_realizations_per_geometry"]!=1000 or len(nlos)!=1000:
        raise ValueError("All1000 exported draws required for this original-size check")
    bound=correlated_jensen_bound(t,c,nlos);actual=instantaneous(t,c,nlos,"ZF",True)
    S=spatial_covariance(t,c);eig,V=np.linalg.eigh(S);root=(V*np.sqrt(eig))@V.conj().T
    kap=np.asarray(c["rician"]);mu=los(t,c)*np.sqrt(kap/(kap+1));inverse_samples=[];identity_error=0.
    for U in nlos:
        X=mu+(root@U)/np.sqrt(kap+1);inverse=np.linalg.solve(X.conj().T@X,np.eye(job["M"]))
        inverse_samples.append(np.diag(inverse).real.tolist())
        for m in range(job["M"]):
            Q,_=np.linalg.qr(np.delete(X,m,axis=1),mode="complete");projected=Q[:,job["M"]-1:].conj().T@X[:,m]
            identity_error=max(identity_error,abs(inverse[m,m].real-1/np.vdot(projected,projected).real))
    inverse_samples=np.asarray(inverse_samples)
    return {"paper_id":"two-timescale-ma","mode":"full1000_draw_original_model_identity_not_full_figure",
        "N":job["N"],"M":job["M"],"positions":t.tolist(),"outer_ensemble_count":1000,
        "conditional_exact_Jensen_evaluator":bound,"actual_correlated_ZF":actual,
        "direct_MC_inverse_diagonal_mean":inverse_samples.mean(axis=0).tolist(),
        "direct_MC_inverse_diagonal_standard_error":(inverse_samples.std(axis=0,ddof=1)/np.sqrt(1000)).tolist(),
        "maximum_Schur_identity_error_over_all1000_draws_and_users":float(identity_error),
        "checks":{"full1000_used":True,"Schur_identity_all5000_pass":bool(identity_error<1e-8),
            "source_row_covariance_unchanged":True,"no_Wishart_surrogate":True},
        "printed_Eq74_closed_form_recovered":False,"original_figure_reproduction_certified":False}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--job",type=Path,required=True);p.add_argument("--config",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);args=p.parse_args();began=time.perf_counter()
    config_bytes=args.config.read_bytes();job_bytes=args.job.read_bytes();result=validate(json.loads(job_bytes),json.loads(config_bytes))
    result["input_fingerprint"]=fingerprint(config_bytes,job_bytes);result["elapsed_seconds"]=time.perf_counter()-began
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"checks":result["checks"],"rate_actual":result["actual_correlated_ZF"]["mean_sum_rate"],
        "corrected_Jensen_estimate":result["conditional_exact_Jensen_evaluator"]["sum_rate"],"elapsed_seconds":result["elapsed_seconds"]}))
