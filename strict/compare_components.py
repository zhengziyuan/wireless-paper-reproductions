"""Compare actual dual-language component outputs, not published figures.

MATLAB serializes a singleton struct array as an object. Only named trajectory
collections are normalized to lists. Scientific values are never replaced.
Convex backends can return different nonunique optimizers; their objectives and
physical residuals, not an arbitrary coordinate vector, are compared there.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def compare(a, b, path, failures, atol, rtol):
    if path.rsplit(".", 1)[-1] in {"QCQP", "restarts", "BB"}:
        if isinstance(a, dict):
            a = [a]
        if isinstance(b, dict):
            b = [b]
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                failures.append(f"{path}.{key}: missing in one language")
            else:
                compare(a[key], b[key], f"{path}.{key}", failures, atol, rtol)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            failures.append(f"{path}: lengths differ {len(a)} != {len(b)}")
        for i, (aa, bb) in enumerate(zip(a, b)):
            compare(aa, bb, f"{path}[{i}]", failures, atol, rtol)
    elif isinstance(a, bool) or isinstance(b, bool):
        if type(a) is not type(b) or a != b:
            failures.append(f"{path}: boolean differs")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not math.isfinite(a) or not math.isfinite(b):
            failures.append(f"{path}: nonfinite")
        elif abs(a - b) > atol + rtol * max(abs(a), abs(b)):
            failures.append(f"{path}: {a:.15g} != {b:.15g}")
    elif a != b:
        failures.append(f"{path}: value differs")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--paper", required=True)
    parser.add_argument("--sections", nargs="+", default=["metrics", "checks", "history", "state"])
    parser.add_argument("--atol", type=float, default=1e-7)
    parser.add_argument("--rtol", type=float, default=1e-6)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    py_path = args.directory / (args.paper + "-python.json")
    mat_path = args.directory / (args.paper + "-matlab.json")
    py = json.loads(py_path.read_text(encoding="utf-8-sig"))
    mat = json.loads(mat_path.read_text(encoding="utf-8-sig"))
    failures = []
    for section in args.sections:
        if section not in py or section not in mat:
            failures.append(f"{section}: output missing")
        else:
            compare(py[section], mat[section], section, failures, args.atol, args.rtol)
    report = {
        "paper_id": args.paper, "scope": "Actual component-output comparison only; NOT full published-figure reproduction",
        "compared_sections": args.sections, "atol": args.atol, "rtol": args.rtol,
        "component_parity_passed": not failures, "full_published_figure_reproduction_passed": False,
        "output_sha256": {"python": sha(py_path), "matlab": sha(mat_path)}, "failures": failures,
        "schema_adapter": "Singleton MATLAB struct collections QCQP/restarts/BB normalized to lists only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
