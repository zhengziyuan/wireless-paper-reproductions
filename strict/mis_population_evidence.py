"""Fail-closed summary coverage gate, not an independent numerical oracle.

Legacy MIS engines use ``overall_full_success`` for the selected best start.
That field cannot certify the complete population. This metadata-only gate
checks every declared start/baseline before a full-figure renderer runs. It
does not reconstruct gradients, endpoint states, RNG or physical channels.
"""
from __future__ import annotations

from collections import Counter
import math


def _finite(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _declared_tolerances(settings, communication):
    if not isinstance(settings, dict) or settings.get("kind") != ("communications" if communication else "sensing"):
        raise ValueError("Declared MIS solver kind/settings required")
    if communication:
        tolerance = settings.get("rcg_gradient_tolerance")
        if not _finite(tolerance) or tolerance <= 0:
            raise ValueError("Declared communication stopping tolerance required")
        return [tolerance]
    initial, minimum = settings.get("epsilon_initial"), settings.get("epsilon_min")
    outer = settings.get("outer_iterations")
    if (type(outer) is not int or outer != 30 or settings.get("rcg_max_iterations") != 4000
            or type(settings.get("rcg_max_iterations")) is not int
            or not _finite(initial) or not _finite(minimum) or not 0 < minimum <= initial):
        raise ValueError("Original sensing30/4000 budgets and declared epsilon schedule required")
    factor = (minimum / initial) ** (1 / outer)
    values = []
    epsilon = initial
    for _ in range(outer):
        values.append(epsilon)
        epsilon = max(minimum, factor * epsilon)
    return values


def _run(run, name, expected, tolerances, communication):
    if not isinstance(run, dict):
        raise ValueError(f"Missing full start-bank evidence: {name}")
    rows = run.get("all_start_summaries")
    if (type(run.get("number_of_starts")) is not int or run["number_of_starts"] != expected
            or run.get("full_start_budget_execution_complete") is not True
            or not isinstance(rows, list) or len(rows) != expected):
        raise ValueError(f"All{expected} start summaries required: {name}")
    identifiers = [row.get("start") if isinstance(row, dict) else None for row in rows]
    if (any(type(index) is not int for index in identifiers)
            or Counter(identifiers) != Counter(range(1, expected + 1))):
        raise ValueError(f"Duplicate, missing or invalid start identifiers: {name}")
    for row in rows:
        status = row.get("solver_status", {})
        if (row.get("feasible") is not True or row.get("binary_eta_feasible") is not True
                or not _finite(row.get("score"))
                or not _finite(row.get("min_binary_metric"))
                or (communication and row["score"] != row["min_binary_metric"])
                or not isinstance(status, dict)
                or any(status.get(key) is not True for key in
                       ("convergence_verified", "all_inner_tolerances_satisfied",
                        "final_inner_stationary", "continuation_complete"))
                or type(status.get("inner_iteration_cap_exits")) is not int
                or status["inner_iteration_cap_exits"] != 0
                or type(status.get("inner_failure_exits")) is not int
                or status["inner_failure_exits"] != 0
                or type(status.get("outer_stopping_applicable")) is not bool
                or status["outer_stopping_applicable"] != (not communication)
                or (status.get("outer_stopping_applicable") is True
                    and status.get("outer_stopping_met") is not True)
                or not _finite(status.get("final_inner_residual"))
                or not _finite(status.get("final_inner_tolerance"))
                or not 0 <= status["final_inner_residual"] <= status["final_inner_tolerance"]
                or status["final_inner_tolerance"] <= 0
                or not any(math.isclose(status["final_inner_tolerance"], value,
                                        rel_tol=2e-14, abs_tol=0) for value in tolerances)):
            raise ValueError(f"Capped, failed or unverified start{row['start']}: {name}")
    best = run.get("best_feasible")
    if (not isinstance(best, dict) or type(best.get("start")) is not int
            or not _finite(best.get("score"))):
        raise ValueError(f"Missing selected-start provenance: {name}")
    selected = next((row for row in rows if row["start"] == best["start"]), None)
    # Original strict > update retains the earliest start on an exact tie.
    maximum = max(rows, key=lambda row: (row["score"], -row["start"]))
    metrics = best.get("metrics")
    score_key = "min_binary_snr" if communication else "eta"
    binary_key = "min_binary_snr" if communication else "min_binary_metric"
    if (selected is None or best.get("score") != selected["score"]
            or best["start"] != maximum["start"]
            or best.get("binary_eta_feasible") is not True
            or best.get("solver_status") != selected["solver_status"]
            or not isinstance(metrics, dict) or not _finite(metrics.get(score_key))
            or not _finite(metrics.get(binary_key))
            or metrics[score_key] != selected["score"]
            or metrics[binary_key] != selected["min_binary_metric"]):
        raise ValueError(f"Selected-start summary and provenance disagree: {name}")
    return {"bank": name, "required_starts": expected, "checked_start_summaries": len(rows),
            "all_summary_domain_and_stop_gates_passed": True,
            "selected_original_maximum_and_exact_tie_rule_verified": True,
            "selected_plot_scalars_match_start_summary": True,
            "final_tolerance_belongs_to_declared_schedule": True,
            "every_start_full_epsilon_history_independently_verified": False}


def verify_full_mis_summary_population(data, source_figure):
    """Require all original summary slots; source/physical certificates separate.

``source_figure`` is the canonical figures.json item, not user-supplied result
metadata. Analytical closed-form panels have no invented random start bank.
RIS curves require transparent per-target banks, not an aggregate best flag.
"""
    if (data.get("paper_id") not in ("mis-communications", "mis-sensing")
            or not isinstance(source_figure, dict)):
        raise ValueError("MIS source-mapped figure evidence required")
    points = data.get("points")
    if not isinstance(points, list) or len(points) != len(source_figure["points"]):
        raise ValueError("Complete original point population required")
    analytical = source_figure["objective"] == "closed_form_sinr"
    baselines = source_figure.get("baselines", [])
    requires_bank = (not analytical or any("SMS" in name or name.startswith("ralm_reference")
                    or name.startswith("RIS_") for name in baselines))
    settings = data.get("settings", {})
    if requires_bank and (not isinstance(settings, dict)
            or type(settings.get("number_of_starts")) is not int or settings["number_of_starts"] != 6000):
        raise ValueError("Original6000-start population required")
    communication = data["paper_id"] == "mis-communications"
    tolerances = _declared_tolerances(settings, communication) if requires_bank else None
    reports = []
    for index, entry in enumerate(points):
        if not isinstance(entry, dict):
            raise ValueError("Invalid original point record")
        prefix = f"point{index}"
        if analytical:
            result = entry.get("result", {})
            if result.get("available") is not True or not _finite(result.get("minimum_sinr")):
                raise ValueError("Analytical full-size result is unavailable or nonfinite")
        else:
            reports.append(_run(entry.get("result"), prefix + "/MIS", 6000, tolerances, communication))
        if any("SMS" in name for name in baselines):
            reports.append(_run(entry.get("SMS"), prefix + "/SMS", 6000, tolerances, communication))
        if "closed_form" in baselines:
            closed = entry.get("closed_form", {})
            if closed.get("available") is not True or not _finite(closed.get("minimum_sinr")):
                raise ValueError("Original closed-form comparator is missing or nonfinite")
        if any(name.startswith("ralm_reference") for name in baselines):
            if tolerances is None:
                tolerances = _declared_tolerances(settings, communication)
            reports.append(_run(entry.get("RALM_reference"), prefix + "/RALM-reference", 6000, tolerances, communication))
        if any(name.startswith("RIS_") for name in baselines):
            ris = entry.get("RIS", {})
            targets = entry["configuration"]["Kphi"] * entry["configuration"]["Ktheta"]
            banks = ris.get("target_start_banks")
            if (ris.get("available") is not True or not isinstance(banks, list)
                    or len(banks) != targets):
                raise ValueError("RIS aggregate best flags do not prove all per-target start banks")
            for target, bank in enumerate(banks):
                reports.append(_run(bank, prefix + f"/RIS-target{target}", 6000, tolerances, communication))
            for key in ("continuous", "one_bit", "two_bit"):
                values = ris.get(key)
                if (not isinstance(values, list) or len(values) != targets
                        or any(not _finite(value) or value < 0 for value in values)):
                    raise ValueError(f"Every original RIS target's finite{key} scalar required")
            binary_key = "min_binary_snr" if communication else "min_binary_metric"
            if any(ris["continuous"][target] != bank["best_feasible"]["metrics"][binary_key]
                   for target, bank in enumerate(banks)):
                raise ValueError("RIS continuous plotted scalars and target-bank selection disagree")
    return {"scope": "complete_MIS_start_summary_coverage_and_stored_stop_fields_only",
            "required_start_banks": len(reports),
            "checked_start_summaries": sum(row["checked_start_summaries"] for row in reports),
            "all_summary_coverage_and_stop_fields_verified": True, "banks": reports,
            "independent_endpoint_gradients_or_physical_model_verified": False,
            "quantized_RIS_states_or_physical_metrics_independently_verified": False,
            "source_runtime_RNG_identity_verified": False,
            "original_figure_agreement_verified": False, "full_reproduction_certified": False}
