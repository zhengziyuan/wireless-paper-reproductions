"""Full100x1000 MA figure aggregation with explicit terminal hold.

No average over successful survivors, invented iterations or replacement
correlated-Wishart formula. Incomplete full banks yield readiness only.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from ma_metadata import bank_complete,complete,implemented_complete,implementation_fingerprint,original_scope_available
from figures import write_or_verify


def terminal_hold_mean(values):
    """Final accepted iterate held unchanged; no fictitious AO update."""
    arrays=[np.asarray(value,dtype=float) for value in values]
    if not arrays or any(a.ndim!=1 or not len(a) or not np.all(np.isfinite(a)) for a in arrays):
        raise ValueError("All100 finite nonempty original trajectories required")
    length=max(map(len,arrays));return np.mean([np.pad(a,(0,length-len(a)),mode="edge") for a in arrays],axis=0)


def nested(record,path):
    for name in path.split("."):record=record[name]
    return record


def checked_saved_mean(record, name, expected_count):
    """Validate the saved plotted mean against its complete stored samples.

    This is an engineering consistency check only; it does not establish
    convergence, physical feasibility or agreement with a paper figure.
    The tolerance bounds accumulated binary64 roundoff for two nonnegative
    sums and subsequent division. Subnormal inputs fail closed rather than relying
    on an unsupported relative-error bound.
    """
    metric=nested(record,name) if name.startswith("metrics.") else record["metrics"]["schemes"][name]
    rates=metric["sample_sum_rates"]; saved=metric["mean_sum_rate"]
    if not isinstance(rates,list) or type(expected_count) is not int or expected_count<=0 or len(rates)!=expected_count:
        raise ValueError("incomplete saved rate samples")
    if type(saved) not in (int,float) or not math.isfinite(saved) or saved<0:
        raise ValueError("invalid saved rate mean")
    tiny=np.finfo(float).tiny
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 or (0<x<tiny) for x in rates):
        raise ValueError("invalid or subnormal saved rate")
    with np.errstate(over="ignore",invalid="ignore"):
        observed=float(np.mean(rates))
    if not math.isfinite(observed) or (0<observed<tiny) or (0<saved<tiny):
        raise ValueError("invalid or subnormal rate mean")
    unit_roundoff=np.finfo(float).eps/2
    nu=(expected_count+4)*unit_roundoff
    if nu>=1:raise ValueError("unsupported sample count for rounding bound")
    allowance=(2*nu/(1-nu))*max(abs(observed),abs(saved))
    if abs(saved-observed)>allowance:raise ValueError("saved mean is inconsistent with samples")
    return float(saved)


def aggregate(bank):
    config_bytes=(bank/"run_config.json").read_bytes();config=json.loads(config_bytes)
    manifest=json.loads((bank/"manifest.json").read_text());plan=json.loads((bank/"plan.json").read_text())
    if (config["geometry_realizations"]!=100 or config["nlos_realizations_per_geometry"]!=1000
        or not bank_complete(bank/"jobs",manifest,config_bytes)):
        raise ValueError("Immutable full100 geometry x1000 NLoS bank required")
    catalog=json.loads(Path(__file__).with_name("figure_catalog.json").read_text())
    spec=next(item for item in catalog["numerical_figures"] if item["figure"]==plan["figure"])
    by_case=[[] for _ in plan["cases"]];missing=[];invalid=[];original_scope=all(original_scope_available(c) for c in plan["cases"])
    for entry in manifest["files"]:
        path=bank/(Path(entry["filename"]).stem+"-python.json")
        if not path.exists():missing.append(path.name);continue
        try:record=json.loads(path.read_text())
        except (OSError,ValueError):invalid.append(path.name);continue
        try:
            job=json.loads((bank/"jobs"/entry["filename"]).read_text())
            valid=implemented_complete(record,entry["input_fingerprint"],job,config)
        except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError):
            invalid.append(path.name);continue
        if not valid:invalid.append(path.name);continue
        if plan["figure"] not in [3,4,13,14,15,16]:
            names=catalog["default_schemes"] if spec["series"]=="default_schemes" else spec["series"]
            try:
                for name in names:checked_saved_mean(record,name,config["nlos_realizations_per_geometry"])
            except (KeyError,TypeError,ValueError,OverflowError,AttributeError):invalid.append(path.name);continue
        by_case[entry["case_index"]].append(record)
    ready=not missing and not invalid and all(len(items)==100 for items in by_case)
    receipt={"paper_id":"two-timescale-ma","figure":plan["figure"],"engine":"python",
        "input_bank_complete":True,"expected_jobs":manifest["expected_jobs"],"complete_jobs":sum(map(len,by_case)),
        "overall_implemented_scope_success":ready,"full_execution_verified":False,
        "original_scenarios_independently_verified":False,
        "original_scope_available":original_scope,"printed_correlated_ZF_closed_form_recovered":False,
        "missing_results":missing,"invalid_or_nonconverged_results":invalid,"geometries_per_point":100,"nlos_per_geometry":1000,
        "failed_samples_discarded_for_curve":False,"original_curve_closeness_verified":False,
        "implementation_fingerprint":implementation_fingerprint()}
    if not ready or not original_scope:return receipt,None
    figure=spec["figure"];series=[]
    if figure in [3,4,13,14,15,16]:
        for case,items in zip(plan["cases"],by_case):
            for source_path in spec["series"]:
                curve=terminal_hold_mean([nested(r,source_path) for r in items])
                series.append({"label":f'{source_path}; kappa={case["kappa"]:.6g}',"source_path":source_path,
                    "x":list(range(len(curve))),"y":curve.tolist()})
        aggregation="all100 original trajectories; final accepted state explicitly held for unequal stopping lengths; no fictitious updates"
    else:
        names=catalog["default_schemes"] if spec["series"]=="default_schemes" else spec["series"]
        groups={}
        for index,case in enumerate(plan["cases"]):
            key=(case["N"],case["M"] if figure not in [11,12] else None,case["kappa"] if figure not in [7,8] else None)
            groups.setdefault(key,[]).append(index)
        for key,indices in groups.items():
            indices.sort(key=lambda i:plan["cases"][i]["point"])
            for name in names:
                if name.startswith("metrics."):
                    values=[float(np.mean([nested(r,name)["mean_sum_rate"] for r in by_case[i]])) for i in indices]
                else:values=[float(np.mean([r["metrics"]["schemes"][name]["mean_sum_rate"] for r in by_case[i]])) for i in indices]
                x=[plan["cases"][i]["point"]*(100 if figure==18 else 1) for i in indices]
                label=f'{name}; N={key[0]}'+(f', kappa={key[2]:.6g}' if key[2] is not None else '')
                series.append({"label":label,"scheme":name,"x":x,"y":values})
        aggregation="mean all1000 NLoS draws within each geometry, then mean all100 geometries; no discarded sample"
    return receipt,{**receipt,"data_kind":"independent_simulation_curves","source_artifact":spec["source_artifact"],
        "x_name":spec["x"],"x_unit":spec["x_unit"],"y_name":spec["y"],"y_unit":spec["y_unit"],
        "aggregation":aggregation,"series":series}


def render(data,path):
    import io
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams['svg.hashsalt']='two-timescale-ma-v2'
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8.2,5.2));markers=["o","s","^","D","v","P"]
    for i,series in enumerate(data["series"]):
        ax.plot(series["x"],series["y"],label=series["label"],marker=markers[i%6],linewidth=1.5,
            markersize=3,markevery=max(1,len(series["x"])//12))
    ax.set_xlabel(f'{data["x_name"]} ({data["x_unit"]})');ax.set_ylabel(f'{data["y_name"]} ({data["y_unit"]})')
    ax.grid(True,alpha=.25);ax.legend(fontsize=6);fig.tight_layout()
    # Compare fully rendered bytes before any existing file can be reused.
    # A partial render remains evidence and is never silently overwritten.
    try:
        png=io.BytesIO();svg=io.BytesIO()
        fig.savefig(png,format='png',dpi=220)
        fig.savefig(svg,format='svg',metadata={'Date':None})
        write_or_verify(path.with_suffix('.png'),png.getvalue())
        write_or_verify(path.with_suffix('.svg'),svg.getvalue())
    finally:plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--bank",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True);receipt,data=aggregate(args.bank)
    write_or_verify(args.output_dir/"readiness_v2.json",(json.dumps(receipt,indent=2)+"\n").encode())
    if data is not None:
        path=args.output_dir/f'ma-figure-{data["figure"]:02d}-v2'
        write_or_verify(path.with_suffix(".json"),(json.dumps(data,indent=2,allow_nan=False)+"\n").encode());render(data,path)
    print(json.dumps({"full_execution_verified":receipt["full_execution_verified"],"figure_rendered":data is not None,"complete_jobs":receipt["complete_jobs"]}))
