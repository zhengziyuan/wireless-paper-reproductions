"""Compare two saved outputs; does not reproduce the MATLAB simulation."""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(path):
    with path.open("rb") as f:
        raw = f.read(262145)
    if len(raw) > 262144:
        raise ValueError("saved output exceeds input limit")
    return json.loads(raw)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matlab-output', type=Path, default=ROOT / 'matlab-result.json')
    args = parser.parse_args()
    p = load(ROOT / "python_winner_projection.json")
    m = load(args.matlab_output)
    if p.get("sample_count_per_mode") != 1000 or m.get("sample_count_per_mode") != 1000:
        raise ValueError("sample count mismatch")
    if len(p["modes"]) != 2 or len(m["modes"]) != 2:
        raise ValueError("mode count mismatch")
    rows = []
    for a, b in zip(p["modes"], m["modes"]):
        if a["mode"] != b["mode"] or a["grid_indices_zero_based"] != b["grid_indices_zero_based"] or a["positions"] != b["positions"]:
            raise ValueError("saved mode or winner mismatch")
        x, y = a["original_instantaneous_return"], b["original_native_instantaneous_return"]
        row = {"mode": a["mode"], "python_mean_sum_rate": x["mean_sum_rate"], "matlab_mean_sum_rate": y["mean_sum_rate"]}
        for key in ("sample_sum_rates", "powers", "off_diagonal_amplitude"):
            aa, bb = x[key], y[key]
            if len(aa) != 1000 or len(bb) != 1000 or not all(math.isfinite(t) for t in aa + bb):
                raise ValueError("sample count or finite check failed")
            row[key + "_max_abs_difference"] = max(abs(u-v) for u,v in zip(aa,bb))
        if any(t < 0 for t in y["sample_sum_rates"]):
            raise ValueError("negative MATLAB saved rate")
        rows.append(row)
    print(json.dumps({"scope":"saved outputs only; no independent search or input authentication", "modes":rows},separators=(",",":"), allow_nan=False))

if __name__ == "__main__":
    main()
