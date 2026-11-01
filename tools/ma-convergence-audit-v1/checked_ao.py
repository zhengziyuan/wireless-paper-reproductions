"""Versioned AO wrapper around the unchanged original MA numerical routines.

No import starts an optimization.  Call only under a separately admitted job.
The coordinate solves, ordering and positive fractional stopping test are the
same as core.optimize; abnormal stops are retained and reported unconverged.
"""
import numpy as np
import math
from convergence_gate import classify


class AoEvaluationFailure(RuntimeError):
    """An AO numerical exception plus the completed partial trajectory."""
    def __init__(self, message, details):
        super().__init__(message)
        self.details = details


def optimize_checked(core, initial, c, mode):
    if mode not in ("MRT", "ZF"):
        raise ValueError("mode must be MRT or ZF")
    t = np.asarray(initial, dtype=float).copy()
    def value():
        return (core.mrt_statistics(t, c)[0] if mode == "MRT"
                else core.zf_statistics(t, c)[0])
    try:
        initial_value = value()
    except Exception as exc:
        raise AoEvaluationFailure("Initial AO objective evaluation failed",
            {"mode": mode, "phase": "initial_objective", "sweep_one_based": None,
             "antenna_one_based": None, "positions": t.tolist(), "objective": [],
             "position_history": [], "coordinate_updates": []}) from exc
    if not math.isfinite(float(initial_value)):
        exc = ValueError("AO initial objective is nonfinite")
        raise AoEvaluationFailure(str(exc),
            {"mode": mode, "phase": "initial_objective", "sweep_one_based": None,
             "antenna_one_based": None, "positions": t.tolist(),
             "objective": [str(initial_value)], "position_history": [],
             "coordinate_updates": []}) from exc
    history = [initial_value]
    positions = [t.tolist()]
    coordinates = []
    undefined = []
    converged = False
    termination = "configured_iteration_cap"
    for sweep in range(c["maximum_AO_iterations"]):
        for n in range(len(t)):
            try:
                t, record = core.solve_coordinate(t, c, n, mode)
            except Exception as exc:
                raise AoEvaluationFailure("AO coordinate solve failed",
                    {"mode": mode, "phase": "coordinate", "sweep_one_based": sweep + 1,
                     "antenna_one_based": n + 1, "positions": t.tolist(),
                     "objective": list(history), "position_history": list(positions),
                     "coordinate_updates": list(coordinates)}) from exc
            record.update({"sweep": sweep, "antenna": n})
            coordinates.append(record)
        try:
            new_value = value()
        except Exception as exc:
            raise AoEvaluationFailure("AO sweep objective evaluation failed",
                {"mode": mode, "phase": "sweep_objective", "sweep_one_based": sweep + 1,
                 "antenna_one_based": None, "positions": t.tolist(),
                 "objective": list(history), "position_history": list(positions),
                 "coordinate_updates": list(coordinates)}) from exc
        history.append(new_value)
        positions.append(t.tolist())
        reason, _ = classify(history[-2], history[-1], c["fractional_increase_threshold"])
        if reason.startswith("nonfinite_"):
            safe_history = [v if math.isfinite(float(v)) else str(v) for v in history]
            exc = ValueError("AO numeric stopping test is nonfinite: " + reason)
            raise AoEvaluationFailure(str(exc),
                {"mode": mode, "phase": "fractional_stop", "reason": reason,
                 "sweep_one_based": sweep + 1, "antenna_one_based": None,
                 "positions": t.tolist(), "objective": safe_history,
                 "position_history": list(positions), "coordinate_updates": list(coordinates)}) from exc
        if reason == "undefined_fractional_increase":
            undefined.append(sweep + 1)
            continue
        if reason != "continue":
            termination = reason
            converged = reason == "fractional_increase"
            break
    result = {"objective": history, "positions": positions,
              "coordinate_updates": coordinates, "converged": converged,
              "termination": termination}
    if undefined:
        result["undefined_fractional_increase_sweeps_one_based"] = undefined
    return t, result
