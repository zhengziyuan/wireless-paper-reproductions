"""Full100-channel renderer with the paper's exact series selection.

Incomplete/failed banks produce a readiness receipt, never a survivor average.
This adapter is separate from the solver and does not change running inputs.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from isac_metadata import bank_complete,complete,implementation_fingerprint


def aggregate(bank,engine="python"):
    config_bytes=(bank/"run_config.json").read_bytes();manifest=json.loads((bank/"manifest.json").read_text())
    plan=json.loads((bank/"plan.json").read_text());catalog=json.loads(Path(__file__).with_name("figure_catalog.json").read_text())
    if manifest.get("realizations_per_case")!=100 or not bank_complete(bank/"jobs",manifest,config_bytes):
        raise ValueError("All100 unchanged channel inputs per point required")
    if engine!="python":raise ValueError("MATLAB verification is separate; no mixed-engine aggregation")
    case_results=[[] for _ in plan["cases"]];missing=[];invalid=[]
    for entry in manifest["files"]:
        result_path=bank/(Path(entry["filename"]).stem+f"-{engine}.json")
        if not result_path.exists():missing.append(result_path.name);continue
        try:result=json.loads(result_path.read_text())
        except (OSError,ValueError):invalid.append(result_path.name);continue
        if not complete(result,entry["input_fingerprint"]):invalid.append(result_path.name);continue
        case_results[entry["case_index"]].append(result)
    ready=not missing and not invalid and all(len(items)==100 for items in case_results)
    receipt={"paper_id":"rotatable-isac","family":plan["family"],"engine":engine,
        "expected_jobs":manifest["expected_jobs"],"full_execution_verified":ready,
        "input_bank_complete":True,"complete_jobs":sum(map(len,case_results)),
        "missing_results":missing,"invalid_or_nonconverged_results":invalid,
        "failed_samples_discarded_for_curve":False,"channels_per_point":100,
        "implementation_fingerprint":implementation_fingerprint(),"original_curve_closeness_verified":False}
    if not ready:return receipt,[]
    figures=[]
    for spec in catalog["numerical_figures"]:
        if spec["family"]!=plan["family"]:continue
        series=[]
        if spec["series"]=="rotation_reference_series":
            for legend in catalog["rotation_reference_series"]:
                pairs=[(case,items) for case,items in zip(plan["cases"],case_results)
                    if case["rotation_legend"]["swept_array"]==legend["swept_array"]
                    and case["rotation_legend"]["other_fixed_half_width_deg"]==legend["other_fixed_half_width_deg"]]
                pairs.sort(key=lambda pair:pair[0]["point"])
                series.append({"label":legend["legend"],"scheme":legend["scheme"],
                    "x":[case["point"] for case,_ in pairs],
                    "y":[float(np.mean([r["metrics"][legend["scheme"]][spec["y"]] for r in items])) for _,items in pairs]})
        else:
            names=catalog[spec["series"]]
            for name in names:
                values=lambda items,key:float(np.mean([r["metrics"][name][key] for r in items]))
                x=[values(items,"nmse") if spec.get("parametric") else case["point"] for case,items in zip(plan["cases"],case_results)]
                series.append({"label":name,"scheme":name,"x":x,"y":[values(items,spec["y"]) for items in case_results]})
        figures.append({**receipt,"figure":spec["figure"],"data_kind":"independent_simulation_curves",
            "source_artifact":spec["source_artifact"],"x_name":spec["x"],"x_unit":spec["x_unit"],
            "y_name":spec["y"],"y_unit":spec["y_unit"],"series":series,
            "aggregation":"arithmetic mean over all100 verified channels, no dropped sample",
            "x_direction":spec.get("x_direction","increasing_left_to_right"),
            "reference_x_limits_left_to_right":spec.get("reference_x_limits_left_to_right")})
    return receipt,figures


def render(data,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.2,4.8));markers=["o","s","^","D","v","P"]
    for i,series in enumerate(data["series"]):
        ax.plot(series["x"],series["y"],label=series["label"],marker=markers[i%len(markers)],linewidth=1.6,markersize=4)
    if data.get("reference_x_limits_left_to_right"):ax.set_xlim(*data["reference_x_limits_left_to_right"])
    ax.set_xlabel(f'{data["x_name"]} ({data["x_unit"]})');ax.set_ylabel(f'{data["y_name"]} ({data["y_unit"]})')
    ax.grid(True,alpha=.25);ax.legend(fontsize=8);fig.tight_layout()
    fig.savefig(path.with_suffix(".png"),dpi=220);fig.savefig(path.with_suffix(".svg"));plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--bank",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True);receipt,figures=aggregate(args.bank)
    (args.output_dir/"readiness.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    for data in figures:
        path=args.output_dir/f'isac-figure-{data["figure"]:02d}'
        path.with_suffix(".json").write_text(json.dumps(data,indent=2,allow_nan=False)+"\n",encoding="utf-8");render(data,path)
    print(json.dumps({"full_execution_verified":receipt["full_execution_verified"],"figures_rendered":len(figures),"complete_jobs":receipt["complete_jobs"]}))
