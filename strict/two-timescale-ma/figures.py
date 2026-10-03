"""Full published scenario families, explicit planning/preparation/execution.

Generated shared-input jobs can also be consumed by the independent MATLAB
entrypoint. No simulations start when importing this module or asking for a plan.
"""
from __future__ import annotations
import argparse,copy,json,hashlib
from pathlib import Path
import numpy as np
from run import run_job
from ma_metadata import fingerprint,reusable,bank_complete,implementation_fingerprint,original_scope_available


def cases(config,figure):
    sweep=config["sweeps"];base=dict(N=6,M=5,kappa=100.,power=1.,A=2.)
    records=[]
    def add(point,**kw):records.append(dict(base,figure=figure,point=point,**kw))
    if figure in [3,4]:
        for kap in [6,100]:add(kap,kappa=kap)
    elif figure in [5,6]:
        for p in sweep["power_dbm"]:add(p,kappa=100 if figure==5 else 6,power=10**((p-30)/10))
    elif figure in [7,8]:
        for kap in sweep["rician_db"]:add(kap,kappa=10**(kap/10),N=6 if figure==7 else 4,M=5 if figure==7 else 3)
    elif figure in [9,10]:
        for kap in [6,100]:
            for A in sweep["region_A"]:add(A,kappa=kap,A=A,N=6 if figure==9 else 4,M=5 if figure==9 else 3)
    elif figure in [11,12]:
        for N in [6,8]:
            for M in sweep["user_counts_N"+str(N)]:add(M,N=N,M=M,kappa=100 if figure==11 else 6)
    elif figure in [13,14,15,16]:
        for kap in [5,10,15]:add(kap,N=8 if figure in [13,14] else 6,kappa=10**(kap/10),correlated=True)
    elif figure in [17,18]:
        for N,M in [(4,3),(6,5)]:
            key="user_error_m" if figure==17 else "antenna_error_lambda"
            for error in sweep[key]:add(error,N=N,M=M,kappa=100,error_type=key,error_amplitude=error)
    elif figure in [19,20]:
        for D in sweep["brute_force_points_per_axis"]:
            add(D,N=4 if figure==19 else 6,M=3 if figure==19 else 5,kappa=100,
                region_lower=[-1.6,-1.6],region_upper=[1.6,1.6 if figure==19 else 2.4],brute_force_D=D)
    else:raise ValueError("Paper numerical figures are 3 through 20.")
    return records


