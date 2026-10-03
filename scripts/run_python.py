"""Run independent per-paper implementations, without changing their fixtures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", default="all")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "python")
    args = parser.parse_args()
    papers = json.loads((ROOT / "papers.json").read_text(encoding="utf-8"))
    selected = [p for p in papers if args.paper in ("all", p["id"])]
    if not selected:
        parser.error("Unknown paper id. See papers.json.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for paper in selected:
        command = [sys.executable, str(ROOT / "papers" / paper["id"] / "run.py"),
                   "--output", str(args.output_dir.resolve() / (paper["id"] + ".json"))]
        subprocess.run(command, check=True, cwd=ROOT)
        print("Completed", paper["id"], flush=True)


if __name__ == "__main__":
    main()
