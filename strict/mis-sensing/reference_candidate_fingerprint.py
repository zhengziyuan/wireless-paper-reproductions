"""Original-model, full-dimension parameter fingerprint, NOT a 6000-start figure.

Every four-target/six-power case uses the original RALM per-start budgets and
one explicitly deterministic continuous-target matching initializer. A scalar
effective normalization factor is supplied by its separately marked settings.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from engine import Model, sensing_solve, serialize
import run

HERE=Path(__file__).resolve().parent
REFERENCE=HERE.parent/"figure-reference/mis-sensing-fig15.json"


def source_hashes(settings_path):
    # Bind the files actually executed by Python. Unexecuted MATLAB/test-file
    # edits must not invalidate a frozen Python computation.
    files=[HERE/name for name in ["engine.py","run.py","normalization.py","reference_candidate_fingerprint.py"]]
    files += [Path(settings_path),REFERENCE]
    return {file.name:hashlib.sha256(file.read_bytes()).hexdigest()
            for file in sorted(files,key=lambda file:file.name)}


def run_fingerprint(settings_path):
    settings_path=Path(settings_path)
    settings=json.loads(settings_path.read_text())
    if (settings["number_of_starts"],settings["outer_iterations"],settings["rcg_max_iterations"])!=(6000,30,4000):
        raise ValueError("Fingerprint uses complete original per-start budgets; no reduced configuration allowed")
    hashes=source_hashes(settings_path)
    reference=json.loads(REFERENCE.read_text())
    began=time.perf_counter();points=[]
    for power in range(15,31,3):
        model=run.make_model(dict(ms1=[10,10],ms2=[0,0],Kphi=2,Ktheta=2,power_dbm=power),settings)
        targets=[]
        for target in range(model.targets):
            order=[target]+[j for j in range(model.targets) if j!=target]
            cfg=dict(model.config,
                     azimuth_deg=[model.config["azimuth_deg"][j] for j in order],
                     elevation_deg=[model.config["elevation_deg"][j] for j in order],
                     number_of_targets=1,
                     echo_beta_squared=model.beta[order].tolist())
            ris=Model(cfg)
            state=dict(phi=np.conj(ris.c[0]),theta=np.empty(0,dtype=complex),
                       X=np.ones((1,1)),eta=np.asarray(settings["initialization"]["eta_initial"]))
            started=time.perf_counter()
            state,history,metrics=sensing_solve(ris,state,run.solver_options(settings),"sinr")
            quantized={}
            for bits,name in [(1,"one_bit"),(2,"two_bit")]:
                step=2*np.pi/(2**bits)
                z=dict(state,phi=np.exp(1j*step*np.floor(np.angle(state["phi"])/step+.5)))
                quantized[name]=float(ris.metric(z,"sinr")[0,0])
            targets.append(dict(target_index=target,
                                target_azimuth_deg=model.config["azimuth_deg"][target],
                                target_elevation_deg=model.config["elevation_deg"][target],
                                metrics=metrics,
                                solver_status=run.solver_diagnostics(history,settings,"sinr"),
                                history=history,state=serialize(state),quantized_sinr=quantized,
                                elapsed_seconds=time.perf_counter()-started))
        minimum={"RIS continuous":min(t["metrics"]["min_binary_metric"] for t in targets),
                 "RIS 1-bit":min(t["quantized_sinr"]["one_bit"] for t in targets),
                 "RIS 2-bit":min(t["quantized_sinr"]["two_bit"] for t in targets)}
        values={label:float(10*np.log10(value)) for label,value in minimum.items()}
        points.append(dict(power_dbm=power,normalization_contract=model.config["normalization_contract"],
                           target_runs=targets,minimum_sinr_db=values))
        print(json.dumps(dict(power_dbm=power,minimum_sinr_db=values)),flush=True)
    comparisons=[]
    for curve in reference["curves"]:
        label=curve["label"]
        if label not in points[0]["minimum_sinr_db"]:continue
        values=np.array([p["minimum_sinr_db"][label] for p in points])
        errors=values-np.asarray(curve["y"])
        comparisons.append(dict(label=label,power_dbm=curve["x"],original_plot_vector_reference_db=curve["y"],
                                independently_evaluated_simulation_db=values.tolist(),errors_db=errors.tolist(),
                                maximum_absolute_error_db=float(np.max(np.abs(errors))),
                                root_mean_square_error_db=float(np.sqrt(np.mean(errors**2)))))
    unchanged=hashes==source_hashes(settings_path)
    return dict(paper_id="mis-sensing",language="python",figure="fig15_RIS_parameter_fingerprint",
                data_kind="independent_original_model_parameter_fingerprint_simulation_NOT_original_reference_copy",
                scope="four_original_targets_six_original_powers_one_deterministic_full_budget_start_NOT_6000_start_figure",
                initializer="conjugate_target_steering_no_fitted_phases",
                quantization="nearest_fixed_zero_alphabet_no_fitted_global_rotation_no_separate_discrete_optimizer",
                normalization_origin="effective_factor_inferred_physical_attribution_not_uniquely_identified_NOT_author_Tp_count_verified",
                settings=settings,original_number_of_starts=settings["number_of_starts"],
                executed_starts_per_target_point=1,point_count=len(points),target_count=4,
                source_hashes=hashes,source_hash_scope="executed_python_modules_selected_settings_original_reference",
                runtime_source_unchanged=unchanged,
                original_reference_sha256=reference["source_sha256"],points=points,comparison=comparisons,
                all_selected_targets_feasible=all(t["metrics"]["maximum_constraint"]<=settings["feasibility_tolerance"] for p in points for t in p["target_runs"]),
                all_stopping_criteria_verified=all(t["solver_status"]["convergence_verified"] for p in points for t in p["target_runs"]),
                all_original_parameter_values_recovered=False,full_figure_execution_complete=False,
                original_figure_reproduction_certified=False,elapsed_seconds=time.perf_counter()-began)


def render_fingerprint(receipt,output_prefix):
    """Original vectors are dashed reference overlays, never simulation curves."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":11,"axes.labelsize":12,"lines.linewidth":1.6})
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout="constrained")
    colors={"RIS continuous":"#197e89","RIS 2-bit":"#b96b13","RIS 1-bit":"#b33c70"}
    for curve in receipt["comparison"]:
        label=curve["label"];color=colors[label];x=curve["power_dbm"]
        axes[0].plot(x,curve["original_plot_vector_reference_db"],"--",color=color,alpha=.65,label=label+" / original reference")
        axes[0].plot(x,curve["independently_evaluated_simulation_db"],"o-",color=color,markersize=4,label=label+" / computed candidate")
        axes[1].plot(x,curve["errors_db"],"o-",color=color,label=label)
    axes[0].set_ylabel("Worst-target sensing SINR (dB)")
    axes[1].set_ylabel("Computed minus original reference (dB)")
    for ax in axes:
        ax.set_xlabel("BS transmit power (dBm)");ax.set_xticks([15,18,21,24,27,30]);ax.grid(alpha=.25)
    axes[1].axhline(0,color="0.3",linewidth=.7)
    axes[0].legend(fontsize=8,loc="upper left");axes[1].legend(fontsize=9,loc="best")
    gain=receipt["settings"]["effective_reference_gain_factor"]
    fig.suptitle(f"Full 10x10 RIS, four targets, six power points | explicit {gain:g}-fold normalization contract\nOne deterministic original-RALM start per target; NOT the complete 6000-start figure",fontsize=11)
    output_prefix=Path(output_prefix);output_prefix.parent.mkdir(parents=True,exist_ok=True)
    for suffix in [".png",".svg"]:fig.savefig(output_prefix.with_suffix(suffix),dpi=170)
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--settings",type=Path,default=HERE/"settings_reference_candidate.json")
    parser.add_argument("--output",type=Path,default=HERE/"outputs/reference-candidate-v2/ris-fingerprint-python.json")
    parser.add_argument("--render-receipt",type=Path,help="Render an existing actual receipt, without simulating again")
    args=parser.parse_args()
    if args.render_receipt:receipt=json.loads(args.render_receipt.read_text())
    else:
        receipt=run_fingerprint(args.settings)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(receipt,indent=2),encoding="utf-8")
        if not receipt["runtime_source_unchanged"]:raise RuntimeError("Sources changed during execution; receipt preserved but must not be treated as frozen evidence")
    render_fingerprint(receipt,args.output.with_suffix(""))
    print(json.dumps({k:receipt[k] for k in ["scope","comparison","all_selected_targets_feasible","all_stopping_criteria_verified","original_figure_reproduction_certified"]}))


if __name__=="__main__":main()
