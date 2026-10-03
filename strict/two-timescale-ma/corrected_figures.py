"""Explicit corrected-source full Figs14/16; never historical recovery.

The original frozen engine owns the unchanged iid Algorithm2 trajectory and
all original benchmarks. This adapter evaluates both ORIGINAL channel models
at every accepted position using all1000 configured draws and the exact
original-model Jensen inverse-moment integral. No partial-bank plot.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from corrected_zf_position import evaluator_fingerprint,position_evidence_complete
from evaluate_correlated_zf import evaluate
from execute_bank import atomic_json,execute
from figures import cases,make_job
from ma_metadata import bank_complete,implemented_complete,implementation_fingerprint
from render_figures import terminal_hold_mean


COUNT_PROVENANCE="100 geometries and1000 NLoS draws are disclosed configured choices; source does not report original counts"


def verify_source(bank):
    bank=Path(bank);config_bytes=(bank/"run_config.json").read_bytes();config=json.loads(config_bytes)
    manifest_bytes=(bank/"manifest.json").read_bytes();manifest=json.loads(manifest_bytes)
    plan=json.loads((bank/"plan.json").read_text());figure=plan["figure"]
    if figure not in [14,16]:raise ValueError("Corrected-source ZF figures14/16 only")
    expected_cases=cases(config,figure)
    if (config.get("geometry_realizations")!=100 or config.get("nlos_realizations_per_geometry")!=1000
        or manifest.get("expected_jobs")!=300 or manifest.get("case_count")!=3
        or manifest.get("realizations_per_case")!=100 or manifest.get("nlos_per_geometry")!=1000
        or plan.get("cases")!=expected_cases
        or manifest.get("config_sha256")!=hashlib.sha256(config_bytes).hexdigest()
        or not bank_complete(bank/"jobs",manifest,config_bytes)):
        raise ValueError("Immutable complete3-kappa ×100-geometry ×1000-NLoS source input bank required")
    records=[];missing=[];invalid=[]
    for entry in manifest["files"]:
        job_bytes=(bank/"jobs"/entry["filename"]).read_bytes()
        regenerated=(json.dumps(make_job(expected_cases[entry["case_index"]],config,entry["realization"]),separators=(",",":"))+"\n").encode()
        if job_bytes!=regenerated:raise ValueError("Exported full input does not exactly regenerate from immutable configured source protocol")
        job=json.loads(job_bytes);path=bank/(Path(entry["filename"]).stem+"-python.json")
        if not path.exists():missing.append(path.name);continue
        try:result_bytes=path.read_bytes();result=json.loads(result_bytes)
        except (OSError,ValueError):invalid.append(path.name);continue
        if not implemented_complete(result,entry["input_fingerprint"],job,config):invalid.append(path.name);continue
        positions=result["history"]["zf"]["positions"]
        if len(positions)!=len(result["history"]["zf"]["objective"]):invalid.append(path.name);continue
        records.append((entry,job,result,result_bytes))
    ready=len(records)==300 and not missing and not invalid
    receipt={"paper_id":"two-timescale-ma","figure":figure,
        "scope":"corrected_source_full_figure_original_model_Jensen_not_historical_recovery",
        "full_source_execution_verified":ready,"source_jobs_required":300,"source_jobs_verified":len(records),
        "all_three_Rician_cases_required_db":[5,10,15],"geometries_per_kappa":100,"nlos_per_geometry":1000,
        "Monte_Carlo_count_provenance":COUNT_PROVENANCE,"input_bank_complete":True,
        "all300_exported_inputs_exactly_regenerate":True,"missing_source_results":missing,
        "invalid_or_nonconverged_source_results":invalid,"source_manifest_sha256":hashlib.sha256(manifest_bytes).hexdigest(),
        "source_config_sha256":hashlib.sha256(config_bytes).hexdigest(),
        "source_implementation_fingerprint":implementation_fingerprint(),
        "source_layout_models":["MA-ZF, Simplified with MA spacing","MA-ZF, Spatially correlated Rayleigh"],
        "source_legend_does_not_identify_actual_MC_vs_analytical_formula":True,
        "trajectory":"unchanged_original_iid_Algorithm2","printed_Eq74_75_recovered":False,
        "original_figure_complete":False,"original_curve_closeness_verified":False,
        "finite_ensemble_lower_bound_guaranteed":False,"partial_success_survivor_average_allowed":False}
    return receipt,config,expected_cases,records


def held_matrix(histories):
    if len(histories)!=100:raise ValueError("All100 geometry histories required")
    # The separately tested terminal-hold rule validates every finite history.
    mean=terminal_hold_mean(histories)
    return np.asarray([np.pad(np.asarray(h,dtype=float),(0,len(mean)-len(h)),mode="edge") for h in histories])


def corrected_evaluation_complete(result,source,m):
    positions=source["history"]["zf"]["positions"]
    try:
        if result.get("trajectory_positions_evaluated")!=len(positions) or len(result["records"])!=len(positions):return False
        if not all(position_evidence_complete(r,p,m) for r,p in zip(result["records"],positions)):return False
        for model in ["iid","correlated"]:
            for history in result["histories"][model].values():
                array=np.asarray(history,dtype=float)
                if array.shape!=(len(positions),) or not np.all(np.isfinite(array)):return False
        return result.get("all_positions_full1000_MC_match_unchanged_source_receipt") is True
    except (ValueError,TypeError,KeyError):return False


def aggregate_records(receipt,case_list,by_case):
    panels={name:[] for name in ["source_layout_MC","exact_population_Jensen_plugin","MC_minus_Jensen_plugin",
                               "Jensen_outer_MC_delta_standard_error","Jensen_quadrature_rate_error_estimate"]}
    keys={"source_layout_MC":"MC_mean","exact_population_Jensen_plugin":"exact_population_Jensen_plugin",
          "MC_minus_Jensen_plugin":"MC_minus_Jensen_plugin","Jensen_outer_MC_delta_standard_error":"Jensen_outer_MC_standard_error_delta_method",
          "Jensen_quadrature_rate_error_estimate":"Jensen_quadrature_rate_error_estimate_first_order"}
    for case,items in zip(case_list,by_case):
        if len(items)!=100:raise ValueError("All100 valid corrected derivation records per kappa required")
        for model in ["iid","correlated"]:
            for panel,key in keys.items():
                matrix=held_matrix([r["histories"][model][key] for r in items]);mean=matrix.mean(axis=0)
                panels[panel].append({"label":f'{"IID" if model=="iid" else "Correlated"}, kappa={case["point"]} dB',
                    "channel_model":model,"kappa_db":case["point"],"x":list(range(len(mean))),"y":mean.tolist(),
                    "geometry_standard_error_of_plotted_mean":(matrix.std(axis=0,ddof=1)/np.sqrt(100)).tolist(),
                    "source_history_key":key})
    return {**receipt,"corrected_source_figure_execution_complete":True,"historical_figure_recovery_claimed":False,
        "full_source_execution_verified":True,"all300_corrected_derivations_complete":True,
        "corrected_evaluator_source_sha256":evaluator_fingerprint(),
        "data_kind":"independent_full_configured_population_corrected_source_curves",
        "source_artifact":"spatial2.eps" if receipt["figure"]==14 else "spatial4.eps",
        "N":8 if receipt["figure"]==14 else 6,"M":5,
        "aggregation":"full100 geometries per kappa; full1000 identical exported draws at every accepted unchanged iid Algorithm2 position; final-state hold explicitly applied to unequal history lengths",
        "source_MC_or_formula_selection_disclosed":"MC panel is explicitly actual MC; exact Jensen panel is separately corrected, not silently identified with ambiguous historical legend",
        "diagnostic_error_scope":"adaptive quadrature estimates and first-order delta standard errors are not interval certificates or confidence intervals",
        "panels":panels}


def render_panels(data,output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    titles={"source_layout_MC":"Original-channel model comparison (MC)","exact_population_Jensen_plugin":"Corrected original-model Jensen evaluation",
        "MC_minus_Jensen_plugin":"MC minus population-Jensen plug-in","Jensen_outer_MC_delta_standard_error":"Outer-MC delta standard error (diagnostic)",
        "Jensen_quadrature_rate_error_estimate":"Quadrature rate error estimate (diagnostic)"}
    with plt.rc_context({"font.family":"serif","font.size":8.5,"axes.labelsize":8.5,"axes.titlesize":8.5,
                         "legend.fontsize":7,"axes.linewidth":.7,"lines.linewidth":1.3}):
        for panel,series in data["panels"].items():
            fig,ax=plt.subplots(figsize=(4.3,3.44));colors={"iid":"#ad3c67","correlated":"#2972a2"};styles={5:"-",10:"--",15:":"};markers={5:"o",10:"s",15:"^"}
            for s in series:
                ax.plot(s["x"],s["y"],label=s["label"],color=colors[s["channel_model"]],linestyle=styles[s["kappa_db"]],
                    marker=markers[s["kappa_db"]],markersize=3,markevery=max(1,len(s["x"])//9))
            ax.set_xlabel("Accepted AO sweep index");ax.set_ylabel("Sum rate (bps/Hz)" if panel in ["source_layout_MC","exact_population_Jensen_plugin"] else "Rate diagnostic (bps/Hz)")
            ax.set_title(titles[panel]);ax.grid(True,which="major",color=".83",linewidth=.45);ax.tick_params(direction="in")
            ax.legend(loc="upper center",bbox_to_anchor=(.5,-.30),ncol=2,frameon=True,framealpha=1,edgecolor=".6")
            if panel=="Jensen_quadrature_rate_error_estimate":ax.ticklabel_format(axis="y",style="sci",scilimits=(0,0))
            fig.subplots_adjust(left=.16,right=.97,top=.88,bottom=.36)
            path=output/f'ma-figure-{data["figure"]:02d}-corrected-{panel}'
            fig.savefig(path.with_suffix(".png"),dpi=260);fig.savefig(path.with_suffix(".svg"));plt.close(fig)


def derive(bank,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    receipt,config,case_list,records=verify_source(bank);atomic_json(output/"source-readiness.json",receipt)
    if not receipt["full_source_execution_verified"]:
        return {"full_source_execution_verified":False,"corrected_figure_rendered":False,"verified_jobs":len(records),"required_jobs":300}
    began=time.perf_counter();by_case=[[] for _ in case_list];engine=evaluator_fingerprint()
    for entry,job,source,source_bytes in records:
        stem=Path(entry["filename"]).stem;path=output/(stem+"-corrected-python.json");cached=None
        source_digest=hashlib.sha256(source_bytes).hexdigest()
        if path.exists():
            try:cached=json.loads(path.read_text())
            except (OSError,ValueError):pass
        if (not cached or cached.get("source_result_sha256")!=source_digest or cached.get("corrected_evaluator_source_sha256")!=engine
            or cached.get("input_fingerprint")!=entry["input_fingerprint"]
            or not corrected_evaluation_complete(cached,source,job["M"])):
            cached=evaluate(job,source,config,entry["input_fingerprint"],output/"position-evidence"/stem)
            cached.update(source_result_sha256=source_digest,case_index=entry["case_index"],realization=entry["realization"])
            atomic_json(path,cached)
        by_case[entry["case_index"]].append(cached)
        atomic_json(output/"derivation-progress.json",{**receipt,"corrected_derivation_jobs_complete":sum(map(len,by_case)),
            "corrected_source_figure_execution_complete":False,"corrected_evaluator_source_sha256":engine,
            "elapsed_seconds":time.perf_counter()-began})
        print(json.dumps({"corrected_derivation_jobs":sum(map(len,by_case)),"required_jobs":300}),flush=True)
    data=aggregate_records(receipt,case_list,by_case);data["elapsed_derivation_seconds"]=time.perf_counter()-began
    data["corrected_derivation_adapter_source_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    atomic_json(output/f'ma-figure-{receipt["figure"]:02d}-corrected.json',data);render_panels(data,output)
    atomic_json(output/"derivation-summary.json",{**receipt,"corrected_source_figure_execution_complete":True,
        "corrected_derivation_jobs_complete":300,"panel_count":len(data["panels"]),"historical_figure_recovery_claimed":False})
    return {"full_source_execution_verified":True,"corrected_figure_rendered":True,"verified_jobs":300,"panel_count":5}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--bank",type=Path,required=True);p.add_argument("--figure",type=int,choices=[14,16])
    p.add_argument("--config",type=Path,default=Path(__file__).with_name("full_config.json"));p.add_argument("--output-dir",type=Path)
    p.add_argument("--prepare",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--workers",type=int,default=1);args=p.parse_args()
    if args.prepare:
        if args.figure is None:p.error("--prepare requires --figure14 or16")
        if (args.bank/"manifest.json").exists():raise ValueError("Use a fresh bank name; never overwrite existing input/evidence")
        subprocess.run([sys.executable,str(Path(__file__).with_name("figures.py")),"--figure",str(args.figure),"--config",str(args.config),
                        "--output-dir",str(args.bank),"--prepare"],check=True)
        atomic_json(args.bank/"corrected-plan.json",{"paper_id":"two-timescale-ma","figure":args.figure,"scope":"corrected_source_not_historical_recovery",
            "unchanged_original_iid_Algorithm2":True,"exact_original_models":["iid","Eq68_correlated"],"expected_source_jobs":300,
            "geometries_per_kappa":100,"nlos_per_geometry":1000,"Monte_Carlo_count_provenance":COUNT_PROVENANCE,
            "exact_Jensen_integral_not_printed_Eq75":True,"historical_figure_recovery_claimed":False,"executed":False})
    if args.execute:
        if not 1<=args.workers<=4:raise ValueError("Resource-bounded1..4 workers required")
        execute(args.bank,args.workers)
    if args.execute or args.output_dir:
        print(json.dumps(derive(args.bank,args.output_dir or args.bank/"corrected-source-figures")),flush=True)
