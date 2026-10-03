"""Compare actual full-grid MATLAB/Python beams; this is not original-figure agreement."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def compare(python_path, matlab_path):
    paths = {"python":Path(python_path), "matlab":Path(matlab_path)}
    data = {key:json.loads(path.read_text(encoding="utf-8-sig")) for key,path in paths.items()}
    first, second = data["python"], data["matlab"]
    for key in ("paper_id","figure","full_figure_execution_complete","overall_full_success"):
        if first.get(key) != second.get(key):
            raise ValueError(f"Mismatched full result {key}")
    if first.get("full_figure_execution_complete") is not True or len(first.get("points",[])) != 1 or len(second.get("points",[])) != 1:
        raise ValueError("Only a complete original nine-target figure is eligible")
    samples = [d["points"][0]["beampattern_samples"] for d in (first,second)]
    errors = {}
    def equal(a,b,key):
        a,b=np.asarray(a,float),np.asarray(b,float)
        if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError(f"Shape/finite mismatch {key}")
        errors[key] = float(np.max(np.abs(a-b)))
        if not np.allclose(a,b,atol=1e-9,rtol=1e-9):
            raise ValueError(f"Dual outputs disagree for {key}")
    for key in ("azimuth_deg","elevation_deg"):
        equal(samples[0][key],samples[1][key],key)
    if len(samples[0]["maps"]) != 9 or len(samples[1]["maps"]) != 9:
        raise ValueError("Missing original target panel")
    for j,(a,b) in enumerate(zip(samples[0]["maps"],samples[1]["maps"])):
        for key in ("target","pattern","normalized_gain","sinr","target_azimuth_deg","target_elevation_deg","target_metric"):
            equal(a[key],b[key],f"target{j+1}.{key}")
    return {"paper_id":first["paper_id"],"figure":first["figure"],
            "scope":"Actual independent MATLAB/Python full-grid beam comparison; NOT original figure agreement",
            "dual_full_grid_parity_passed":True,"atol":1e-9,"rtol":1e-9,"absolute_errors":errors,
            "output_sha256":{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()},
            "original_figure_reproduction_certified":False}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python",type=Path,required=True)
    parser.add_argument("--matlab",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=compare(args.python,args.matlab)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"dual_full_grid_parity_passed":True,"original_figure_reproduction_certified":False}))
