"""Outside-core all-position/all1000 independent native Fig4 QR audit.

No production numerical modules; numerical execution is separate from the
prepare-only source/input/hash inventory. Do not edit this entry mid-run.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
import traceback

for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_key] = "1"
import numpy as np
from scipy.io import loadmat

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
REPO = WORK.parent / "wireless-paper-reproductions"
ORACLE_PATH = REPO / "strict/validation/two-timescale-ma-corrected-zf/audit_full200_matlab_v1.py"
PLAN_PATH = HERE / "FIGURE04_ALL200_INDEPENDENT_AUDIT_PLAN_V1.md"
NATIVE_HELPER = HERE / "run_native_ma_figure04_from_completed03_work.m"
EXPECTED_HELPER_SHA = "ab7081bea5bc0381dea86510dd5c248cb0d53f6ade2d8f61efbb0f537eee3728"
EXPECTED_ORACLE_SHA = "29c42f0a8920d179fd32f81aa47931119b2f890ef3ed4e7ae63be9a4c562707d"
EXPECTED_SOURCE_FP = "e78708e52bbfe9733a9fe24faaa736188015469a9d87ea90b41c5a1d0966bf37"
RATE_ATOL = 1e-7
MEAN_ATOL = DESIGN_ATOL = 1e-9
RELATIVE_ZF_ATOL = 1e-9
SAVED_LEAKAGE_ATOL = 1e-15


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def atomic(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    # I/O-only retries for OneDrive sharing contention, not numerical retries.
    for attempt in range(12):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(min(.05 * 2**attempt, 1.))


def independent_oracle():
    assert sha(ORACLE_PATH) == EXPECTED_ORACLE_SHA
    spec = importlib.util.spec_from_file_location("independent_fig04_physics_v1", ORACLE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def qr_samples(h, power, noise):
    count, _, users = h.shape
    q, r = np.linalg.qr(h, mode="reduced")
    v = q @ np.linalg.solve(r.conj().transpose(0, 2, 1), np.broadcast_to(np.eye(users), (count, users, users)))
    w = v / np.linalg.norm(v, axis=1)[:, None, :] * np.sqrt(power / users)
    hw = h.conj().transpose(0, 2, 1) @ w
    gains = np.abs(hw)**2
    signal = np.diagonal(gains, axis1=1, axis2=2)
    rates = np.log2(1 + signal / (gains.sum(axis=2) - signal + noise)).sum(axis=1)
    diagonal = np.diagonal(hw, axis1=1, axis2=2)
    off = hw.copy()
    idx = np.arange(users)
    off[:, idx, idx] = 0
    leak = np.abs(off).max(axis=(1, 2))
    scale = np.abs(diagonal).max(axis=1)
    assert np.all(scale > 0)
    powers = np.sum(np.abs(w)**2, axis=(1, 2))
    return rates, powers, leak, leak / scale


def scalar_svd_rates(h, power, noise):
    values = []
    for single in h:
        # The Moore-Penrose solution of H^H V=I is minimum norm, independently
        # found by SVD/lstsq rather than QR or the production normal equations.
        v, _, rank, _ = np.linalg.lstsq(single.conj().T, np.eye(single.shape[1]), rcond=None)
        assert rank == single.shape[1]
        w = v / np.linalg.norm(v, axis=0)[None, :] * np.sqrt(power / single.shape[1])
        gains = np.abs(single.conj().T @ w)**2
        signal = np.diag(gains)
        values.append(float(np.log2(1 + signal / (gains.sum(axis=1) - signal + noise)).sum()))
    return np.array(values)


def prepare(inputs, source, native):
    config_path = inputs / "run_config.json"
    cfg, manifest, plan = read(config_path), read(inputs / "manifest.json"), read(inputs / "plan.json")
    source_identity = read(source / "execution-identity.json")
    start = read(native / "actual-execution-start-binding.json")
    completion = read(native / "actual-completion-receipt.json")
    assert cfg["geometry_realizations"] == 100 and cfg["nlos_realizations_per_geometry"] == 1000
    assert plan["figure"] == 3 and len(plan["cases"]) == 2 and manifest["expected_jobs"] == 200
    assert source_identity["expected_jobs"] == 200 and len(source_identity["records"]) == 200
    assert source_identity["implementation_fingerprint"] == EXPECTED_SOURCE_FP
    assert source_identity["all_result_identities_pass"] and source_identity["source_unchanged_during_run"]
    assert source_identity["runtime_dependency_identity_unchanged"]
    assert start["mode"] == "full200" and start["position_optimization_rerun"] is False
    assert start["source_implementation_fingerprint"] == EXPECTED_SOURCE_FP
    assert completion["actual_evaluated_jobs"] == 200 and completion["native_full200_history_evaluation_complete"]
    assert completion["source_start_binding_sha256"] == sha(native / "actual-execution-start-binding.json")
    assert completion["derivation_source_before_after_unchanged"] and completion["all_required_source200_bytes_unchanged"]
    assert sha(NATIVE_HELPER) == EXPECTED_HELPER_SHA == start["derivation_entry_sha256"]
    assert sha(ORACLE_PATH) == EXPECTED_ORACLE_SHA
    for field, path in (("source_configuration_sha256", config_path),
                        ("source_manifest_sha256", inputs / "manifest.json"),
                        ("source_plan_sha256", inputs / "plan.json"),
                        ("source_execution_identity_sha256", source / "execution-identity.json")):
        assert start[field] == sha(path), field
    bindings = {v["input"]: v for v in start["required_source200_bindings"]}
    source_records = {v["input_filename"]: v for v in source_identity["records"]}
    completion_records = {v["source_input"]: v for v in completion["records"]}
    files = {"audit_entry": Path(__file__), "audit_plan": PLAN_PATH,
             "native_derivation_helper": NATIVE_HELPER, "independent_physical_oracle": ORACLE_PATH,
             "inputs/config": config_path, "inputs/manifest": inputs / "manifest.json", "inputs/plan": inputs / "plan.json",
             "source/execution_identity": source / "execution-identity.json",
             "native/start_binding": native / "actual-execution-start-binding.json",
             "native/completion_receipt": native / "actual-completion-receipt.json"}
    cases, positions = [], 0
    assert len(manifest["files"]) == len(bindings) == len(completion_records) == 200
    for entry in manifest["files"]:
        stem = Path(entry["filename"]).stem
        job_path, raw_path = inputs / "jobs" / entry["filename"], source / (stem + "-matlab.json")
        native_path = native / (stem + "-native-figure04.json")
        rec, item, src = read(native_path), bindings[entry["filename"]], source_records[entry["filename"]]
        mat_path = native / rec["raw_all1000_samples_file"]
        assert mat_path.parent == native and mat_path.is_file()
        fingerprint = hashlib.sha256(b"strict-v1\0" + config_path.read_bytes() + b"\0" + job_path.read_bytes()).hexdigest()
        assert fingerprint == entry["input_fingerprint"] == rec["source_input_fingerprint"] == src["input_fingerprint"]
        assert rec == completion_records[entry["filename"]]
        assert rec["source_input"] == entry["filename"] and rec["case_index"] == entry["case_index"]
        assert rec["realization"] == entry["realization"]
        assert item["input_sha256"] == sha(job_path)
        assert item["source_result_sha256"] == sha(raw_path) == rec["source_raw_result_sha256"] == src["result_sha256"]
        assert rec["raw_all1000_samples_sha256"] == sha(mat_path)
        assert rec["original_positions_reoptimized"] is False and rec["nlos_per_position"] == 1000
        assert rec["N"] == 6 and rec["M"] == 5 and rec["kappa"] in (6, 100)
        positions += rec["accepted_ZF_positions"]
        for prefix, path in (("input", job_path), ("source", raw_path), ("native", native_path), ("native_samples", mat_path)):
            files[prefix + "/" + path.name] = path
        cases.append((entry, job_path, raw_path, native_path, mat_path))
    # Actual counts come from every native record, then are independently
    # checked against each source trajectory during numerical execution.
    assert positions > 200
    assert [sum(v[0]["case_index"] == k for v in cases) for k in (0, 1)] == [100, 100]
    frozen = {key: sha(path) for key, path in files.items()}
    return cfg, cases, files, frozen, positions


def audit_case(entry, job_path, raw_path, native_path, mat_path, cfg, oracle, scalar_check):
    job, raw, rec = read(job_path), read(raw_path), read(native_path)
    history = raw["history"]["zf"]
    positions, objectives = np.array(history["positions"]), np.array(history["objective"])
    count = len(objectives)
    assert job["figure"] == 3 and job["N"] == 6 and job["M"] == 5
    assert positions.shape == (count, 6, 2) and count >= 2 and count == rec["accepted_ZF_positions"]
    initial, lower, upper, draws, noise, channel, design = oracle.geometry_functions(job, cfg)
    assert draws.shape == (1000, 6, 5) and np.array_equal(positions[0], initial)
    saved = loadmat(mat_path)
    samples = np.asarray(saved["sampleSumRates"])
    means = np.asarray(saved["meanRates"]).reshape(-1)
    saved_power = np.asarray(saved["powerErrors"]).reshape(-1)
    saved_leak = np.asarray(saved["offDiagonal"]).reshape(-1)
    assert samples.shape == (count, 1000) and means.shape == saved_power.shape == saved_leak.shape == (count,)
    assert all(np.all(np.isfinite(a)) for a in (positions, objectives, samples, means, saved_power, saved_leak))
    assert np.array_equal(objectives, np.array(rec["original_statistical_objective_history"]))
    assert np.array_equal(means, np.array(rec["actual_full1000_MC_history"]))
    # Recompute the design stop; historical/source booleans cannot supply it.
    direct_design = np.array([design(t, "zf") for t in positions])
    design_error = float(np.max(np.abs(direct_design - objectives)))
    fractional = float((direct_design[-1] - direct_design[-2]) / abs(direct_design[-2]))
    source_checks = {"all_design_objectives": design_error < DESIGN_ATOL,
                     "design_monotonicity": bool(np.all(np.diff(direct_design) >= -cfg["verification_tolerance"])),
                     "actual_fractional_stop": fractional < cfg["fractional_increase_threshold"],
                     "original_stop_label_agrees": history["converged"] is True and history["termination"] == "fractional_increase",
                     "initial_position_exact": True}
    state_checks, failures = [], []
    for k, t in enumerate(positions):
        try:
            h = channel(t)
            assert h.shape == (1000, 6, 5) and np.all(np.isfinite(h))
            rates, powers, leaks, relative = qr_samples(h, job["power"], noise)
            distances = np.linalg.norm(t[:, None, :] - t[None, :, :], axis=2) + np.eye(6) * 1e9
            rate_error = float(np.max(np.abs(rates - samples[k])))
            mean_error = float(abs(np.mean(rates) - means[k]))
            saved_mean_identity = float(abs(np.mean(samples[k]) - means[k]))
            power_error = float(np.max(np.abs(powers - job["power"])))
            power_replay_error = float(abs(power_error - saved_power[k]))
            leakage_replay_error = float(abs(np.max(leaks) - saved_leak[k]))
            checks = {"all1000_sample_rates": rate_error < RATE_ATOL,
                      "fresh_mean": mean_error < MEAN_ATOL,
                      "saved_mean_identity": saved_mean_identity < MEAN_ATOL,
                      "all1000_power_equalities": power_error <= 1e-10 * max(1., job["power"]),
                      "saved_power_error_replay": power_replay_error <= 1e-12 * max(1., job["power"]),
                      "all1000_relative_ZF_residuals": float(np.max(relative)) <= RELATIVE_ZF_ATOL,
                      "saved_leakage_replay": leakage_replay_error <= SAVED_LEAKAGE_ATOL,
                      "spacing": float(np.min(distances)) >= .5 - cfg["verification_tolerance"],
                      "box": bool(np.all(t >= lower - cfg["verification_tolerance"]) and np.all(t <= upper + cfg["verification_tolerance"])),
                      "all1000_finite": bool(np.all(np.isfinite(rates)) and np.all(np.isfinite(powers)))}
            scalar_error = None
            if scalar_check and k in (0, count - 1):
                scalar = scalar_svd_rates(h, job["power"], noise)
                scalar_error = float(np.max(abs(scalar - rates)))
                checks["all1000_scalar_SVD_reference"] = scalar_error < RATE_ATOL
            if k == count - 1:
                terminal = np.array(raw["metrics"]["schemes"]["MA_ZF"]["sample_sum_rates"])
                assert terminal.shape == (1000,)
                checks["source_terminal_samples_exactly_reused"] = bool(np.array_equal(terminal, samples[k]))
                checks["source_terminal_position_exactly_reused"] = bool(np.array_equal(np.array(raw["metrics"]["zf_realized_positions"]), t))
            state_checks.append({"position_index": k, "sample_count": 1000, "checks": checks,
                                 "maximum_sample_rate_abs_error": rate_error, "fresh_mean_abs_error": mean_error,
                                 "saved_mean_identity_abs_error": saved_mean_identity, "maximum_power_abs_error": power_error,
                                 "saved_power_error_abs_difference": power_replay_error,
                                 "maximum_relative_ZF_residual": float(np.max(relative)),
                                 "saved_leakage_abs_difference": leakage_replay_error,
                                 "minimum_spacing": float(np.min(distances)), "scalar_SVD_rate_abs_error": scalar_error})
            if not all(checks.values()):
                failures.append({"position_index": k, "failed_gates": [name for name, passed in checks.items() if not passed]})
        except Exception as exc:
            failures.append({"position_index": k, "type": type(exc).__name__, "message": str(exc), "stack": traceback.format_exc()})
    all_pass = all(source_checks.values()) and len(state_checks) == count and not failures
    return {"case": job_path.stem, "kappa": job["kappa"], "case_index": entry["case_index"],
            "positions_including_initial": count, "post_sweep_positions": count - 1,
            "required_sample_rates": count * 1000, "checked_sample_rates": len(state_checks) * 1000,
            "source_checks": source_checks, "maximum_statistical_design_objective_abs_error": design_error,
            "fresh_final_fractional_increase": fractional, "unchanged_fractional_stop_threshold": cfg["fractional_increase_threshold"],
            "all_position_sample_source_gates_passed": all_pass, "all_position_checks": state_checks, "failures": failures}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs-bank", required=True)
    parser.add_argument("--source-bank", required=True)
    parser.add_argument("--native-bank", required=True)
    parser.add_argument("--out-folder", required=True)
    parser.add_argument("--mode", choices=("full200", "preflight-first-case"), required=True)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    inputs, source, native, out = (Path(p).resolve() for p in (args.inputs_bank, args.source_bank, args.native_bank, args.out_folder))
    assert not out.exists(), "Fresh evidence folder required; do not overwrite prior attempts."
    cfg, cases, files, frozen, required_positions = prepare(inputs, source, native)
    atomic(out / "before-execution-freeze.json", {"scope": "all200_native_Fig4_independent_audit_before_any_numerical_checks",
           "source_input_raw_oracle_entry_sha256": frozen, "required_jobs": 200,
           "required_positions_including_initial": required_positions, "required_sample_rates": required_positions * 1000,
           "no_production_numerical_kernel_import": True, "mode": args.mode, "prepare_only": args.prepare_only,
           "numerical_audit_pass_not_yet_claimed": True,
           "predeclared_tolerances": {"sample_rate_atol": RATE_ATOL, "mean_atol": MEAN_ATOL,
                 "design_objective_atol": DESIGN_ATOL, "relative_ZF_atol": RELATIVE_ZF_ATOL,
                 "saved_leakage_atol": SAVED_LEAKAGE_ATOL, "spacing_box": cfg["verification_tolerance"],
                 "fractional_stop": cfg["fractional_increase_threshold"]}})
    if args.prepare_only:
        print(json.dumps({"all200_hash_bindings_prepared": True, "numerical_audit_executed": False,
                          "frozen_file_count": len(frozen), "before_freeze_sha256": sha(out / "before-execution-freeze.json")}))
        return
    oracle, began = independent_oracle(), time.perf_counter()
    selected = cases if args.mode == "full200" else cases[:1]
    records, failures, positions, samples = [], [], 0, 0
    for index, (entry, job_path, raw_path, native_path, mat_path) in enumerate(selected):
        try:
            result = audit_case(entry, job_path, raw_path, native_path, mat_path, cfg, oracle, index == 0)
            atomic(out / (job_path.stem + "-independent-all-position-audit.json"), result)
            summary = {key: value for key, value in result.items() if key not in ("all_position_checks", "failures")}
            summary["position_evidence_file"] = job_path.stem + "-independent-all-position-audit.json"
            summary["position_evidence_sha256"] = sha(out / summary["position_evidence_file"])
            records.append(summary)
            positions += len(result["all_position_checks"])
            samples += result["checked_sample_rates"]
            if not result["all_position_sample_source_gates_passed"]:
                failures.append({"case": job_path.stem, "source_checks": result["source_checks"], "position_failures": result["failures"]})
        except Exception as exc:
            failures.append({"case": job_path.stem, "type": type(exc).__name__, "message": str(exc), "stack": traceback.format_exc()})
        report = {"scope": "independent_native_Fig4_same_source_ZF_trajectory_all1000_MC_replay_no_reoptimization",
                  "mode": args.mode, "attempted": index + 1, "required_jobs": len(selected), "full_bank_jobs": 200,
                  "checked_positions_including_initial": positions, "checked_sample_rates": samples,
                  "failures": failures, "records": records, "elapsed_seconds": time.perf_counter() - began,
                  "all_required_numeric_gates_passed": index + 1 == len(selected) and not failures,
                  "full200_numeric_audit_passed": args.mode == "full200" and index + 1 == 200 and not failures
                        and positions == required_positions and samples == required_positions * 1000,
                  "historical_original_Fig4_closeness_or_full_Python_design_bank_claimed": False,
                  "counts100_geometry1000_NLoS_are_declared_not_author_reported": True,
                  "before_freeze_sha256": sha(out / "before-execution-freeze.json")}
        atomic(out / "actual-audit-progress.json", report)
        print(json.dumps({key: report[key] for key in ("attempted", "checked_positions_including_initial", "checked_sample_rates", "elapsed_seconds")} | {"failed_cases": len(failures)}), flush=True)
    after = {key: sha(path) for key, path in files.items()}
    report["all_frozen_source_input_raw_oracle_entry_bytes_unchanged"] = after == frozen
    report["after_execution_sha256"] = after
    report["all_required_numeric_gates_passed"] &= after == frozen
    report["full200_numeric_audit_passed"] &= after == frozen
    atomic(out / "actual-audit-completion.json", report)
    assert report["all_required_numeric_gates_passed"], "Retain all failed evidence; never relax the predeclared gates."


if __name__ == "__main__":
    main()
