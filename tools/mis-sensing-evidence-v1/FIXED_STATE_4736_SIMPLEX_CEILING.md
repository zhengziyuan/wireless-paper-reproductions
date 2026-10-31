# MIS sensing: fixed-phase bound for fractional and binary schedules

This note extends the [saved start 4736 binary scheduling comparison](FIXED_STATE_4736_ETA_BOUND.md). The fixed phases and finite serialized SINR estimates are unchanged; no model or optimization is rerun.

In the reproduced sensing constraints the same scalar `eta` is constrained by `eta <= sum_u X[k,u] * Gamma[k,u]` for every target `k`. The relaxed assignment has `X[k,u] >= 0` and `sum_u X[k,u] = 1` for each row. For any such row,

```text
sum_u X[k,u] Gamma[k,u] <= max_u Gamma[k,u].
```

Therefore any common feasible `eta` is bounded above by `min_k max_u Gamma[k,u]`. This applies to **all fractional row-simplex assignments**, including one-hot assignments. With only these independent row-simplex constraints, choosing each row's maximum attains the bound; any additional coupling constraints can only reduce it. The bound does not change the fixed phases.

For the saved approximate values of start 4736, exact rational comparisons show the upper bound is approximately `0.99414220660650509`, at target 7 (one-based), while the saved eta is approximately `0.99414221682402415`. Both the MP80 and MP100 serialized estimates give a positive shortfall of about `1.021751905895366e-8`: no fractional or binary row-simplex schedule can reach the saved eta **exactly for these stored estimates**. The shortfall is below the saved feasibility tolerance of approximately `1e-6`, so the tolerance-based result must remain separate from strict equality.

From the repository root, using Python 3 and a fresh output path:

```sh
python -B tools/mis-sensing-evidence-v1/check_fixed_state_simplex_ceiling_v1.py \
  strict/validation/mis-sensing-fixed-state-4736-bound-v1/saved-gamma.json \
  /path/to/new-simplex-bound-report.json
```

The precise arithmetic applies to the **serialized approximations**, not to an interval enclosing the physical forward model. The result does not establish strict physical infeasibility, exclude other phases or initializations, confirm author normalization or recovery rules, prove convergence, or validate the full figure or paper.
