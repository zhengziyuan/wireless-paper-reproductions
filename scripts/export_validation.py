"""Export passing local evidence with fixture/code hashes, excluding private paths."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matlab-version", required=True, help="Version returned by the MATLAB runtime used")
    args = parser.parse_args()
    report = json.loads((ROOT / "outputs" / "parity.json").read_text(encoding="utf-8"))
    if not report.get("passed"):
        raise SystemExit("Refusing to export failed parity as a validated release")
    destination = ROOT / "validation"
    for language in ("python", "matlab"):
        (destination / language).mkdir(parents=True, exist_ok=True)
    packages = []
    for item in json.loads((ROOT / "papers.json").read_text(encoding="utf-8")):
        folder = ROOT / "papers" / item["id"]
        hashes = {file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                  for file in sorted(folder.rglob("*"))
                  if file.is_file() and file.suffix in (".py", ".m", ".json", ".md")}
        packages.append({"paper_id": item["id"], "sha256": hashes})
        for language in ("python", "matlab"):
            shutil.copyfile(ROOT / "outputs" / language / (item["id"] + ".json"),
                            destination / language / (item["id"] + ".json"))
    shutil.copyfile(ROOT / "outputs" / "parity.json", destination / "parity.json")
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "Core-model and reduced-fixture checks; not a full published-figure campaign",
                "runtimes": {"python": platform.python_version(), "numpy": np.__version__, "matlab": args.matlab_version},
                "packages": packages,
                "tooling_sha256": {file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                                   for folder in (ROOT / "scripts", ROOT / "tests")
                                   for file in sorted(folder.glob("*")) if file.suffix in (".py", ".m")}}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Exported passing evidence to validation/")


if __name__ == "__main__":
    main()
