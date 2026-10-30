"""Check saved AO sweep-boundary geometry using exact binary64 arithmetic.

This does not re-run the optimizer and does not validate intermediate coordinate
updates, original paper curves, the MATLAB run, or a full figure.
"""
import argparse
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path


def F(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("A finite JSON number is required")
    return Fraction.from_float(float(value))


def run(job, cfg, result):
    n = job["N"]
    if type(n) is not int or n < 2 or result.get("mode") != "full_scenario":
        raise ValueError("Invalid saved case")
    for k in ("N", "M", "A", "figure", "point", "realization", "power", "kappa"):
        if job[k] != result["job_metadata"][k]:
            raise ValueError("Saved case metadata mismatch: " + k)
    nr, nc = cfg["antenna_factorization"][str(n)]
    if nr * nc != n:
        raise ValueError("Factorization mismatch")
    if (n, job["M"], job["A"], job["figure"], job["point"], job["realization"], nr, nc) != (6, 5, 2, 5, 30, 0, 2, 3):
        raise ValueError("This witness is scoped to the saved Fig.5 case7 geometry0")
    if "region_lower" in job or "region_upper" in job or "antenna_position_error" in job:
        raise ValueError("Unexpected case-specific geometry override")
    a = F(job["A"])
    default_lo = [-nr*a/2, -nc*a/2]
    default_hi = [nr*a/2, nc*a/2]
    lo = [F(x) for x in job["region_lower"]] if "region_lower" in job else default_lo
    hi = [F(x) for x in job["region_upper"]] if "region_upper" in job else default_hi
    if len(lo) != 2 or len(hi) != 2 or any(l > h for l, h in zip(lo, hi)):
        raise ValueError("Invalid region")
    # run.scenario specifies a normalized minimum spacing of one-half wavelength.
    minimum_spacing = Fraction(1, 2)
    output = {}
    for mode in ("mrt", "zf"):
        history = result["history"][mode]
        poses = history["positions"]
        if not poses or len(poses) != len(history["objective"]):
            raise ValueError("Missing saved sweep positions")
        if (poses[-1] != result["metrics"][mode+"_positions"] or
                poses[-1] != result["metrics"][mode+"_realized_positions"]):
            raise ValueError("Saved final and realized positions differ")
        smallest = None
        margin = None
        spacing_violations = box_violations = pair_checks = point_checks = 0
        start_spacing = end_spacing = None
        for sweep_index, pose in enumerate(poses):
            if len(pose) != n or any(len(x) != 2 for x in pose):
                raise ValueError("Saved position shape mismatch")
            points = [[F(x) for x in row] for row in pose]
            sweep_min = None
            for x, y in itertools.combinations(points, 2):
                d2 = sum((a-b)**2 for a, b in zip(x, y))
                smallest = d2 if smallest is None else min(smallest, d2)
                sweep_min = d2 if sweep_min is None else min(sweep_min, d2)
                spacing_violations += d2 < minimum_spacing**2
                pair_checks += 1
            if sweep_index == 0:
                start_spacing = sweep_min
            if sweep_index == len(poses)-1:
                end_spacing = sweep_min
            for pt in points:
                m = min(pt[0]-lo[0], hi[0]-pt[0], pt[1]-lo[1], hi[1]-pt[1])
                margin = m if margin is None else min(margin, m)
                box_violations += m < 0
                point_checks += 1
        output[mode] = {
            "saved_sweep_positions_including_initial": len(poses),
            "pair_spacing_checks": pair_checks,
            "antenna_box_checks": point_checks,
            "strict_spacing_violation_count": spacing_violations,
            "strict_box_violation_count": box_violations,
            "minimum_squared_spacing_exact": str(smallest),
            "minimum_box_margin_exact": str(margin),
            "minimum_squared_spacing_float": float(smallest),
            "initial_squared_spacing_float": float(start_spacing),
            "final_squared_spacing_float": float(end_spacing),
            "minimum_box_margin_float": float(margin),
        }
    return {
        "schema": "MA_SAVED_AO_SWEEP_GEOMETRY_EXACT_BINARY64_V1",
        "case": result["job_metadata"],
        "box_lower": [float(x) for x in lo],
        "box_upper": [float(x) for x in hi],
        "minimum_spacing": float(minimum_spacing),
        "modes": output,
        "scope": "All stored AO sweep-boundary positions including initial; exact rational comparisons of saved binary64 values.",
        "limits": ["Does not verify coordinate updates between sweep boundaries.",
                   "No recomputation of rates, optimality, convergence, MATLAB, figure or paper agreement.",
                   "No forward-error or interval certification for numerical positions."],
        "optimizer_or_monte_carlo_reexecuted": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("saved_input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    data = json.loads(args.saved_input.read_text(encoding="utf8"))
    if data["schema"] != "MA_FIG5_CASE7_SAVED_SWEEP_GEOMETRY_INPUT_V1":
        raise ValueError("Unexpected source input")
    result = run(data["job"], data["config"], data["result"])
    with args.output.open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")


if __name__ == "__main__":
    main()
