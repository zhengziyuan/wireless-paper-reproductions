#!/usr/bin/env python3
"""Exact rational comparisons of serialized SINR estimates, not a forward-error proof.

For a fixed saved phase state and any one-hot choice in each row, the minimum
selected Gamma is at most min_k max_u Gamma[k,u]. This bound remains valid if
additional constraints restrict schedules. The decimals are the saved MP
approximations, not exact mathematical SINR. No optimizer or model is rerun.
"""
import argparse
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path


def numeric(f):
    with localcontext() as ctx:
        ctx.prec = 80
        return str(Decimal(f.numerator) / Decimal(f.denominator))


def evaluate(source):
    obj = json.loads(source.read_text(encoding="utf-8"))
    assert obj["schema"] == "MIS_NATIVE4736_FIXED_STATE_225_GAMMA_DIAGNOSTIC_V1"
    assert obj["dimensions"]["targets"] == 9 and obj["dimensions"]["positions"] == 25
    assert obj["original_argmax_X_matches_stored_binary_schedule"] is True
    eta = Fraction(obj["original_eta_exact_binary64"])
    cols = obj["original_argmax_X_columns_zero_based"]
    assert len(cols) == 9 and all(type(col) is int and 0 <= col < 25 for col in cols)
    results = {}
    for name in ("80", "100"):
        lane = obj["lanes"][name]
        g = [[Fraction(x) for x in row] for row in lane["Gamma_9x25"]]
        assert len(g) == 9 and all(len(row) == 25 for row in g)
        assert all(x >= 0 for row in g for x in row)
        threshold = Fraction(lane["same_eta_feasibility_threshold_exact_binary64"])
        rowmax = [max(row) for row in g]
        upper = min(rowmax)
        upper_target = rowmax.index(upper)
        selected = [row[cols[k]] for k, row in enumerate(g)]
        original = min(selected)
        original_target = selected.index(original)
        results[name] = {
            "rowwise_upper_bound": numeric(upper),
            "upper_bound_target_zero_based": upper_target,
            "eta_minus_upper_bound": numeric(eta-upper),
            "original_minimum_selected": numeric(original),
            "original_bottleneck_target_zero_based": original_target,
            "eta_minus_original_minimum": numeric(eta-original),
            "feasibility_tolerance": numeric(threshold),
            "rowwise_upper_bound_at_least_eta": upper >= eta,
            "rowwise_upper_bound_passes_tolerance": eta-upper <= threshold,
            "original_schedule_passes_tolerance": eta-original <= threshold,
        }
    return {
        "schema": "MIS_FIXED_STATE_SERIALIZED_GAMMA_EXACT_RATIONAL_BOUND_V1",
        "input": str(source), "figure": 3, "original_start": 4736,
        "eta_is_linear_sinr": True, "eta": numeric(eta), "lanes": results,
        "scope": "Exact comparisons of serialized approximate Gamma values for saved fixed phases; upper bound applies to any one-hot row schedules, with or without additional schedule constraints.",
        "limits": ["Not a certified interval bound for the original physical forward model.", "No claim about other phases, other starts, complete figure or paper.", "Original normalization unit and binary recovery rule remain unconfirmed.", "Tolerance passing is not exact feasibility."],
        "no_new_optimizer_or_monte_carlo": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("saved_diagnostic", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = evaluate(args.saved_diagnostic)
    with args.report.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)
        file.write("\n")


if __name__ == "__main__":
    main()
