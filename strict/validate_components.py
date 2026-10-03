"""Execute original-algorithm component checks, never full-figure validation.

The small iteration counts in a derivative/subproblem test are test controls,
not replacements for the separate production experiment budgets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAPERS = {
    "mis-communications": ("gradient_pass", "constraint_pass", "number_of_positions_correct"),
    "mis-sensing": ("gradient_pass", "pslr_gradient_pass", "constraint_pass", "number_of_positions_correct"),
    "rotatable-isac": ("gradient_pass", "QT_MM_non_decrease", "power_feasible", "finite"),
    "two-timescale-ma": ("gradient_pass", "spacing_feasible", "box_feasible", "finite"),
    "cooperative-satcom": ("qt_identity_pass", "physical_constraint_pass", "gaussian_limit_identity_pass", "finite_cascade_fourth_jensen_pass", "ap_qt_lower_bound_pass"),
    "hotspot-satcom": ("qt_identity_pass", "physical_constraint_pass", "sdr_psd_pass", "sdr_diagonal_pass", "rounding_unit_modulus_pass", "surrogate_bound_pass", "phase_gradient_pass", "phase_criterion_monotone"),
}


def nonfinite_paths(value, path="result"):
    if isinstance(value, dict):
        return [p for key, item in value.items() for p in nonfinite_paths(item, f"{path}.{key}")]
    if isinstance(value, list):
        return [p for i, item in enumerate(value) for p in nonfinite_paths(item, f"{path}[{i}]")]
    if isinstance(value, float) and not math.isfinite(value):
        return [path]
    return []


def source_hashes(folder):
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix in {".py", ".m", ".json", ".md"}]
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", choices=["all", *PAPERS], default="all")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "components")
    parser.add_argument("--timeout-seconds", type=float, default=600,
                        help="Per-component-test timeout, not a production scenario budget.")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for paper, required in PAPERS.items():
        if args.paper not in {"all", paper}:
            continue
        folder = ROOT / paper
        output = args.output_dir / f"{paper}.json"
        # Exercise the formal per-block line-search branch for MIS. The packages
        # retain their literal-printing diagnostic as a separate entry point.
        test_flag = "--guarded-component-test" if paper.startswith("mis-") else "--component-test"
        command = [sys.executable, str(folder / "run.py"), test_flag, "--output", str(output)]
        started = time.perf_counter()
        failures = []
        try:
            completed = subprocess.run(command, text=True, capture_output=True,
                                       timeout=args.timeout_seconds, encoding="utf-8", errors="replace")
            if completed.returncode:
                failures.append(f"Execution returned {completed.returncode}: {completed.stderr[-3000:]}")
            if not output.exists():
                failures.append("Execution output missing")
            elif not failures:
                result = json.loads(output.read_text(encoding="utf-8-sig"))
                checks = result.get("checks", {})
                for key in required:
                    if checks.get(key) is not True:
                        failures.append(f"{key} missing or false")
                failures.extend(f"Non-finite numerical value: {p}" for p in nonfinite_paths(result))
                if result.get("full_reproduction_pass") is True:
                    failures.append("Component test incorrectly claims full reproduction")
                if paper == "rotatable-isac":
                    for key, count in {"full_model_BS_count": 4, "full_model_RIS_count": 36, "full_model_sensing_grid": 66}.items():
                        if checks.get(key) != count:
                            failures.append(f"Full-size component {key} changed")
                if paper == "cooperative-satcom" and result.get("dimensions") != {"J": 3, "U": 2, "N": 16, "M": 25, "K": 1}:
                    failures.append("Satellite component dimensions changed")
                if paper == "hotspot-satcom" and result.get("dimensions") != {"N": 16, "U": 6, "K": 10, "M": 25}:
                    failures.append("Hotspot component dimensions changed")
        except (subprocess.TimeoutExpired, OSError, ValueError) as error:
            failures.append(str(error))
        record = {
            "paper_id": paper, "test_flag": test_flag, "component_checks_passed": not failures,
            "full_published_figure_reproduction_passed": False,
            "elapsed_seconds": time.perf_counter() - started, "failures": failures,
            "source_sha256": source_hashes(folder),
            "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None,
        }
        records.append(record)
        print(paper, "COMPONENT PASS" if not failures else "COMPONENT FAIL", flush=True)
        for failure in failures:
            print(failure, flush=True)
    report = {
        "scope": "Original-algorithm mathematical components only; NOT full-scenario or published-figure reproduction",
        "python_runtime": sys.version, "records": records,
        "component_checks_passed": bool(records) and all(r["component_checks_passed"] for r in records),
        "full_published_figure_reproduction_passed": False,
    }
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return 0 if report["component_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
