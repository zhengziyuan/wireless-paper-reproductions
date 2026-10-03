"""Portable frozen-evidence verifier / unchanged native Fig4 physical audit.

Full numerical replay requires the source-bound original input/native banks.
The fast publication verification does not rerun 59,813,000 channel samples.
"""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen():
    manifest = json.loads((HERE / "freeze-manifest.json").read_bytes())
    for name, expected in manifest["files_sha256"].items():
        assert sha(HERE / name) == expected, name
    report = json.loads((HERE / "independent-full200-physical-audit.json").read_bytes())
    assert report["full200_numeric_audit_passed"] and report["all_frozen_source_input_raw_oracle_entry_bytes_unchanged"]
    assert report["attempted"] == 200 and not report["failures"]
    by_case = {}
    with gzip.open(HERE / "every-position-independent-residuals.jsonl.gz", "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            assert row["sample_count"] == 1000 and all(row["checks"].values())
            case = row["case"]
            previous = by_case.get(case, 0)
            assert row["position_index"] == previous
            by_case[case] = previous + 1
    assert len(by_case) == 200
    assert sum(by_case.values()) == report["checked_positions_including_initial"]
    assert sum(by_case.values()) * 1000 == report["checked_sample_rates"]
    for row in report["records"]:
        assert by_case[row["case"]] == row["positions_including_initial"]
    print(json.dumps({"all_publication_hashes_and_all_position_residual_records_verified": True,
                      "cases": len(by_case), "positions_including_initial": sum(by_case.values()),
                      "retained_actual_checked_sample_rates": report["checked_sample_rates"],
                      "physical_channels_freshly_recomputed_by_this_fast_command": False,
                      "original_curve_closeness_verified": False}))


def execute_same_audit():
    path = HERE / "audit_full200_native_figure04_io_v2.py"
    assert sha(path) == "3c57022a312e8efc7286385b11c8077331479a790cfc663c604a77d024b22176"
    spec = importlib.util.spec_from_file_location("published_unchanged_IO_only_wrapper", path)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    # Repository asset-path adapter only. All assets have the same exact bytes
    # and expected hashes as the actual frozen WORK execution, not new maths.
    wrapper.v1.ORACLE_PATH = REPO / "strict/validation/two-timescale-ma-corrected-zf/audit_full200_matlab_v1.py"
    wrapper.v1.NATIVE_HELPER = HERE / "run_native_ma_figure04_from_completed03_work.m"
    wrapper.v1.PLAN_PATH = HERE / "FIGURE04_ALL200_INDEPENDENT_AUDIT_PLAN_V1.md"
    original_prepare = wrapper.v1.prepare

    def prepare_with_adapter_identity(*args):
        cfg, cases, files, frozen, count = original_prepare(*args)
        files["portable_repository_asset_path_adapter"] = Path(__file__)
        frozen["portable_repository_asset_path_adapter"] = sha(Path(__file__))
        return cfg, cases, files, frozen, count

    wrapper.v1.prepare = prepare_with_adapter_identity
    wrapper.v1.main()


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify-frozen"]:
        verify_frozen()
    else:
        execute_same_audit()
