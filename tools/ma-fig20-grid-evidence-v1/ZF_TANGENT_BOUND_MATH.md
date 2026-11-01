# Mathematical conditions for a ZF tangent bound

This note explains a possible bound for the **selected statistical ZF grid
objective**. It is not a verification of any saved pruning certificate. The
saved D3/g0 witnesses contain digests and tangent-point weights; their actual
upper values and the historical incumbents still require independent recovery
or recomputation.

Let the selected prefix be fixed. For each remaining grid point `j`, write
its Hermitian positive-semidefinite covariance contribution as `A_j`, and
let

```text
Σ(x) = Σ_prefix + sum_j x_j A_j,
0 <= x_j <= 1,    sum_j x_j = r.
```

Here `r` is the number of positions still to select. Assume every matrix in
the domain is Hermitian positive definite, and each fixed user coefficient
`eta_u` is nonnegative. The latter is the coefficient used in the ZF rate,
not the separate MIS sensing threshold also called eta elsewhere.

For user `u`, define `s_u(Σ) = 1 / (Σ⁻¹)_{uu}`. It is the Schur complement
of the other-user principal block. Equivalently,

```text
s_u(Σ) = min { z^H Σ z : z_u = 1 }.
```

For each admissible `z`, the expression is affine in `Σ`; the pointwise
minimum is concave. Since `log(1 + eta_u s)` is concave and nondecreasing
for nonnegative `eta_u` and positive `s`, the sum

```text
f(x) = sum_u log(1 + eta_u s_u(Σ(x)))
```

is concave. Natural logarithms are used here; maximizing this sum is
equivalent to maximizing the corresponding sum of base-2 rates.

At a feasible tangent point `x0`, its gradient component for point `j` is

```text
a_u = (Σ(x0)⁻¹)_{uu}
v_u = Σ(x0)⁻¹ e_u
g_j = sum_u [ eta_u / (1 + eta_u / a_u) ] * (v_u^H A_j v_u) / a_u^2.
```

Concavity then gives `f(x) <= f(x0) + g·(x - x0)`. Over the hypersimplex,
the maximum linear term is the sum of the `r` largest `g_j`. Thus, defining
`delta` as that maximum minus `g·x0`, every feasible completion satisfies

```text
product_u (1 + eta_u s_u(Σ(x))) <=
    product_u (1 + eta_u s_u(Σ(x0))) * exp(delta).
```

`delta >= 0` because `x0` itself is feasible. A separately certified upper
bound on `exp(delta)` can replace the exponential on the right. This bound
uses concavity of the **sum of logs**, not a claim that the product itself is
concave. It applies to a binary completion because binary selections are a
subset of the hypersimplex.

The saved [dyadic-weight check](D3_ZF_DYADIC_WEIGHTS.md) verifies only that
the 18 stored tangent points satisfy the hypersimplex constraints. It does
not check positive definiteness, the five-user gradient, an exponential
ceiling, the witness digest or an incumbent. Exact rational arithmetic on
serialized approximations also does not certify the physical input model,
the author's undisclosed search criterion, MATLAB, or the full figure.
