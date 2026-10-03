"""Plot recorded reduced-fixture iteration metrics, not published paper curves."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "outputs" / "python")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "iteration-traces.png")
    args = parser.parse_args()
    papers = json.loads((ROOT / "papers.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), layout="constrained")
    for ax, paper in zip(axes.flat, papers):
        data = json.loads((args.input_dir / (paper["id"] + ".json")).read_text(encoding="utf-8-sig"))
        history = data["history"]
        preferred = {
            "mis-communications": ["softmin", "incumbent_minimum"],
            "mis-sensing": ["minimum_sinr", "incumbent_minimum_sinr"],
            "cooperative-satcom": ["phase_utility"],
        }.get(paper["id"], [])
        if isinstance(history, dict):
            series = {key: history[key] for key in preferred} if preferred else history
        elif isinstance(history, list) and history and isinstance(history[0], dict):
            names = preferred or [key for key in history[0]
                                  if key not in ("iteration", "outer_iteration", "step", "penalty", "gradient_norm")
                                  and isinstance(history[0][key], (float, int))][:2]
            series = {key: [row[key] for row in history] for key in names}
        else:
            series = {"recorded metric": history}
        for label, values in series.items():
            array = np.asarray(values, dtype=float)
            if array.ndim == 1 and len(array) > 1:
                ax.plot(np.arange(len(array)), array, label=label.replace("_", " "), linewidth=1.8)
        ax.set_title(paper["id"], fontsize=12)
        ax.set_xlabel("Recorded iteration / checkpoint")
        ax.set_ylabel({"mis-communications": "Worst-user SNR / soft minimum (linear)",
                       "mis-sensing": "Minimum-target SINR (linear)",
                       "rotatable-isac": "Sum rate minus weighted NMSE",
                       "two-timescale-ma": "Approx. MRT sum rate (bit/s/Hz)",
                       "cooperative-satcom": "Soft-min SINR minus residual penalty",
                       "hotspot-satcom": "RIS decorrelation criterion F"}[paper["id"]])
        ax.grid(alpha=0.25)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(fontsize=8, loc="best")
    fig.suptitle("Independent implementations · reduced-fixture iteration traces\nNot a reproduction of the published figure set", fontsize=15)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
