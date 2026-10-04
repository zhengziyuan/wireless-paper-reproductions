"""Replay saved full12000 summaries, not optimization or physical certification."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / "packet-files.json").read_bytes())
    for name, expected in manifest["files_sha256"].items():
        if sha(HERE / name) != expected:
            raise ValueError("Frozen summary-replay source/input changed: " + name)
    sys.path.insert(0, str(HERE / "frozen-strict"))
    from mis_population_evidence import verify_full_mis_summary_population
    from render_figure import render
    raw = gzip.decompress((HERE / "full-result-python.json.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest["uncompressed_original_result_sha256"]:
        raise ValueError("Original saved result bytes changed")
    data = json.loads(raw)
    original = next(item for item in json.loads((HERE / "frozen-strict/mis-communications/figures.json").read_bytes())
                    if item["id"] == "fig7")
    evidence = verify_full_mis_summary_population(data, original)
    assert evidence["checked_start_summaries"] == 12000
    negatives = []
    for mutation in ("hidden_cap", "missing_start", "duplicate_start", "missing_SMS",
                     "false_final_residual", "false_best_score", "false_bool_status",
                     "nonmaximum_selected", "wrong_plot_scalar", "floating_start_count",
                     "floating_settings_count", "relaxed_stored_tolerance",
                     "boolean_best_score", "nonselected_communication_metric_mismatch"):
        candidate = copy.deepcopy(data); run = candidate["points"][0]["result"]
        rows = run["all_start_summaries"]
        if mutation == "hidden_cap": rows[-1]["solver_status"]["inner_iteration_cap_exits"] = 1
        elif mutation == "missing_start": rows.pop()
        elif mutation == "duplicate_start": rows[-1]["start"] = 1
        elif mutation == "missing_SMS": del candidate["points"][0]["SMS"]
        elif mutation == "false_final_residual": rows[-1]["solver_status"]["final_inner_residual"] = 2 * rows[-1]["solver_status"]["final_inner_tolerance"]
        elif mutation == "false_best_score": run["best_feasible"]["score"] += 1
        elif mutation == "false_bool_status": rows[-1]["solver_status"]["convergence_verified"] = 1
        elif mutation == "nonmaximum_selected":
            other = next(row for row in rows if row["start"] != run["best_feasible"]["start"])
            other["score"] = other["min_binary_metric"] = run["best_feasible"]["score"] + 1
        elif mutation == "wrong_plot_scalar": run["best_feasible"]["metrics"]["min_binary_snr"] += 1
        elif mutation == "floating_start_count": run["number_of_starts"] = 6000.
        elif mutation == "floating_settings_count": candidate["settings"]["number_of_starts"] = 6000.
        elif mutation == "relaxed_stored_tolerance": rows[-1]["solver_status"].update(final_inner_tolerance=1., final_inner_residual=.01)
        elif mutation == "boolean_best_score": run["best_feasible"]["score"] = True
        else:
            other = next(row for row in rows if row["start"] != run["best_feasible"]["start"])
            other["score"] = other["min_binary_metric"] / 2
        try: verify_full_mis_summary_population(candidate, original)
        except ValueError as error: negatives.append(dict(mutation=mutation, rejected=True, message=str(error)))
        else: raise AssertionError("Corrupted summary accepted: " + mutation)
    with tempfile.TemporaryDirectory(prefix="mis-summary-replay-") as tmp:
        source = Path(tmp) / "full-result-python.json"; source.write_bytes(raw)
        bypass = copy.deepcopy(data); bypass["scope"] = "independent_simulation_curves"
        bad = Path(tmp) / "bypass.json"; bad.write_text(json.dumps(bypass), encoding="utf-8")
        try: render(bad, Path(tmp) / "forbidden")
        except ValueError as error: negatives.append(dict(mutation="MIS_generic_curve_scope_bypass", rejected=True, message=str(error)))
        else: raise AssertionError("MIS generic-scope bypass accepted")
        assert not (Path(tmp) / "forbidden").exists()
        result = render(source, args.output_dir / "plots")
    assert result["complete_start_summary_population_evidence"] == evidence
    assert result["patterns"] == 2 and result["angle_samples"] == 361
    for name, expected in manifest["files_sha256"].items():
        assert sha(HERE / name) == expected
    receipt = dict(scope="portable_saved_full12000_summary_and_renderer_replay_only",
                   packet_manifest_sha256=sha(HERE / "packet-files.json"),
                   original_uncompressed_result_sha256=hashlib.sha256(raw).hexdigest(),
                   checked_start_summaries=12000, all_summary_gates_passed=True,
                   negative_control_count=len(negatives), negative_controls=negatives,
                   complete_saved_bank_actually_rendered=True, summary_evidence=evidence,
                   frozen_packet_source_and_input_before_after_match=True,
                   fresh_optimizer_or_MC_or_native_MATLAB_executed=False,
                   independent_endpoint_gradients_or_physical_model_verified=False,
                   source_runtime_RNG_identity_verified=False,
                   original_figure_agreement_verified=False, full_reproduction_certified=False)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "actual-portable-replay.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("scope", "checked_start_summaries", "negative_control_count",
          "complete_saved_bank_actually_rendered", "full_reproduction_certified")}))


if __name__ == "__main__": main()
