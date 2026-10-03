"""Render model-evaluated MIS outputs, refusing incomplete or reference-only data.

PNG/SVG and a provenance receipt are written together. Display cropping changes
neither computed samples nor physical scenarios. No curve is fabricated to fill
a missing point. Original-figure agreement remains a separate comparison gate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def finite(values):
    array = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError("Nonfinite numerical samples are not plot-ready")
    return array


def db(values):
    values = finite(values)
    if np.any(values <= 0):
        raise ValueError("Nonpositive log ordinate; no undisclosed floor")
    return 10 * np.log10(values)


def best(entry, key="result"):
    run = entry[key]
    result = run.get("best_feasible")
    if result is None:
        raise ValueError("Missing feasible optimized result; do not replace it with a reference")
    return result


def save(fig, folder, basename):
    fig.savefig(folder / (basename + ".png"), dpi=180)
    fig.savefig(folder / (basename + ".svg"))
    plt.close(fig)


def render_sensing_beams(data, folder):
    points = data["points"]
    if len(points) != 1:
        raise ValueError("Beampattern source requires one complete original configuration")
    samples = points[0]["beampattern_samples"]
    az, el = finite(samples["azimuth_deg"]), finite(samples["elevation_deg"])
    panels = samples["maps"]
    if len(panels) != 9:
        raise ValueError("Original figure requires all nine target panels")
    fig, axes = plt.subplots(3, 3, figsize=(12.5, 9.8), constrained_layout=True)
    scalars = []
    for index, (ax, panel) in enumerate(zip(axes.flat, panels)):
        values = finite(panel["normalized_gain"])
        if values.shape != (len(el), len(az)) or panel["target"] != index:
            raise ValueError("Target order or full beampattern grid mismatch")
        # Original display uses a -35dB color limit; data remain unmodified.
        handle = ax.pcolormesh(az, el, 10*np.log10(np.maximum(values, 1e-300)),
                               shading="auto", cmap="viridis", vmin=-35, vmax=0, rasterized=True)
        ta, te = panel["target_azimuth_deg"], panel["target_elevation_deg"]
        ax.scatter([ta], [te], marker="x", s=60, c="white", linewidths=1.7)
        metric = float(db(panel["target_metric"]))
        ax.set(xlim=(-15, 105), ylim=(20, 80), xticks=[0, 45, 90], yticks=[30, 50, 70],
               xlabel="Azimuth (degrees)", ylabel="Elevation (degrees)",
               title=f"Target {index+1}: {panel['target_metric_name']} {metric:.2f} dB")
        scalars.append({"target": index+1, "azimuth_deg": ta, "elevation_deg": te,
                        "metric": panel["target_metric_name"], "metric_db": metric})
    fig.colorbar(handle, ax=list(axes.flat), label="Normalized gain (dB)", shrink=.75)
    fig.suptitle(f"{data['figure']} · independent full-size calculation · reference agreement NOT verified", fontsize=12)
    save(fig, folder, data["figure"])
    return {"kind": "nine_beampattern_panels", "target_metrics": scalars,
            "computed_grid": [len(el), len(az)], "display_crop_only": [-15, 105, 20, 80],
            "color_display_limits_db": [-35, 0], "simulation_samples_modified": False}


def sensing_curves(data):
    number = int(data["figure"].removeprefix("fig"))
    groups = {}
    def add(label, x, y):
        groups.setdefault(label, []).append((float(x), float(y)))
    for entry in data["points"]:
        cfg, run = entry["configuration"], entry["result"]
        if number in (7, 8, 15):
            x = cfg["power_dbm"]
        elif number in (9, 10, 11, 12):
            x = cfg["ms1"][0]
        elif number in (13,14):
            # The original four groups share Kphi=2..7 display positions.
            # Tick labels express Kphi*Ktheta; different Ktheta groups must
            # not be shifted to unrelated x positions.
            x = cfg["Kphi"]
        else:
            x = cfg["Kphi"] * cfg["Ktheta"]
        if number in (15, 16):
            add("MIS", x, db(best(entry)["metrics"]["min_binary_metric"]))
            for source, label in (("one_bit", "RIS 1-bit"), ("two_bit", "RIS 2-bit"), ("continuous", "RIS continuous")):
                add(label, x, db(np.min(entry["RIS"][source])))
        elif number in (7, 8, 11, 12):
            label = f"N={cfg['ms2'][0]}"
            y = run["minimum_sinr"] if number == 8 else best(entry)["metrics"]["min_binary_metric"]
            add(label, x, db(y))
            if number == 8 and cfg["ms2"][0] == 6:
                add("RALM N=6", x, db(best(entry, "RALM_reference")["metrics"]["min_binary_metric"]))
        elif number in (9, 10):
            label = f"gap={cfg['gap']}"
            y = run["minimum_sinr"] if number == 10 else best(entry)["metrics"]["min_binary_metric"]
            add(label, x, db(y))
            if number == 10 and cfg["gap"] == 4:
                add("RALM gap=4", x, db(best(entry, "RALM_reference")["metrics"]["min_binary_metric"]))
        elif number in (13, 14):
            label = f"N={cfg['ms2'][0]}, Ktheta={cfg['Ktheta']}"
            y = run["minimum_sinr"] if number == 14 else best(entry)["metrics"]["min_binary_metric"]
            add(label, x, db(y))
            if number == 14 and cfg["ms2"][0] == 16 and cfg["Ktheta"] == 3:
                add("RALM N=16, Ktheta=3", x, db(best(entry, "RALM_reference")["metrics"]["min_binary_metric"]))
        else:
            raise ValueError("Use the same Fig3 full initialization bank for convergence Figs5/6; do not rerun/select a different best start")
    curves = []
    for label, pairs in groups.items():
        pairs.sort()
        if len(set(x for x,y in pairs)) != len(pairs):
            raise ValueError("Duplicate curve abscissas")
        curves.append({"label": label, "x": [x for x,y in pairs], "y": [y for x,y in pairs]})
    return curves


def render_curves(curves, folder, basename, xlabel, ylabel, reference=None):
    fig, ax = plt.subplots(figsize=(7, 4.8), constrained_layout=True)
    for curve in curves:
        ax.plot(finite(curve["x"]), finite(curve["y"]), "o-", label=curve["label"])
    if reference:
        for curve in reference["curves"]:
            ax.plot(finite(curve["x"]), finite(curve["y"]), "--", alpha=.65,
                    label="Original reference: " + curve["label"])
    ax.set(xlabel=xlabel, ylabel=ylabel, title="Independent calculation · original agreement NOT certified")
    ax.grid(True, alpha=.25)
    ax.legend(fontsize=8)
    save(fig, folder, basename)


def render(source, output, reference_path=None):
    source, output = Path(source), Path(output)
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    if data.get("scope") not in ("full_size_full_budget_independent_reimplementation", "independent_simulation_curves"):
        raise ValueError("Partial starts, components and references cannot be rendered as full original figures")
    if data.get("scope") != "independent_simulation_curves":
        mapping = json.loads((HERE / data["paper_id"] / "figure_map.json").read_text(encoding="utf-8-sig"))
        specification = next(x for x in mapping["figures"] if x["id"] == data["figure"])
        if len(data["points"]) != specification["point_count"] or not data.get("full_figure_execution_complete"):
            raise ValueError("Missing original figure configurations/full execution receipt; refusing partial plot")
    output.mkdir(parents=True, exist_ok=True)
    if data["paper_id"] == "mis-sensing" and data["figure"] in ("fig2", "fig3", "fig4"):
        result = render_sensing_beams(data, output)
    elif data["paper_id"] == "mis-sensing":
        curves = sensing_curves(data)
        document = {"paper_id": data["paper_id"], "figure": int(data["figure"][3:]),
                    "data_kind": "independent_simulation_curves", "curves": curves,
                    "full_execution_verified": bool(data.get("overall_full_success")),
                    "source_result_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        (output / "curves.json").write_text(json.dumps(document, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        reference = json.loads(Path(reference_path).read_text(encoding="utf-8-sig")) if reference_path else None
        render_curves(curves, output, data["figure"], specification["x"], "SINR/PSLR (dB)", reference)
        result = {"kind": "multi_curve", "curve_count": len(curves)}
    elif data.get("data_kind") == "independent_simulation_curves":
        render_curves(data["curves"], output, "figure", data["x_label"], data["y_label"])
        result = {"kind": "multi_curve", "curve_count": len(data["curves"])}
    else:
        raise ValueError("Renderer is not yet implemented for this source schema; no placeholder plot")
    result.update(paper_id=data["paper_id"], figure=data["figure"], source_result_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  full_figure_execution_complete=bool(data.get("full_figure_execution_complete", False)),
                  overall_full_success=bool(data.get("overall_full_success", False)),
                  original_figure_reproduction_certified=False)
    (output / "render_receipt.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    print(json.dumps(render(args.result, args.output_dir, args.reference)))
