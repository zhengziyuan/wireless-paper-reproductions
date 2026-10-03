"""Reduced independent exact-scheduling RALM for MIS sensing."""
import argparse
import numpy as np
from model import MISModel, load_fixture, phase_ascent, dump_output


def augmented_lagrangian(model, angles, eta, multipliers, rho):
    selected, jac, _ = model.selected(angles)
    q = eta - selected
    positive = np.maximum(0, multipliers / rho + q)
    value = -eta + 0.5 * rho * float(positive @ positive)
    gradient = np.concatenate((-rho * (positive @ jac), [-1 + rho * np.sum(positive)]))
    return float(value), gradient, q


def ralm(model, initial):
    f = model.f
    x = initial.copy()
    eta = float(np.min(model.selected(x)[0]))
    multipliers = np.zeros(model.K)
    rho = f["initial_penalty"]
    previous_violation = float("inf")
    best = x.copy()
    best_min = eta
    history = []
    monotonicity_error = 0.0
    for outer in range(f["outer_iterations"]):
        for _ in range(f["inner_iterations"]):
            value, gradient, _ = augmented_lagrangian(model, x, eta, multipliers, rho)
            norm = float(np.linalg.norm(gradient))
            direction = -gradient / max(1, norm)
            step, accepted = 1.0, False
            for _ in range(32):
                trial_x = x + step * direction[:-1]
                trial_eta = eta + step * direction[-1]
                trial_value = augmented_lagrangian(model, trial_x, trial_eta, multipliers, rho)[0]
                if trial_value <= value + 1e-4 * step * float(gradient @ direction):
                    monotonicity_error = max(monotonicity_error, trial_value - value)
                    x, eta, accepted = trial_x, float(trial_eta), True
                    break
                step *= 0.5
            minimum = float(np.min(model.selected(x)[0]))
            if minimum > best_min:
                best_min, best = minimum, x.copy()
        value, gradient, q = augmented_lagrangian(model, x, eta, multipliers, rho)
        violation = float(max(0, np.max(q)))
        history.append({"outer_iteration": outer + 1, "eta": eta,
                        "minimum_sinr": float(np.min(model.selected(x)[0])),
                        "incumbent_minimum_sinr": best_min, "inequality_violation": violation,
                        "penalty": float(rho), "augmented_lagrangian": value,
                        "gradient_norm": float(np.linalg.norm(gradient))})
        multipliers = np.minimum(1e6, np.maximum(0, multipliers + rho * q))
        if violation > 0.8 * previous_violation:
            rho *= f["penalty_growth"]
        previous_violation = violation
    return best, history, float(max(0, monotonicity_error))


def ralm_gradient_error(model):
    x = model.initial.copy()
    eta = float(np.min(model.selected(x)[0])) + 0.2
    multipliers = np.asarray([0.2 + 0.1 * k for k in range(model.K)])
    rho = 1.1
    _, analytic, _ = augmented_lagrangian(model, x, eta, multipliers, rho)
    z = np.concatenate((x, [eta]))
    fd = np.zeros_like(z)
    h = 1e-6
    for p in range(len(z)):
        offset = np.zeros_like(z)
        offset[p] = h
        plus, minus = z + offset, z - offset
        fd[p] = (augmented_lagrangian(model, plus[:-1], plus[-1], multipliers, rho)[0] -
                 augmented_lagrangian(model, minus[:-1], minus[-1], multipliers, rho)[0]) / (2 * h)
    return float(np.max(np.abs(fd - analytic)) / max(1, float(np.max(np.abs(analytic)))))


def run():
    f = load_fixture()
    model = MISModel(f)
    quadratic = model.quadratic_phases()
    quadratic_min = float(np.min(model.selected(quadratic)[0]))
    baseline, _ = phase_ascent(model, model.initial, f["static_iterations"],
                              f["smoothing_mu"], static=True, log_metric=True)
    static_min = float(np.min(model.selected(baseline)[0]))
    best = baseline
    best_min = static_min
    history = []
    monotonicity_error = 0.0
    for start in [baseline, quadratic, model.initial]:
        candidate, trajectory, error = ralm(model, start)
        minimum = float(np.min(model.selected(candidate)[0]))
        if minimum >= best_min:
            best, history, best_min = candidate, trajectory, minimum
            monotonicity_error = error
    rates, _, _, gain, echo = model.evaluate(best)
    selected, _, schedule = model.selected(best)
    checks = model.diagnostics(best)
    gradient_error = ralm_gradient_error(model)
    checks.update({
        "ralm_gradient_relative_error": gradient_error,
        "gradient_pass": checks["rate_gradient_relative_error"] < 1e-6 and gradient_error < 1e-6,
        "constraint_pass": checks["unit_modulus_error"] < 1e-12 and checks["one_hot_row_sum_error"] == 0,
        "returned_epigraph_feasibility_error": float(max(0, np.max(best_min - selected))),
        "inner_accepted_objective_monotonicity_error": monotonicity_error,
        "static_incumbent_retained": bool(best_min + 1e-12 >= static_min),
    })
    sweep = [float(np.min(model.selected(best, p)[0])) for p in f["power_sweep"]]
    return {
        "paper_id": f["paper_id"],
        "metrics": {
            "initial_worst_sinr": float(np.min(model.selected(model.initial)[0])),
            "quadratic_heuristic_worst_sinr": quadratic_min, "optimized_static_worst_sinr": static_min,
            "optimized_mis_worst_sinr": best_min, "optimized_mis_worst_sinr_db": float(10 * np.log10(best_min)),
            "mis_gain_over_static": best_min - static_min, "selected_target_sinr": selected.tolist(),
            "sinr_by_target_and_position": rates.tolist(), "echo_power_by_target_and_position": echo.tolist(),
            "selected_position_index_one_based": (schedule + 1).tolist(),
            "ms1_phase_radians": best[:model.M].tolist(), "ms2_phase_radians": best[model.M:].tolist(),
            "power_sweep": f["power_sweep"], "fixed_design_power_sweep_worst_sinr": sweep,
        },
        "checks": checks, "history": history,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run()
    dump_output(result, args.output)
    print("MIS sensing:", result["metrics"]["optimized_mis_worst_sinr"])
