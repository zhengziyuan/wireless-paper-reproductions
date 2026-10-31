"""Compare complete author MAT triplets to saved Fig. 5 EPS ordinates.

Fixed column-to-ordinal comparison only: no fitting, interpolation, scaling or
optimization. A negative result is scoped to the explicitly enumerated groups,
not a claim that the author's data or the original figure are unavailable.
"""
import argparse
import json
import math
import zipfile
from pathlib import Path

from check_cooperative_saved_fig4_triplicate_means import matrix, require

ENTRIES = ("plot_record0119.mat", "plot_record0120.mat")


def evaluate(archive_path, report_path):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schema") == "COOPERATIVE_FIG5_THESIS_EPS_96_REFERENCE_ORDINATES_V1":
        rows = report["rows"]
        require(len(rows) == 96 and all(r["figure"] == 5 for r in rows),
                "Expected 96 Fig. 5 reference ordinates")
    else:
        require(report["actual_point_count"] == 24 and report["actual_method_ordinates"] == 192,
                "Expected saved 24-point comparison report")
        rows = [r for r in report["rows"] if r["figure"] == 5]
    names = sorted({r["method"] for r in rows})
    require(len(names) == 8, "Expected eight Fig. 5 methods")
    references = {}
    for name in names:
        rr = sorted((r for r in rows if r["method"] == name),
                    key=lambda r: r["ordinal_one_based"])
        require([r["ordinal_one_based"] for r in rr] == list(range(1, 13)),
                "Expected exactly twelve ordered reference points")
        require(all(math.isfinite(r["original_mapped_y_linear_SINR"]) and
                    math.isfinite(r["EPS_full_y_ordinate_rounding_step"]) and
                    r["EPS_full_y_ordinate_rounding_step"] > 0 for r in rr),
                "Finite reference and positive ordinate step required")
        references[name] = rr
    candidates = []
    with zipfile.ZipFile(archive_path) as z:
        for entry in ENTRIES:
            entry_path = "test_varsigma_316/" + entry
            info = z.getinfo(entry_path)
            require(info.file_size <= 65536, "Bounded MAT entry")
            a = matrix(z.read(info))
            for sl in range(5):
                for first in range(0, 18, 3):
                    triples = [[a[first+r+18*c+360*sl] for r in range(3)]
                               for c in range(12)]
                    if any(not all(math.isfinite(x) and x != 0 for x in t)
                           for t in triples):
                        continue
                    means = [sum(t)/3 for t in triples]
                    comparisons = []
                    for name in names:
                        rr = references[name]
                        d = [abs(v-r["original_mapped_y_linear_SINR"])
                             for v, r in zip(means, rr)]
                        comparisons.append({
                            "method": name,
                            "within_half_step": sum(v <= r["EPS_full_y_ordinate_rounding_step"]/2
                                                    for v, r in zip(d, rr)),
                            "max_abs_difference": max(d),
                            "rms_difference": math.sqrt(sum(v*v for v in d)/12),
                        })
                    candidates.append({"mat_entry": entry, "slice_one_based": sl+1,
                                       "triplet_rows_one_based": [first+1,first+2,first+3],
                                       "comparisons": comparisons})
    total = sum(c["within_half_step"] for g in candidates for c in g["comparisons"])
    return {"schema":"COOPERATIVE_FIG5_COMPLETE_TRIPLET_FIXED_ORDINAL_CHECK_V1",
            "method_count":len(names), "points_per_method":12,
            "complete_triplet_candidates":len(candidates),
            "individual_ordinal_comparisons":len(candidates)*len(names)*12,
            "within_half_step":total, "candidates":candidates,
            "limits":["Only 2 MAT entries and groups of three consecutive rows, "
                       "one slice at a time, with all 36 values finite and nonzero.",
                       "No inference for excluded zero-containing groups, alternate "
                       "row groupings, averaging, figures, sources, or reference normalization.",
                       "EPS ordinates are the existing author-thesis vector reference, "
                       "not direct digitization of the final publisher PDF.",
                       "No optimizer, Monte Carlo, new input, curve fit, or figure/paper acceptance."]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--author-zip",type=Path,required=True)
    ap.add_argument("--saved-eps-report",type=Path,required=True,
                    help="Full saved comparison report or compact Fig. 5 reference JSON")
    ap.add_argument("--report",type=Path,required=True)
    a=ap.parse_args()
    result=evaluate(a.author_zip,a.saved_eps_report)
    with a.report.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
        f.write("\n")

if __name__ == "__main__":
    main()
