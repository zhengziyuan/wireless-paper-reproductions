"""Compare independent simulation curves with original references; never fit them."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def compare(simulation, reference, max_abs_error=None, x_tolerance=.002):
    if simulation.get("data_kind") != "independent_simulation_curves":
        raise ValueError("Only independently computed simulation curves are eligible")
    if reference.get("data_kind") != "original_plot_vector_reference_NOT_simulation":
        raise ValueError("Reference must be explicitly labeled original, not simulation")
    for key in ("paper_id", "figure"):
        if simulation.get(key) != reference.get(key):
            raise ValueError(f"Mismatched {key}")
    if max_abs_error is not None and (not np.isfinite(max_abs_error) or max_abs_error < 0):
        raise ValueError("An explicit finite nonnegative ordinate-error criterion is required")
    if not np.isfinite(x_tolerance) or x_tolerance < 0:
        raise ValueError("Invalid abscissa tolerance")
    def unique_curves(document):
        result = {}
        for curve in document.get("curves", []):
            label = curve["label"]
            if label in result:
                raise ValueError("Duplicate curve label")
            x, y = np.asarray(curve["x"], float), np.asarray(curve["y"], float)
            if x.ndim != 1 or x.size == 0 or y.shape != x.shape or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
                raise ValueError("Empty, nonfinite, or malformed curve")
            if not np.all(np.diff(x) > 0):
                raise ValueError("Curve samples must be strictly ordered, without duplicates")
            result[label] = (x, y)
        if not result:
            raise ValueError("No curves")
        return result
    simulated, original = unique_curves(simulation), unique_curves(reference)
    missing, extra = sorted(original.keys() - simulated.keys()), sorted(simulated.keys() - original.keys())
    curves = []
    complete = not missing and not extra
    for label in sorted(original.keys() & simulated.keys()):
        sx, sy = simulated[label]
        rx, ry = original[label]
        # Reference decimal EPS coordinates need small x calibration tolerance.
        # No interpolation/extrapolation, fitted vertical offsets, or y rescaling.
        distance = np.abs(rx[:, None] - sx[None, :])
        indices = distance.argmin(axis=1)
        matched = distance[np.arange(len(rx)), indices] <= x_tolerance
        grid_complete = bool(len(sx) == len(rx) and matched.all() and len(set(indices.tolist())) == len(rx))
        complete = complete and grid_complete
        difference = sy[indices[matched]] - ry[matched]
        curves.append({"label": label, "reference_samples": len(rx), "simulation_samples": len(sx),
                       "matched_samples": int(matched.sum()), "same_full_grid": grid_complete,
                       "max_abs_error": float(np.max(np.abs(difference))) if difference.size else None,
                       "rmse": float(np.sqrt(np.mean(difference ** 2))) if difference.size else None,
                       "signed_error": difference.tolist(), "matched_x": rx[matched].tolist()})
    eligible = simulation.get("full_execution_verified") is True
    numerical_match = complete and bool(curves) and max_abs_error is not None and all(
        c["max_abs_error"] is not None and c["max_abs_error"] <= max_abs_error for c in curves)
    return {"paper_id": simulation["paper_id"], "figure": simulation["figure"],
            "method": "same-grid absolute ordinate errors; no fitting, interpolation, extrapolation or cherry-picking",
            "x_tolerance": x_tolerance, "explicit_max_abs_error_criterion": max_abs_error,
            "missing_curves": missing, "extra_curves": extra, "all_curves_and_grids_complete": complete,
            "full_execution_verified": eligible, "curves": curves,
            "numerical_agreement_under_explicit_criterion": bool(numerical_match),
            "full_execution_and_reference_agreement": bool(eligible and numerical_match),
            "published_figure_reproduction_certified": False,
            "certification_note": "Numerical agreement alone does not resolve source/version/model contradictions."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulation", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--max-abs-error", type=float)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.simulation.read_text(encoding="utf-8-sig")), json.loads(args.reference.read_text(encoding="utf-8-sig")), args.max_abs_error)
    result["input_sha256"] = {"simulation": hashlib.sha256(args.simulation.read_bytes()).hexdigest(),
                              "reference": hashlib.sha256(args.reference.read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
