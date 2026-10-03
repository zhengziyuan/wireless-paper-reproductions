# Distinct v5: same Euclidean tangent-cone projection, not a new solver

For a stored simplex row `x`, let `P = {j : x_j > 0}` and let `Z` contain its
exactly zero coordinates. The closed-simplex Euclidean tangent cone is

`C(x) = {d : sum_j d_j = 0, d_j >= 0 for j in Z}`.

The unique minimizer of `||d-y||^2 / 2` over this cone satisfies the exact KKT
equations `d_j = y_j - tau` for `j in P` and `d_j = max(y_j-tau,0)` for `j in Z`.
Its scalar row sum is continuous, strictly decreasing because `P` is nonempty,
and crosses zero exactly once. Sort the raw optional values in descending
order. For each finite optional prefix of length `k`, the unique candidate is

`tau_k = (sum_{j in P} y_j + sum_{first k of Z} y_j) / (|P| + k)`.

The valid interval is `y_k > tau_k >= y_{k+1}`, omitting nonexistent endpoints.
Checking at most `|Z|+1` sorted candidates finds the same projection; it does
not depend on repeated floating membership iteration stabilizing. Equal
optional values exactly at the threshold project to zero. No small positive
stored coordinate, or nonzero projected direction, is removed by a cutoff.

The old v4 floating membership loop alternated and threw an exception on a
fresh original-input start 377, outer 1, inner iteration 138 (zero-based).
The captured raw values have an exact, unique cone projection. This is our
implementation's numerical failure, **not evidence that the paper's Euclidean
projection equation is false**.

The v5 fast evaluation uses only the exact common-offset invariance of this
projection plus a sorted finite threshold. Roundoff-uncertain rows escalate to
exact **raw binary value** membership comparisons. Python uses `Fraction`.
MATLAB uses exact `BigDecimal(double)` numerators and scaled comparisons before
division; its returned components use 128-digit decimal division followed by
binary floating conversion. Tests include strict per-small-component bounds
on cross-scale counterexamples; the historical row-scale-only test would have
masked an earlier MATLAB helper order defect. The original defective helper
and its old limited receipts are preserved and are not used by v5 production.

All preexisting scientific code outside the declared cone function is verified
unchanged: Python AST equality and MATLAB newline-normalized source equality.
The original v4 settings/figure bytes, model, raw product PR, retraction,
initial eta/lambda/random state, Armijo/curvature checks, epsilon/multiplier/rho
updates, 4000-inner/30-outer budgets, and 6000-start population are unchanged.
The already disclosed corrected-product-RCG branch remains distinct from the
paper's printed separate-block update; v5 does not remove that distinction.

Actual evidence so far: Python and native MATLAB each pass all 1025 projection
cases and their own full cold start 377. Both complete all 30 actual inner
stops and independently pass the final original physical KKT/constraints at
Decimal60. They consume the same original Park-Miller state (before 790890689,
after 411326038, 881 draws) but reach different nonconvex local solutions:
Python eta 43.6907272, MATLAB eta 48.9905312. No bitwise/curve agreement or
global-optimality statement follows. No complete v5 6000-start bank is implied.

The old v4 379 saved results and all 36 capped/unverified starts remain. A new
versioned executor writes numerical exceptions as immutable failed-start
records and continues subsequent starts. An exception cannot enter an
incumbent, be counted as a completed full-budget solve, or generate a fabricated
6000-population mean. Finite 4000 iteration convergence is still not guaranteed.
