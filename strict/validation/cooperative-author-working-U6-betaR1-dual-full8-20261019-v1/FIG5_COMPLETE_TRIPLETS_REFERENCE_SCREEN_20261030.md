# Fig. 5: fixed-ordinal screen of complete saved triplets

This screen concerns the author-supplied `test_varsigma_316.zip` working
archive and the existing author-thesis EPS vector reference for Figure 5. It
complements a narrowly defined correspondence check; neither the archive's
production history nor the final publisher figure's provenance is established.
The supplied archive is not redistributed.

For each of `plot_record0119.mat` and `plot_record0120.mat`, the screen considers
all five array slices and the six consecutive three-row groups (rows 1–3,
4–6, ..., 16–18). A group is included only if each of its three stored values
is finite and nonzero in every one of the first 12 columns. For every included
group, the arithmetic mean of the three saved values in column `i` is compared
without fitting, interpolation, rescaling, or reordering to ordinal `i` on each
of eight Fig. 5 curves. A point matches only when its absolute difference is at
most half the corresponding EPS ordinate quantization step.

| MAT member | Included groups | Group-to-curve comparisons | Point comparisons | Points within half a step |
|:--|--:|--:|--:|--:|
| `plot_record0119.mat` | 12 | 96 | 1,152 | 0 |
| `plot_record0120.mat` | 9 | 72 | 864 | 0 |
| Total | 21 | 168 | 2,016 | 0 |

An independent MAT-v5 decoding and comparison implementation reproduced these
counts and each reported maximum and RMS difference. The closest RMS among the
168 tested pairings was approximately 0.669945 in the mapped linear-SINR
ordinates; this is a post-hoc descriptive minimum, not evidence of a
correspondence or a fitted match.

[The screen script](../../../tools/check_cooperative_saved_fig5_triplicate_candidates.py)
reads two members of the supplied author archive and either the full saved
native-24 comparison report or the [compact Fig. 5 reference](fig5-thesis-eps-reference.json).
The compact input contains the 96 retained EPS curve ordinates, their ordinal
indices, and their quantization steps. Both inputs produced byte-identical
reports for this check. The script reuses the MAT reader from the adjacent
[Fig. 4 comparison script](../../../tools/check_cooperative_saved_fig4_triplicate_means.py).
The author archive is not included. From the repository root, with an
independently supplied author ZIP and a report path that does not yet exist:

```sh
python tools/check_cooperative_saved_fig5_triplicate_candidates.py \
  --author-zip /path/to/test_varsigma_316.zip \
  --saved-eps-report strict/validation/cooperative-author-working-U6-betaR1-dual-full8-20261019-v1/fig5-thesis-eps-reference.json \
  --report /path/to/new-fig5-screen.json
```

The EPS ordinates are the retained thesis vector references, not a fresh
digitization of the publisher PDF. The screen runs no optimizer, Monte Carlo,
or channel generation and writes no copies of the original author files.

This negative finding excludes only the 21 included candidates under this
specific ordinal and mean rule. Groups containing zeros were excluded solely
to preserve the earlier complete-triplet criterion: a zero is a stored number,
not proof of missing, failed or invalid data. This check does not exclude other
row groupings, zero-inclusive averages, weighting, normalization, ordering,
source files, or historical versions. It does not determine the generation
procedure of the final publisher curves and establishes no full-figure or
full-paper pass or failure. The interference-axis unit issue documented in
[the Fig. 4/5 axis note](FIG4_FIG5_AXIS_AND_SAVED_MEANS_EVIDENCE_20261030.md)
also remains unresolved.
