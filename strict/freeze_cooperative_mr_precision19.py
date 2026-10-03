"""Verify actual final183 failures and freeze19 same-QT precision witnesses.

No original author papers/artwork/private files are copied. Generated numerical
fixtures and the complete old native result remain local and are SHA-bound.
This never upgrades a failed old point or certifies a new full183 run.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

STRICT = Path(__file__).resolve().parent
WORKSPACE = STRICT.parent.parent
BASE = STRICT / "cooperative-satcom"
WORK = WORKSPACE / "work/cooperative-rgd-audit"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main(args):
    bank_path = BASE / "outputs/guarded-all-figures-final-python.json"
    native = read(bank_path)
    summary = read(args.input_dir / "all-final183-MR-failure-components.json")
    snapshot_path = args.input_dir / "final183-failure-snapshot.json"
    snapshot = read(snapshot_path)
    failures = [p for p in native["results"] if not p["valid_figure_point"]]
    required = [p for p in failures if (p.get("failure_receipt") or {}).get("block") == "mr_QT_same_problem"]
    assert len(native["results"]) == 183 and len(failures) == 29 and len(required) == 19
    assert native["source_unchanged_during_run"]
    assert snapshot["native_sha256"] == sha(bank_path)
    assert snapshot["actual_valid_points"] == 154 and snapshot["actual_failed_points"] == 29
    assert snapshot["all_failure_snapshot"] == [{
        **{k: p.get(k) for k in ("sweep", "parameter", "value", "status", "error", "constraint_pass",
            "convergence_pass", "solver_primal_pass", "qt_bound_pass", "valid_figure_point")},
        "block": (p.get("failure_receipt") or {}).get("block"),
        "original_attempts": (p.get("failure_receipt") or {}).get("attempts"),
        "generated_fixture": (p.get("failure_receipt") or {}).get("generated_fixture"),
        "original_failure_kept": True} for p in failures]
    assert summary["snapshot_sha256"] == sha(snapshot_path)
    assert summary["required_snapshot_components"] == summary["actually_completed_components"] == 19
    assert summary["all_required_components_precision_pass"] and summary["source_unchanged_during_batch"]
    scientific_hashes = {n: sha(BASE / n) for n in native["executed_source_hashes"]}
    assert scientific_hashes == native["executed_source_hashes"] == snapshot["executed_source_hashes"]
    assert all(v is False for v in native["checks"].values())
    expected = {(p["sweep"], p["value"]): p for p in required}
    assert len(expected) == 19
    actual_keys = set()
    components = []
    input_manifest = []
    helper_sources = {}
    for recorded in summary["actual_results"]:
        key = (recorded["sweep"], recorded["value"])
        assert key in expected and key not in actual_keys
        actual_keys.add(key)
        original = expected[key]
        fixture = original["failure_receipt"]["generated_fixture"]
        fixture_path = BASE / fixture["filename"]
        assert sha(fixture_path) == fixture["sha256"] == recorded["fixture_sha256"]
        component_path = args.input_dir / recorded["component_receipt"]
        receipt = read(component_path)
        assert sha(component_path) == recorded["component_receipt_sha256"]
        assert receipt["fixture_sha256"] == fixture["sha256"]
        assert recorded["actual_status"] == "executed" and recorded["actual_error"] is None
        assert recorded["all_original_and_independent_precision_gates_pass"] and recorded["component_source_unchanged"]
        assert receipt["source_unchanged_during_run"] and receipt["original_all_precision_gates_pass"]
        assert receipt["all_original_and_independent_precision_gates_pass"]
        assert receipt["independent80digit_dual"]["all_independent80digit_precision_pass"]
        assert all(receipt["independent80digit_dual"]["checks"].values())
        assert receipt["independent80digit_dual"]["precision_decimal_digits"] == 80
        for field in ("true_feasible_primal_dual_gap", "actual_raw_primal_dual_gap"):
            assert 0 <= float(receipt["independent80digit_dual"][field]) <= 1e-5
        assert receipt["independent_random_identity_tests"] == 1000
        assert receipt["identity_maximum_relative_error"] < 1e-12
        assert receipt["executed_source_hashes"] == {n: scientific_hashes[n] for n in receipt["executed_source_hashes"]}
        for name, digest in receipt["executed_WORK_hashes"].items():
            assert sha(WORK / name) == digest
            if name in helper_sources:
                assert helper_sources[name] == digest
            helper_sources[name] = digest
        input_manifest.append({"sweep": key[0], "value": key[1], "fixture_sha256": fixture["sha256"],
            "native_component_sha256": sha(component_path)})
        components.append({
            "sweep": key[0], "value": key[1], "fixture_sha256": fixture["sha256"],
            "native_component_sha256": sha(component_path),
            "original_same_QT_precision_pass": receipt["original_all_precision_gates_pass"],
            "actual_QT_before_and_after": {n: receipt["actual_info"][n] for n in ("before", "after")},
            "actual_QT_solver_diagnostics": receipt["actual_info"]["solver_diagnostics"],
            "original_QT_bound_max_violation": receipt["actual_info"]["qt_bound_max_violation"],
            "independent80digit_primal_dual_certificate": receipt["independent80digit_dual"],
            "independent_identity_draws": receipt["independent_random_identity_tests"],
            "identity_maximum_relative_error": receipt["identity_maximum_relative_error"],
            "source_unchanged_during_run": True,
            "whole_old_failed_point_repaired_or_rerun": False,
        })
    assert actual_keys == set(expected)
    source_final = {n: sha(BASE / n) for n in scientific_hashes}
    assert source_final == scientific_hashes
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "scope": "actual_Python_all19_original_failed_MR_QT_inputs_exact_factor_identity_and80digit_precision_NOT_complete_183_rerun",
        "exact_identity": "sqrt(scale*v)=sqrt(scale)*sqrt(v), scale>0; move only fixed constant outside square-root cone",
        "unchanged": ["original finite-Rician moments", "all independent J*U powers", "same original QT auxiliaries",
            "same power and interference constraints", "original1e-5 numerical acceptance gates", "all original failing inputs"],
        "required_actual_failure_components": 19, "actual_components_executed": 19,
        "all_original_and_independent_precision_components_pass": True,
        "actual_identity_test_draws": 19000,
        "maximum_identity_relative_error": max(x["identity_maximum_relative_error"] for x in components),
        "maximum_true_feasible_primal_dual_gap": max(float(x["independent80digit_primal_dual_certificate"]["true_feasible_primal_dual_gap"]) for x in components),
        "all_component_scientific_sources_unchanged": True,
        "actual_components": components,
        "complete_old183_native_sha256": sha(bank_path), "complete_old183_native_size_bytes": bank_path.stat().st_size,
        "old183_completed": 183, "old183_valid": 154, "old183_failed": 29,
        "old_failed_points_kept_and_not_upgraded": True,
        "new_complete183_rerun_executed": False, "MATLAB19_precision_execution_verified": False,
        "historical_figure_agreement_verified": False, "full_reproduction_pass": False,
        "executed_scientific_source_hashes": scientific_hashes,
        "executed_WORK_component_source_hashes": helper_sources,
    }
    failure_output = {k: snapshot[k] for k in ("scope", "native_sha256", "native_size_bytes", "actual_full_points",
        "actual_valid_points", "actual_failed_points", "actual_elapsed_seconds", "original_all_scope_checks",
        "failure_groups", "executed_source_hashes", "source_unchanged_during_run", "all_failure_snapshot", "full_reproduction_pass")}
    failure_output["scope"] = "actual_complete_old183_Python_bank_failure_evidence_NOT_new_version_success"
    write(args.output_dir / "same-QT-precision19-python.json", receipt)
    write(args.output_dir / "old183-failure-snapshot.json", failure_output)
    (args.output_dir / "README.md").write_text(
        "# Same-QT numerical precision: all19 actual failed inputs\n\n"
        "The complete older Python sweep executed183 points:154 valid and29 failed. "
        "All29 failures remain failures in that bank. Ten are phase Armijo failures;19 are MR QT precision failures.\n\n"
        "Every one of those19 actual generated QT inputs was executed again in a separate WORK diagnostic. "
        "The only algebraic change moves sqrt(scale), an exact positive constant, outside the square-root cone. "
        "All19 pass the unchanged original feasibility, QT bound and monotonicity gates, plus independent80-digit "
        "feasible-primal/dual-gap checks at the same1e-5 threshold.19000 independent random identity checks also pass.\n\n"
        "These receipts do not certify a new complete183 sweep, MATLAB execution of all19 inputs, historical "
        "channel/geometry recovery, or agreement with published curves. Generated original fixtures and the large "
        "old bank stay local; their hashes bind the actual inputs and evidence. No author manuscript or artwork is copied.\n\n"
        "The manifest binds current executed scientific/helper sources and the two compact actual receipts. "
        "Do not reinterpret numeric component success as full figure reproduction.\n", encoding="utf-8")
    files = {p.name: {"sha256": sha(p), "bytes": p.stat().st_size} for p in args.output_dir.iterdir()
             if p.is_file() and p.name != "manifest.json"}
    manifest = {"scope": receipt["scope"], "verification": "all19 required actual input/source/receipt identities and unchanged precision gates checked",
        "executed_scientific_source_hashes": scientific_hashes,
        "executed_WORK_component_source_hashes": helper_sources,
        "freezer_source_sha256": sha(__file__), "original_actual_inputs": input_manifest,
        "original_complete_bank_sha256": sha(bank_path), "source_unchanged_during_freeze": source_final == scientific_hashes,
        "public_files": files, "new_full183_success": False, "full_reproduction_pass": False}
    write(args.output_dir / "manifest.json", manifest)
    print(json.dumps({"output": str(args.output_dir), "actual_required_components": 19,
        "all_original_and_independent_precision_components_pass": True,
        "maximum_true_feasible_primal_dual_gap": receipt["maximum_true_feasible_primal_dual_gap"],
        "old183": {"valid": 154, "failed": 29}, "new_complete183_rerun_executed": False,
        "public_files": len(files) + 1}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=WORK / "final183-all-MR-fixtures-v1")
    parser.add_argument("--output-dir", type=Path, default=STRICT / "validation/cooperative-mr-precision19-python-v1")
    main(parser.parse_args())
