# MIS sensing: fixed-state scheduling bound for saved start 4736

This note concerns **one saved MATLAB initialization** from the Figure 3
campaign: original start 4736. It is distinct from start 3072 selected for the
[existing 6,000-start saved-figure capsule](../../strict/validation/mis-sensing-fig3-5-6-saved6000-20261019-v1/README.md).
It does not change the saved outcome or establish a result for the full figure.

## Fixed-state bound

For the saved phases, let `Gamma[k,u]` be the stored estimate of the **linear**
SINR of target `k` at placement `u`. The implementation compares each target's
selected SINR against the same linear threshold `eta`. With one selected
placement per target, every schedule obeys

```
min_k Gamma[k, u(k)] <= min_k max_u Gamma[k,u].
```

This upper bound also holds if further constraints restrict the choice of
placements. It concerns the fixed saved phases only; it does not optimize the
phases. The stored estimate has 9 target rows and 25 placement columns.

Using exact rational comparisons of the serialized MP80 and MP100 estimates,
both give the same outcome below. Values shown are rounded for readability.
Targets and placements in this table are **one-based**.

| Target | Original placement | Original selected SINR | Row-max placement | Row maximum SINR |
|---:|---:|---:|---:|---:|
| 1 | 4 | 0.998606598746253 | 4 | 0.998606598746253 |
| 2 | 7 | 0.994143621469197 | 7 | 0.994143621469197 |
| 3 | 8 | 0.994146824060076 | 8 | 0.994146824060076 |
| 4 | 22 | 0.994140763983133 | 5 | 1.00493884035687 |
| 5 | 13 | 0.994617586881783 | 13 | 0.994617586881783 |
| 6 | 2 | 1.68065450520758 | 2 | 1.68065450520758 |
| 7 | 1 | 0.994142206606505 | 1 | 0.994142206606505 |
| 8 | 1 | 0.994142229164921 | 1 | 0.994142229164921 |
| 9 | 24 | 0.994185255843289 | 24 | 0.994185255843289 |

The saved `eta` is approximately **0.99414221682402415**. For the original
argmax-X schedule, the minimum selected SINR occurs at target 4, and
`eta - min selected SINR` is approximately **1.452840890698329e-6**. This
exceeds the original binary feasibility tolerance, approximately **1e-6**.
For the rowwise upper bound, the bottleneck is target 7 and `eta - upper`
is approximately **1.021751905895366e-8**. The bound is below eta for the
serialized estimates, although its shortfall is inside the stated tolerance.
Thus the alternative's tolerance-based pass should not be read as exact
same-eta feasibility. The prior diagnostic already recorded individual
shortfalls; this note makes their scheduling upper-bound consequence explicit.

## Reproduction and limits

The companion script compares the saved decimal estimates with exact rational
arithmetic; it does not rerun the optimizer, samples, or field model. The
minimal evidence file contains both complete 9-by-25 matrices and the saved
schedule, eta and tolerance. From the repository root, reproduce this check
with Python 3 (the report path must not already exist):

```sh
python tools/mis-sensing-evidence-v1/check_fixed_state_eta_schedule_bound_v1.py \
  strict/validation/mis-sensing-fixed-state-4736-bound-v1/saved-gamma.json \
  /path/to/new-report.json
```

The rounded table alone is not sufficient to reproduce the full row-max
comparison.

Agreement of MP80 and MP100 is not a certified forward-error interval. The
strict bound above is exact **for the serialized estimates**, not a proof that
the unrounded physical forward model has the same strict sign. The assumed
inverse-watt reference unit and the author's binary-recovery rule remain
unconfirmed. The result makes no claim about different phases, other starts,
full-figure convergence, agreement with the published curves, or a mathematical
error in the paper. Both the original failure and any alternative tolerance
result must remain separately reported.
