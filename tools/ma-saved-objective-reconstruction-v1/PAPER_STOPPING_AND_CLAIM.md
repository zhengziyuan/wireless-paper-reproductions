# MA-ZF stopping rule and optimality statement

The final IEEE version of [the paper](https://doi.org/10.1109/TCOMM.2025.3585515)
specifies in Algorithm 2 (printed p. 10565) a fractional-increase stopping
rule. Its Fig. 3/4 numerical discussion (printed p. 10566) gives a threshold
of 0.5 × 10⁻⁴. The saved Fig. 5 case-007/mc-000 uses that same threshold;
its last recorded fractional increase is approximately 4.90975 × 10⁻⁵.
The recorded stop therefore satisfies the saved configuration and the form
of the published rule. The original Fig. 5 threshold has not been independently
established.

On printed p. 10564 the paper appeals to nondecreasing objective values when
claiming convergence to a locally optimal solution. Monotonicity alone does
not establish that conclusion: maximize `f(x) = x` on `[0, 1]` and take
`x_k = 1/2 - 1/(k+2)` for `k >= 0`. The feasible objectives increase to
`1/2`, which is not a local maximizer. This exposes an insufficiency of the
stated justification; it does not rule out a stronger theorem for the actual
algorithm under additional verified assumptions.

For the same saved case, `verify_zf_feasible_improvement.py` checks a nearby
feasible point whose floating-point ZF statistical objective is approximately
0.00033353 bit/s/Hz higher. Its exact comparisons concern the stored binary64
geometry; its objective is not interval-certified. This single witness does
not establish a paper error in the stopping rule, a global optimality gap,
or full reproduction. Keep “stopping rule met” distinct from independently
verified stationarity or local optimality.
