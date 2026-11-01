# Complete preserved ISAC record audit

This tool replays the complete retained numerical records of one local legacy
MATLAB bundle. It preserves the unresolved source-version, model and record
discrepancies. It does not certify the final paper's optimized figures.

From the repository root, with Python 3.12:

```text
python -m pip install -r tools/isac-legacy-record-audit/requirements.txt
python -B tools/isac-legacy-record-audit/replay_full_evidence.py --output-dir <new-output-directory>
```

Use a new output directory for every run. On the maintained Windows host,
numerical outputs and caches belong under the configured E-drive data home.

The packet retains all 1,000 by 13 native-exported MAT ordinates and all 1,000
saved task descriptors, its separate 20-row original CSV, the complete 20 by 5
exponent grid, the complete 10 by 6 power grid including its zero row, and all
138 numeric variables in one actual saved initial state. No record is filtered
because it reaches a cap, exceeds a threshold, differs from another file, or
contains an otherwise unexplained zero outcome.

Fresh MP80 and MP100 evaluations reform all eleven full physical matrices,
7,940 real/imaginary matrix coordinates and 69 metric values per precision.
They compare every coordinate with the complete sealed local references and
compare all 772 actual saved field coordinates and 69 saved metrics with the
original initial state. Two exact first-user ray-pair geometry certificates
are recomputed. All 27 field, table, source-cohort, grid and transport controls
must be rejected.

The legacy state uses negative-cosine communication gains and unweighted
target steering, as explicitly retained in its historical script. Target
directions are independently reconstructed in MP from the exact saved grid
angles; the original per-cell binary64 intermediates were not saved. The
historical raw-MSE hinge objective differs from the final R1 scaled-NMSE
weighted utility. These legacy definitions remain separate from the unchanged
final-model reproduction campaigns.

The 49-member archive correspondence, four natural-exit-0 source readers and
three failed intake/host/control epochs are retained local provenance. Public
cold replay reads derived complete numeric primitives and references. It reads
zero original MAT files, zero full historical MATLAB source files, zero full
author/publisher manuscripts, and performs zero native MAT exports, original
optimizer calls, initializations, random draws or Monte Carlo runs. The
original source archive and complete manuscripts are not redistributed.

The saved MAT contains 200 seed labels, while the neighboring original CSV has
20 rows. All twenty matched-parameter CSV rows disagree with the MAT in at
least one metric beyond disclosed ASCII roundoff. The MAT retains 636 rows at
the saved source's 1,500-iteration cap and 296 rows above its 0.1 raw-MSE
threshold; these categories can overlap. Exact executed-source equivalence
and per-record original stationarity have not been recovered. Neither the
preserved `.m` driver nor its `.asv` counterpart matches the entire 1,000-task
cohort. The matching 20-row subset is not a replacement for that cohort.

The audit retains all 150 original figure/table-language tasks of the broader
project. Original model, physical mechanism, algorithm convergence, paired
languages, author-reference agreement and full six-paper completion remain
separate gates.

The tested runtimes are pinned to [NumPy 2.5.3](https://pypi.org/project/numpy/2.5.3/)
and [mpmath 1.4.1](https://pypi.org/project/mpmath/1.4.1/).
