"""Check the assumptions behind a fractional-increase convergence flag.

The paper's AO algorithms use a fractional-increase stop with a monotone
objective in exact arithmetic.  This module does not modify the source solver
or assert mathematical convergence: it detects when a saved numeric history
cannot justify that flag.  All comparisons use the supplied floating values;
they do not certify forward error.
"""
from __future__ import annotations

import math


def classify(previous, current, threshold):
    """Return (reason, fractional_increase) for one numeric transition.

    A negative numerical step and a zero denominator are deliberately not
    treated as convergence.  Callers retain a zero-denominator observation
    and continue until the ratio is defined or the iteration budget is spent.
    The signed fractional stop is unchanged for finite, nonnegative steps
    with a nonzero denominator.
    """
    previous, current, threshold = map(float, (previous, current, threshold))
    if not all(math.isfinite(v) for v in (previous, current, threshold)):
        return "nonfinite_value", None
    if threshold < 0:
        raise ValueError("fractional-increase threshold must be nonnegative")
    delta = current - previous
    if not math.isfinite(delta):
        return "nonfinite_increment", None
    if delta < 0:
        return "numerical_decrease", None
    if previous == 0:
        return "undefined_fractional_increase", None
    ratio = delta / abs(previous)
    if not math.isfinite(ratio):
        return "nonfinite_fractional_increase", None
    return ("fractional_increase" if ratio < threshold else "continue"), ratio


def audit_history(objective, threshold, recorded_converged):
    """Report numerical flags without changing a stored objective history."""
    if type(recorded_converged) is not bool:
        raise ValueError("recorded_converged must be boolean")
    values = list(objective)
    if not values or not all(math.isfinite(float(v)) for v in values):
        raise ValueError("a finite nonempty objective history is required")
    outcomes = [classify(a, b, threshold) for a, b in zip(values, values[1:])]
    anomalies = [{"transition_one_based": i, "reason": reason}
                 for i, (reason, _) in enumerate(outcomes, 1)
                 if reason not in ("fractional_increase", "continue")]
    anomalies.extend({"transition_one_based": i,
                      "reason": "termination_criterion_met_before_final_transition"}
                     for i, (reason, _) in enumerate(outcomes[:-1], 1)
                     if reason == "fractional_increase")
    final_reason, final_ratio = outcomes[-1] if outcomes else ("no_transition", None)
    blocking = [item for item in anomalies if item["reason"] != "undefined_fractional_increase"]
    return {"recorded_converged": recorded_converged,
            "numeric_stop_consistent": bool(recorded_converged and not blocking and
                                            final_reason == "fractional_increase"),
            "final_transition": final_reason,
            "final_fractional_increase": final_ratio,
            "anomalies": anomalies,
            "scope": "numeric stop assumptions only; not physical feasibility or convergence proof"}
