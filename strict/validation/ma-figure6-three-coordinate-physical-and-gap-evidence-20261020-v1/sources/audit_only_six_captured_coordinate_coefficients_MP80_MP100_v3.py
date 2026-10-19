"""Saved-only fixed-rounded-coefficient diagnostics; never imports a MA solver.

No coordinate solve, new root, optimization, physical expansion, MC, or RNG.
Exact rational intersections below are certificate geometry only, not solver
candidates. Historical producer operands and the three old path gates remain
unrecovered. Original tolerances are captured inputs, never tuned here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

import mpmath as mp
import numpy as np
from scipy.io import loadmat


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path.resolve()), "SHA256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def check_pin(expected):
    actual = pin(expected["path"])
    require(actual["SHA256"] == expected["SHA256"], "SHA256 mismatch: " + str(expected["path"]))
    if "bytes" in expected:
        require(actual["bytes"] == expected["bytes"], "length mismatch: " + str(expected["path"]))
    return actual


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    payload = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)


def host_failure_representation(value):
    """Output-only labels: no nonfinite is silently treated as a passing value."""
    if isinstance(value, dict):
        return {str(k): host_failure_representation(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [host_failure_representation(v) for v in value]
    if isinstance(value, np.ndarray):
        return host_failure_representation(value.tolist())
    if isinstance(value, np.generic):
        return host_failure_representation(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return {"retained_nonfinite_output_only": value.hex()}
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return {"unserialized_output_type": type(value).__name__, "representation": repr(value)}


def write_host_failure_new(path, error, rows):
    # An exceptional numeric display cannot cause the same serializer to fail
    # a second time. Filesystem errors still propagate and are held by owner.
    try:
        value = host_failure_representation({"error": repr(error), "traceback": traceback.format_exc(),
                "completed_rows": rows, "original_failures_not_overwritten": True, "no_automatic_retry": True})
        payload = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    except Exception as serialization_error:
        payload = json.dumps({"error_type": type(error).__name__,
                  "host_failure_serialization_error_type": type(serialization_error).__name__,
                  "completed_rows_unavailable": True, "original_failures_not_overwritten": True, "no_automatic_retry": True}) + "\n"
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)


def restore_python(value, arrays):
    if isinstance(value, dict):
        if "array_key" in value:
            a = arrays[value["array_key"]]
            require(a.dtype.str == value["dtype"] and list(a.shape) == value["shape"], "typed NPZ tag mismatch")
            return a.copy()
        if "original_nonfinite_float" in value:
            return float(value["original_nonfinite_float"])
        return {k: restore_python(v, arrays) for k, v in value.items()}
    if isinstance(value, list):
        return [restore_python(v, arrays) for v in value]
    return value


def scalar(value):
    a = np.asarray(value)
    require(a.size == 1 and not np.iscomplexobj(a), "expected real scalar")
    return float(a.reshape(-1)[0])


def vector(value):
    a = np.asarray(value)
    require(not np.iscomplexobj(a), "expected real vector")
    return a.astype(np.float64).reshape(-1)


def matrix(value, columns):
    a = np.asarray(value)
    require(not np.iscomplexobj(a), "expected real matrix")
    return a.astype(np.float64).reshape(-1, columns)


def inventory(value):
    a = np.asarray(value)
    return {"loaded_storage_dtype": a.dtype.str, "shape": list(a.shape),
            "iscomplex": bool(np.iscomplexobj(a)), "Fbytes_SHA256": hashlib.sha256(a.tobytes(order="F")).hexdigest()}


def one_event(events, name):
    selected = [data for stage, data in events if stage == name]
    require(len(selected) == 1, "expected one actual event: " + name)
    return selected[0]


def load_lane(row, lane):
    binding = row["lanes"][lane]
    report = read_json(binding["actual_report"]["path"])
    require(binding["actual_sameheld_natural_exit"] == 0 and binding["sourceclosed"] is True, "capture not closed0")
    require(report["original_function_returned"] is True, "capture did not return")
    require((report.get("observer_errors") == [] if lane == "python" else report.get("observer_error_count") == 0), "capture observer error")
    journal = read_json(binding["held_journal"]["path"])
    require(journal["natural_wait_completed"] is True and journal["actual_child_terminal_exit_code"] == 0
            and journal["exact_original_handle_birth_and_exit_match"] is True
            and journal["all_watched_source_and_job_bytes_unchanged"] is True and journal["host_errors"] == [], "held capture not closed0/sourceclosed")
    if lane == "python":
        require(report["source_input_before"] == report["source_input_after"], "python interval not closed")
        with np.load(binding["actual_numeric_capture"]["path"], allow_pickle=False) as arrays:
            events = [(o["stage"], restore_python(o["data"], arrays)) for o in report["actual_observations"]]
        args = one_event(events, "actual_original_solver_arguments")
        choice = one_event(events, "actual_original_candidates_before_tie_selection")
        returned = one_event(events, "actual_original_solve_return")
        winner, certificate = returned["original_return"]
        last = returned["locals"]
        candidates = matrix(choice["candidates"], 2)
        valid = matrix(choice["valid"], 2)
        stored_values = vector(choice["values"])
        require(len(valid) == len(stored_values), "python valid/value mismatch")
        # Values correspond to valid candidates only, not every saved candidate.
        stored_pairs = [(x, float(v)) for x, v in zip(valid, stored_values)]
        ties = vector(choice["tied"]).astype(int).tolist()
        geometry = choice
        if row["mode"] == "ZF":
            require(np.asarray(args["minor_gradient"]).ndim == 2 and np.asarray(args["minor_gradient"]).shape[1] == 2, "python actual G must have two columns")
        before = args["objective_before"]
        coeff = {"g": vector(args["gradient"]), "q": scalar(args["curvature"])} if row["mode"] == "MRT" else {
            "a": vector(args["base"]), "G": matrix(args["minor_gradient"], 2), "q": vector(args["minor_curvature"])}
        gradient_saved = vector(last["g"])
        storage = {k: inventory(args[k]) for k in (["gradient", "curvature"] if row["mode"] == "MRT" else ["base", "minor_gradient", "minor_curvature"])}
    else:
        require(report["source_input_interval_closed"] is True and report["source_before"] == report["source_after"], "native interval not closed")
        # mat_dtype=False preserves complex values. No MAT class-diagnostic data
        # are used as numeric operands. Compact real MI storage is losslessly
        # promoted by vector/matrix, and remains visible in storage_inventory.
        data = loadmat(binding["actual_numeric_capture"]["path"], simplify_cells=True, mat_dtype=False)
        records = data["observation"]["records"]
        if isinstance(records, dict):
            records = [records]
        events = [(o["stage"], o["actual_locals"]) for o in records]
        args = one_event(events, "actual_original_solver_arguments")
        geometry = one_event(events, "actual_original_polygon")
        choice = one_event(events, "actual_original_candidates_and_values")
        returned = one_event(events, "actual_original_exact_coordinate_return")
        tie = one_event(events, "actual_original_tie_set")
        winner, certificate = returned["winner"], returned["certificate"]
        candidates = matrix(choice["candidates"], 2)
        stored_values = vector(choice["values"])
        require(len(candidates) == len(stored_values), "native candidate/value mismatch")
        stored_pairs = [(x, float(v)) for x, v in zip(candidates, stored_values)]
        ties = (vector(tie["ties"]).astype(int) - 1).tolist()
        if row["mode"] == "ZF":
            require(np.asarray(args["G"]).ndim == 2 and np.asarray(args["G"]).shape[1] == 2, "native actual G must have two columns")
        before = args["objectiveBefore"]
        coeff = {"g": vector(args["gradient"]), "q": scalar(args["curvature"])} if row["mode"] == "MRT" else {
            "a": vector(args["base"]), "G": matrix(args["G"], 2), "q": vector(args["q"])}
        gradient_saved = vector(returned["gradientAtWinner"])
        storage = {k: inventory(args[k]) for k in (["gradient", "curvature"] if row["mode"] == "MRT" else ["base", "G", "q"])}
    if row["mode"] == "MRT":
        require(coeff["g"].shape == (2,) and np.asarray(coeff["q"]).size == 1, "MRT actual g/q dimensions")
    else:
        count = len(coeff["a"])
        require(count > 0 and coeff["a"].shape == (count,) and coeff["G"].shape == (count, 2) and coeff["q"].shape == (count,), "ZF actual a/G/q dimensions")
    require(vector(winner).shape == (2,) and gradient_saved.shape == (2,), "saved winner/gradient must have two components")
    A, b, vertices = matrix(geometry["A"], 2), vector(geometry["b"]), matrix(geometry["vertices"], 2)
    require(A.shape == (len(b), 2), "actual A/b row mismatch")
    require(np.isfinite(A).all() and np.isfinite(b).all() and np.isfinite(candidates).all(), "nonfinite actual geometry/candidates")
    for k, v in coeff.items():
        require(np.isfinite(v).all(), "nonfinite actual coefficient: " + k)
    feas = scalar(certificate["normalized_constraint_tolerance"])
    gap_tol = scalar(certificate["global_objective_gap_tolerance"])
    return {"lane": lane, "mode": row["mode"], "coeff": coeff, "A": A, "b": b,
            "vertices": vertices, "winner": vector(winner), "candidates": candidates,
            "stored_pairs": stored_pairs, "stored_tie_indices_zero_based": ties,
            "tie_index_basis": "valid_only" if lane == "python" else "all_candidates",
            "stored_certificate": certificate, "stored_gradient_at_winner": gradient_saved,
            "objective_before": scalar(before), "feas_tol": feas, "gap_tol": gap_tol,
            "events": events, "storage_inventory": storage}


def exact(value):
    """Promote the binary64 input exactly, without decimal str conversion."""
    value = float(value)
    require(math.isfinite(value), "nonfinite MP operand")
    n, d = value.as_integer_ratio()
    return mp.mpf(n) / d


def mvec(value):
    return [exact(v) for v in np.asarray(value).reshape(-1)]


def dot(a, b):
    return mp.fsum(x * y for x, y in zip(a, b))


def number(value):
    return mp.nstr(value, mp.mp.dps, strip_zeros=False)


def evaluate(model, x):
    c = model["coeff"]
    xx = dot(x, x)
    if model["mode"] == "MRT":
        g, q = mvec(c["g"]), exact(c["q"])
        return dot(g, x) - q * xx / 2, [g[j] - q*x[j] for j in range(2)], [[q, mp.mpf(0)], [mp.mpf(0), q]], []
    a, q = mvec(c["a"]), mvec(c["q"])
    G = [mvec(r) for r in c["G"]]
    delta = [dot(row, x) - qi*xx/2 for row, qi in zip(G, q)]
    r = [ai+di for ai, di in zip(a, delta)]
    if any(ri <= 0 for ri in r):
        return None
    vi = [[row[j] - qi*x[j] for j in range(2)] for row, qi in zip(G, q)]
    ln2 = mp.log(2)
    value = mp.fsum(mp.log1p(di/ai) for ai, di in zip(a, delta))/ln2
    grad = [mp.fsum(v[j]/ri for v, ri in zip(vi, r))/ln2 for j in range(2)]
    h = [[(mp.fsum(qi/ri for qi, ri in zip(q, r)) if j == k else 0)
          + mp.fsum(v[j]*v[k]/ri**2 for v, ri in zip(vi, r)) for k in range(2)] for j in range(2)]
    h = [[entry/ln2 for entry in row] for row in h]
    return value, grad, h, r


def exact_certificate_vertices(A, b):
    """All exact rational halfspace intersections; proof geometry only."""
    require(A.ndim == 2 and A.shape == (len(b), 2) and np.isfinite(A).all() and np.isfinite(b).all(), "finite two-dimensional A/b required")
    # Four finite axis bounds ensure a bounded rectangle; merely finding one
    # intersection does not prove boundedness. Positive multiples are accepted.
    for axis in range(2):
        for sign in (-1, 1):
            require(any(row[1-axis] == 0 and sign*row[axis] > 0 for row in A), "missing finite signed-axis bound: " + str((axis, sign)))
    aa = [[Fraction.from_float(float(x)) for x in row] for row in A]
    bb = [Fraction.from_float(float(x)) for x in b]
    vertices = set()
    for i in range(len(aa)):
        for j in range(i):
            det = aa[i][0]*aa[j][1] - aa[i][1]*aa[j][0]
            if det == 0:
                continue
            x = ((bb[i]*aa[j][1] - aa[i][1]*bb[j])/det,
                 (aa[i][0]*bb[j] - bb[i]*aa[j][0])/det)
            if all(row[0]*x[0] + row[1]*x[1] <= rhs for row, rhs in zip(aa, bb)):
                vertices.add(x)
    require(vertices, "actual fixed halfspaces have no bounded certificate vertices")
    return sorted(vertices)


def fraction_mp(value):
    return mp.mpf(value.numerator) / value.denominator


def point_evidence(model, point, geometry_vertices):
    x = mvec(point)
    primal = max([mp.mpf(0)] + [dot(mvec(row), x) - exact(rhs) for row, rhs in zip(model["A"], model["b"])])
    ev = evaluate(model, x)
    out = {"point_binary64_hex": [float(v).hex() for v in point], "maximum_normalized_violation": number(primal),
           "within_original_feasibility_tolerance": bool(primal <= exact(model["feas_tol"])), "domain_positive": ev is not None}
    if ev is None:
        return out
    value, grad, h, domain = ev
    saved_gap = max([mp.mpf(0)] + [dot([v[j]-x[j] for j in range(2)], grad) for v in map(mvec, model["vertices"])])
    exact_gap = max([mp.mpf(0)] + [dot([fraction_mp(v[j])-x[j] for j in range(2)], grad) for v in geometry_vertices])
    lo = (h[0][0]+h[1][1]-mp.sqrt((h[0][0]-h[1][1])**2+4*h[0][1]**2))/2
    hi = h[0][0]+h[1][1]-lo
    out.update(objective=number(value), gradient=[number(v) for v in grad],
               gradient_norm=number(mp.sqrt(dot(grad, grad))),
               negative_hessian_eigenvalues=[number(lo), number(hi)],
               domain_values=[number(v) for v in domain],
               saved_rounded_vertex_first_order_gap=number(saved_gap),
               exact_halfspace_geometry_first_order_gap=number(exact_gap),
               gap_below_original_tolerance=bool(exact_gap <= exact(model["gap_tol"])))
    return out


def ulp_error(reference, stored):
    if not math.isfinite(float(stored)):
        return {"stored_nonfinite": str(stored)}
    error = abs(reference-exact(stored))
    spacing = math.ulp(float(stored))
    return {"stored_binary64_hex": float(stored).hex(), "absolute_error": number(error),
            "error_in_ULP_at_stored": number(error/exact(spacing))}


def root_evidence(model):
    """Evaluate only actual saved parameters; never refine or generate roots."""
    rows, edge, bracket = [], None, None
    for stage, data in model["events"]:
        samples = []
        if stage == "actual_original_edge_interval_return":
            value = data["original_return"]
            edge = None if value is None else (value[0], value[1], int(data["locals"]["index"]))
        elif stage == "actual_scipy_brentq_input":
            require(edge is not None, "Brent root has no captured edge")
            bracket = data
        elif stage == "actual_original_derivative_return":
            require(edge is not None, "saved derivative has no captured edge")
            samples = [(data["locals"]["parameter"], data["original_return"], "actual_derivative_return")]
        elif stage == "actual_scipy_brentq_return":
            require(edge is not None and bracket is not None, "Brent return missing input")
            samples = [(data["root"], None, "actual_brentq_return")]
        elif stage == "actual_original_edge_root_initial_bracket":
            edge = (data["p"], data["v"], int(scalar(data["index"]))-1)
            samples = [(data["L"], data["dL"], "actual_left_endpoint"), (data["R"], data["dR"], "actual_right_endpoint")]
        elif stage == "actual_original_native_bisection_trial":
            require(edge is not None and edge[2] == int(scalar(data["index"]))-1, "native root edge identity mismatch")
            samples = [(data["middle"], data["derivative"], "actual_bisection_middle")]
        elif stage == "actual_original_edge_root_final_bracket":
            edge = (data["p"], data["v"], int(scalar(data["index"]))-1)
            samples = [(data["parameter"], None, "actual_final_parameter")]
        for parameter, stored, kind in samples:
            p, v = mvec(edge[0]), mvec(edge[1])
            t = exact(scalar(parameter))
            # Both points shown: exact affine use of the stored parameter, and
            # a declared NumPy binary64 reconstruction. The latter is NOT an
            # observed source trial vector (that vector was not captured).
            affine = [p[j]+t*v[j] for j in range(2)]
            source_point = vector(edge[0]) + scalar(parameter)*vector(edge[1])
            ev = evaluate(model, mvec(source_point))
            row = {"kind": kind, "edge_zero_based": edge[2], "parameter_hex": scalar(parameter).hex(),
                   "exact_affine_point": [number(x) for x in affine],
                   "reconstructed_numpy_binary64_expression_point_hex": [float(x).hex() for x in source_point],
                   "source_trial_vector_not_observed": True, "domain_positive": ev is not None}
            if ev is not None:
                derivative = dot(ev[1], v)
                row["fixed_coeff_derivative_at_reconstructed_numpy_expression"] = number(derivative)
                exact_ev = evaluate(model, affine)
                row["fixed_coeff_derivative_at_exact_affine_point"] = None if exact_ev is None else number(dot(exact_ev[1], v))
                row["original_stored_derivative_error"] = None if stored is None else ulp_error(derivative, scalar(stored))
            rows.append(row)
    return rows


def audit_precision(model, dps, geometry_vertices, other_winner):
    with mp.workdps(dps):
        winner = point_evidence(model, model["winner"], geometry_vertices)
        candidates = [point_evidence(model, x, geometry_vertices) for x in model["candidates"]]
        stored_errors = []
        for point, stored in model["stored_pairs"]:
            ev = evaluate(model, mvec(point))
            stored_errors.append({"point_hex": [float(x).hex() for x in point], "domain_positive": ev is not None,
                                  "value_error": None if ev is None else ulp_error(ev[0], stored)})
        valid = [x for x in candidates if x["domain_positive"] and x["within_original_feasibility_tolerance"]]
        values = [mp.mpf(x["objective"]) for x in valid]
        require(values and winner["domain_positive"], "no valid actual candidates/winner")
        best = max(values)
        maximum_stored = max(v for _, v in model["stored_pairs"] if math.isfinite(v))
        tie_window = 8*np.finfo(np.float64).eps*max(1., abs(maximum_stored))
        distinct = {tuple(x["point_binary64_hex"]) for x in valid}
        sorted_values = sorted(set(values), reverse=True)
        margin = None if len(sorted_values) < 2 else best-sorted_values[1]
        c = model["coeff"]
        concave = c["q"] >= 0 if model["mode"] == "MRT" else bool(np.all(c["a"] > 0) and np.all(c["q"] >= 0))
        strict = c["q"] > 0 if model["mode"] == "MRT" else bool(concave and np.any(c["q"] > 0))
        gap_tol = exact(model["gap_tol"])
        checks = {"global_concavity_coefficient_condition": bool(concave),
                  "selected_domain_positive": winner["domain_positive"],
                  "selected_primal_within_original_tolerance": winner["within_original_feasibility_tolerance"],
                  "selected_independent_geometry_gap_within_original_tolerance": winner["gap_below_original_tolerance"]}
        return {"decimal_precision": dps, "strict_concavity_sufficient_condition": bool(strict),
                "unique_exact_optimizer_if_nonempty_feasible_domain": bool(strict),
                "winner": winner, "all_actual_saved_candidates": candidates, "stored_value_rounding_errors": stored_errors,
                "saved_gradient_at_winner_errors": [ulp_error(mp.mpf(x), y) for x, y in zip(winner["gradient"], model["stored_gradient_at_winner"])],
                "stored_certificate_gap_error": ulp_error(mp.mpf(winner["saved_rounded_vertex_first_order_gap"]), scalar(model["stored_certificate"]["global_objective_gap_upper_bound"])),
                "original_gap_tolerance": number(gap_tol), "original_gap_tolerance_binary64_hex": model["gap_tol"].hex(),
                "original_feasibility_tolerance": number(exact(model["feas_tol"])),
                "original_tie_window_binary64_hex": float(tie_window).hex(), "original_tie_window": number(exact(tie_window)),
                "original_tie_indices_zero_based": model["stored_tie_indices_zero_based"], "tie_index_basis": model["tie_index_basis"],
                "MP_saved_candidate_maximum": number(best), "selected_deficit_from_saved_candidate_maximum": number(best-mp.mpf(winner["objective"])),
                "selected_within_original_tie_window_MP": bool(best-mp.mpf(winner["objective"]) <= exact(tie_window)),
                "distinct_saved_candidate_points": len(distinct), "positive_distinct_value_margin": None if margin is None else number(margin),
                "saved_candidate_near_tie_window": None if margin is None else bool(margin <= exact(tie_window)),
                "other_language_saved_winner_under_this_fixed_coefficient_model": point_evidence(model, other_winner, geometry_vertices),
                "only_actual_saved_root_samples": root_evidence(model), "original_tolerance_checks": checks,
                "fixed_coeff_original_gap_and_primal_pass": all(checks.values())}


def displayed_exact_ULP_ratio(a, b):
    ratio = abs(Fraction.from_float(float(a))-Fraction.from_float(float(b))) / Fraction.from_float(math.ulp(float(a)))
    with localcontext() as context:
        context.prec = 50
        return format(Decimal(ratio.numerator)/Decimal(ratio.denominator), ".49e")


def array_difference(a, b):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.shape != b.shape:
        return {"same_semantic_shape": False, "shape_python": list(a.shape), "shape_native": list(b.shape), "bits_equal": False}
    same = a.tobytes(order="F") == b.tobytes(order="F")
    changed = np.argwhere(a.view(np.uint64).reshape(a.shape) != b.view(np.uint64).reshape(b.shape))
    examples = []
    for index in changed[:8]:
        ix = tuple(index)
        av, bv = float(a[ix]), float(b[ix])
        examples.append({"index": [int(i) for i in ix], "python_hex": av.hex(), "native_hex": bv.hex(),
                         "absolute_difference": abs(av-bv), "difference_over_python_ULP": displayed_exact_ULP_ratio(av, bv)})
    return {"same_semantic_shape": True, "bits_equal": same, "different_entries": int(len(changed)),
            "maximum_absolute_difference": float(np.max(np.abs(a-b))) if a.size else 0., "first_differences": examples}


def compare_lanes(models):
    p, n = models["python"], models["native"]
    fields = [("solver_coefficients."+k, p["coeff"][k], n["coeff"][k]) for k in p["coeff"]]
    fields += [(k, p[k], n[k]) for k in ["A", "b", "vertices", "candidates", "winner"]]
    rows = [{"field_in_captured_dataflow_order": k, **array_difference(a, b)} for k, a, b in fields]
    first = next((r["field_in_captured_dataflow_order"] for r in rows if not r["bits_equal"]), None)
    return {"first_observed_difference_in_compared_readset": first, "fields": rows,
            "not_a_proof_of_historical_first_divergence_or_physical_model_correctness": True,
            "root_methods_differ": {"python": "captured scipy Brentq", "native": "captured bisection; no new root solve"}}


def run(plan_path, admission_path, output):
    consumed_metadata_before = [pin(plan_path), pin(admission_path)]
    plan = read_json(plan_path)
    admission = read_json(admission_path)
    require(admission.get("root_admitted_saved_only_six_fixed_coeff_MP") is True, "root admission false")
    require(admission["plan_SHA256"] == pin(plan_path)["SHA256"], "admission plan mismatch")
    require(str(Path(admission["output_directory"]).resolve()) == str(output.resolve()), "admission output mismatch")
    before = consumed_metadata_before + [check_pin(p) for p in plan["readset_pins"] + [plan["entry"]]]
    aggregate = read_json(plan["six_closed_capture_aggregate"]["path"])
    require(len(aggregate["rows"]) == 3, "exactly three pairs required")
    require(not output.exists(), "fresh output required")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    try:
        for row in aggregate["rows"]:
            models = {lane: load_lane(row, lane) for lane in ["python", "native"]}
            result = {"case": row["case"], "mode": row["mode"], "lanes": {}, "cross_lane_saved_readset": compare_lanes(models)}
            for lane, model in models.items():
                vertices = exact_certificate_vertices(model["A"], model["b"])
                precisions = [audit_precision(model, dps, vertices, models["native" if lane == "python" else "python"]["winner"]) for dps in [80, 100]]
                metrics = ["objective", "gradient_norm", "exact_halfspace_geometry_first_order_gap"]
                with mp.workdps(100):
                    disagreement = {k: number(abs(mp.mpf(precisions[0]["winner"][k])-mp.mpf(precisions[1]["winner"][k]))) for k in metrics}
                result["lanes"][lane] = {"storage_inventory_before_semantic_real_promotion": model["storage_inventory"],
                    "stored_certificate": model["stored_certificate"], "objective_before": model["objective_before"],
                    "certificate_geometry_exact_rational_vertices": [[[str(x.numerator), str(x.denominator)] for x in v] for v in vertices],
                    "certificate_intersections_never_used_as_new_optimization_candidates": True,
                    "precision_lanes": precisions, "80_100_absolute_disagreement": disagreement,
                    "80_100_original_tolerance_classifications_equal": precisions[0]["original_tolerance_checks"] == precisions[1]["original_tolerance_checks"]}
            rows.append(result)
        after = [check_pin(p) for p in before]
        passed = all(e["fixed_coeff_original_gap_and_primal_pass"] for row in rows for lane in row["lanes"].values() for e in lane["precision_lanes"])
        passed = passed and all(lane["80_100_original_tolerance_classifications_equal"] for row in rows for lane in row["lanes"].values())
        report = {"schema": "actual-only-six-new-captured-coordinate-fixed-rounded-coeff-MP80-MP100-v1",
                  "created_UTC": datetime.now(timezone.utc).isoformat(), "plan": pin(plan_path), "admission": pin(admission_path),
                  "source_and_input_before": before, "source_and_input_after": after, "source_input_interval_closed": before == after,
                  "rows": rows, "all_fixed_coeff_original_tolerance_checks_pass": passed,
                  "physical_model_MP_performed": False, "new_coordinate_or_root_solve_performed": False,
                  "historical_internal_operands_recovered": False, "original_three_trajectory_path_gates_remain_false": True,
                  "original_reference_or_full900_or_dual_path_PASS": False,
                  "scope": plan["scope_and_limits"], "actual_exit_code": 0 if passed else 2}
        write_new(output/"ACTUAL_ONLY_SIX_FIXED_COEFFICIENT_MP80_MP100_CANDIDATES_ROOTS_AND_GAPS_V1.json", report)
        return report["actual_exit_code"]
    except Exception as error:
        write_host_failure_new(output/"ACTUAL_FIXED_COEFFICIENT_READER_HOST_FAILURE_V1.json", error, rows)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--admission", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require(args.execute, "prepared only: --execute and root true admission required")
    return run(args.plan, args.admission, args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
