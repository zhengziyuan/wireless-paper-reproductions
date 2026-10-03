"""Render real stored beam samples; never synthesize a replacement numerical curve."""
import argparse, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser()
parser.add_argument("result",type=Path)
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
data=json.loads(args.result.read_text())
samples=data["points"][0]["beampattern_samples"]
az=np.array(samples["azimuth_deg"]);el=np.array(samples["elevation_deg"])
maps=samples["maps"]
args.output.mkdir(parents=True,exist_ok=True)
for panel in maps:
    fig,axes=plt.subplots(1,2,figsize=(9,3.8),constrained_layout=True)
    for ax,key,title in zip(axes,["normalized_gain","sinr"],["Normalized gain (dB)","Echo SINR (dB)"]):
        values=10*np.log10(np.maximum(np.array(panel[key]),1e-300))
        handle=ax.pcolormesh(az,el,np.maximum(values,-120),shading="auto",cmap="viridis")
        ax.set(xlabel="Azimuth (degrees)",ylabel="Elevation (degrees)",title=title)
        fig.colorbar(handle,ax=ax)
    fig.suptitle("Independent full-size result: target "+str(panel["target"]+1)+", pattern "+str(panel["pattern"]+1))
    fig.savefig(args.output/("target-"+str(panel["target"]+1)+".png"),dpi=150)
    plt.close(fig)

