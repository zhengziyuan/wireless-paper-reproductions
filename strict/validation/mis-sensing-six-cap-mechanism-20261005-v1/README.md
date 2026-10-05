# Complete six-path sensing cap diagnosis

The six saved corrected-product-PR paths have now been processed completely,
with a genuine owned worker exit 0, no fatal exception, and unchanged declared
source/input/runtime bytes. This is a **closed trajectory diagnosis**, not a
successful complete Fig. 3 reproduction or a proof of why the caps occurred.
The findings and receipt identities are published here; the large private
recording/replay payload is not represented as a portable public replay.

All starts 4, 5, 6, 9, 11 and 13 retain their original 30 outer iterations and
all 1,538 real coordinates. The actual totals are 180 outer solves, 37,029
preupdates, 36,855 attempted steps and 138,125 line-search trials. All original
numerical histories, endpoint value bytes and failed statuses are preserved.
There are six `iteration_cap` and 174 `gradient_tolerance` inner terminations.
Each capped solve contains all 4,000 steps: 24,000 capped steps and 88,386
associated trials in total. No start or failed outer solve is dropped.

| Start / capped outer | Saved inner projected-KKT mapping | Required epsilon |
| --- | ---: | ---: |
| 4 / 1 | 0.002901511794803753 | 0.001 |
| 5 / 1 | 0.18765073484955233 | 0.001 |
| 6 / 18 | 0.00039642291597359 | 0.000019952623149688793 |
| 9 / 5 | 0.07104691633025542 | 0.00039810717055349724 |
| 11 / 15 | 0.00015012795575000782 | 0.00003981071705534972 |
| 13 / 1 | 0.0016388963178523108 | 0.001 |

These are the original solver's saved **ALM subproblem** stopping quantities,
not a new independent final-P2.1 KKT certificate. Every capped inner solve fails
its own epsilon. Later outer solves remain present; an early inner cap alone
does not imply that the final original-problem KKT condition fails.

The complete line-search count is exactly the attempted-step count (36,855).
The recorded state machine requires at least one search per step and a second
search for an exhausted-search retry. Thus these six paths contain no such
second-search retry. Their caps cannot simply be described as exhaustion of
the 60-trial line-search budget. This is consistency of the original captured
binary64 search records, not an independent trial-EG or curvature certificate.

## Direction observations and a diagnostic-label erratum

The observed maximum used-direction / projected-gradient norm ratios range
across the six capped solves from 41.63 to 2,756.40 for phi, 46.15 to 2,662.28
for theta, 1.215 to 3,341.93 for X, and 1,869.14 to 92,643.70 for eta. These
are point observations, not rigorous bounds or a proved cause of slow progress.

The frozen diagnostic field `descent_cosine_pg_point` is **misnamed in our
observer**: its actual numerator is minus the inner product of `g` and `d`,
while its denominator is `norm(pg) * norm(d)`. It is not the cosine formed
using `pg` in the numerator. Negative values or values below minus one must
not be used as a true projected-gradient angle argument. The original records
remain unchanged; this explicit erratum corrects their interpretation.

The implementation's joint descent guard uses zero minimum positive margin
and no direction-norm ratio cap. This does not establish uniform
gradient-related directions, but neither that fact nor large blockwise ratios
prove the causal origin of these six caps. A joint descent condition is not a
requirement that each individual block be descending.

## What remains unresolved

The recordings lack actual trial candidates and Euclidean gradients, some
Gamma/q/chi evaluation details, the exact NumPy guard-norm return, and
independent one-sided physical derivatives. The exact-Fraction support analysis
describes the unrounded analytical ray of the decoded floats, not the actual
rounded NumPy trial candidate. Hessian conditioning, an alternate-restart path,
and the printed blockwise-PR path were not computed by this diagnosis.

The corrected joint product-PR/closed-simplex path is not silently called the
printed independent-block PR algorithm. No algorithm, threshold, reported
4,000-step budget, winner, ordinate or old failure was changed. `cause_proved`,
complete 6,000-start/figure validation and literal-algorithm certification all
remain false. This diagnosis does not resolve the separate conditional
30.20 dB versus plotted 32.02 dB normalization discrepancy.

Closed receipt SHA256 identities:

```text
Genuine durable parent:
91200ea3246403dca1f56ea2aa398da28e94466004439044d6b4774238e41e84
Complete six-path diagnosis:
5db4cf56d797b27c4388dd9b85a4382dbcd00f0c6b05321ce45e19339ed65d8a
```
