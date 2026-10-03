"""Compare complete numerical outputs from actual MATLAB and Python executions."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compare(left, right, path, failures, atol, rtol):
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            failures.append(f"{path}: keys differ {set(left) ^ set(right)}")
            return
        for key in left:
            compare(left[key], right[key], f"{path}.{key}", failures, atol, rtol)
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            failures.append(f"{path}: lengths differ {len(left)} != {len(right)}")
            return
        for index, (a, b) in enumerate(zip(left, right)):
            compare(a, b, f"{path}[{index}]", failures, atol, rtol)
    elif isinstance(left, bool) or isinstance(right, bool):
        if type(left) is not type(right) or left != right:
            failures.append(f"{path}: boolean differs")
    elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if not math.isfinite(left) or not math.isfinite(right):
            failures.append(f"{path}: non-finite value")
        elif abs(left - right) > atol + rtol * max(abs(left), abs(right)):
            failures.append(f"{path}: {left:.15g} != {right:.15g}")
    elif left != right:
        failures.append(f"{path}: value/type differs")


def false_checks(value, path="checks"):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(false_checks(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(false_checks(item, f"{path}[{index}]"))
    elif isinstance(value, bool) and not value:
        found.append(f"{path}: validation false")
    elif isinstance(value, (int, float)) and not math.isfinite(value):
        found.append(f"{path}: non-finite check")
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", default="all")
    parser.add_argument("--python-dir", type=Path, default=ROOT / "outputs" / "python")
    parser.add_argument("--matlab-dir", type=Path, default=ROOT / "outputs" / "matlab")
    parser.add_argument("--atol", type=float, default=1e-7)
    parser.add_argument("--rtol", type=float, default=1e-6)
    parser.add_argument("--report", type=Path, default=ROOT / "outputs" / "parity.json")
    args = parser.parse_args()
    papers = json.loads((ROOT / "papers.json").read_text(encoding="utf-8"))
    papers = [p for p in papers if args.paper in ("all", p["id"])]
    if not papers:
        parser.error("Unknown paper id. See papers.json.")
    records = []
    for paper in papers:
        failures = []
        hashes = {}
        for label, directory in [("python", args.python_dir), ("matlab", args.matlab_dir)]:
            file = directory / (paper["id"] + ".json")
            if not file.is_file():
                failures.append(f"{label}: execution output missing")
                continue
            hashes[label] = hashlib.sha256(file.read_bytes()).hexdigest()
        if not failures:
            python = json.loads((args.python_dir / (paper["id"] + ".json")).read_text(encoding="utf-8-sig"))
            matlab = json.loads((args.matlab_dir / (paper["id"] + ".json")).read_text(encoding="utf-8-sig"))
            for label, output in [("python", python), ("matlab", matlab)]:
                if output.get("paper_id") != paper["id"]:
                    failures.append(f"{label}: paper_id mismatch")
                for key in ("metrics", "checks", "history"):
                    if key not in output:
                        failures.append(f"{label}: {key} missing")
                failures.extend(false_checks(output.get("checks", {}), label + ".checks"))
            compare(python, matlab, paper["id"], failures, args.atol, args.rtol)
        records.append({"paper_id": paper["id"], "passed": not failures,
                        "failures": failures, "output_sha256": hashes})
        print(paper["id"], "PASS" if not failures else "FAIL")
        for error in failures[:12]:
            print(" ", error)
    report = {"scope": "Shared-fixture numerical and core-check parity, not original-paper figure reproduction",
              "atol": args.atol, "rtol": args.rtol, "papers": records,
              "passed": all(item["passed"] for item in records)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
