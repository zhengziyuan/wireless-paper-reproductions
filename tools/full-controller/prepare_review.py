"""Actual STD-only source preparation; never invokes a scientific task."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import run_all_full as driver

HERE = Path(__file__).resolve().parent
SOURCES = ("run_all_full.py", "native_dispatch.py", "test_controller.py", "prepare_review.py", "README.md")


def source_hashes():
    return {name: driver.sha(HERE / name) for name in SOURCES}


def position_ast_sha(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    return hashlib.sha256(ast.dump(tree, include_attributes=True).encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-stem", required=True)
    args = parser.parse_args()
    if Path(args.output_stem).name != args.output_stem:
        raise ValueError("Fresh own directory filename stem only")
    repo = driver.repo_root(args.repo)
    before = source_hashes()
    inputs = driver.metadata_inputs(repo)
    original = repo / "strict/reproduce.py"
    original_bytes, original_ast = driver.sha(original), position_ast_sha(original)
    prior_modules = set(sys.modules)
    sys.argv = [str(HERE / "test_controller.py"), str(repo)]
    import test_controller
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_controller))
    added_scientific = sorted(name for name in set(sys.modules) - prior_modules if name.split(".")[0] in ("numpy", "scipy", "h5py", "mpmath", "cvxpy"))
    for name in SOURCES:
        if name.endswith(".py"):
            ast.parse((HERE / name).read_text(encoding="utf-8-sig"))
    plan = driver.make_plan(repo, HERE / "FUTURE-explicit-full150-campaign-not-created", sys.executable)
    after = source_hashes()
    metadata_after = driver.metadata_inputs(repo)
    success = result.wasSuccessful() and before == after and inputs == metadata_after and not added_scientific and driver.sha(original) == original_bytes and position_ast_sha(original) == original_ast
    receipt = {"schema": "all-paper-controller-actual-STD-source-controls-v1", "actual_utc": driver.utc(),
               "source_sha256_before": before, "source_sha256_after": after, "source_B_A": before == after,
               "metadata_sha256_before": inputs, "metadata_sha256_after": metadata_after, "metadata_B_A": inputs == metadata_after,
               "whole_original_reproduce_sha256_before": original_bytes, "whole_original_reproduce_sha256_after": driver.sha(original),
               "whole_original_reproduce_position_AST_sha256_before": original_ast,
               "whole_original_reproduce_position_AST_sha256_after": position_ast_sha(original),
               "actual_STD_tests_run": result.testsRun, "actual_failures": len(result.failures), "actual_errors": len(result.errors),
               "actual_STD_stdout": output.getvalue(), "new_scientific_modules": added_scientific,
               "metadata_artifact_count": 75, "metadata_dual_language_task_count": 150,
               "metadata_blocked_tasks": [task["id"] for task in plan["tasks"] if task["blockers"]],
               "controls_passed": success, "scientific_execution_performed": False,
               "paper_numeric_bank_decoded": False, "native_or_model_started": False,
               "scientific_reproduction_certified": False,
               "actual_plan_is_metadata_only_never_dispatched": True}
    receipt_path = HERE / (args.output_stem + "-STD-controls.json")
    plan_path = HERE / (args.output_stem + "-metadata-plan.json")
    driver.write_new(receipt_path, receipt)
    driver.write_new(plan_path, plan)
    packet = {"schema": "all-paper-controller-source-only-review-v1", "source_sha256": after,
              "actual_STD_receipt": str(receipt_path), "actual_STD_receipt_sha256": driver.sha(receipt_path),
              "metadata_plan": str(plan_path), "metadata_plan_sha256": driver.sha(plan_path),
              "actual_controls_passed": success, "publishable_source_candidates": list(SOURCES),
              "default_is_readonly_plan": True, "scientific_worker_or_bank_created": False,
              "actual_scientific_execution_or_launchplan": False, "scientific_reproduction_certified": False}
    packet_path = HERE / (args.output_stem + "-review-packet.json")
    driver.write_new(packet_path, packet)
    print(json.dumps({"packet": str(packet_path), "packet_sha256": driver.sha(packet_path), "receipt_sha256": driver.sha(receipt_path), "metadata_plan_sha256": driver.sha(plan_path), "success": success, "source_sha256": after}, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
