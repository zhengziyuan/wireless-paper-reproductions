"""Reduced independent MIS communications algorithm, using the shared fixture."""
import argparse
import numpy as np
from model import MISModel, load_fixture, phase_ascent, dump_output


def run():
    f = load_fixture()
    model = MISModel(f)
    initial_min = float(np.min(model.selected(model.initial)[0]))
    baseline, _ = phase_ascent(model, model.initial, f["static_iterations"],
                              f["smoothing_mu"], static=True)
    static_min = float(np.min(model.selected(baseline)[0]))
    best, history = baseline, []
    best_min = static_min
    for start in [baseline, model.initial]:
        candidate, trajectory = phase_ascent(model, start, f["iterations"], f["smoothing_mu"])
        minimum = float(np.min(model.selected(candidate)[0]))
        if minimum >= best_min:
            best, history, best_min = candidate, trajectory, minimum
    rates, _, _, _, _ = model.evaluate(best)
    selected, _, schedule = model.selected(best)
    value, _ = model.softmin(best, f["smoothing_mu"])
    checks = model.diagnostics(best)
    checks.update({
        "gradient_pass": checks["rate_gradient_relative_error"] < 1e-6,
        "constraint_pass": checks["unit_modulus_error"] < 1e-12 and checks["one_hot_row_sum_error"] == 0,
        "static_incumbent_retained": bool(best_min + 1e-12 >= static_min),
        "softmin_lower_bound_error": float(max(0, value - best_min)),
        "softmin_upper_bound_error": float(max(0, best_min - value - f["smoothing_mu"] * np.log(model.K))),
    })
    if history:
        trajectory_values = [row["softmin"] for row in history]
        checks["accepted_objective_monotonicity_error"] = float(max(
            0, -min(np.diff(trajectory_values), default=0)))
    else:
        checks["accepted_objective_monotonicity_error"] = 0.0
    return {
        "paper_id": f["paper_id"],
        "metrics": {
            "initial_worst_snr": initial_min, "optimized_static_worst_snr": static_min,
            "optimized_mis_worst_snr": best_min, "mis_gain_over_static": best_min - static_min,
            "selected_user_snr": selected.tolist(), "snr_by_user_and_position": rates.tolist(),
            "selected_position_index_one_based": (schedule + 1).tolist(),
            "ms1_phase_radians": best[:model.M].tolist(), "ms2_phase_radians": best[model.M:].tolist(),
            "softmin_value": float(value), "smoothing_gap_bound": float(f["smoothing_mu"] * np.log(model.K)),
        },
        "checks": checks, "history": history,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run()
    dump_output(result, args.output)
    print("MIS communications:", result["metrics"]["optimized_mis_worst_snr"])

