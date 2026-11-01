# Fixed-state MIS schedule candidates at the saved eta

This is an exact rational comparison of **serialized approximate** SINR
values from saved native Fig. 3 start 4736. It is not a recomputation of the
physical forward model or a certificate for its floating-point error.

For each target row `k` and position `j`, the criterion is the same saved
linear-SINR threshold `eta - Gamma[k,j] <= tolerance`. There is no additional
row normalization. The diagnostic's tolerance is serialized as a rounded
60-digit decimal (approximately `1e-6`), despite its `exact_binary64` field
label. This analysis checks both the literal serialized decimal and the
binary64 value recovered by rounding it; these are distinct rationals. The
recovered binary64 value is `0x1.0c6f7a0b5ed8dp-20`, and the serialized
decimal is smaller by `1/12800000000000000000000000000000000000000000000000000000000000000000`.
The candidate sets agree under both comparisons. A tolerance is not an
exact-feasibility claim.

In both the 80-digit and 100-digit serialized tables, each of the nine rows
has exactly one candidate under this criterion. In zero-based indexing, the
row-only candidate is `[3, 6, 7, 4, 12, 1, 0, 0, 23]`; the originally saved
argmax-X schedule is `[3, 6, 7, 21, 12, 1, 0, 0, 23]`. Only row 3 differs.
Without tolerance, row 6 has no candidate, so no row-only one-hot schedule
meets the saved eta exactly for these serialized values.

These are rowwise facts. They do not establish satisfaction of any additional
column, timing, motion, physical, or author-specific recovery constraints;
two rows select column 0. The original failed record is not replaced, and
passing a numerical tolerance does not mean exact feasibility or scientific
acceptance. The author's original binary recovery convention and the
physical-forward interval remain unverified.

Run with Python 3 and a **new** output path. The input below is the already
published compact saved table, not another copy of the original result:

```text
python -B check_fixed_state_unique_schedule_v1.py ../../strict/validation/mis-sensing-fixed-state-4736-bound-v1/saved-gamma.json /path/to/new-output.json
```
