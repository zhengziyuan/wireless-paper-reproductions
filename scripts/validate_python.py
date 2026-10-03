"""Gate the reduced shared-fixture runs; passing does not certify paper figures."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect(value, path="output"):
    errors = []
    if isinstance(value, dict):
        for key, item in value.items():
            errors.extend(inspect(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for n, item in enumerate(value):
            errors.extend(inspect(item, f"{path}[{n}]"))
    elif isinstance(value, bool):
        if path.startswith("output.checks") and not value:
            errors.append(f"{path}: failed check")
    elif isinstance(value, (int, float)) and not math.isfinite(value):
        errors.append(f"{path}: non-finite number")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "python")
    args = parser.parse_args()
    failures = []
    for item in json.loads((ROOT / "papers.json").read_text(encoding="utf-8")):
        folder = ROOT / "papers" / item["id"]
        for file in ("run.py", item["matlab_entry"] + ".m", "fixture.json", "README.md", "source_map.json"):
            if not (folder / file).is_file():
                failures.append(f"{item['id']}: missing {file}")
        output_path = args.output_dir / (item["id"] + ".json")
        if not output_path.is_file():
            failures.append(f"{item['id']}: missing execution output")
            continue
        output = json.loads(output_path.read_text(encoding="utf-8-sig"))
        if output.get("paper_id") != item["id"]:
            failures.append(f"{item['id']}: wrong output paper_id")
        for field in ("metrics", "checks", "history"):
            if not output.get(field):
                failures.append(f"{item['id']}: empty or missing {field}")
        checks = output.get("checks", {})
        if not any(isinstance(value, bool) for value in checks.values()):
            failures.append(f"{item['id']}: no explicit pass/fail checks")
        failures.extend(f"{item['id']}: {error}" for error in inspect(output))
        print(item["id"], "output inspected")
    for error in failures:
        print(error)
    print("PASS" if not failures else "FAIL")
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
