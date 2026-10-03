"""Verify the checked-in component evidence against current source hashes.

This utility cannot promote a component test to full-figure reproduction.
Run both languages and compare their actual outputs before calling it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from validate_components import PAPERS, source_hashes

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-report", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "validation")
    args = parser.parse_args()
    py_report = read(args.python_report)
    failures = []
    records = []
    reported = {r["paper_id"]: r for r in py_report["records"]}
    if set(reported) != set(PAPERS):
        failures.append("Python execution report does not cover all six packages")
    for paper in PAPERS:
        execution = reported.get(paper, {})
        paths = {language: args.evidence_dir / "components" / f"{paper}-{language}.json"
                 for language in ("python", "matlab", "parity")}
        if not all(p.exists() for p in paths.values()):
            failures.append(f"{paper}: missing actual language/parity evidence")
            continue
        parity = read(paths["parity"])
        hashes = {language: sha(path) for language, path in paths.items()}
        current_hashes = source_hashes(ROOT / paper)
        if execution.get("component_checks_passed") is not True:
            failures.append(f"{paper}: Python component checks not passed")
        if execution.get("source_sha256") != current_hashes:
            failures.append(f"{paper}: source changed after recorded Python execution")
        if execution.get("output_sha256") != hashes["python"]:
            failures.append(f"{paper}: checked-in Python output is not the recorded execution")
        if parity.get("component_parity_passed") is not True:
            failures.append(f"{paper}: component parity failed")
        if parity.get("output_sha256") != {k: hashes[k] for k in ("python", "matlab")}:
            failures.append(f"{paper}: parity report does not bind these exact outputs")
        if parity.get("full_published_figure_reproduction_passed") is not False:
            failures.append(f"{paper}: component evidence incorrectly claims full reproduction")
        records.append({"paper_id": paper, "compared_sections": parity["compared_sections"],
                        "atol": parity["atol"], "rtol": parity["rtol"],
                        "evidence_sha256": hashes, "source_sha256": current_hashes})
    report = {
        "scope": "Actual mathematical components and dual-language comparisons only; NOT complete paper figures",
        "verification_timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "python_runtime": py_report["python_runtime"],
        "component_evidence_verified": not failures and len(records) == 6,
        "full_published_figure_reproduction_passed": False,
        "records": records, "failures": failures,
        "limitations": ["MATLAB and Python full experiment banks have not all converged/executed",
                        "Final publisher-version equivalence and original figure agreement remain unverified",
                        "Genuine source-formulation gaps remain explicit in package contracts"],
    }
    (args.evidence_dir / "summary.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("COMPONENT EVIDENCE VERIFIED" if report["component_evidence_verified"] else "EVIDENCE NOT VERIFIED")
    for failure in failures:
        print(failure)
    return 0 if report["component_evidence_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
