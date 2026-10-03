"""Verify a published partial dual receipt; never promote it to full200."""
from pathlib import Path
import hashlib
import json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    manifest = json.loads((folder/"freeze-manifest.json").read_bytes())
    for name, digest in manifest["public_file_sha256"].items():
        assert sha(folder/name) == digest, ("changed public evidence", name)
    for name, digest in manifest["independent_oracle_sha256"].items():
        path = (folder/name).resolve()
        assert path.is_relative_to(folder.parent)
        assert sha(path) == digest, ("changed independent oracle", name)
    freeze = json.loads((folder/"predeclared-completion-snapshot-freeze.json").read_bytes())
    report = json.loads((folder/"partial-dual-completed-snapshot-v1.json").read_bytes())
    count = freeze["snapshot_record_count"]
    assert 0 < count < 200
    assert report["snapshot_count"] == report["attempted"] == report["validated"] == count
    assert report["validation_failures"] == 0 and not report["failures"]
    assert report["all_snapshot_independent_validation_gates_passed"]
    assert report["all_frozen_source_inputs_and_both_raw_outputs_unchanged_at_end"]
    assert not report["full200_dual_pass_claimed"] and not report["original_curve_closeness_claimed"]
    assert report["freeze_sha256"] == sha(folder/"predeclared-completion-snapshot-freeze.json")
    assert {Path(r["filename"]).stem for r in freeze["snapshot_records"]} == {r["case"] for r in report["records"]}
    for row in report["records"]:
        assert row["all_independent_validation_gates"]
        for language in ["python", "matlab"]:
            evidence = row["languages"][language]
            assert evidence["all_independent_physical_stop_and_coordinate_certificate_gates"]
            for history in evidence["histories"].values():
                assert history["actual_source_stop_verified"]
                assert history["actual_final_fractional_increase"] < history["source_fractional_threshold"] == 5e-5
            for scheme in evidence["schemes"].values():
                assert scheme["sample_count"] == 1000
                assert scheme["all_terminal_samples_independently_recomputed"]
                assert scheme["all1000_original_benchmark_stops_and_power_constraints_verified"]
        assert not row["differences"]["input_difference"]
        assert not row["differences"]["metric_evaluator_difference_above_independent_validation_gates"]
    print(json.dumps({"all_public_hashes_and_snapshot_bindings_passed": True,
                      "actual_audited_snapshot_cases": count, "expected_full_bank_cases": 200,
                      "both_languages_all_terminal1000_draws_checked": True,
                      "no_full200_dual_or_historical_graph_recovery_claim": True}, indent=2))


if __name__ == "__main__":
    main()