def make_job(case,config,realization):
    # Same geometry/NLoS ensemble across sweep points whenever N/M agree.
    rng=np.random.default_rng(np.random.SeedSequence([config["seed"],case["N"],case["M"],realization]))
    m,n=case["M"],case["N"]
    geometry={"distances_m":rng.uniform(50,70,m).tolist(),"elevation":rng.uniform(-np.pi/2,np.pi/2,m).tolist(),"azimuth":rng.uniform(-np.pi/2,np.pi/2,m).tolist()}
    z=(rng.normal(size=(config["nlos_realizations_per_geometry"],n,m))+1j*rng.normal(size=(config["nlos_realizations_per_geometry"],n,m)))/np.sqrt(2)
    job=dict(case,realization=realization,geometry=geometry,nlos_re=z.real.tolist(),nlos_im=z.imag.tolist())
    if case.get("error_type")=="user_error_m":
        d=np.asarray(geometry["distances_m"]);theta=np.asarray(geometry["elevation"]);phi=np.asarray(geometry["azimuth"])
        xyz=d[:,None]*np.c_[np.cos(theta)*np.cos(phi),np.cos(theta)*np.sin(phi),np.sin(theta)]
        estimate=xyz+rng.uniform(-case["error_amplitude"],case["error_amplitude"],xyz.shape)
        distance=np.linalg.norm(estimate,axis=1)
        job["estimated_geometry"]={"distances_m":distance.tolist(),"elevation":np.arcsin(estimate[:,2]/distance).tolist(),"azimuth":np.arctan2(estimate[:,1],estimate[:,0]).tolist()}
    if case.get("error_type")=="antenna_error_lambda":
        job["antenna_position_error"]=rng.uniform(-case["error_amplitude"],case["error_amplitude"],(n,2)).tolist()
    return job


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--figure",type=int,required=True);p.add_argument("--config",type=Path,default=Path(__file__).with_name("full_config.json"));p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--prepare",action="store_true");p.add_argument("--execute",action="store_true");args=p.parse_args();config_bytes=args.config.read_bytes();config=json.loads(config_bytes);case_list=cases(config,args.figure)
    original_available=all(original_scope_available(case) for case in case_list)
    blockers=[] if original_available else ["Correlated Eq72/74/75 dimension mismatch; correlated MC evaluates uncorrelated MRT/ZF optimized positions, not Eq69/75 optimized curves."]
    plan={"paper_id":"two-timescale-ma","figure":args.figure,"full":True,"geometry_realizations":config["geometry_realizations"],"nlos_per_geometry":config["nlos_realizations_per_geometry"],"cases":case_list,"jobs":len(case_list)*config["geometry_realizations"],
          "original_figure_scope_available":original_available,"original_figure_blockers":blockers,
          "warning":"Figs19/20 are exhaustive and may be computationally prohibitive. Correlated-ZF analytical75 remains blocked; correlated MC uses valid model68.","executed":False}
    args.output_dir.mkdir(parents=True,exist_ok=True);(args.output_dir/"plan.json").write_text(json.dumps(plan,indent=2)+"\n")
    if args.prepare or args.execute:
        jobs_dir=args.output_dir/"jobs";jobs_dir.mkdir(exist_ok=True)
        (args.output_dir/"run_config.json").write_bytes(config_bytes)
        entries=[];successful=np.zeros((len(case_list),config["geometry_realizations"]),dtype=bool);implemented_successful=np.zeros_like(successful)
        for index,case in enumerate(case_list):
            for realization in range(config["geometry_realizations"]):
                stem=f"case-{index:03d}-mc-{realization:03d}";job=make_job(case,config,realization)
                job_bytes=(json.dumps(job,separators=(",",":"))+"\n").encode("utf-8")
                expected=fingerprint(config_bytes,job_bytes)
                path=jobs_dir/(stem+".json");path.write_bytes(job_bytes)
                entries.append({"filename":path.name,"case_index":index,"realization":realization,"input_fingerprint":expected})
                if args.execute:
                    result_path=args.output_dir/(stem+"-python.json")
                    if not reusable(result_path,expected,job,config):
                        try:result=run_job(job,config)
                        except Exception as error:result={"paper_id":"two-timescale-ma","mode":"full_scenario","status":"failed","error":str(error),"case":case,"realization":realization}
                        result["input_fingerprint"]=expected
                        result["implementation_fingerprint"]=implementation_fingerprint()
                        result_path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
                    implemented_successful[index,realization]=reusable(result_path,expected,job,config)
                    successful[index,realization]=implemented_successful[index,realization] and original_scope_available(job)
        manifest={"paper_id":"two-timescale-ma","case_count":len(case_list),"realizations_per_case":config["geometry_realizations"],
                  "nlos_per_geometry":config["nlos_realizations_per_geometry"],"expected_jobs":len(entries),"input_bank_complete":True,
                  "config_sha256":hashlib.sha256(config_bytes).hexdigest(),"files":entries}
        valid_bank=bank_complete(jobs_dir,manifest,config_bytes);manifest["input_bank_complete"]=valid_bank
        (args.output_dir/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        summary={"paper_id":"two-timescale-ma","figure":args.figure,"input_bank_complete":valid_bank,"expected_jobs":len(entries),
                 "successful_jobs":int(successful.sum()),"per_case_all_success":successful.all(axis=1).tolist(),
                 "implemented_scope_successful_jobs":int(implemented_successful.sum()),"per_case_implemented_scope_success":implemented_successful.all(axis=1).tolist(),
                 "overall_implemented_scope_success":bool(args.execute and valid_bank and implemented_successful.all()),
                 "overall_full_success":bool(args.execute and valid_bank and successful.all()),
                 "original_figure_complete":bool(args.execute and valid_bank and successful.all()),
                 "original_figure_status":"blocked_by_source_formulation" if not original_available else ("complete" if args.execute and valid_bank and successful.all() else "not_run_or_incomplete"),
                 "original_figure_blockers":blockers,"executed":args.execute}
        (args.output_dir/"full_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(plan))
