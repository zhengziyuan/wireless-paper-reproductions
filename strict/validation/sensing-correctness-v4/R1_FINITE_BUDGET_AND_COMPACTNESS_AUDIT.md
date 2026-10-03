# MIS sensing R1: finite budgets, compactness, and the initial stopping check

This is a source-specific audit, not a claim that the entire RALM/RCG theory is
invalid. It does not change the source-frozen numerical package or any running
bank. The audited author LaTeX is the R1 manuscript with SHA-256
`b0ac3782b11cdb7d2b0d1dfe581bfcfbe17c72c52f64aef3e55cd0bfce25592a`.
Line numbers below refer to that exact file, rather than a downloaded final PDF.

## 1. The printed RCG loop forces an initial iteration

Algorithm 1, line 578, tests `i = 0 OR gradient_norm >= epsilon_RCG`. Thus the
printed algorithm executes at least one update even if its supplied initial
point already meets the current inner accuracy. It is incorrect to describe
that printed loop as permitting an initial zero-update return.

The **corrected implementation** evaluates its declared physical projected-KKT
measure before an update and returns immediately when that measure is strictly
below the supplied tolerance (`mis-sensing/solver_erratum.py`, lines 110–113 in
the frozen v4 package). This is an explicit implementation erratum/safeguard,
not a literal transcription of line 578. It avoids attempting an unnecessary
line search from an already satisfactory point. It does not increase the
tolerance, declare a failed residual successful, or assert global optimality.
The closed-simplex projected-KKT measure is itself part of the disclosed
corrected boundary treatment; it should not be conflated with the printed
open-simplex row-mean gradient measure.

## 2. Inner accuracy is a condition, not a finite-budget guarantee

Algorithm 2, lines 613–615, requires each current augmented-Lagrangian
subproblem to be solved with its current `epsilon_RCG^(ell)`. The convergence
discussion at line 599 explicitly conditions its conclusion on the inner
solver returning approximate stationary points at those accuracies, together
with the other regularity assumptions.

Line 934 explicitly prescribes all three budgets:

- 30 outer iterations;
- at most 4000 inner RCG iterations per outer iteration;
- 6000 random initializations, selecting the best feasible result.

Neither that paragraph nor the cited conditional statement provides a uniform
theorem that every nonconvex initialization reaches each requested tolerance
within 4000 iterations. An actual cap with a residual above its current
tolerance is therefore a **missed inner accuracy**, not convergence. A smaller
objective change, a feasible later iterate, or a later original-problem KKT
check cannot retroactively verify that earlier inner call. The original cap is
retained; a longer diagnostic run is not an original-budget reproduction.

The geometric schedule uses a factor
`(1e-6 / 1e-3)^(1/30)`. Under the explicit zero-based outer indexing, the 30
calls use indices 0 through 29; the last used accuracy is approximately
`1.2589254117941667e-6`. The next scheduled accuracy is `1e-6`, but must not be
reported as the tolerance actually used by the last call. Completion of the
prescribed 30-call budget is distinct from the optional early-termination AND
condition in line 934. Neither type of termination, on its own, verifies the
inner residuals or the original constrained KKT conditions.

## 3. The declared full product is not compact

Lines 307–320 impose strictly positive simplex entries and declare the scalar
coordinate `eta` to range over the whole real line. Line 599 nevertheless
asserts that a compact product manifold holds in this setting. As stated,
that particular assumption is not satisfied:

1. Fix both phase arrays and a positive row-simplex scheduling matrix. The
   sequence with `eta_n = n` lies in the declared product and has no convergent
   subsequence. Equivalently, its projection onto the `eta` coordinate is the
   noncompact set of all real numbers.
2. Independently, for `U >= 2`, a row with first entry `1/n` and all remaining
   entries `(1 - 1/n)/(U - 1)` is strictly positive for `n >= 2`, but its limit
   has a zero first entry and is outside the open simplex. The open simplex is
   bounded but not closed and is not compact.

Unit circles are compact. Replacing the open simplex by its closed simplex
also gives a compact scheduling set, but its boundary is not the smooth open
multinomial manifold declared in the paper. At such a boundary, row-mean
tangent-space stationarity and feasible-cone/projected KKT stationarity need
not agree. The corrected implementation's closure, cone treatment, and
boundary line-search behavior are therefore disclosed separately, rather than
claimed to inherit a smooth-manifold theorem automatically.

## 4. A valid bounded-sublevel statement can be proved instead

This repair concerns the fixed inner subproblem; it is **not** a proof of the
entire outer method under all its changing parameters.

For the original SINR model, assume the same positive scalar noise, finite
nonnegative echo powers, unit-modulus steering coefficients and phase entries,
and a nonnegative row-simplex scheduling matrix. Each field is a sum of `M`
unit-modulus terms. Consequently its echo power is at most `beta_k M^4`, while
its full denominator, including every self-excluded interferer, is at least
the original noise. The scheduled target metrics `a_k` are therefore bounded
uniformly between zero and `B = max_k beta_k M^4 / noise`. This is a physical
bound, not an inferred processing gain or a fit to a reference curve.

For fixed finite multipliers `lambda` and fixed `rho > 0`, the inner objective
is

`L(eta, phases, X) = -eta + sum_k max(0, lambda_k + rho (eta-a_k))^2 / (2 rho) - sum_k lambda_k^2 / (2 rho)`.

As `eta -> -infinity`, all the active-square terms vanish uniformly over the
bounded `a_k`, leaving `-eta` plus a fixed constant; hence `L -> +infinity`.
As `eta -> +infinity`, all terms eventually become active uniformly and their
positive quadratic growth dominates `-eta`; again `L -> +infinity`. Thus an
inner sublevel `L <= C` bounds `eta` on both sides. With the **closed** simplex
and unit circles, continuity and these bounds make each fixed-inner sublevel
compact.

This establishes a usable fixed-inner boundedness fact without falsely calling
the full product compact. For the printed **open** simplex it bounds `eta` but
does not remove possible boundary accumulation. Nor does it, by itself,
establish a uniform outer sublevel bound, a constraint qualification, a
descent-angle condition for raw PR, smoothness at projected-face changes, or a
4000-step complexity guarantee. Those requirements remain separate.

## 5. Scope of a correct numerical claim

A source-bound result may report the exact physical scene, actual budgets,
initial input and numerical settings; each actual inner residual/exit; and an
independently verified original constrained-KKT certificate for its selected
state. These are different claims. A selected-state KKT certificate is local
stationarity, not a global optimum, not a certificate that all 6000 starts
converged, and not proof that the unpublished author normalization or every
reference figure has been recovered. Failed and unverified starts remain
visible in the bank.

The two demonstrated domain counterexamples and the finite-budget distinction
limit the particular assertions above. They do not refute properly qualified
RALM/RCG convergence results on suitable domains with their required line
search, inner accuracy, boundedness and constraint-qualification assumptions.
