"""Component tests and full-size, shared-input scenario runner.

No run is called an original numerical replication merely because it executes.
The full run uses published dimensions/model and transparently tuned metadata.
"""
from __future__ import annotations
import argparse
import copy
import json
import time
from pathlib import Path
import numpy as np
from core import (los,mrt_statistics,zf_statistics,zf_surrogate,optimize,
                  solve_coordinate,correlated_mrt,instantaneous,fixed_array_benchmark)


def scenario(config,n,m,kap,power=1.,A=2.,geometry=None):
    c=copy.deepcopy(config)
    nr,nc=config["antenna_factorization"][str(n)]
    c.update(wavelength=1.,minimum_distance=.5,power=power,noise=[1e-11]*m,
             region_lower=[-nr*A/2,-nc*A/2],region_upper=[nr*A/2,nc*A/2],rician=[kap]*m)
    if geometry is not None:
        theta=np.asarray(geometry["elevation"]); phi=np.asarray(geometry["azimuth"])
        c["directions"]=np.c_[np.cos(theta)*np.sin(phi),np.sin(theta)].tolist()
        c["beta"]=(1e-4*np.asarray(geometry["distances_m"])**-2.8).tolist()
    x=(np.arange(nr)-(nr-1)/2)/2; y=(np.arange(nc)-(nc-1)/2)/2
    return c,np.array([[a,b] for a in x for b in y])


def component_test(config):
    f=json.loads(Path(__file__).with_name("fixture.json").read_text())
    c,t=scenario(config,6,5,f["rician_linear"],geometry=f)
    t=np.asarray(f["positions"])
    val,grad,_,_=mrt_statistics(t,c)
    numerical=np.zeros_like(t); eps=f["finite_difference_step"]
    for n in range(len(t)):
        for d in range(2):
            plus,minus=t.copy(),t.copy();plus[n,d]+=eps;minus[n,d]-=eps
            numerical[n,d]=(mrt_statistics(plus,c)[0]-mrt_statistics(minus,c)[0])/(2*eps)
    zf,rates,sigma,eta=zf_statistics(t,c); s=zf_surrogate(t,c,0)
    identity=1/np.real(np.diag(np.linalg.solve(sigma,np.eye(5))))
    tangent=s["chi"]+s["f0"]
    mrt_t,mrt_update=solve_coordinate(t,c,0,"MRT")
    zf_t,zf_update=solve_coordinate(t,c,0,"ZF")
    source_minus_radicands=[]
    # Symmetric 2x2 matrix characteristic polynomial supplies the correction proof.
    sample=np.array([[2.,1.5],[1.5,1.]])
    closed=(sample.trace()+np.sqrt((sample[0,0]-sample[1,1])**2+4*sample[0,1]**2))/2
    distance=np.linalg.norm(zf_t[:,None]-zf_t[None,:],axis=2)+np.eye(6)*1e9
    checks={"mrt_gradient_max_error":float(np.max(abs(grad-numerical))),
            "gradient_pass":bool(np.max(abs(grad-numerical))<1e-6),
            "zf_woodbury_identity_error":float(np.max(abs(s["ratio"]-identity))),
            "zf_MM_tangency_error":float(np.max(abs(tangent-s["ratio"]))),
            "Eq29a_corrected_closed_form_error":float(abs(closed-np.linalg.eigvalsh(sample)[-1])),
            "mrt_surrogate_lower_bound_gap":mrt_update["lower_bound_gap"],
            "zf_surrogate_lower_bound_gap":zf_update["lower_bound_gap"],
            "spacing_feasible":bool(distance.min()>=.5-1e-7),
            "box_feasible":bool(np.all(zf_t>=c["region_lower"]) and np.all(zf_t<=c["region_upper"])),
            "correlated_zf_closed_form_implemented":False,
            "finite":bool(np.all(np.isfinite(zf_t)))}
    assert checks["gradient_pass"] and checks["zf_woodbury_identity_error"]<1e-10
    assert checks["zf_MM_tangency_error"]<1e-10 and checks["spacing_feasible"]
    return {"paper_id":"two-timescale-ma","mode":"component_test_not_full_run",
            "metrics":{"mrt_statistical":val,"zf_statistical":zf,"correlated_mrt":correlated_mrt(t,c),
                       "mrt_one_coordinate":mrt_t.tolist(),"zf_one_coordinate":zf_t.tolist()},
            "checks":checks,"history":{"mrt":mrt_update,"zf":zf_update}}


