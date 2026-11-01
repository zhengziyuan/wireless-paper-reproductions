# Cooperative paper Fig. 5: zero-inclusive triplet screen

This check extends the [previous complete-triplet screen](../../strict/validation/cooperative-author-working-U6-betaR1-dual-full8-20261019-v1/FIG5_COMPLETE_TRIPLETS_REFERENCE_SCREEN_20261030.md). It includes all fixed groups of three consecutive rows in the two author-supplied `plot_record0119.mat` and `plot_record0120.mat` files, even if one or more saved entries are zero. The author ZIP is not redistributed.

For each MAT file, the check examines five slices and six row groups, with twelve ordered columns each. It compares each three-value arithmetic mean to the corresponding ordinal of each of the eight retained Figure 5 thesis EPS curves, without fitting, scaling, interpolation, or reordering. One point matches if its absolute difference is no larger than half of that reference's vertical quantization step.

There are 60 groups: 21 have no zero among their 36 entries, and 39 contain at least one zero. The check performs 5,760 point comparisons; none is within half a reference step. The results for the 21 zero-free groups reproduce the previous screen's counts and RMS differences exactly. Including zeros in an arithmetic mean here is a testable convention, not a claim about the historical program or whether a zero signifies missing data.

From the repository root, with Python 3 and the author ZIP supplied separately, choose a fresh report path:

```sh
python -B tools/cooperative-fig5-all-triplets-v1/check_all_triplets.py \
  /path/to/test_varsigma_316.zip \
  strict/validation/cooperative-author-working-U6-betaR1-dual-full8-20261019-v1/fig5-thesis-eps-reference.json \
  /path/to/new-fig5-triplets-report.json
```

The reference consists of retained thesis EPS vector ordinates, not a fresh digitization of the final IEEE publisher figure. This negative screen does not exclude nonconsecutive groups, alternative averaging or weighting, different ordering, normalization, other files, or other source revisions. It neither reconstructs the historical plotting pipeline nor proves that Figure 5 or the paper fails. It runs no optimization and draws no random samples.
