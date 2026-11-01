"""Full 100-channel, six-scheme paper scenario families and shared input export."""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from run import build_scenario,run_scenario
from isac_metadata import fingerprint,reusable,bank_complete,implementation_fingerprint


def cases(config,family):
    sweep=config["sweeps"];out=[]
    def add(point,**kw):out.append(dict(family=family,point=point,**kw))
    if family in ["power-b0","power-b2"]:
        b=0 if family=="power-b0" else 2
        for p in sweep["power_dbm"]:add(p,K=2,b=b,power=10**((p-30)/10),rho=10,bs_shape=[2,2],figures=[2,4,6] if b==0 else [3,5,7])
    elif family=="bs-count":
        for count in sweep["bs_antenna_count"]:add(count,K=3,b=0,power=1.,rho=10,bs_shape=[1,count],figures=[8,9,10])
    elif family=="users":
        for k in sweep["users"]:add(k,K=k,b=2,power=1.,rho=10,bs_shape=[2,4],figures=[11,12,13])
    elif family=="rotation":
        for legend in config["rotation_legend_pairs"]:
            for degree in sweep["rotation_degrees"]:
                add(degree,K=2,b=2,power=1.,rho=10,bs_shape=[2,2],figures=[14,15,16],rotation_legend=legend)
    elif family=="rho":
        for rho in sweep["rho"]:add(rho,K=2,b=2,power=1.,rho=rho,bs_shape=[2,2],figures=[17])
    else:raise ValueError("Choose power-b0,power-b2,bs-count,users,rotation,rho.")
    return out


def make_scenario(case,config,realization):
    rng=np.random.default_rng(np.random.SeedSequence([config["seed"],case["K"],*case["bs_shape"],realization]))
    scene=build_scenario(config,case["K"],case["b"],case["power"],case["rho"],case["bs_shape"],rng)
    scene["case_metadata"]=dict(case,realization=realization)
    if "rotation_legend" in case:
        legend=case["rotation_legend"];swept=np.deg2rad(case["point"]);fixed=np.deg2rad(legend["other_fixed_half_width_deg"])
        scene["rotation_bs_half_width"]=swept if legend["swept_array"]=="BS" else fixed
        scene["rotation_ris_half_width"]=swept if legend["swept_array"]=="RIS" else fixed
    return scene


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--family",required=True);p.add_argument("--config",type=Path,default=Path(__file__).with_name("full_config.json"));p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--prepare",action="store_true");p.add_argument("--execute",action="store_true");args=p.parse_args();config_bytes=args.config.read_bytes();config=json.loads(config_bytes);case_list=cases(config,args.family)
    if config["channel_realizations"]!=100:raise ValueError("Original full scene requires 100 independent channel realizations.")
    plan={"paper_id":"rotatable-isac","family":args.family,"full":True,"channel_realizations":100,"scheme_count":6,
          "cases":case_list,"scenario_jobs":len(case_list)*100,"AO_jobs":len(case_list)*100*6,"executed":False,
          "warning":"Non-paper numeric settings and necessary safeguards are classified in full_config.json. This plan is not an executed result."}
    args.output_dir.mkdir(parents=True,exist_ok=True);(args.output_dir/"plan.json").write_text(json.dumps(plan,indent=2)+"\n")
    if args.prepare or args.execute:
        job_dir=args.output_dir/"jobs";job_dir.mkdir(exist_ok=True)
        (args.output_dir/"run_config.json").write_bytes(config_bytes)
        entries=[];successful=np.zeros((len(case_list),100),dtype=bool)
        for index,case in enumerate(case_list):
            for realization in range(100):
                stem=f"case-{index:03d}-mc-{realization:03d}";scene=make_scenario(case,config,realization)
                scene_bytes=(json.dumps(scene,separators=(",",":"))+"\n").encode("utf-8")
                expected=fingerprint(config_bytes,scene_bytes)
                path=job_dir/(stem+".json");path.write_bytes(scene_bytes)
                entries.append({"filename":path.name,"case_index":index,"realization":realization,"input_fingerprint":expected})
                if args.execute:
                    output=args.output_dir/(stem+"-python.json")
                    if not reusable(output,expected):
                        result=run_scenario(scene);result["case_metadata"]=scene["case_metadata"]
                        result["input_fingerprint"]=expected
                        result["implementation_fingerprint"]=implementation_fingerprint()
                        output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
                    successful[index,realization]=reusable(output,expected)
        manifest={"paper_id":"rotatable-isac","case_count":len(case_list),"realizations_per_case":100,"expected_jobs":len(entries),
                  "input_bank_complete":True,"config_sha256":hashlib.sha256(config_bytes).hexdigest(),"files":entries}
        valid_bank=bank_complete(job_dir,manifest,config_bytes);manifest["input_bank_complete"]=valid_bank
        (args.output_dir/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        summary={"paper_id":"rotatable-isac","family":args.family,"input_bank_complete":valid_bank,"expected_jobs":len(entries),
                 "successful_jobs":int(successful.sum()),"per_case_all_success":successful.all(axis=1).tolist(),
                 "overall_full_success":bool(args.execute and valid_bank and successful.all()),"executed":args.execute}
        (args.output_dir/"full_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(plan))
