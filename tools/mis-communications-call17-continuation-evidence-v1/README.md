# MIS communication: conditional continuation of one reconstructed start

This is the recorded continuation of Fig. 11 point 0, Python start 4869,
after the saved call 17 stopped with `block_line_search_exhausted_phi`. It
starts from the previously published **modified initial state**: a zero-step
binary64 retraction was applied to the saved phase vector, and one joint
step was computed. The prior failure was retained. The step's projected
gradient and returned state were recorded; its returned direction was not.
For this exact source and recorded branch, the direction `d = -g` was
**inferred** from the implementation; it was not directly observed. The
continuation is conditional on that inference and the reconstructed current
source. Historical source, full state, and all dependencies were not
reauthenticated. The saved run used NumPy 2.5.3; this run used 2.3.5.

The current implementation uses guarded per-block backtracking and an
additional joint-coupling Armijo check; those engineering choices must not
be attributed unconditionally to the authors' executable algorithm. The
4,000-iteration RCG cap, 1e-6 projected-KKT threshold, initial-mu range,
terminal mu and 6,000 starts are **implementation settings**; the
communication paper did not specify these values. The full cap was available
to each stage, not consumed when stopping early.

| Completed mu | Inner stopping reason | Projected KKT at stop |
|---|---|---:|
| 0.0118255615234375 | gradient_tolerance | 6.7578207491e-7 |
| 0.00591278076171875 | gradient_tolerance | 5.7936386314e-7 |
| 0.002956390380859375 | block_line_search_exhausted_phi | 2.4551652842e-6 |
| 0.0014781951904296875 | block_line_search_exhausted_phi | 4.8066706300e-6 |

At the first listed mu the imported boundary already contained the previously
recorded joint step; the continued events start at iteration 1. `gradient_tolerance`
means only that the current implementation's projected stopping measure met
its configured tolerance at those two stages. The final two stages failed
line search. The current implementation still advances mu after an inner
failure; that behavior does not certify convergence. Its returned final
relaxed and binary minimum-SNR quantities are both approximately 35.6240584411
under its reconstructed model; these values are not a paper-reference
agreement or a validated 6,000-start winner. Comparisons across all starts,
MATLAB verification, source provenance, full physics and reference agreement
remain open. No scientific or full-paper pass is asserted.

The 13 events contain the conditional starting boundary, each subsequent
completed RCG iteration, each mu-stage result, and the final stored metric.
The successful Windows Job terminal confirms one natural bounded run, with
130,547 output bytes before the final terminal record; the 1-second space
poll is not a hard filesystem quota. This resource result is not scientific
acceptance.
