# RCG direction and stopping notation in the IEEE early-access version

The 16-page IEEE Xplore author version of
[10.1109/JSTSP.2026.3693227](https://doi.org/10.1109/JSTSP.2026.3693227)
is marked accepted but not fully edited; the final typeset publication has not
been checked here. On its PDF p. 8, Eq. (58) defines the utility `F`, P3.1
minimizes `-F`, and Eq. (64) defines `Rgrad F` as the tangent projection of the
Euclidean gradient of `F`. Equation (66) instead starts its descent direction
with `-Rgrad F`; Algorithm 2 on p. 9 initializes the same direction. Unless
the notation is reinterpreted, moving in that direction decreases `F` locally,
whereas descending `-F` requires `+Rgrad F`. The independent script below
checks a simple smooth unit-circle example and the sign of the directional
derivative. This is a notation/algorithm inconsistency in the inspected early
version, not a claim about an official erratum, historical results, or final
typeset text.

Algorithm 2's displayed stop condition uses the Euclidean norm
`||grad F||/sqrt(N)`, while the implementation's `update_theta` uses the norm
of `Rgrad F` divided by `sqrt(N)`. These differ at a constrained stationary
point when the Euclidean gradient has a nonzero normal component. The code's
projected check is a mathematically meaningful constrained-stationarity
interpretation, but is not the literal displayed Euclidean stopping rule. The
single-coordinate example demonstrates the distinction; it does not certify
any saved run, optimizer convergence or paper figure.

Run `python -B demonstrate_rcg_notation.py`. It uses no project data, solver,
output files or random samples.
