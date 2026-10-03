"""Frozen completed-subset dual audit; not a reduced full-bank experiment.

The live Python bank continues unchanged. One immutable completion snapshot
defines every case to audit, including any failed record. Neither nearest
matching local solutions nor source figure endpoints select the population.
Only separately frozen independent audit primitives are imported.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import time
import traceback

import numpy as np


PY_FP = "b3b8134f4c9be5213dee91930e240792be509003a1b840848131e1f2621ee5ef"
MAT_FP = "e78708e52bbfe9733a9fe24faaa736188015469a9d87ea90b41c5a1d0966bf37"
PRIMITIVE_HASHES = {
    "audit_full200_matlab_v1.py": "29c42f0a8920d179fd32f81aa47931119b2f890ef3ed4e7ae63be9a4c562707d",
    "audit_full200_coordinate_certificates_v1.py": "d740e6f6cae955f824131886cb8a510e7f478fc40e4f51e5eb5f24b2058c6834",
}
SAMPLE_ATOL = 1e-7
MEAN_ATOL = DESIGN_ATOL = POSITION_COMPARISON_ATOL = 1e-9
SCHEMES = ["MA-MRT", "MA-ZF", "FPA-MRT", "FPA-ZF", "FPA-OPT"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_primitives():
    base = Path(__file__).resolve().parent.parent / "two-timescale-ma-corrected-zf"
    loaded = {}
    for filename, digest in PRIMITIVE_HASHES.items():
        path = base / filename
        assert sha(path) == digest, (filename, "independent oracle source changed")
        name = path.stem
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    return loaded["audit_full200_matlab_v1"], loaded["audit_full200_coordinate_certificates_v1"], base


def history_audit(raw, job, cfg, independent):
    initial, lower, upper, draws, noise, channel, design = independent.geometry_functions(job, cfg)
    assert draws.shape == (1000, 6, 5)
    reports = {}
    for mode in ["mrt", "zf"]:
        history = raw["history"][mode]
        values = np.asarray(history["objective"], float)
        positions = np.asarray(history["positions"], float)
        assert len(values) >= 2 and positions.shape == (len(values), 6, 2)
        assert np.array_equal(positions[0], initial)
        direct = np.array([design(t, mode) for t in positions])
        error = float(np.max(abs(direct-values)))
        assert error < DESIGN_ATOL and np.all(np.diff(values) >= -cfg["verification_tolerance"])
        fractional = float((values[-1]-values[-2])/abs(values[-2]))
        assert history["converged"] and history["termination"] == "fractional_increase"
        assert fractional < cfg["fractional_increase_threshold"]
        distances = np.linalg.norm(positions[:, :, None]-positions[:, None, :], axis=3)
        distances += np.eye(6)[None]*1e9
        assert distances.min() >= .5-cfg["verification_tolerance"]
        assert np.all(positions >= lower-cfg["verification_tolerance"])
        assert np.all(positions <= upper+cfg["verification_tolerance"])
        assert np.array_equal(positions[-1], raw["metrics"][mode+"_positions"])
        assert np.array_equal(positions[-1], raw["metrics"][mode+"_realized_positions"])
        updates = history["coordinate_updates"]
        assert len(updates) == (len(values)-1)*6
        maximum_coordinate_error = 0.
        for index, update in enumerate(updates):
            sweep, antenna = divmod(index, 6)
            assert update["sweep"] == sweep and update["antenna"] == antenna
            before = positions[sweep].copy()
            before[:antenna] = positions[sweep+1, :antenna]
            after = before.copy()
            after[antenna] = positions[sweep+1, antenna]
            error = max(abs(design(before, mode)-update["before"]),
                        abs(design(after, mode)-update["after"]))
            maximum_coordinate_error = max(maximum_coordinate_error, error)
            assert error < DESIGN_ATOL
            assert update["original_subproblem_unchanged"]
            certificate = update["certificate"]
            assert certificate["original_subproblem_unchanged"]
            assert certificate["certified_without_conic_solver_status"]
            assert abs(update["surrogate"]-update["before"]-certificate["minorant_increment"]) < DESIGN_ATOL
            assert abs(update["after"]-update["surrogate"]-update["lower_bound_gap"]) < DESIGN_ATOL
            assert update["lower_bound_gap"] >= -DESIGN_ATOL
        reports[mode] = {
            "accepted_position_count": len(values), "coordinate_count": len(updates),
            "all_design_objectives_and_ordered_coordinate_rate_identities_recomputed": True,
            "maximum_design_abs_error": float(np.max(abs(direct-values))),
            "maximum_coordinate_abs_error": maximum_coordinate_error,
            "all_spacing_box_constraints_verified": True,
            "actual_final_fractional_increase": fractional,
            "source_fractional_threshold": cfg["fractional_increase_threshold"],
            "actual_source_stop_verified": True,
        }
    return reports, initial, noise, channel


def terminal_audit(raw, job, cfg, independent, initial, noise, channel, language,
                   cache, scalar_oracle):
    reports, recomputed, scalar = {}, {}, []
    for scheme in SCHEMES:
        key = scheme if language == "python" else scheme.replace("-", "_")
        position = (np.asarray(raw["metrics"]["mrt_realized_positions" if scheme == "MA-MRT"
                               else "zf_realized_positions"], float)
                    if scheme.startswith("MA-") else initial)
        cache_key = (scheme, position.tobytes())
        if cache_key not in cache:
            h = channel(position)
            if scheme.startswith("MA-"):
                values, powers = independent.ma_rates(h, job["power"], noise,
                                                     "mrt" if scheme == "MA-MRT" else "zf")
                stops = np.ones(1000, bool)
            else:
                values, stops, powers = independent.fixed_batch(h, job["power"], noise,
                                                               scheme, cfg["benchmark_solver"])
                if scalar_oracle:
                    reference = [independent.fixed(sample, job["power"], noise,
                                                   scheme, cfg["benchmark_solver"]) for sample in h]
                    scalar_values = np.array([v[0] for v in reference])
                    scalar_stops = np.array([v[1] for v in reference])
                    error = float(np.max(abs(values-scalar_values)))
                    assert error < SAMPLE_ATOL and np.array_equal(stops, scalar_stops)
                    scalar.append({"scheme": scheme, "all1000_scalar_oracle_checked": True,
                                   "maximum_scalar_batch_abs_error": error})
            cache[cache_key] = values, stops, powers
        values, stops, powers = cache[cache_key]
        saved = raw["metrics"]["schemes"][key]
        sample_rates = np.asarray(saved["sample_sum_rates"], float)
        assert sample_rates.shape == (1000,) and np.all(np.isfinite(sample_rates))
        error = float(np.max(abs(values-sample_rates)))
        mean_error = float(abs(saved["mean_sum_rate"]-np.mean(sample_rates)))
        assert error < SAMPLE_ATOL and mean_error < MEAN_ATOL
        assert np.all(stops) and saved.get("nonconverged_samples", 0) == 0
        assert float(np.max(powers)-job["power"]) < MEAN_ATOL
        if scheme.startswith("MA-"):
            assert np.max(abs(np.asarray(saved["powers"])-powers)) < MEAN_ATOL
        if scheme == "MA-MRT":
            assert abs(raw["history"]["mrt"]["instantaneous_MC_mean"][-1]-np.mean(values)) < MEAN_ATOL
        reports[scheme] = {
            "sample_count": 1000, "all_terminal_samples_independently_recomputed": True,
            "maximum_saved_independent_sample_abs_error": error,
            "saved_mean_identity_abs_error": mean_error,
            "all1000_original_benchmark_stops_and_power_constraints_verified": True,
            "fresh_independent_mean_sum_rate": float(np.mean(values)),
            "maximum_power_excess": float(np.max(powers)-job["power"]),
        }
        recomputed[scheme] = values
    return reports, recomputed, scalar


def compare_states(py, mat, independent_values):
    histories = {}
    for mode in ["mrt", "zf"]:
        ph, mh = py["history"][mode], mat["history"][mode]
        pp, mp = np.asarray(ph["positions"]), np.asarray(mh["positions"])
        po, mo = np.asarray(ph["objective"]), np.asarray(mh["objective"])
        count = min(len(po), len(mo))
        row_position_difference = np.max(abs(pp[:count]-mp[:count]), axis=(1, 2))
        row_objective_difference = abs(po[:count]-mo[:count])
        different = np.flatnonzero((row_position_difference > POSITION_COMPARISON_ATOL)
                                   | (row_objective_difference > DESIGN_ATOL))
        histories[mode] = {
            "python_position_count": len(po), "matlab_position_count": len(mo),
            "same_length": len(po) == len(mo),
            "shared_prefix_position_max_abs_difference": float(np.max(row_position_difference)),
            "shared_prefix_objective_max_abs_difference": float(np.max(row_objective_difference)),
            "first_shared_prefix_position_or_objective_difference_above_fixed_comparison_gate":
                int(different[0]) if len(different) else None,
            "terminal_position_max_abs_difference": float(np.max(abs(pp[-1]-mp[-1]))),
            "terminal_design_objective_difference_python_minus_matlab": float(po[-1]-mo[-1]),
            "same_path_within_fixed_comparison_gates": not len(different) and len(po) == len(mo),
            "terminal_state_bitwise_equal": bool(np.array_equal(pp[-1], mp[-1])),
            "solver_enumeration_and_null_serialization_not_bitwise_equal_required": True,
        }
    schemes = {}
    for scheme in SCHEMES:
        pv, mv = independent_values["python"][scheme], independent_values["matlab"][scheme]
        ps = np.asarray(py["metrics"]["schemes"][scheme]["sample_sum_rates"])
        ms = np.asarray(mat["metrics"]["schemes"][scheme.replace("-", "_")]["sample_sum_rates"])
        residual = (ps-ms)-(pv-mv)
        schemes[scheme] = {
            "saved_sample_rate_difference_max_abs": float(np.max(abs(ps-ms))),
            "independent_same_evaluator_at_own_states_sample_difference_max_abs": float(np.max(abs(pv-mv))),
            "independent_mean_difference_python_minus_matlab": float(np.mean(pv)-np.mean(mv)),
            "evaluator_residual_after_own_state_difference_max_abs": float(np.max(abs(residual))),
            "same_terminal_samples_within_fixed_sample_comparison_gate": bool(np.max(abs(ps-ms)) < SAMPLE_ATOL),
        }
    return {"input_difference": False,
            "metric_evaluator_difference_above_independent_validation_gates": False,
            "solver_state_or_trajectory_difference": any(not h["same_path_within_fixed_comparison_gates"]
                                                          for h in histories.values()),
            "histories": histories, "schemes": schemes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bank", required=True)
    parser.add_argument("--matlab-bank", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--public", required=True)
    args = parser.parse_args()
    pybank, matbank = Path(args.python_bank).resolve(), Path(args.matlab_bank).resolve()
    out, public = Path(args.out).resolve(), Path(args.public).resolve()
    assert not out.exists() and not public.exists(), "Distinct immutable audit version required."
    independent, certificates, oracle_base = load_primitives()
    cfgpath, progresspath = pybank/"run_config.json", pybank/"execution-progress.json"
    cfgbytes, progressbytes = cfgpath.read_bytes(), progresspath.read_bytes()
    cfg, snapshot = json.loads(cfgbytes), json.loads(progressbytes)
    records = snapshot["records"]
    assert 0 < len(records) < 200 and snapshot["finished_jobs"] == len(records)
    assert len({r["filename"] for r in records}) == len(records)
    assert cfg["geometry_realizations"] == 100 and cfg["nlos_realizations_per_geometry"] == 1000
    assert cfg["fractional_increase_threshold"] == 5e-5
    assert cfg["maximum_AO_iterations"] == 10000 and snapshot["implementation_fingerprint"] == PY_FP
    frozen = {"independent_audit_script": sha(Path(__file__)), "inputs/run_config.json": sha(cfgpath)}
    for name in PRIMITIVE_HASHES:
        frozen["independent_oracle/"+name] = sha(oracle_base/name)
    files = {"independent_audit_script": Path(__file__), "inputs/run_config.json": cfgpath}
    files.update({"independent_oracle/"+name: oracle_base/name for name in PRIMITIVE_HASHES})
    for record in records:
        name = record["filename"]
        paths = {"inputs/"+name: pybank/"jobs"/name,
                 "python_raw/"+record["result"]: pybank/record["result"],
                 "matlab_raw/"+Path(name).stem+"-matlab.json": matbank/(Path(name).stem+"-matlab.json")}
        files.update(paths)
        frozen.update({key: sha(path) for key, path in paths.items()})
    frozen["matlab_execution_identity"] = sha(matbank/"execution-identity.json")
    files["matlab_execution_identity"] = matbank/"execution-identity.json"
    freeze = {"scope": "all_actual_completed_Python_records_at_one_snapshot_not_full200_dual",
              "snapshot_record_count": len(records), "expected_full_bank_count": 200,
              "snapshot_progress_sha256": hashlib.sha256(progressbytes).hexdigest(),
              "snapshot_records": records, "sources_inputs_raw_sha256": frozen,
              "python_implementation_fingerprint": PY_FP, "matlab_implementation_fingerprint": MAT_FP,
              "fixed_sample_atol": SAMPLE_ATOL, "fixed_mean_design_atol": MEAN_ATOL,
              "fixed_position_comparison_atol": POSITION_COMPARISON_ATOL,
              "subset_selected_only_by_completion_snapshot_not_rate_or_nearest_solution": True,
              "no_full200_dual_or_source_graph_closeness_claim": True}
    freezepath = out.with_name(out.stem+"-freeze.json")
    independent.atomic(freezepath, freeze)
    completed, failures = [], []
    started = time.perf_counter()
    for index, record in enumerate(records):
        name, stem = record["filename"], Path(record["filename"]).stem
        try:
            jobpath = pybank/"jobs"/name
            job = json.loads(jobpath.read_bytes())
            expected = hashlib.sha256(b"strict-v1\0"+cfgbytes+b"\0"+jobpath.read_bytes()).hexdigest()
            py = json.loads((pybank/record["result"]).read_bytes())
            mat = json.loads((matbank/(stem+"-matlab.json")).read_bytes())
            assert record["status"] == "converged_complete", ("saved runner status", record["status"])
            assert py["implementation_fingerprint"] == PY_FP and mat["implementation_fingerprint"] == MAT_FP
            assert py["input_fingerprint"] == mat["input_fingerprint"] == record["input_fingerprint"] == expected
            assert py["job_metadata"] == mat["job_metadata"]
            assert mat["runtime_source_identity"]["fresh_before_after_not_persistent_cache"]
            assert mat["matlab_source_version"] == "MATLAB-full-v2-history-storage"
            pair, values, cache = {}, {}, {}
            for language, raw in [("python", py), ("matlab", mat)]:
                assert raw["checks"]["full_N"] == 6 and raw["checks"]["full_M"] == 5
                assert raw["checks"]["nlos_samples"] == 1000
                histories, initial, noise, channel = history_audit(raw, job, cfg, independent)
                schemes, current_values, scalar = terminal_audit(raw, job, cfg, independent,
                    initial, noise, channel, language, cache, scalar_oracle=index == 0 and language == "python")
                certificate_checks = certificates.check_case(raw, job, cfg)
                pair[language] = {"all_independent_physical_stop_and_coordinate_certificate_gates": True,
                                  "histories": histories, "schemes": schemes,
                                  "independent_global_coordinate_certificate_checks": certificate_checks,
                                  "first_snapshot_case_all1000_scalar_oracles": scalar}
                values[language] = current_values
            completed.append({"case": stem, "input_fingerprint": expected,
                              "all_independent_validation_gates": True,
                              "languages": pair, "differences": compare_states(py, mat, values)})
        except Exception as exc:
            failures.append({"case": stem, "type": type(exc).__name__, "message": str(exc),
                             "stack": traceback.format_exc(), "failure_preserved_not_dropped": True})
        report = {"scope": "frozen_completed_subset_all_same_input_actual_Python_MATLAB_terminal1000_and_original_stops",
                  "snapshot_count": len(records), "expected_full_bank_count": 200,
                  "attempted": index+1, "validated": len(completed), "validation_failures": len(failures),
                  "all_snapshot_independent_validation_gates_passed": index+1 == len(records) and not failures,
                  "full200_dual_pass_claimed": False, "original_curve_closeness_claimed": False,
                  "counts100_geometry1000_NLoS_are_configured_not_reported_author_MC_counts": True,
                  "no_selection_reweight_offset_threshold_relaxation_or_live_source_edit": True,
                  "source_stop_threshold": 5e-5,
                  "certificate_scope": "global original concave coordinate minorant only, not global nonconvex AO optimum",
                  "same_nonconvex_local_solution_not_guaranteed": True,
                  "records": completed, "failures": failures,
                  "elapsed_seconds": time.perf_counter()-started, "freeze_sha256": sha(freezepath)}
        independent.atomic(out, report)
        print(json.dumps({k: report[k] for k in ["attempted", "snapshot_count", "validated", "validation_failures", "elapsed_seconds"]}), flush=True)
    unchanged = frozen == {key: sha(path) for key, path in files.items()}
    report["all_frozen_source_inputs_and_both_raw_outputs_unchanged_at_end"] = unchanged
    report["difference_counts"] = {
        "input": 0 if not failures else None,
        "metric_evaluator_above_independent_gates": 0 if not failures else None,
        "solver_state_or_trajectory": sum(row["differences"]["solver_state_or_trajectory_difference"] for row in completed),
        "terminal_samples_above_fixed_sample_gate_by_scheme": {
            scheme: sum(not row["differences"]["schemes"][scheme]["same_terminal_samples_within_fixed_sample_comparison_gate"]
                        for row in completed) for scheme in SCHEMES}}
    independent.atomic(out, report)
    independent.atomic(public, report)
    assert unchanged, "Retain changed-identity failure, never claim frozen evidence."
    assert report["all_snapshot_independent_validation_gates_passed"], "Retain all actual independent-gate failures."


if __name__ == "__main__":
    main()
