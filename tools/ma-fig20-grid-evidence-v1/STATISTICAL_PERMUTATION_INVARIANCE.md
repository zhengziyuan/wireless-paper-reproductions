# Antenna permutation invariance of the selected statistical objectives

The D3/g0 checkpoint uses `paper_statistical_design_objective`, the explicitly
selected reconstruction in `strict/two-timescale-ma/brute_force.py`. The
following is an algebraic property of the mathematical objectives implemented
by `mrt_statistics` and `zf_statistics` in `strict/two-timescale-ma/core.py`.
It does not establish the original author's undisclosed search criterion.

Let the position matrix `T` contain one antenna position per row, and let
`P` be an arbitrary permutation matrix. The same system parameters are used
for every antenna row; user parameters remain attached to their users.

For MRT, each position-dependent term in a user denominator has the form

```text
| sum_n exp(i * wave * t_n · (direction_u - direction_v)) |^2.
```

Permuting the antenna rows changes only the order of summation. All other
terms depend on user parameters or the number of antennas, so the MRT
statistical objective is unchanged in exact arithmetic.

For ZF, the LOS matrix satisfies `H(P T) = P H(T)`. Therefore

```text
H(P T)^H H(P T) = H(T)^H P^H P H(T) = H(T)^H H(T).
```

The implemented statistical covariance, its inverse, and the resulting ZF
rates consequently remain unchanged wherever the formula is defined. The
box and pairwise-distance constraints are also unchanged by relabelling.
Thus, for these two ideal statistical objectives and the same feasible grid,
one unordered set represents all of its labelled permutations. Binary64
rounding can still change evaluated sums or ties. In the saved D3/g0 grid,
the 84 distinct six-point subsets therefore represent 84 × 6! = 60,480
labelled placements under this ideal statistical objective.

This argument does **not** prove the saved pruning bounds, that the remaining
leaves were evaluated, MATLAB/Python agreement, or the published figure. It
does not apply automatically to `instantaneous_MC`: permuting only the
positions while keeping an antenna-indexed finite NLoS bank fixed does not
generally permute the complete channel. The full stored sample bank would also
need a matching row permutation for the channel to be relabelled.
