"""Instrument ONE full-size/original-budget start; not a full figure run.

The observer calls the unchanged production RCG and records block safeguards.
Thread controls only affect the numerical runtime, not the published dimensions.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import time

# Set before importing NumPy; the output captures these controls explicitly.
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(name, "1")
import numpy as np
import engine
import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", default="fig3")
    parser.add_argument("--point", type=int, default=0)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--settings", type=Path, default=run.HERE / "settings.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text(encoding="utf-8"))
    figures = json.loads((run.HERE / "figures.json").read_text(encoding="utf-8"))
    figure = next(f for f in figures if f["id"] == args.figure)
    observations = []
    digest, manifest = run.implementation_digest()
    started = time.perf_counter()
    original_rcg = engine.rcg

    def observe(z, evaluate, options):
        begin = time.perf_counter()
        out, history, stop = original_rcg(z, evaluate, options)
        rg = engine.project(out, evaluate(out)[1])
        reasons = Counter()
        inactive = Counter()
        block_steps = {b: [] for b in z}
        for item in history:
            for block, values in item.get("block_restart_reasons", {}).items():
                reasons.update(block + ":" + v for v in values)
            inactive.update(b for b, value in item.get("inactive_projected_blocks", {}).items() if value)
            for block, value in item.get("block_step_sizes", {}).items():
                block_steps[block].append(value)
        observation = {
            "outer_call": len(observations) + 1,
            "elapsed_seconds": time.perf_counter() - begin,
            "inner_iterations": len(history), "stop": stop,
            "eta": float(out["eta"]),
            "maximum_q": float(np.max(evaluate(out)[2]["q"])),
            "block_gradient_norms": {b: float(np.linalg.norm(g)) for b, g in rg.items()},
            "restart_counts_by_block_and_reason": dict(reasons),
            "inactive_block_counts": dict(inactive),
            "coupling_backtracks_total": sum(v.get("coupling_backtracks", 0) for v in history),
            "block_step_ranges": {b: [min(v), max(v)] for b, v in block_steps.items() if v},
        }
        observations.append(observation)
        run.atomic_json(args.output.with_suffix(".progress.json"), {
            "scope": "single_full_budget_start_in_progress_not_full_figure",
            "implementation_digest_at_start": digest, "settings": settings,
            "observations": observations,
        })
        print(json.dumps(observation), flush=True)
        return out, history, stop

    engine.rcg = observe
    try:
        result = run.diagnostic_start(figure, settings, args.start, args.point)
    finally:
        engine.rcg = original_rcg
    # Preserve the full state and every outer update; store reduced diagnostics
    # instead of hundreds of thousands of redundant inner JSON rows.
    history = result.pop("history")
    groups = [history] if figure["objective"] != "pslr" else [stage["outer"] for stage in history]
    result["outer_summary"] = [
        {k: v for k, v in entry.items() if k != "inner"}
        for group in groups for entry in group
    ]
    result["observations"] = observations
    result["elapsed_seconds"] = time.perf_counter() - started
    result["implementation_digest_at_start"] = digest
    result["implementation_manifest_at_start"] = manifest
    result["source_changed_during_execution"] = digest != result["implementation_digest"]
    result["diagnostic_observer_changes_optimizer"] = False
    result["full_6000_start_figure_completed"] = False
    run.atomic_json(args.output, result)
    print(json.dumps({k: result[k] for k in ("elapsed_seconds", "metrics", "solver_status")}), flush=True)


if __name__ == "__main__":
    main()
