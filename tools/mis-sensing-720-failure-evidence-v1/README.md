# MIS sensing: saved fields for 720 non-passing starts

The saved assembly reports 6,000 starts, of which 5,280 have a true combined
flag and 720 have a false combined flag. These are saved flags, not independent
certificates of physical feasibility, convergence, or agreement with a figure.

The two small inputs here cover only those 720 IDs. The `recorded_695.json`
file contains a later targeted read of the 252 early and 443 late IDs: 695
reports read, zero read errors, about 1.19 MB read in total, with no traversal
of the other 5,305 reports. The separately retained `middle25_projection.json`
projects an earlier summary of 25 additional IDs and adds selected fields from
the saved start-2223 receipt. It does not reproduce the original optimizer.

Across the 720 saved records, **688 record at least one inner iteration-cap
exit**, **44 have a false saved final-KKT flag**, and **34 fail a binary
inequality derived from saved values and the saved tolerance**. These groups
overlap and must not be added. The 695-record file calculates its binary test
from saved binary64 values; the earlier 25-record summary uses its own saved
scalar comparison and reported field-error bound. Neither derived classification
is the author's verified original rounding rule or a new physical feasibility
test. Saved-state-check flags in the 695 subset are distinct from the original
combined flag, which was false for each selected ID.

In the 25-record subset, 24 record cap exits, including both final-KKT and
derived-binary failures. Start 2223 is the remaining no-cap case: its saved
receipt records one `inner_failure_exit` and `all_inner_tolerances_satisfied`
as false, despite a true final KKT flag. Other failure causes were not inferred;
in particular, a cap incidence is not a causal proof of the combined failure.

Historical report content was not freshly authenticated, and individually
held reads do not establish a whole-population atomic snapshot. The publisher's
final text and the author's exact binary selection/threshold implementation are
not established here. No original inputs, thresholds, iteration budgets, or
failed outcomes were changed. This is not a full-paper or 6,000-start pass.

From the repository root, run:

```text
python -I -S -B tools/mis-sensing-720-failure-evidence-v1/verify_saved_counts.py
```

This recomputes the counts from these small saved projections. It does not
reread historical reports or rerun the original experiment.