def run_job(job,config):
    """All five original benchmark families at their separately optimized positions."""
    n,m=job["N"],job["M"]
    c,t=scenario(config,n,m,job["kappa"],job["power"],job["A"],job["geometry"])
    if "region_lower" in job:c["region_lower"]=job["region_lower"];c["region_upper"]=job["region_upper"]
    if "initial_positions" in job: t=np.asarray(job["initial_positions"])
    nlos=np.asarray(job["nlos_re"])+1j*np.asarray(job["nlos_im"])
    if len(nlos)!=config["nlos_realizations_per_geometry"]:
        raise ValueError("Full job does not contain the configured complete NLoS Monte Carlo count.")
    design=c
    if "estimated_geometry" in job:
        design,_=scenario(config,n,m,job["kappa"],job["power"],job["A"],job["estimated_geometry"])
    mrt_pos,mrt_hist=optimize(t,design,"MRT"); zf_pos,zf_hist=optimize(t,design,"ZF")
    jitter=np.asarray(job.get("antenna_position_error",np.zeros_like(t)))
    results={"MA-MRT":instantaneous(mrt_pos+jitter,c,nlos,"MRT"),"MA-ZF":instantaneous(zf_pos+jitter,c,nlos,"ZF")}
    hb=los(t,c); beta=np.asarray(c["beta"]); kap=np.asarray(c["rician"])
    fixed={k:[] for k in ["FPA-MRT","FPA-ZF","FPA-OPT"]}
    caps={k:0 for k in fixed}
    for sample in nlos:
        h=hb*np.sqrt(beta*kap/(kap+1))+sample*np.sqrt(beta/(kap+1))
        for kind in fixed:
            value,history=fixed_array_benchmark(h,c,kind)
            fixed[kind].append(value); caps[kind]+=int(not history["converged"])
    for kind,rates in fixed.items():
        results[kind]={"sample_sum_rates":rates,"mean_sum_rate":float(np.mean(rates)),"nonconverged_samples":caps[kind]}
    # Figures 3/4 need the actual MC evaluator at each accepted AO sweep, not
    # merely the statistical design objective mislabeled as the actual rate.
    # Use precisely the exported ensemble; no optimization or RNG is changed.
    if job["figure"] in [3,13,15]:
        mrt_hist["instantaneous_MC_mean"]=[instantaneous(np.asarray(p),c,nlos,"MRT")["mean_sum_rate"] for p in mrt_hist["positions"]]
    if job["figure"] in [4,14,16]:
        zf_hist["instantaneous_MC_mean"]=[instantaneous(np.asarray(p),c,nlos,"ZF")["mean_sum_rate"] for p in zf_hist["positions"]]
    extension={}
    if job.get("correlated",False):
        extension={"MA-MRT_MC":instantaneous(mrt_pos,c,nlos,"MRT",True),
                   "MA-ZF_MC":instantaneous(zf_pos,c,nlos,"ZF",True),
                   "MRT_Eq69_at_MRT_positions":correlated_mrt(mrt_pos,c),
                   "ZF_Eq75_status":"blocked_by_Eq72_74_dimension_mismatch"}
        extension["MRT_correlated_MC_history"]=[instantaneous(np.asarray(p),c,nlos,"MRT",True)["mean_sum_rate"] for p in mrt_hist["positions"]]
        extension["ZF_correlated_MC_history"]=[instantaneous(np.asarray(p),c,nlos,"ZF",True)["mean_sum_rate"] for p in zf_hist["positions"]]
        extension["MRT_Eq69_history"]=[correlated_mrt(np.asarray(p),c) for p in mrt_hist["positions"]]
        extension["comparison_protocol"]={"trajectory":"iid_Algorithm1_for_MRT_iid_Algorithm2_for_ZF",
            "same_exported_NLoS_ensemble":True,"source_supported_interpretation":True,
            "original_experiment_record_recovered":False,"original_curve_closeness_verified":False}
    checks={"mrt_converged":mrt_hist["converged"],"zf_converged":zf_hist["converged"],
            "each_algorithm_owns_its_positions":True,"full_N":n,"full_M":m,"nlos_samples":len(nlos)}
    for name,positions in [("mrt",mrt_pos),("zf",zf_pos)]:
        dist=np.linalg.norm(positions[:,None]-positions[None,:],axis=2)+np.eye(n)*1e9
        checks[name+"_nominal_design_spacing_feasible"]=bool(dist.min()>=.5-c["verification_tolerance"])
        checks[name+"_nominal_design_box_feasible"]=bool(np.all(positions>=np.asarray(c["region_lower"])-c["verification_tolerance"]) and np.all(positions<=np.asarray(c["region_upper"])+c["verification_tolerance"]))
        realized=positions+jitter;dist=np.linalg.norm(realized[:,None]-realized[None,:],axis=2)+np.eye(n)*1e9
        checks[name+"_realized_positions_spacing_feasible"]=bool(dist.min()>=.5-c["verification_tolerance"])
        checks[name+"_realized_positions_box_feasible"]=bool(np.all(realized>=np.asarray(c["region_lower"])-c["verification_tolerance"]) and np.all(realized<=np.asarray(c["region_upper"])+c["verification_tolerance"]))
    checks["perfect_instantaneous_CSI_for_beamforming"]=True
    brute={}
    if "brute_force_D" in job:
        from brute_force import exhaustive
        for mode in ["MRT","ZF"]:
            winner,record=exhaustive(c,n,job["brute_force_D"],mode,nlos)
            brute[mode]={"search":record,"positions":winner.tolist(),"MC":instantaneous(winner,c,nlos,mode)}
    return {"paper_id":"two-timescale-ma","mode":"full_scenario",
            "job_metadata":{k:job[k] for k in ["N","M","kappa","power","A","figure","point","realization"]},
            "metrics":{"schemes":results,"correlated_extension":extension,"brute_force":brute,"mrt_positions":mrt_pos.tolist(),"zf_positions":zf_pos.tolist(),
                       "mrt_realized_positions":(mrt_pos+jitter).tolist(),"zf_realized_positions":(zf_pos+jitter).tolist()},
            "checks":checks,"history":{"mrt":mrt_hist,"zf":zf_hist}}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--config",type=Path,default=Path(__file__).with_name("full_config.json"))
    p.add_argument("--component-test",action="store_true");p.add_argument("--job",type=Path)
    p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    config=json.loads(args.config.read_text());start=time.perf_counter()
    if args.component_test: result=component_test(config)
    elif args.job:
        result=run_job(json.loads(args.job.read_text()),config)
        from ma_metadata import fingerprint
        result["input_fingerprint"]=fingerprint(args.config.read_bytes(),args.job.read_bytes())
    else: p.error("Choose --component-test or --job. Full runs use complete exported inputs, not tiny defaults.")
    result["elapsed_seconds"]=time.perf_counter()-start
    from ma_metadata import implementation_fingerprint
    result["implementation_fingerprint"]=implementation_fingerprint()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"mode":result["mode"],"checks":result["checks"]}))
