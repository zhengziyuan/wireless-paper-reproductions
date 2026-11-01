#!/usr/bin/env python3
"""Assess saved MA case rates and reported powers; not a beamformer recomputation."""
import argparse
import json
import math
from fractions import Fraction
from pathlib import Path

NAMES=("MA-MRT","MA-ZF","FPA-MRT","FPA-ZF","FPA-OPT")

def number(x):
    if type(x) not in (float,int) or not math.isfinite(x):
        raise ValueError("finite numeric scalar required")
    return float(x)

def evaluate(data):
    if data["schema"] != "MA_FIG5_CASE7_SAVED_RATE_POWER_INPUT_V1":
        raise ValueError("wrong input schema")
    job=data["job"]
    if (job["figure"],job["point"],job["realization"],job["N"],job["M"]) != (5,30,0,6,5):
        raise ValueError("not this saved case")
    count=data["nlos_realizations_per_geometry"]
    if type(count) is not int or count != 1000:
        raise ValueError("published sample count not present")
    power=Fraction.from_float(number(job["power"]))
    tol=Fraction.from_float(number(data["verification_tolerance"]))
    if power <= 0 or tol < 0:
        raise ValueError("invalid power or verification tolerance")
    if set(data["schemes"]) != set(NAMES):
        raise ValueError("five saved schemes required")
    schemes={}
    for name in NAMES:
        source=data["schemes"][name]
        rates=[number(x) for x in source["sample_sum_rates"]]
        if len(rates)!=count:
            raise ValueError("missing saved samples")
        saved_mean=number(source["mean_sum_rate"])
        actual_mean=math.fsum(rates)/count
        mean_gap=abs(saved_mean-actual_mean)
        result={"samples":len(rates),"negative_saved_rate_count":sum(x<0 for x in rates),
                "mean_saved_rate":saved_mean,"mean_recomputed_from_saved_rates":actual_mean,
                "mean_absolute_gap":mean_gap,
                "mean_within_1e_minus_12_relative":mean_gap<=1e-12*max(1,abs(actual_mean))}
        if "powers" not in source:
            result["saved_power_status"]="not_saved"
        else:
            powers=[Fraction.from_float(number(x)) for x in source["powers"]]
            if len(powers)!=count:
                raise ValueError("incomplete saved powers")
            result.update({"saved_power_status":"checked",
                "strict_power_excess_count":sum(x>power for x in powers),
                "tolerance_power_excess_count":sum(x>power+tol for x in powers),
                "negative_saved_power_count":sum(x<0 for x in powers),
                "minimum_saved_power":float(min(powers)),"maximum_saved_power":float(max(powers))})
        if "nonconverged_samples" in source:
            x=source["nonconverged_samples"]
            if type(x) is not int or not 0<=x<=count: raise ValueError("invalid reported nonconvergence count")
            result["reported_nonconverged_samples"]=x
        schemes[name]=result
    return {"schema":"MA_FIG5_CASE7_SAVED_RATE_POWER_CHECK_V1","job":job,"schemes":schemes,
            "scope":"One saved Python job; compares stored rates and reported total beamformer powers only.",
            "limits":["No beamformer matrices, channels, or SINR are recomputed.",
                      "FPA powers and FPA per-sample histories are missing; their feasibility and convergence are not proven.",
                      "No MATLAB, reference agreement, complete figure, or paper acceptance."],
            "full_five_scheme_power_feasibility_proven":False,"full_figure_or_paper_pass":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("input",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    result=evaluate(json.loads(a.input.read_text(encoding="utf8")))
    with a.output.open("x",encoding="utf8",newline="\n") as f:json.dump(result,f,indent=2,allow_nan=False);f.write("\n")
if __name__=="__main__":main()
