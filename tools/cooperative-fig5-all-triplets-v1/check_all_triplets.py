"""Screen all retained contiguous Fig.5 triplets, including stored zero values.

Reads two small MAT entries in place.  This is a source-data/figure comparison,
not an optimizer run, original-reference certificate, or full-figure result.
"""
import argparse
import json
import math
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_cooperative_saved_fig4_triplicate_means import matrix, require


def run(archive, reference):
    obj = json.loads(reference.read_text(encoding="utf8"))
    require(obj.get("schema") == "COOPERATIVE_FIG5_THESIS_EPS_96_REFERENCE_ORDINATES_V1", "Unexpected reference")
    rows = obj["rows"]
    names = sorted({row["method"] for row in rows})
    require(len(rows) == 96 and len(names) == 8 and all(row["figure"] == 5 for row in rows), "Wrong Fig.5 reference size")
    refs = {}
    for name in names:
        sequence = sorted((row for row in rows if row["method"] == name), key=lambda r: r["ordinal_one_based"])
        require([r["ordinal_one_based"] for r in sequence] == list(range(1, 13)), "Reference order")
        require(all(math.isfinite(r["original_mapped_y_linear_SINR"]) and math.isfinite(r["EPS_full_y_ordinate_rounding_step"]) and r["EPS_full_y_ordinate_rounding_step"] > 0 for r in sequence), "Invalid reference")
        refs[name] = sequence
    groups = []
    with zipfile.ZipFile(archive) as z:
        for file_name in ("plot_record0119.mat", "plot_record0120.mat"):
            info = z.getinfo("test_varsigma_316/" + file_name)
            require(info.file_size <= 65536, "Oversized MAT entry")
            a = matrix(z.read(info))
            for sl in range(5):
                for first in range(0, 18, 3):
                    triples = [[a[first + r + 18*c + 360*sl] for r in range(3)] for c in range(12)]
                    require(all(math.isfinite(x) for t in triples for x in t), "Nonfinite saved value")
                    means = [sum(t)/3 for t in triples]
                    results = []
                    for name in names:
                        rr = refs[name]
                        diffs = [abs(x - r["original_mapped_y_linear_SINR"]) for x, r in zip(means, rr)]
                        hits = sum(v <= r["EPS_full_y_ordinate_rounding_step"] / 2 for v, r in zip(diffs, rr))
                        results.append({"method": name, "points_within_half_step": hits,
                                        "rms_difference": math.sqrt(sum(x*x for x in diffs)/12)})
                    groups.append({"mat_entry": file_name, "slice_one_based": sl+1,
                                   "rows_one_based": [first+1, first+2, first+3],
                                   "zero_value_count": sum(x == 0 for t in triples for x in t),
                                   "methods": results})
    require(len(groups) == 60, "Incomplete group enumeration")
    hits = sum(x["points_within_half_step"] for g in groups for x in g["methods"])
    return {"schema": "COOPERATIVE_FIG5_ALL_CONTIGUOUS_TRIPLETS_V1",
            "groups": len(groups), "zero_free_groups": sum(g["zero_value_count"] == 0 for g in groups),
            "zero_containing_groups": sum(g["zero_value_count"] > 0 for g in groups),
            "methods_per_group": len(names), "points_per_method": 12,
            "individual_ordinal_comparisons": len(groups)*len(names)*12,
            "points_within_half_step": hits, "group_results": groups,
            "scope": "Fixed ordinal arithmetic means of all 60 three-row groups and two retained MAT entries, including zero entries; against thesis EPS references only.",
            "limits": ["Does not establish how zero entries arose or whether they should enter the historical average.",
                       "Other groupings, weights, ordering, source files or historical versions are not excluded.",
                       "Thesis EPS is not a fresh digitization of publisher artwork.",
                       "No optimization, random samples, complete figure or paper pass/fail is implied."]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("author_zip", type=Path)
    parser.add_argument("eps_reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(args.author_zip, args.eps_reference)
    with args.output.open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")


if __name__ == "__main__":
    main()
